import hashlib
import struct
from dataclasses import dataclass
from typing import Optional, BinaryIO
import io

HASH_SIZE = 32

class Hash(bytes):
    """32-byte hash type with string representation"""
    def __new__(cls, data):
        if isinstance(data, bytes) and len(data) == HASH_SIZE:
            return super().__new__(cls, data)
        raise ValueError("Hash must be 32 bytes")
        
    def __str__(self) -> str:
        """Returns hex string of byte-reversed hash"""
        reversed_hash = bytes(reversed(self))
        return reversed_hash.hex()

@dataclass
class LeafData:
    """
    All data that goes into a leaf in the utreexo accumulator.
    Contains enough data to verify Bitcoin signatures.
    """
    block_hash: bytes = bytes(HASH_SIZE)  # 32 bytes
    tx_hash: Hash = Hash(bytes(HASH_SIZE))
    index: int = 0  # uint32, txout index
    height: int = 0  # int32
    coinbase: bool = False
    amt: int = 0  # int64
    pk_script: bytes = b""

    def to_string(self) -> str:
        """Convert LeafData to detailed string representation"""
        parts = [
            self.op_string(),
            f"h {self.height}",
            f"cb {self.coinbase}",
            f"amt {self.amt}",
            f"pks {self.pk_script.hex()}",
            f"{self.leaf_hash().hex()}",
            f"size {self.serialize_size()}"
        ]
        return " ".join(parts)

    def op_string(self) -> str:
        """Get outpoint string representation"""
        return f"{self.tx_hash}:{self.index}"

    def serialize(self, w: BinaryIO) -> None:
        """Write LeafData to binary stream"""
        # Combine height and coinbase into single int32
        hcb = self.height << 1
        if self.coinbase:
            hcb |= 1

        # Write fields
        w.write(self.block_hash)
        w.write(self.tx_hash)
        w.write(struct.pack(">I", self.index))
        w.write(struct.pack(">i", hcb))
        w.write(struct.pack(">q", self.amt))
        
        if len(self.pk_script) > 10000:
            raise ValueError("pksize too long")
            
        w.write(struct.pack(">H", len(self.pk_script)))
        w.write(self.pk_script)

    def serialize_size(self) -> int:
        """Get serialized size in bytes"""
        # 32B blockhash + 32B txhash + 4B index + 4B height/coinbase + 
        # 8B amount + 2B pkscript_len + pkscript
        return 82 + len(self.pk_script)

    def deserialize(self, r: BinaryIO) -> None:
        """Read LeafData from binary stream"""
        self.block_hash = r.read(HASH_SIZE)
        self.tx_hash = Hash(r.read(HASH_SIZE))
        self.index = struct.unpack(">I", r.read(4))[0]
        
        # Read combined height/coinbase
        hcb = struct.unpack(">i", r.read(4))[0]
        self.amt = struct.unpack(">q", r.read(8))[0]
        
        # Read pkscript
        pk_size = struct.unpack(">H", r.read(2))[0]
        if pk_size > 10000:
            raise ValueError(
                f"bh {self.block_hash.hex()} op {self.op_string()} "
                f"pksize {pk_size} bytes too long"
            )
            
        self.pk_script = r.read(pk_size)
        
        # Extract height and coinbase
        self.coinbase = bool(hcb & 1)
        self.height = hcb >> 1

    def leaf_hash(self) -> bytes:
        """Calculate leaf hash using SHA512/256"""
        buf = io.BytesIO()
        self.serialize(buf)
        return hashlib.sha512(buf.getvalue()).digest()[:HASH_SIZE] 
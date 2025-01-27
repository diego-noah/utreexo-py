import struct
import io
from dataclasses import dataclass, field
from typing import List, BinaryIO, Optional

from accumulator import BatchProof, Forest, Hash
from .btcacc import LeafData


@dataclass
class UData:
    """
    UData contains the block height, accumulator proof, spent TXO data,
    and TXO time-to-live values
    """

    height: int = 0  # int32
    acc_proof: BatchProof = field(default_factory=BatchProof)
    stxos: List[LeafData] = field(default_factory=list)
    txo_ttls: List[int] = field(default_factory=list)  # List[int32]

    def proof_sanity(self, nl: int, h: int) -> bool:
        """
        Check consistency of uData: verify UTXOs are proven in the batch proof
        """
        if len(self.acc_proof.targets) != len(self.stxos):
            print(
                f"Verify failed: {len(self.acc_proof.targets)} targets but "
                f"{len(self.stxos)} leafdatas"
            )

        return True

    def serialize(self, w: BinaryIO) -> None:
        """
        Serialize UData to binary stream.
        Format:
        - height (4 bytes)
        - num TTLs (4 bytes)
        - TTL values (4 bytes each)
        - batch proof
        - LeafData entries
        """
        # Write height and number of TTLs
        w.write(struct.pack(">i", self.height))
        w.write(struct.pack(">I", len(self.txo_ttls)))

        # Write TTL values
        for ttl in self.txo_ttls:
            w.write(struct.pack(">i", ttl))

        # Write batch proof
        self.acc_proof.serialize(w)

        # Write leaf data
        for ld in self.stxos:
            ld.serialize(w)

    def serialize_size(self) -> int:
        """Calculate serialized size in bytes"""
        # Calculate leaf data size
        ld_size = sum(ld.serialize_size() for ld in self.stxos)

        # Get proof size
        buf = io.BytesIO()
        self.acc_proof.serialize(buf)
        proof_size = len(buf.getvalue())

        if buf.tell() != self.acc_proof.serialize_size():
            print(
                f" buf.tell() {buf.tell()}, "
                f"AccProof.serialize_size() {self.acc_proof.serialize_size()}"
            )

        # 8 bytes for height & numTTLs + 4 bytes per TTL + proof size + leaf sizes
        return 8 + (4 * len(self.txo_ttls)) + proof_size + ld_size

    def deserialize(self, r: BinaryIO) -> None:
        """Read UData from binary stream"""
        try:
            # Read height
            self.height = struct.unpack(">i", r.read(4))[0]

            # Read number of TTLs
            num_ttls = struct.unpack(">I", r.read(4))[0]

            # Read TTL values
            self.txo_ttls = []
            for _ in range(num_ttls):
                ttl = struct.unpack(">i", r.read(4))[0]
                self.txo_ttls.append(ttl)

            # Read batch proof
            self.acc_proof = BatchProof()
            self.acc_proof.deserialize(r)

            # Read leaf data
            self.stxos = []
            for _ in range(len(self.acc_proof.targets)):
                ld = LeafData()
                ld.deserialize(r)
                self.stxos.append(ld)

        except Exception as e:
            raise ValueError(f"UData deserialize error: {str(e)}")

    def to_compact_bytes(self) -> bytes:
        """Convert to compact byte format
        Compact format:
        - height (4 bytes)
        - num_stxos (4 bytes)
        - stxos (variable length)
        - proof data (variable length)
        """
        buf = io.BytesIO()

        # Write height and number of STXOs
        buf.write(struct.pack(">i", self.height))
        buf.write(struct.pack(">I", len(self.stxos)))

        # Write STXO data
        for stxo in self.stxos:
            stxo.serialize(buf)

        # Write proof data
        self.acc_proof.serialize(buf)

        return buf.getvalue()

    @staticmethod
    def from_compact_bytes(b: bytes) -> "UData":
        """Create UData from compact byte format"""
        buf = io.BytesIO(b)
        udata = UData()

        try:
            # Read height and number of STXOs
            udata.height = struct.unpack(">i", buf.read(4))[0]
            num_stxos = struct.unpack(">I", buf.read(4))[0]

            # Read STXO data
            udata.stxos = []
            for _ in range(num_stxos):
                ld = LeafData()
                ld.deserialize(buf)
                udata.stxos.append(ld)

            # Read proof data
            udata.acc_proof = BatchProof()
            udata.acc_proof.deserialize(buf)

            # Verify consistency
            if len(udata.acc_proof.targets) != num_stxos:
                raise ValueError(
                    f"Inconsistent data: {len(udata.acc_proof.targets)} targets "
                    f"but {num_stxos} STXOs"
                )

            return udata

        except Exception as e:
            raise ValueError(f"Error deserializing compact UData: {str(e)}")

    @staticmethod
    def gen_udata(del_leaves: List[LeafData], forest: Forest, height: int) -> "UData":
        """
        Generate block proof by calling forest.prove_batch with leaf indexes
        to get batched inclusion proof from accumulator.
        """
        ud = UData(height=height, stxos=del_leaves)

        # Create hashes from leaf data
        del_hashes = [ld.leaf_hash() for ld in ud.stxos]

        # Generate block proof
        try:
            ud.acc_proof = forest.prove_batch(del_hashes)
        except Exception as e:
            raise ValueError(
                f"genUData failed at block {height} {forest.stats()} {str(e)}"
            )

        if len(ud.acc_proof.targets) != len(del_leaves):
            raise ValueError(
                f"genUData {len(ud.acc_proof.targets)} targets but "
                f"{len(del_leaves)} leafData"
            )

        return ud

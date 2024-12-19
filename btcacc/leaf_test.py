import io
import struct

class LeafData:
    def __init__(self, tx_hash, index, height, coinbase, amt, pk_script):
        self.tx_hash = tx_hash  # List of bytes (hash)
        self.index = index  # Integer
        self.height = height  # Integer
        self.coinbase = coinbase  # Boolean
        self.amt = amt  # Integer
        self.pk_script = pk_script  # List of bytes

    def serialize(self, writer):
        """Serializes the object into the writer (io.BytesIO)."""
        writer.write(bytes(self.tx_hash))
        writer.write(struct.pack('<I', self.index))  # Unsigned int (4 bytes)
        writer.write(struct.pack('<I', self.height))  # Unsigned int (4 bytes)
        writer.write(struct.pack('<?', self.coinbase))  # Boolean (1 byte)
        writer.write(struct.pack('<Q', self.amt))  # Unsigned long long (8 bytes)
        writer.write(struct.pack('<I', len(self.pk_script)))  # Script length
        writer.write(bytes(self.pk_script))

    @classmethod
    def deserialize(cls, reader):
        """Deserializes the object from the reader (io.BytesIO)."""
        tx_hash = list(reader.read(4))  # Read 4 bytes for tx_hash
        index = struct.unpack('<I', reader.read(4))[0]
        height = struct.unpack('<I', reader.read(4))[0]
        coinbase = struct.unpack('<?', reader.read(1))[0]
        amt = struct.unpack('<Q', reader.read(8))[0]
        script_len = struct.unpack('<I', reader.read(4))[0]
        pk_script = list(reader.read(script_len))
        return cls(tx_hash, index, height, coinbase, amt, pk_script)

    def __eq__(self, other):
        """Equality check for testing."""
        return (
            self.tx_hash == other.tx_hash and
            self.index == other.index and
            self.height == other.height and
            self.coinbase == other.coinbase and
            self.amt == other.amt and
            self.pk_script == other.pk_script
        )

if __name__ == "__main__":
    original = LeafData(
        tx_hash=[1, 2, 3, 4],
        index=0,
        height=2,
        coinbase=False,
        amt=3000,
        pk_script=[1, 2, 3, 4, 5, 6]
    )

    writer = io.BytesIO()
    original.serialize(writer)
    before_bytes = writer.getvalue()

    writer.seek(0)
    deserialized = LeafData.deserialize(writer)

    after_writer = io.BytesIO()
    deserialized.serialize(after_writer)
    after_bytes = after_writer.getvalue()

    assert before_bytes == after_bytes, (
        f"Serialize/Deserialize LeafData failed:\n"
        f"Before bytes len: {len(before_bytes)}\nAfter bytes len: {len(after_bytes)}"
    )
    print("Test passed: Serialize and Deserialize work correctly.")


import unittest
import io
from your_module import Hash, LeafData

class TestHash(unittest.TestCase):
    def test_valid_hash_creation(self):
        valid_data = b'\x00' * 32
        h = Hash(valid_data)
        self.assertEqual(len(h), 32)
        self.assertEqual(str(h), "0" * 64)

    def test_invalid_hash_length(self):
        with self.assertRaises(ValueError):
            Hash(b'\x00' * 31)  # Too short

        with self.assertRaises(ValueError):
            Hash(b'\x00' * 33)  # Too long

    def test_hash_string_representation(self):
        data = bytes(range(32))
        h = Hash(data)
        reversed_hex = bytes(reversed(data)).hex()
        self.assertEqual(str(h), reversed_hex)

class TestLeafData(unittest.TestCase):
    def setUp(self):
        self.leaf_data = LeafData(
            block_hash=b'\x01' * 32,
            tx_hash=Hash(b'\x02' * 32),
            index=1,
            height=100,
            coinbase=True,
            amt=5000,
            pk_script=b'\x03' * 20,
        )

    def test_op_string(self):
        self.assertEqual(self.leaf_data.op_string(), f"{self.leaf_data.tx_hash}:1")

    def test_to_string(self):
        result = self.leaf_data.to_string()
        self.assertIn("h 100", result)
        self.assertIn("cb True", result)
        self.assertIn("amt 5000", result)
        self.assertIn("pks 0303030303030303030303030303030303030303", result)

    def test_leaf_hash(self):
        leaf_hash = self.leaf_data.leaf_hash()
        self.assertEqual(len(leaf_hash), 32)

    def test_serialize_and_deserialize(self):
        buffer = io.BytesIO()
        self.leaf_data.serialize(buffer)

        serialized_data = buffer.getvalue()
        self.assertEqual(len(serialized_data), self.leaf_data.serialize_size())

        new_leaf_data = LeafData()
        buffer.seek(0)
        new_leaf_data.deserialize(buffer)

        self.assertEqual(new_leaf_data.block_hash, self.leaf_data.block_hash)
        self.assertEqual(new_leaf_data.tx_hash, self.leaf_data.tx_hash)
        self.assertEqual(new_leaf_data.index, self.leaf_data.index)
        self.assertEqual(new_leaf_data.height, self.leaf_data.height)
        self.assertEqual(new_leaf_data.coinbase, self.leaf_data.coinbase)
        self.assertEqual(new_leaf_data.amt, self.leaf_data.amt)
        self.assertEqual(new_leaf_data.pk_script, self.leaf_data.pk_script)

    def test_serialize_size(self):
        self.assertEqual(self.leaf_data.serialize_size(), 82 + len(self.leaf_data.pk_script))

    def test_pk_script_too_long(self):
        self.leaf_data.pk_script = b'\x04' * 10001  # Exceed the limit
        with self.assertRaises(ValueError):
            buffer = io.BytesIO()
            self.leaf_data.serialize(buffer)

    def test_invalid_deserialize_pk_script_size(self):
        invalid_data = io.BytesIO(b'\x01' * 82 + struct.pack(">H", 10001) + b'\x04' * 10001)
        with self.assertRaises(ValueError):
            self.leaf_data.deserialize(invalid_data)

if __name__ == '__main__':
    unittest.main()

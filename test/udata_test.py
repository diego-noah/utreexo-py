import unittest
import io
from unittest.mock import MagicMock
from your_module.udata import UData
from accumulator import BatchProof, LeafData

class TestUData(unittest.TestCase):
    def setUp(self):
        self.mock_batch_proof = MagicMock(spec=BatchProof)
        self.mock_batch_proof.targets = [0, 1]
        self.mock_batch_proof.serialize = MagicMock()
        self.mock_batch_proof.deserialize = MagicMock()
        self.mock_batch_proof.serialize_size = MagicMock(return_value=10)

        self.mock_leaf_data = MagicMock(spec=LeafData)
        self.mock_leaf_data.serialize = MagicMock()
        self.mock_leaf_data.deserialize = MagicMock()
        self.mock_leaf_data.serialize_size = MagicMock(return_value=20)
        self.mock_leaf_data.leaf_hash = MagicMock(return_value=b"hash")

        self.udata = UData(
            height=42,
            acc_proof=self.mock_batch_proof,
            stxos=[self.mock_leaf_data, self.mock_leaf_data],
            txo_ttls=[100, 200]
        )

    def test_proof_sanity(self):
        self.assertTrue(self.udata.proof_sanity(0, 0))

    def test_serialize_and_deserialize(self):
        buf = io.BytesIO()

        self.udata.serialize(buf)
        serialized_data = buf.getvalue()

        self.mock_batch_proof.serialize.assert_called_once()
        self.assertEqual(self.mock_leaf_data.serialize.call_count, 2)

        buf.seek(0)
        new_udata = UData()
        new_udata.deserialize(buf)

        self.assertEqual(new_udata.height, self.udata.height)
        self.assertEqual(new_udata.txo_ttls, self.udata.txo_ttls)

        self.mock_batch_proof.deserialize.assert_called_once()
        self.assertEqual(len(new_udata.stxos), 2)
        self.assertEqual(self.mock_leaf_data.deserialize.call_count, 2)

    def test_serialize_size(self):
        size = self.udata.serialize_size()
        expected_size = 8 + (4 * len(self.udata.txo_ttls)) + 10 + (2 * 20)
        self.assertEqual(size, expected_size)

    def test_deserialize_invalid_data(self):
        buf = io.BytesIO(b"\x00\x00\x00\x2A\x00\x00\x00\x02\x00\x00")
        with self.assertRaises(ValueError):
            self.udata.deserialize(buf)

    def test_gen_udata(self):
        mock_forest = MagicMock()
        mock_forest.prove_batch = MagicMock(return_value=self.mock_batch_proof)
        mock_forest.stats = MagicMock(return_value="mock stats")

        del_leaves = [self.mock_leaf_data, self.mock_leaf_data]
        height = 100

        result = UData.gen_udata(del_leaves, mock_forest, height)

        self.assertEqual(result.height, height)
        self.assertEqual(result.stxos, del_leaves)
        self.assertEqual(result.acc_proof, self.mock_batch_proof)
        mock_forest.prove_batch.assert_called_once_with([b"hash", b"hash"])

    def test_gen_udata_proof_mismatch(self):
        mock_forest = MagicMock()
        mock_forest.prove_batch = MagicMock(return_value=self.mock_batch_proof)

        del_leaves = [self.mock_leaf_data]
        with self.assertRaises(ValueError):
            UData.gen_udata(del_leaves, mock_forest, 100)

    def test_to_compact_bytes(self):
        compact_bytes = self.udata.to_compact_bytes()
        self.assertIsInstance(compact_bytes, bytes)
        self.assertGreater(len(compact_bytes), 0)

    def test_from_compact_bytes(self):
        compact_bytes = self.udata.to_compact_bytes()
        new_udata = UData.from_compact_bytes(compact_bytes)
        
        self.assertEqual(new_udata.height, self.udata.height)
        self.assertEqual(len(new_udata.stxos), len(self.udata.stxos))
        self.assertEqual(new_udata.acc_proof.targets, self.udata.acc_proof.targets)

    def test_from_compact_bytes_invalid_data(self):
        with self.assertRaises(ValueError):
            UData.from_compact_bytes(b"\x00\x00\x00")

    def test_serialize_empty_data(self):
        empty_udata = UData()
        buf = io.BytesIO()
        empty_udata.serialize(buf)
        self.assertGreater(len(buf.getvalue()), 0)

    def test_deserialize_empty_data(self):
        empty_udata = UData()
        buf = io.BytesIO()
        empty_udata.serialize(buf)
        buf.seek(0)
        new_udata = UData()
        new_udata.deserialize(buf)
        self.assertEqual(new_udata.height, empty_udata.height)
        self.assertEqual(len(new_udata.stxos), len(empty_udata.stxos))
        self.assertEqual(new_udata.acc_proof.targets, empty_udata.acc_proof.targets)

    def test_proof_sanity_invalid(self):
        self.udata.acc_proof.targets = [0, 1, 2]
        self.assertFalse(self.udata.proof_sanity(0, 0))

    def test_serialize_size_with_no_stxos(self):
        empty_udata = UData()
        size = empty_udata.serialize_size()
        self.assertEqual(size, 8)

    def test_serialize_and_deserialize_with_multiple_ttls(self):
        self.udata.txo_ttls = [100, 200, 300]
        buf = io.BytesIO()
        self.udata.serialize(buf)
        buf.seek(0)
        new_udata = UData()
        new_udata.deserialize(buf)
        self.assertEqual(new_udata.txo_ttls, self.udata.txo_ttls)

    def test_gen_udata_with_empty_forest(self):
        mock_forest = MagicMock()
        mock_forest.prove_batch = MagicMock(return_value=BatchProof())
        with self.assertRaises(ValueError):
            UData.gen_udata([], mock_forest, 100)

if __name__ == "__main__":
    unittest.main()

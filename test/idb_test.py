import unittest
from unittest.mock import MagicMock, patch
from csn_module import Csn, Config, Block, OutPoint, LeafData

class TestCsn(unittest.TestCase):
    def setUp(self):
        self.csn = Csn()
        self.csn.pollard = MagicMock()
        self.csn.pollard.stats = MagicMock(return_value="Pollard stats")

    def test_ibd_thread_stops_on_queue_empty(self):
        """Test that the IBD thread stops when the queue is empty."""
        self.csn.put_block_in_pollard = MagicMock()
        self.csn.scan_block = MagicMock()
        
        cfg = Config(quit_after=1)
        sig_chan = []
        self.csn.ibd_thread(cfg, sig_chan)
        
        self.assertIn(True, sig_chan)

    def test_scan_block_utxo_loss(self):
        """Test the scan_block method handles UTXO loss correctly."""
        mock_block = MagicMock(spec=Block)
        mock_tx = MagicMock()
        mock_tx.msg_tx.tx_in = [MagicMock(previous_out_point="outpoint1")]
        mock_block.transactions = [mock_tx]

        self.csn.utxo_store["outpoint1"] = LeafData(tx_hash="hash1", index=0, amt=100)

        self.csn.scan_block(mock_block)
        
        self.assertNotIn("outpoint1", self.csn.utxo_store)
        self.assertEqual(self.csn.total_score, 0)

    def test_scan_block_utxo_gain(self):
        """Test the scan_block method handles UTXO gain correctly."""
        mock_block = MagicMock(spec=Block)
        mock_tx = MagicMock()
        mock_tx.hash.return_value = "txhash"
        mock_tx.msg_tx.tx_out = [
            MagicMock(pk_script=b"\x00" * 2 + b"\x01" * 20, value=50),
            MagicMock(pk_script=b"\x00" * 2 + b"\x02" * 20, value=70),
        ]
        mock_block.transactions = [mock_tx]

        self.csn.watch_addrs = {b"\x01" * 20}
        self.csn.scan_block(mock_block)
        
        self.assertEqual(len(self.csn.utxo_store), 1)
        self.assertEqual(self.csn.total_score, 50)

    def test_put_block_in_pollard_handles_error(self):
        """Test put_block_in_pollard raises an error when proof_sanity fails."""
        mock_ub = MagicMock()
        mock_ub.proof_sanity.return_value = "Error in proof"

        with self.assertRaises(Exception):
            self.csn.put_block_in_pollard(mock_ub, 0, 0, 0)

    def test_register_out_point_called_correctly(self):
        """Test register_out_point is called with the correct parameters."""
        self.csn.register_out_point = MagicMock()
        out_point = OutPoint(hash="somehash", index=1)

        self.csn.register_out_point(out_point)

        self.csn.register_out_point.assert_called_with(out_point)

if __name__ == "__main__":
    unittest.main()

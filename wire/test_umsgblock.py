import unittest
from unittest.mock import Mock, patch
import io
from queue import Queue

from btcd.wire import MsgBlock, TxOut, OutPoint
from btcd.btcutil import Block
from btcd.chaincfg import MainNetParams
from btcd.chaincfg.chainhash import Hash

from wire.umsgblock import UBlock, ublock_network_reader
from btcacc import UData, LeafData
from accumulator import Leaf


class TestUBlock(unittest.TestCase):
    def setUp(self):
        # Create mock block and utreexo data
        self.mock_block = Mock(spec=Block)
        self.mock_block.transactions = [Mock(), Mock()]  # Coinbase + 1 transaction
        self.mock_block.transactions[0].hash.return_value = b"coinbase_tx_hash"
        self.mock_block.transactions[1].hash.return_value = b"regular_tx_hash"

        # Mock transaction outputs
        mock_txout = Mock(spec=TxOut)
        mock_txout.value = 50000000
        mock_txout.pk_script = b"mock_script"
        self.mock_block.transactions[0].msg_tx.tx_out = [mock_txout]
        self.mock_block.transactions[1].msg_tx.tx_out = [mock_txout]

        # Create UData
        self.utreexo_data = UData()
        self.utreexo_data.height = 100
        self.utreexo_data.stxos = []

        # Create UBlock
        self.ublock = UBlock(self.utreexo_data, self.mock_block)

    def test_block_to_add_leaves(self):
        """Test converting block outputs to leaves"""
        remember = [True, False]
        skiplist = []
        height = 100
        out_count = 2

        leaves = UBlock.block_to_add_leaves(
            self.mock_block, remember, skiplist, height, out_count
        )

        self.assertEqual(len(leaves), 2)
        self.assertTrue(isinstance(leaves[0], Leaf))
        self.assertTrue(leaves[0].remember)
        self.assertFalse(leaves[1].remember)

    def test_to_utxo_view(self):
        """Test converting UData to UtxoViewpoint"""
        # Add a mock STXO
        leaf_data = LeafData()
        leaf_data.tx_hash = b"test_hash"
        leaf_data.index = 0
        leaf_data.height = 100
        leaf_data.coinbase = True
        leaf_data.amt = 50000000
        leaf_data.pk_script = b"test_script"
        self.utreexo_data.stxos.append(leaf_data)

        view = self.ublock.to_utxo_view()

        # Check that the view contains our STXO
        op = OutPoint(hash=Hash(b"test_hash"), index=0)
        entry = view.entries[op]
        self.assertEqual(entry.height, 100)
        self.assertEqual(entry.coinbase, True)
        self.assertEqual(entry.txo.value, 50000000)
        self.assertEqual(entry.txo.pk_script, b"test_script")

    def test_check_block(self):
        """Test block validation"""
        params = MainNetParams
        outskip = []

        # Mock necessary methods for validation
        self.mock_block.transactions[1].check_transaction_inputs.return_value = True
        self.mock_block.transactions[1].validate_transaction_scripts.return_value = True

        result = self.ublock.check_block(outskip, params)
        self.assertTrue(result)

    def test_serialization(self):
        """Test UBlock serialization and deserialization"""
        # Mock serialization methods
        self.mock_block.msg_block.serialize.return_value = None
        self.mock_block.msg_block.serialize_size.return_value = 100

        # Test serialize_size
        size = self.ublock.serialize_size()
        self.assertEqual(size, 100 + self.utreexo_data.serialize_size())

        # Test serialization
        buffer = io.BytesIO()
        self.ublock.serialize(buffer)

        # Verify that serialize was called on both components
        self.mock_block.msg_block.serialize.assert_called_once()

    @patch("socket.create_connection")
    def test_ublock_network_reader(self, mock_create_connection):
        """Test network reader functionality"""
        # Setup
        block_chan = Queue()
        remote_server = "localhost:8333"
        cur_height = 100
        lookahead = 10

        # Mock socket
        mock_socket = Mock()
        mock_create_connection.return_value = mock_socket

        # Mock socket receiving data
        mock_socket.recv.side_effect = Exception("Test connection closed")

        # Test connection error handling
        with self.assertRaises(Exception):
            ublock_network_reader(block_chan, remote_server, cur_height, lookahead)

        # Verify socket was closed
        mock_socket.close.assert_called_once()

        # Verify None was put in channel to signal end
        self.assertIsNone(block_chan.get_nowait())


if __name__ == "__main__":
    unittest.main()

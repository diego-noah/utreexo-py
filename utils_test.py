import unittest
from collections import defaultdict
from typing import List, Tuple

class TestHash(unittest.TestCase):

    def test_valid_hash_initialization(self):
        valid_hash = bytes([0] * 32)
        self.assertIsInstance(Hash(valid_hash), Hash)

    def test_invalid_hash_initialization(self):
        invalid_hash = bytes([0] * 31)  # Only 31 bytes
        with self.assertRaises(ValueError):
            Hash(invalid_hash)

    def test_gen_hash_for_net(self):
        mainnet_params = ChainParams("mainnet")
        self.assertEqual(gen_hash_for_net(mainnet_params), main_net_gen_hash)

        testnet3_params = ChainParams("testnet3")
        self.assertEqual(gen_hash_for_net(testnet3_params), test_net3_gen_hash)

        regtest_params = ChainParams("regtest")
        self.assertEqual(gen_hash_for_net(regtest_params), reg_test_gen_hash)

        signet_params = ChainParams("signet")
        self.assertEqual(gen_hash_for_net(signet_params), sig_net_gen_hash)

        unknown_params = ChainParams("unknown")
        with self.assertRaises(ValueError):
            gen_hash_for_net(unknown_params)

    def test_hash_from_string(self):
        input_string = "test"
        hash_result = hash_from_string(input_string)
        self.assertEqual(len(hash_result), 32)

    def test_outpoint_to_bytes(self):
        txid = bytes([0] * 32)
        index = 1
        result = outpoint_to_bytes(txid, index)
        self.assertEqual(len(result), 36)
        self.assertEqual(result[-4:], struct.pack('>I', index))

        invalid_txid = bytes([0] * 31)  # Only 31 bytes
        with self.assertRaises(ValueError):
            outpoint_to_bytes(invalid_txid, index)

    def test_outpoint_equality(self):
        op1 = OutPoint("hash1", 1)
        op2 = OutPoint("hash1", 1)
        op3 = OutPoint("hash2", 2)
        self.assertEqual(op1, op2)
        self.assertNotEqual(op1, op3)

    def test_block_to_del_ops(self):
        tx_in = TxIn(OutPoint("hash1", 0))
        tx_out = TxOut(False)
        tx = Tx([tx_in], [tx_out])
        block = Block([tx])
        result = block_to_del_ops(block)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], tx_in.previous_out_point)

    def test_dedupe_block(self):
        tx_in1 = TxIn(OutPoint("hash1", 0))
        tx_out1 = TxOut(False)
        tx1 = Tx([tx_in1], [tx_out1])

        tx_in2 = TxIn(OutPoint("hash2", 0))
        tx_out2 = TxOut(True)  # Unspendable
        tx2 = Tx([tx_in2], [tx_out2])

        block = Block([tx1, tx2])
        in_count, out_count, inskip, outskip = dedupe_block(block)
        self.assertEqual(in_count, 2)
        self.assertEqual(out_count, 2)
        self.assertIn(0, inskip)
        self.assertIn(1, outskip)

    def test_is_unspendable(self):
        tx_out_spendable = TxOut(False)
        tx_out_unspendable = TxOut(True)
        self.assertFalse(is_unspendable(tx_out_spendable))
        self.assertTrue(is_unspendable(tx_out_unspendable))

if __name__ == "__main__":
    unittest.main()

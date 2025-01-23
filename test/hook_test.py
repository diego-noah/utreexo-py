import unittest

class TestChainHookImplementation(unittest.TestCase):
    class MockChainHook(ChainHook):
        def __init__(self):
            self.addresses = []
            self.out_points = []

        def start(self, height, host, path, proxy_url, params):
            return ("tx_channel", "height_channel")

        def register_address(self, address: bytes):
            self.addresses.append(address)

        def register_out_point(self, out_point):
            self.out_points.append(out_point)

        def unregister_out_point(self, out_point):
            self.out_points.remove(out_point)

        def push_tx(self, tx):
            return f"Transaction {tx} pushed."

        def raw_blocks(self):
            return "Raw block data."

    def setUp(self):
        self.hook = self.MockChainHook()

    def test_start(self):
        tx_channel, height_channel = self.hook.start(0, "localhost", "/path", "http://proxy", {})
        self.assertEqual(tx_channel, "tx_channel")
        self.assertEqual(height_channel, "height_channel")

    def test_register_address(self):
        address = b"test_address"
        self.hook.register_address(address)
        self.assertIn(address, self.hook.addresses)

    def test_register_out_point(self):
        out_point = "test_out_point"
        self.hook.register_out_point(out_point)
        self.assertIn(out_point, self.hook.out_points)

    def test_unregister_out_point(self):
        out_point = "test_out_point"
        self.hook.register_out_point(out_point)
        self.hook.unregister_out_point(out_point)
        self.assertNotIn(out_point, self.hook.out_points)

    def test_push_tx(self):
        result = self.hook.push_tx("tx1")
        self.assertEqual(result, "Transaction tx1 pushed.")

    def test_raw_blocks(self):
        result = self.hook.raw_blocks()
        self.assertEqual(result, "Raw block data.")


class TestCsn(unittest.TestCase):
    def setUp(self):
        self.params = {"example_param": 42}
        self.csn = Csn(self.params)

    def test_register_out_point(self):
        out_point = "test_out_point"
        self.csn.register_out_point(out_point)
        self.assertIn(out_point, self.csn.watch_ops)
        self.assertTrue(self.csn.watch_ops[out_point])

    def test_unregister_out_point(self):
        out_point = "test_out_point"
        self.csn.register_out_point(out_point)
        self.csn.unregister_out_point(out_point)
        self.assertNotIn(out_point, self.csn.watch_ops)

    def test_register_address(self):
        address = b"test_address"
        self.csn.register_address(address)
        self.assertIn(address, self.csn.watch_addresses)
        self.assertTrue(self.csn.watch_addresses[address])

    def test_push_tx(self):
        with self.assertLogs() as log:
            self.csn.push_tx("tx1")
            self.assertIn("PushTx not yet implemented.", log.output[0])


if __name__ == "__main__":
    unittest.main()

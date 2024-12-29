import unittest
from unittest.mock import patch, MagicMock
import signal
from your_module import Bridge, SignalHandler

class TestBridge(unittest.TestCase):

    def test_parse_missing_arguments(self):
        with self.assertRaises(ValueError):
            Bridge.parse([])

    def test_parse_valid_arguments(self):
        args = ["arg1"]
        cfg, err = Bridge.parse(args)
        self.assertIsNone(err)
        self.assertIn("CpuProf", cfg)
        self.assertIn("TraceProf", cfg)
        self.assertIn("MemProf", cfg)

    @patch("your_module.signal.signal")
    def test_signal_handler_initialization(self, mock_signal):
        cfg = {"CpuProf": "", "TraceProf": "", "MemProf": ""}
        sig_handler = SignalHandler(cfg)
        sig_handler.start()
        self.assertTrue(mock_signal.called)
        self.assertEqual(mock_signal.call_count, 3)

    @patch("your_module.Bridge.start")
    def test_bridge_start_signal_received(self, mock_start):
        mock_queue = MagicMock()
        mock_queue.poll.side_effect = [False, True]
        Bridge.start({"CpuProf": "", "TraceProf": "", "MemProf": ""}, mock_queue)
        self.assertTrue(mock_queue.poll.called)

    @patch("your_module.Bridge.parse")
    @patch("your_module.SignalHandler")
    @patch("your_module.Bridge.start")
    def test_main_integration(self, mock_start, mock_signal_handler, mock_parse):
        mock_parse.return_value = ({"CpuProf": "", "TraceProf": "", "MemProf": ""}, None)
        mock_signal_handler.return_value.queue = MagicMock()

        with patch("your_module.os.sys.argv", ["script_name", "arg1"]):
            try:
                from your_module import main
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)

if __name__ == "__main__":
    unittest.main()

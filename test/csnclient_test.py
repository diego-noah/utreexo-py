import unittest
from unittest.mock import patch, MagicMock
import signal
import sys
from csn import parse, run_ibd, HelpMsg
from main import main, handle_int_sig

class TestMainModule(unittest.TestCase):

    @patch('csn.parse')
    def test_parse_arguments_success(self, mock_parse):
        mock_parse.return_value = "parsed_config"
        with patch('sys.argv', ['script_name', 'arg1', 'arg2']):
            result = parse(sys.argv[1:])
            mock_parse.assert_called_once_with(['arg1', 'arg2'])
            self.assertEqual(result, "parsed_config")

    @patch('csn.parse')
    def test_parse_arguments_failure(self, mock_parse):
        mock_parse.side_effect = Exception("Invalid arguments")
        with patch('sys.argv', ['script_name', 'invalid_arg']), patch('sys.exit') as mock_exit, patch('builtins.print') as mock_print:
            with self.assertRaises(SystemExit):
                main()
            mock_parse.assert_called_once()
            mock_print.assert_any_call("Invalid arguments")
            mock_print.assert_any_call(HelpMsg)
            mock_exit.assert_called_once_with(1)

    @patch('signal.signal')
    def test_signal_handlers_registration(self, mock_signal):
        with patch('csn.parse', return_value="parsed_config"), patch('csn.run_ibd') as mock_run_ibd:
            with patch('sys.argv', ['script_name', 'arg1']):
                main()
                mock_signal.assert_any_call(signal.SIGINT, unittest.mock.ANY)
                mock_signal.assert_any_call(signal.SIGTERM, unittest.mock.ANY)
                mock_signal.assert_any_call(signal.SIGQUIT, unittest.mock.ANY)

    def test_handle_int_sig(self):
        sig = []
        handle_int_sig(signal.SIGINT, None, sig, None)
        self.assertTrue(sig)
        self.assertTrue(sig[0])

    @patch('csn.run_ibd')
    def test_run_ibd_success(self, mock_run_ibd):
        with patch('csn.parse', return_value="parsed_config"), patch('signal.signal'), patch('sys.argv', ['script_name', 'arg1']):
            main()
            mock_run_ibd.assert_called_once_with("parsed_config", unittest.mock.ANY)

    @patch('csn.run_ibd')
    def test_run_ibd_failure(self, mock_run_ibd):
        mock_run_ibd.side_effect = Exception("IBD Error")
        with patch('csn.parse', return_value="parsed_config"), patch('signal.signal'), patch('builtins.print') as mock_print, patch('sys.exit') as mock_exit:
            with patch('sys.argv', ['script_name', 'arg1']):
                with self.assertRaises(SystemExit):
                    main()
                mock_run_ibd.assert_called_once()
                mock_print.assert_called_with("An error occurred: IBD Error")
                mock_exit.assert_called_once_with(1)

if __name__ == "__main__":
    unittest.main()

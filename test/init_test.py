import unittest
from unittest.mock import patch, MagicMock
import threading
from your_module import Config, run_ibd, start_cpu_profile, start_trace, run_profiler_server

class TestIBD(unittest.TestCase):
    
    @patch("your_module.start_cpu_profile")
    def test_start_cpu_profile(self, mock_start_cpu_profile):
        config = Config(cpu_prof="cpu.prof")
        sig = threading.Event()
        run_ibd(config, sig)
        mock_start_cpu_profile.assert_called_once_with("cpu.prof")

    @patch("your_module.start_trace")
    def test_start_trace(self, mock_start_trace):
        config = Config(trace_prof="trace.prof")
        sig = threading.Event()
        run_ibd(config, sig)
        mock_start_trace.assert_called_once_with("trace.prof")
    
    @patch("your_module.run_profiler_server")
    def test_run_profiler_server(self, mock_run_profiler_server):
        config = Config(prof_server="8080")
        sig = threading.Event()
        run_ibd(config, sig)
        mock_run_profiler_server.assert_called_once_with(8080)
    
    @patch("your_module.bech32_decode", return_value=("bc", b"0123456789abcdefghij"))
    @patch("your_module.Csn")
    @patch("your_module.init_csn_state", return_value=(MagicMock(), 0, MagicMock()))
    def test_watch_addr_decoding(self, mock_init_csn_state, mock_Csn, mock_bech32_decode):
        config = Config(watch_addr="bc1qexampleaddress")
        sig = threading.Event()
        run_ibd(config, sig)
        mock_bech32_decode.assert_called_once_with("bc1qexampleaddress")
        mock_Csn.return_value.register_address.assert_called_once()

    @patch("your_module.init_csn_state", side_effect=Exception("init error"))
    def test_init_csn_state_failure(self, mock_init_csn_state):
        config = Config()
        sig = threading.Event()
        run_ibd(config, sig)
        mock_init_csn_state.assert_called_once()
    
if __name__ == "__main__":
    unittest.main()

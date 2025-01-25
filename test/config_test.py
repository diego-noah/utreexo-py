import unittest
from unittest.mock import patch
from your_module import parse_args, Config

class TestParseArgs(unittest.TestCase):

    def test_default_args(self):
        args = []
        with patch('sys.argv', ['script_name'] + args):
            config = parse_args(args)

        self.assertEqual(config.params, "TestNet3Params")
        self.assertEqual(config.remote_host, "127.0.0.1:8338")
        self.assertEqual(config.watch_addr, "")
        self.assertEqual(config.lookahead, 1000)
        self.assertEqual(config.quitafter, -1)
        self.assertTrue(config.checksig)
        self.assertEqual(config.trace_prof, "")
        self.assertEqual(config.cpu_prof, "")
        self.assertEqual(config.mem_prof, "")
        self.assertEqual(config.prof_server, "")

    def test_custom_network(self):
        args = ['-net=mainnet']
        with patch('sys.argv', ['script_name'] + args):
            config = parse_args(args)

        self.assertEqual(config.params, "MainNetParams")

    def test_invalid_network(self):
        args = ['-net=invalidnet']
        with patch('sys.argv', ['script_name'] + args):
            with self.assertRaises(ValueError) as context:
                parse_args(args)

            self.assertEqual(str(context.exception), "Invalid network: invalidnet")

    def test_custom_host_and_port(self):
        args = ['-host=192.168.1.1:1234']
        with patch('sys.argv', ['script_name'] + args):
            config = parse_args(args)

        self.assertEqual(config.remote_host, "192.168.1.1:1234")

    def test_host_without_port(self):
        args = ['-host=192.168.1.1']
        with patch('sys.argv', ['script_name'] + args):
            config = parse_args(args)

        self.assertEqual(config.remote_host, "192.168.1.1:8338")

    def test_cpu_and_memory_profiling(self):
        args = ['-cpuprof=cpu.prof', '-memprof=mem.prof']
        with patch('sys.argv', ['script_name'] + args):
            config = parse_args(args)

        self.assertEqual(config.cpu_prof, "cpu.prof")
        self.assertEqual(config.mem_prof, "mem.prof")

    def test_all_arguments(self):
        args = [
            '-net=regtest',
            '-cpuprof=cpu.prof',
            '-memprof=mem.prof',
            '-trace=trace.log',
            '-watchaddr=address123',
            '-host=10.0.0.1:8080',
            '-checksig=False',
            '-lookahead=500',
            '-quitafter=10',
            '-profserver=8000'
        ]
        with patch('sys.argv', ['script_name'] + args):
            config = parse_args(args)

        self.assertEqual(config.params, "RegressionNetParams")
        self.assertEqual(config.remote_host, "10.0.0.1:8080")
        self.assertEqual(config.watch_addr, "address123")
        self.assertEqual(config.lookahead, 500)
        self.assertEqual(config.quitafter, 10)
        self.assertFalse(config.checksig)
        self.assertEqual(config.trace_prof, "trace.log")
        self.assertEqual(config.cpu_prof, "cpu.prof")
        self.assertEqual(config.mem_prof, "mem.prof")
        self.assertEqual(config.prof_server, "8000")

if __name__ == '__main__':
    unittest.main()

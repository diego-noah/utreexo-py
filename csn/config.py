import argparse

class Config:
    def __init__(self, params, remote_host, watch_addr, lookahead, quitafter, checksig, trace_prof, cpu_prof, mem_prof, prof_server):
        self.params = params
        self.remote_host = remote_host
        self.watch_addr = watch_addr
        self.lookahead = lookahead
        self.quitafter = quitafter
        self.checksig = checksig
        self.trace_prof = trace_prof
        self.cpu_prof = cpu_prof
        self.mem_prof = mem_prof
        self.prof_server = prof_server

def parse_args(args):
    parser = argparse.ArgumentParser(description="A dynamic hash-based accumulator designed for the Bitcoin UTXO set.")

    parser.add_argument("-net", type=str, default="testnet", 
                        help="Target network. Options: testnet, signet, regtest, mainnet. Usage: '-net=regtest'")
    parser.add_argument("-cpuprof", type=str, default="", 
                        help="Enable CPU profiling. Usage: 'cpuprof=path/to/file'")
    parser.add_argument("-memprof", type=str, default="", 
                        help="Enable heap profiling. Usage: 'memprof=path/to/file'")
    parser.add_argument("-trace", type=str, default="", 
                        help="Enable trace. Usage: 'trace=path/to/file'")
    parser.add_argument("-watchaddr", type=str, default="", 
                        help="Address to watch & report transactions. Only bech32 p2wpkh supported.")
    parser.add_argument("-host", type=str, default="127.0.0.1", 
                        help="Remote server to connect to. Defaults to localhost.")
    parser.add_argument("-checksig", type=bool, default=True, 
                        help="Check Bitcoin transaction signatures. (slower)")
    parser.add_argument("-lookahead", type=int, default=1000, 
                        help="Size of the look-ahead cache in blocks.")
    parser.add_argument("-quitafter", type=int, default=-1, 
                        help="Quit IBD after n blocks. (for testing)")
    parser.add_argument("-profserver", type=str, default="", 
                        help="Enable profiling HTTP server. Usage: 'profserver=port'")

    parsed_args = parser.parse_args(args)

    # Configure network parameters
    params_map = {
        "testnet": "TestNet3Params",
        "regtest": "RegressionNetParams",
        "mainnet": "MainNetParams",
        "signet": "SigNetParams"
    }
    params = params_map.get(parsed_args.net)
    if not params:
        raise ValueError(f"Invalid network: {parsed_args.net}")

    # Default host to localhost if empty
    remote_host = parsed_args.host or "127.0.0.1:8338"
    if ":" not in remote_host:
        remote_host += ":8338"

    config = Config(
        params=params,
        remote_host=remote_host,
        watch_addr=parsed_args.watchaddr,
        lookahead=parsed_args.lookahead,
        quitafter=parsed_args.quitafter,
        checksig=parsed_args.checksig,
        trace_prof=parsed_args.trace,
        cpu_prof=parsed_args.cpuprof,
        mem_prof=parsed_args.memprof,
        prof_server=parsed_args.profserver
    )
    return config


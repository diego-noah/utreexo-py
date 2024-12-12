import os
import threading
import time
from http.server import SimpleHTTPRequestHandler, HTTPServer
from bech32 import bech32_decode

class Config:
    def __init__(self, cpu_prof=None, trace_prof=None, prof_server=None, look_ahead=0, check_sig=False, watch_addr=""):
        self.cpu_prof = cpu_prof
        self.trace_prof = trace_prof
        self.prof_server = prof_server
        self.look_ahead = look_ahead
        self.check_sig = check_sig
        self.watch_addr = watch_addr

def start_cpu_profile(file_path):
    pass

def start_trace(file_path):
    pass

def run_profiler_server(port):
    def handler():
        server = HTTPServer(("", port), SimpleHTTPRequestHandler)
        print(f"Profiler server running at http://localhost:{port}/")
        server.serve_forever()

    thread = threading.Thread(target=handler)
    thread.daemon = True
    thread.start()

def run_ibd(cfg: Config, sig: threading.Event):
    if cfg.cpu_prof:
        try:
            start_cpu_profile(cfg.cpu_prof)
        except Exception as e:
            print(f"Error starting CPU profile: {e}")
            return

    if cfg.trace_prof:
        try:
            start_trace(cfg.trace_prof)
        except Exception as e:
            print(f"Error starting trace profile: {e}")
            return

    if cfg.prof_server:
        run_profiler_server(int(cfg.prof_server))

    try:
        pol, height, utxos = init_csn_state()
    except Exception as e:
        print(f"init_csn_state error: {e}")
        return

    pol.lookahead = cfg.look_ahead

    c = Csn(
        pollard=pol,
        check_signatures=cfg.check_sig,
        utxo_store=utxos
    )

    try:
        tx_chan, height_chan = c.start(cfg, height, "compactstate", "", sig)
    except Exception as e:
        print(f"CSN start error: {e}")
        return

    if cfg.watch_addr:
        print(f"Decoding watch address: {cfg.watch_addr}")
        try:
            hrp, data = bech32_decode(cfg.watch_addr)
            if len(data) != 20:
                raise ValueError(f"Expected 20-byte p2wpkh address, got {len(data)} bytes.")
            c.register_address(bytes(data))
        except Exception as e:
            print(f"SegWitAddressDecode error: {e}")
            return

    while True:
        try:
            if not tx_chan.empty():
                tx = tx_chan.get()
                print(f"Wallet got transaction {tx.tx_hash()}")

            if not height_chan.empty():
                height = height_chan.get()
                if height % 1000 == 0:
                    print(f"Reached height {height}")

            if sig.is_set():
                print("Termination signal received.")
                break

            time.sleep(0.1)
        except KeyboardInterrupt:
            print("Exiting...")
            break

if __name__ == "__main__":
    config = Config(cpu_prof="cpu.prof", trace_prof="trace.prof", prof_server="8080", look_ahead=1000, check_sig=True, watch_addr="bc1qexampleaddress")
    termination_signal = threading.Event()
    run_ibd(config, termination_signal)

import os
import signal
import tracemalloc
import gc
from multiprocessing import Process

class Bridge:
    @staticmethod
    def parse(args):
        # Simulate config parsing
        if len(args) < 1:
            raise ValueError("Missing arguments")
        return {"CpuProf": "", "TraceProf": "", "MemProf": ""}, None

    @staticmethod
    def start(config, sig):
        print("Bridge started with config:", config)
        try:
            while True:
                if sig.poll():
                    print("Signal received, stopping bridge...")
                    break
        except KeyboardInterrupt:
            print("Keyboard interrupt detected.")

def main():
    # Set garbage collection threshold for more frequent collections
    gc.set_threshold(700, 10, 10)

    # Parse configuration
    try:
        cfg, err = Bridge.parse(os.sys.argv[1:])
        if err:
            print(err)
            exit(1)
    except Exception as e:
        print(e)
        print("Usage: <script> [arguments]")
        exit(1)

    # Signal handling
    sig = SignalHandler(cfg)
    sig.start()

    try:
        Bridge.start(cfg, sig.queue)
    except Exception as e:
        print("Error:", e)
        exit(1)


class SignalHandler:
    def __init__(self, cfg):
        self.cfg = cfg
        self.queue = Process(target=self._handle_signal)
        self.queue.daemon = True

    def start(self):
        signal.signal(signal.SIGINT, self._handler)
        signal.signal(signal.SIGTERM, self._handler)
        signal.signal(signal.SIGQUIT, self._handler)
    
    def _handler(self, signum, frame):
        print(f"Received signal: {signum}")
        if self.cfg["CpuProf"]:
            print("Stopping CPU profile...")

        if self.cfg["TraceProf"]:
            tracemalloc.stop()

        if self.cfg["MemProf"]:
            print(f"Writing memory profile to {self.cfg['MemProf']}...")
            with open(self.cfg["MemProf"], "w") as f:
                gc.collect()
                tracemalloc.start()


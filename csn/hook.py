class ChainHook:
    """
    Interface for ChainHook. Should be implemented to plug a wallet into.
    """

    def start(self, height: int, host: str, path: str, proxy_url: str, params):
        """
        Start the chain hook.

        Returns:
            tuple: (channel of transactions, channel of heights)
        """
        raise NotImplementedError

    def register_address(self, address: bytes):
        """Register an address."""
        raise NotImplementedError

    def register_out_point(self, out_point):
        """Register an outpoint."""
        raise NotImplementedError

    def unregister_out_point(self, out_point):
        """Unregister an outpoint."""
        raise NotImplementedError

    def push_tx(self, tx):
        """Push a transaction."""
        raise NotImplementedError

    def raw_blocks(self):
        """Get raw blocks."""
        raise NotImplementedError


class Csn:
    """
    Main stateful class for the Compact State Node.
    Tracks block height and relevant transactions.
    """

    def __init__(self, params):
        self.current_height = 0
        self.pollard = None  # Placeholder for the accumulator Pollard
        self.watch_ops = {}
        self.watch_addresses = {}
        self.tx_channel = []
        self.height_channel = []
        self.check_signatures = False
        self.params = params
        self.remote_host = ""
        self.utxo_store = {}
        self.total_score = 0

    def register_out_point(self, out_point):
        """Register an outpoint."""
        self.watch_ops[out_point] = True

    def unregister_out_point(self, out_point):
        """Unregister an outpoint."""
        if out_point in self.watch_ops:
            del self.watch_ops[out_point]

    def register_address(self, address: bytes):
        """Register an address."""
        self.watch_addresses[address] = True

    def push_tx(self, tx):
        """Push a transaction."""
        print("PushTx not yet implemented.")
        return None

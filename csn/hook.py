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

    def process_block(self, block):
        """
        Process a new block and update state.

        Args:
            block: Block object containing transactions and header
        """
        if not block:
            return False

        # Verify block height matches expected
        if block.height != self.current_height + 1:
            return False

        # Process all transactions in block
        for tx in block.transactions:
            self.process_transaction(tx)

        self.current_height = block.height
        self.height_channel.append(block.height)
        return True

    def process_transaction(self, tx):
        """
        Process a single transaction, updating UTXO set and notifying listeners.

        Args:
            tx: Transaction object
        """
        # Check if transaction is relevant to watched addresses/outpoints
        is_relevant = False

        # Remove spent inputs from UTXO set
        for tx_in in tx.inputs:
            outpoint = tx_in.previous_output
            if outpoint in self.watch_ops:
                is_relevant = True
                if outpoint in self.utxo_store:
                    del self.utxo_store[outpoint]

        # Add new outputs to UTXO set if watching address
        for index, tx_out in enumerate(tx.outputs):
            if tx_out.address in self.watch_addresses:
                is_relevant = True
                outpoint = (tx.txid, index)
                self.utxo_store[outpoint] = tx_out

        # Notify listeners if transaction is relevant
        if is_relevant:
            self.tx_channel.append(tx)

    def get_utxos(self, address: bytes):
        """
        Get all UTXOs for a given address.

        Args:
            address: Address to get UTXOs for

        Returns:
            dict: Dictionary of outpoint -> output for address
        """
        address_utxos = {}
        for outpoint, output in self.utxo_store.items():
            if output.address == address:
                address_utxos[outpoint] = output
        return address_utxos

    def get_balance(self, address: bytes):
        """
        Get total balance for an address.

        Args:
            address: Address to get balance for

        Returns:
            int: Total balance in satoshis
        """
        utxos = self.get_utxos(address)
        return sum(output.value for output in utxos.values())

    def start(self, height: int, host: str):
        """
        Start the CSN from a given height.

        Args:
            height: Block height to start from
            host: Remote node host to connect to
        """
        self.current_height = height
        self.remote_host = host
        self.height_channel = []
        self.tx_channel = []

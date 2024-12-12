import socket
import struct
from dataclasses import dataclass
from typing import List, Tuple, Dict
import threading
from queue import Queue

from btcd.chaincfg.chainhash import Hash
from btcd.wire import OutPoint, TxOut, MsgBlock
from btcd.blockchain import UtxoViewpoint, UtxoEntry
from btcd.txscript import SigCache, HashCache
from btcd.btcutil import Block
from btcd.chaincfg import Params

from accumulator import Leaf, Pollard
from btcacc import LeafData, UData
from util import is_unspendable

@dataclass
class UBlock:
    """A regular block with Utreexo data attached"""
    utreexo_data: UData
    block: Block

    @staticmethod
    def block_to_add_leaves(
        blk: Block,
        remember: List[bool],
        skiplist: List[int],
        height: int,
        out_count: int
    ) -> List[Leaf]:
        """
        Turns all new UTXOs in a block into leaf TXOs.
        """
        # Pre-allocate leaves list with estimated capacity
        leaves = []
        txonum = 0
        
        for coinbase_if_0, tx in enumerate(blk.transactions):
            # Cache txid
            txid = tx.hash()
            
            for i, out in enumerate(tx.msg_tx.tx_out):
                # Skip unspendable outputs
                if is_unspendable(out):
                    txonum += 1
                    continue
                    
                # Skip txos in skiplist
                if skiplist and skiplist[0] == txonum:
                    skiplist = skiplist[1:]
                    txonum += 1
                    continue

                # Create leaf data
                l = LeafData()
                l.tx_hash = txid
                l.index = i
                l.height = height
                l.coinbase = coinbase_if_0 == 0
                l.amt = out.value
                l.pk_script = out.pk_script

                # Create leaf
                uleaf = Leaf(hash=l.leaf_hash())
                if len(remember) > txonum:
                    uleaf.remember = remember[txonum]
                    
                leaves.append(uleaf)
                txonum += 1

        return leaves

    def proof_sanity(self, nl: int, h: int) -> None:
        """Check consistency of UBlock proof"""
        # Get outpoints needing proof
        prove_ops = self.block_to_del_ops()

        # Check all outpoints are provided
        if len(prove_ops) != len(self.utreexo_data.stxos):
            raise Exception(
                f"height {self.utreexo_data.height} {len(prove_ops)} "
                f"outpoints need proofs but only {len(self.utreexo_data.stxos)} proven"
            )

        # Verify outpoint matches
        for i, op in enumerate(prove_ops):
            stxo = self.utreexo_data.stxos[i]
            if op.hash != stxo.tx_hash or op.index != stxo.index:
                raise Exception(
                    f"block/utxoData mismatch {op} vs {stxo.op_string()}"
                )

        # Check proof sanity
        if not self.utreexo_data.proof_sanity(nl, h):
            raise Exception(f"height {self.utreexo_data.height} LeafData / Proof mismatch")

    def to_utxo_view(self) -> UtxoViewpoint:
        """Convert UData to UtxoViewpoint"""
        view = UtxoViewpoint()
        
        for ld in self.utreexo_data.stxos:
            txo = TxOut(value=ld.amt, pk_script=ld.pk_script)
            utxo = UtxoEntry(txo=txo, height=ld.height, coinbase=ld.coinbase)
            op = OutPoint(hash=Hash(ld.tx_hash), index=ld.index)
            view.entries[op] = utxo
            
        return view

    def check_block(self, outskip: List[int], params: Params) -> bool:
        """Perform internal block checks"""
        view = self.to_utxo_view()
        view_map = view.entries
        txonum = 0

        sig_cache = SigCache(0)
        hash_cache = HashCache(0)

        # Skip coinbase tx
        transactions = self.block.transactions[1:]
        
        def check_tx(tx):
            # Check transaction inputs
            height = self.utreexo_data.height
            if not tx.check_transaction_inputs(height, view, params):
                raise Exception(f"Tx {tx.hash()} fails CheckTransactionInputs")

            # Validate transaction scripts
            if not tx.validate_transaction_scripts(view, 0, sig_cache, hash_cache):
                raise Exception(f"Tx {tx.hash()} fails ValidateTransactionScripts")

        # Check transactions in parallel
        threads = []
        for tx in transactions:
            t = threading.Thread(target=check_tx, args=(tx,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        return True

    def deserialize(self, r) -> None:
        """Deserialize UBlock from reader"""
        msg_block = MsgBlock()
        msg_block.deserialize(r)
        self.block = Block(msg_block)
        self.utreexo_data = UData()
        self.utreexo_data.deserialize(r)

    def serialize(self, w) -> None:
        """Serialize UBlock to writer"""
        self.block.msg_block.serialize(w)
        self.utreexo_data.serialize(w)

    def serialize_size(self) -> int:
        """Get serialized size in bytes"""
        return self.block.msg_block.serialize_size() + self.utreexo_data.serialize_size()


def ublock_network_reader(block_chan: Queue, remote_server: str, cur_height: int, lookahead: int):
    """Gets Ublocks from remote host and puts them in channel"""
    try:
        sock = socket.create_connection(remote_server.split(':'), timeout=2)
    except Exception as e:
        raise Exception(f"Connection error: {str(e)}")

    try:
        # Request block range
        sock.send(struct.pack(">i", cur_height))
        sock.send(struct.pack(">i", 0x7fffffff))  # MaxInt32

        # Read blocks
        while True:
            ub = UBlock(None, None)
            try:
                ub.deserialize(sock)
                block_chan.put(ub)
                cur_height += 1
            except Exception as e:
                print(f"Deserialize error from {remote_server}: {str(e)}")
                break

    finally:
        sock.close()
        block_chan.put(None)  # Signal end 
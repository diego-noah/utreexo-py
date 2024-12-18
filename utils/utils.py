import hashlib
import struct

class Hash(bytes):
    def __new__(cls, value):
        if len(value) != 32:
            raise ValueError("Hash must be exactly 32 bytes long")
        return super().__new__(cls, value)

main_net_gen_hash = Hash(
    bytes([
        0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
        0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
        0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
        0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00,
    ])
)

test_net3_gen_hash = Hash(
    bytes([
        0x43, 0x49, 0x7f, 0xd7, 0xf8, 0x26, 0x95, 0x71,
        0x08, 0xf4, 0xa3, 0x0f, 0xd9, 0xce, 0xc3, 0xae,
        0xba, 0x79, 0x97, 0x20, 0x84, 0xe9, 0x0e, 0xad,
        0x01, 0xea, 0x33, 0x09, 0x00, 0x00, 0x00, 0x00,
    ])
)

reg_test_gen_hash = Hash(
    bytes([
        0x06, 0x22, 0x6e, 0x46, 0x11, 0x1a, 0x0b, 0x59,
        0xca, 0xaf, 0x12, 0x60, 0x43, 0xeb, 0x5b, 0xbf,
        0x28, 0xc3, 0x4f, 0x3a, 0x5e, 0x33, 0x2a, 0x1f,
        0xc7, 0xb2, 0xb7, 0x3c, 0xf1, 0x88, 0x91, 0x0f,
    ])
)

sig_net_gen_hash = Hash(
    bytes([
        0xf6, 0x1e, 0xee, 0x3b, 0x63, 0xa3, 0x80, 0xa4,
        0x77, 0xa0, 0x63, 0xaf, 0x32, 0xb2, 0xbb, 0xc9,
        0x7c, 0x9f, 0xf9, 0xf0, 0x1f, 0x2c, 0x42, 0x25,
        0xe9, 0x73, 0x98, 0x81, 0x08, 0x00, 0x00, 0x00,
    ])
)

class ChainParams:
    def __init__(self, name):
        self.name = name

def gen_hash_for_net(params):
    if params.name == "testnet3":
        return test_net3_gen_hash
    elif params.name == "mainnet":
        return main_net_gen_hash
    elif params.name == "regtest":
        return reg_test_gen_hash
    elif params.name == "signet":
        return sig_net_gen_hash
    else:
        raise ValueError("Network not supported")

def hash_from_string(s):
    return Hash(hashlib.sha256(s.encode()).digest())

def outpoint_to_bytes(txid, index):
    if len(txid) != 32:
        raise ValueError("TXID must be exactly 32 bytes")
    return txid[::-1] + struct.pack('>I', index)

class OutPoint:
    def __init__(self, hash: str, index: int):
        self.hash = hash
        self.index = index

    def __eq__(self, other):
        return isinstance(other, OutPoint) and self.hash == other.hash and self.index == other.index

    def __hash__(self):
        return hash((self.hash, self.index))


class TxIn:
    def __init__(self, previous_out_point: OutPoint):
        self.previous_out_point = previous_out_point


class TxOut:
    def __init__(self, unspendable: bool):
        self.unspendable = unspendable


class Tx:
    def __init__(self, tx_in: List[TxIn], tx_out: List[TxOut]):
        self.tx_in = tx_in
        self.tx_out = tx_out

    def msg_tx(self):
        return self


class Block:
    def __init__(self, transactions: List[Tx]):
        self.transactions = transactions


def block_to_del_ops(blk: Block) -> List[OutPoint]:
    transactions = blk.transactions
    in_count, _, inskip, _ = dedupe_block(blk)

    del_ops = []
    input_in_block = 0

    for tx in transactions:
        for txin in tx.msg_tx().tx_in:
            if inskip and inskip[0] == input_in_block:
                inskip.pop(0)
                input_in_block += 1
                continue

            del_ops.append(txin.previous_out_point)
            input_in_block += 1

    return del_ops


def dedupe_block(blk: Block) -> Tuple[int, int, List[int], List[int]]:
    in_count = 0
    out_count = 0
    inskip = []
    outskip = []

    in_map = defaultdict(int)
    i = 0

    for coinbase_if_zero, tx in enumerate(blk.transactions):
        if coinbase_if_zero == 0:
            inskip = [0]
            i += len(tx.msg_tx().tx_in)
            continue

        for txin in tx.msg_tx().tx_in:
            in_map[txin.previous_out_point] = i
            i += 1

    in_count = i
    i = 0

    for tx in blk.transactions:
        for out_idx, tx_out in enumerate(tx.msg_tx().tx_out):
            if is_unspendable(tx_out):
                outskip.append(i)
                i += 1
                continue

            op = OutPoint(hash(tx), out_idx)
            if op in in_map:
                inskip.append(in_map[op])
                outskip.append(i)
            i += 1

    out_count = i
    inskip.sort()
    return in_count, out_count, inskip, outskip


def is_unspendable(tx_out: TxOut) -> bool:
    return tx_out.unspendable


def hash(tx: Tx) -> str:
    return "some_hash_representation"

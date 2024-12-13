import hashlib
import struct
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import os

from btcd.wire import OutPoint, TxOut
from btcd.btcutil import Block
from btcd.chaincfg import Params

class Hash(bytes):
    """32-byte hash type"""
    def __new__(cls, data):
        if isinstance(data, bytes) and len(data) == 32:
            return super().__new__(cls, data)
        raise ValueError("Hash must be 32 bytes")

# Network genesis hashes
MAINNET_GEN_HASH = Hash(bytes([
    0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
    0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
    0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
    0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00,
]))

TESTNET3_GEN_HASH = Hash(bytes([
    0x43, 0x49, 0x7f, 0xd7, 0xf8, 0x26, 0x95, 0x71,
    0x08, 0xf4, 0xa3, 0x0f, 0xd9, 0xce, 0xc3, 0xae,
    0xba, 0x79, 0x97, 0x20, 0x84, 0xe9, 0x0e, 0xad,
    0x01, 0xea, 0x33, 0x09, 0x00, 0x00, 0x00, 0x00,
]))

REGTEST_GEN_HASH = Hash(bytes([
    0x06, 0x22, 0x6e, 0x46, 0x11, 0x1a, 0x0b, 0x59,
    0xca, 0xaf, 0x12, 0x60, 0x43, 0xeb, 0x5b, 0xbf,
    0x28, 0xc3, 0x4f, 0x3a, 0x5e, 0x33, 0x2a, 0x1f,
    0xc7, 0xb2, 0xb7, 0x3c, 0xf1, 0x88, 0x91, 0x0f,
]))

SIGNET_GEN_HASH = Hash(bytes([
    0xf6, 0x1e, 0xee, 0x3b, 0x63, 0xa3, 0x80, 0xa4,
    0x77, 0xa0, 0x63, 0xaf, 0x32, 0xb2, 0xbb, 0xc9,
    0x7c, 0x9f, 0xf9, 0xf0, 0x1f, 0x2c, 0x42, 0x25,
    0xe9, 0x73, 0x98, 0x81, 0x08, 0x00, 0x00, 0x00,
]))

def gen_hash_for_net(params: Params) -> Hash:
    """Get genesis hash for given network parameters"""
    if params.name == "testnet3":
        return TESTNET3_GEN_HASH
    elif params.name == "mainnet":
        return MAINNET_GEN_HASH
    elif params.name == "regtest":
        return REGTEST_GEN_HASH
    elif params.name == "signet":
        return SIGNET_GEN_HASH
    raise ValueError("Network not supported")

def hash_from_string(s: str) -> Hash:
    """Create Hash from string using SHA256"""
    return Hash(hashlib.sha256(s.encode()).digest())

def outpoint_to_bytes(op: OutPoint) -> bytes:
    """Convert OutPoint to 36 bytes"""
    return op.hash + struct.pack(">I", op.index)

def block_to_del_ops(blk: Block) -> List[OutPoint]:
    """Get all UTXOs in block that need proofs for deletion"""
    transactions = blk.transactions
    in_count, _, inskip, _ = dedupe_block(blk)
    
    del_ops = []
    input_in_block = 0
    
    for tx in transactions:
        for tx_in in tx.msg_tx.tx_in:
            if inskip and inskip[0] == input_in_block:
                inskip = inskip[1:]
                input_in_block += 1
                continue
                
            del_ops.append(tx_in.previous_out_point)
            input_in_block += 1
            
    return del_ops

def dedupe_block(blk: Block) -> Tuple[int, int, List[int], List[int]]:
    """
    Find duplicate inputs/outputs in block
    Returns (input_count, output_count, input_skip_list, output_skip_list)
    """
    i = 0
    inmap: Dict[OutPoint, int] = {}
    
    # Build input map
    for coinbase_if_zero, tx in enumerate(blk.transactions):
        if coinbase_if_zero == 0:
            inskip = [0]
            i += len(tx.msg_tx.tx_in)
            continue
            
        for tx_in in tx.msg_tx.tx_in:
            inmap[tx_in.previous_out_point] = i
            i += 1
            
    in_count = i
    i = 0
    outskip = []
    
    # Find outputs to skip
    for tx in blk.transactions:
        for out_idx, tx_out in enumerate(tx.msg_tx.tx_out):
            if is_unspendable(tx_out):
                outskip.append(i)
                i += 1
                continue
                
            op = OutPoint(hash=tx.hash(), index=out_idx)
            if op in inmap:
                inskip.append(inmap[op])
                outskip.append(i)
            i += 1
            
    out_count = i
    inskip.sort()
    
    return in_count, out_count, inskip, outskip

def prefix_len16(b: bytes) -> bytes:
    """Add 2-byte length prefix to bytes"""
    return struct.pack(">H", len(b)) + b

def pop_prefix_len16(b: bytes) -> Tuple[bytes, bytes]:
    """Remove and parse 2-byte length prefix"""
    if len(b) < 2:
        raise ValueError(f"PrefixedLen slice only {len(b)} long")
        
    l = struct.unpack(">H", b[:2])[0]
    payload = b[2:]
    
    if l > len(payload):
        raise ValueError(f"Prefixed {l} but payload {len(payload)} left")
        
    return payload[:l], payload[l:]

def check_magic_byte(bytes_given: bytes) -> bool:
    """Check if bytes match Bitcoin network magic bytes"""
    magic_bytes = {
        b'\x0b\x11\x09\x07',  # testnet
        b'\xf9\xbe\xb4\xd9',  # mainnet
        b'\xfa\xbf\xb5\xda',  # regtest
        b'\x0a\x03\xcf\x40'   # signet
    }
    
    if bytes_given not in magic_bytes:
        print(f"got non magic bytes {bytes_given.hex()}, finishing")
        return False
    return True

def has_access(file_name: str) -> bool:
    """Check if we have access to named file"""
    try:
        os.stat(file_name)
        return True
    except FileNotFoundError:
        return False

def is_unspendable(o: TxOut) -> bool:
    """Determine if TxOut is spendable"""
    if len(o.pk_script) > 10000:
        return True
    if len(o.pk_script) > 0 and o.pk_script[0] == 0x6a:  # OP_RETURN
        return True
    return False 
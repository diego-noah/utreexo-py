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
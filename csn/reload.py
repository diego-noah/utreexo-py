import struct
from dataclasses import dataclass
from typing import Dict, Tuple
from pathlib import Path

from btcd.chaincfg.chainhash import Hash
from btcd.wire import OutPoint
from accumulator import Pollard
from btcacc import LeafData

# Constants
POLLARD_FILE_PATH = "pollard.dat"

def restore_pollard() -> Tuple[int, Pollard, Dict[OutPoint, LeafData]]:
    """
    Restores the pollard from disk to memory.
    Returns height, pollard, and utxos.
    """
    try:
        with open(POLLARD_FILE_PATH, "rb") as pollard_file:
            # Restore UTXOs
            num_utxos = struct.unpack(">I", pollard_file.read(4))[0]
            
            utxos = {}
            for _ in range(num_utxos):
                utxo = LeafData.deserialize(pollard_file)
                op = OutPoint(
                    hash=Hash(utxo.tx_hash),
                    index=utxo.index
                )
                utxos[op] = utxo
            
            # Read height
            height = struct.unpack(">i", pollard_file.read(4))[0]
            
            # Restore pollard
            pollard = Pollard()
            pollard.restore_pollard(pollard_file)
            
            return height, pollard, utxos
            
    except FileNotFoundError:
        # Return empty state if file doesn't exist
        return 0, Pollard(), {}
    except Exception as e:
        raise Exception(f"Error restoring pollard: {str(e)}")

def save_ibd_sim_data(csn) -> None:
    """
    Saves the state of IBD simulation for later resumption.
    Saves height, UTXOs, and pollard state.
    """
    try:
        with open(POLLARD_FILE_PATH, "wb") as pol_file:
            # Save number of UTXOs
            pol_file.write(struct.pack(">I", len(csn.utxo_store)))
            
            # Save all found UTXOs
            for utxo in csn.utxo_store.values():
                utxo.serialize(pol_file)
            
            # Save current height
            pol_file.write(struct.pack(">i", csn.current_height))
            
            # Save pollard state
            csn.pollard.write_pollard(pol_file)
            
    except Exception as e:
        raise Exception(f"Error saving IBD sim data: {str(e)}") 
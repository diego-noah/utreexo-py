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
    if not pollard_exists():
        return 0, Pollard(), {}

    try:
        with get_pollard_path().open("rb") as pollard_file:
            # Restore UTXOs
            num_utxos = struct.unpack(">I", pollard_file.read(4))[0]

            utxos = {}
            for _ in range(num_utxos):
                utxo = LeafData.deserialize(pollard_file)
                op = OutPoint(hash=Hash(utxo.tx_hash), index=utxo.index)
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
        with get_pollard_path().open("wb") as pol_file:
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


def get_pollard_path(custom_path: str = None) -> Path:
    """
    Returns the path to the pollard file, allowing for a custom path override.

    Args:
        custom_path: Optional custom path for the pollard file

    Returns:
        Path object for the pollard file location
    """
    if custom_path:
        return Path(custom_path)
    return Path(POLLARD_FILE_PATH)


def pollard_exists(custom_path: str = None) -> bool:
    """
    Checks if a pollard file exists at the specified location.

    Args:
        custom_path: Optional custom path to check

    Returns:
        bool: True if pollard file exists, False otherwise
    """
    return get_pollard_path(custom_path).exists()


def delete_pollard(custom_path: str = None) -> None:
    """
    Deletes the pollard file if it exists.

    Args:
        custom_path: Optional custom path to the pollard file to delete

    Raises:
        Exception: If deletion fails
    """
    path = get_pollard_path(custom_path)
    try:
        if path.exists():
            path.unlink()
    except Exception as e:
        raise Exception(f"Failed to delete pollard file at {path}: {str(e)}")


def get_pollard_size(custom_path: str = None) -> int:
    """
    Returns the size of the pollard file in bytes.

    Args:
        custom_path: Optional custom path to the pollard file

    Returns:
        int: Size of pollard file in bytes, 0 if file doesn't exist
    """
    path = get_pollard_path(custom_path)
    try:
        return path.stat().st_size if path.exists() else 0
    except Exception as e:
        raise Exception(f"Failed to get pollard file size at {path}: {str(e)}")

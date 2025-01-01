import unittest
from unittest.mock import MagicMock, patch, mock_open
from io import BytesIO
from btcd.wire import OutPoint
from accumulator import Pollard
from btcacc import LeafData

from pollard_module import restore_pollard, save_ibd_sim_data, POLLARD_FILE_PATH

class TestPollardFunctions(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data=b'\x00\x00\x00\x02' + b'\x00' * 32 + b'\x00\x00\x00\x01' + b'\x00\x00\x00\x01')
    @patch("struct.unpack", side_effect=lambda fmt, data: (2,) if fmt == ">I" else (1,) if fmt == ">i" else (0,))
    def test_restore_pollard_success(self, mock_unpack, mock_open):
        mock_utxo = MagicMock(spec=LeafData)
        mock_utxo.deserialize.return_value = mock_utxo
        mock_pollard = MagicMock(spec=Pollard)
        mock_pollard.restore_pollard = MagicMock()

        height, pollard, utxos = restore_pollard()

        mock_open.assert_called_with(POLLARD_FILE_PATH, "rb")

        self.assertEqual(height, 1)
        self.assertIsInstance(pollard, Pollard)
        self.assertEqual(len(utxos), 2)

        mock_pollard.restore_pollard.assert_called_once_with(mock_open())

    @patch("builtins.open", new_callable=mock_open)
    @patch("struct.pack", return_value=None)
    def test_save_ibd_sim_data_success(self, mock_pack, mock_open):
        mock_csn = MagicMock()
        mock_csn.utxo_store = {OutPoint(hash=b"123", index=1): LeafData()}
        mock_csn.current_height = 100
        mock_csn.pollard.write_pollard = MagicMock()

        save_ibd_sim_data(mock_csn)

        mock_open.assert_called_with(POLLARD_FILE_PATH, "wb")

        mock_open().write.assert_called()

        mock_csn.pollard.write_pollard.assert_called_once_with(mock_open())

    @patch("builtins.open", new_callable=mock_open)
    @patch("struct.pack", return_value=None)
    def test_save_ibd_sim_data_error(self, mock_pack, mock_open):
        mock_open.side_effect = IOError("Unable to write to file")
        mock_csn = MagicMock()

        with self.assertRaises(Exception):
            save_ibd_sim_data(mock_csn)

    @patch("builtins.open", new_callable=mock_open, read_data=b'')
    def test_restore_pollard_file_not_found(self, mock_open):
        mock_open.side_effect = FileNotFoundError

        height, pollard, utxos = restore_pollard()

        self.assertEqual(height, 0)
        self.assertIsInstance(pollard, Pollard)
        self.assertEqual(len(utxos), 0)

if __name__ == "__main__":
    unittest.main()

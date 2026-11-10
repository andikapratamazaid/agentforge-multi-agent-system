"""Tes penanganan kesalahan CLI: pesan ramah, bukan traceback."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from agentforge.cli import main


class TestCliErrors(unittest.TestCase):
    def _run(self, argv):
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = main(argv)
        return code, err.getvalue()

    def test_missing_input_file(self):
        code, err = self._run(
            ["run", "--workflow", "konten", "--input-file", "tidak/ada.txt"]
        )
        self.assertEqual(code, 2)
        self.assertIn("File input tidak ditemukan", err)
        self.assertNotIn("Traceback", err)

    def test_laporan_data_without_csv(self):
        code, err = self._run(
            ["run", "--workflow", "laporan_data", "--title", "X", "--input", "laporan data"]
        )
        self.assertEqual(code, 2)
        self.assertIn("--csv", err)
        self.assertNotIn("Traceback", err)

    def test_missing_csv_file(self):
        code, err = self._run(
            ["run", "--workflow", "laporan_data", "--csv", "tidak/ada.csv", "--input", "laporan"]
        )
        self.assertEqual(code, 2)
        self.assertIn("File CSV tidak ditemukan", err)
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()

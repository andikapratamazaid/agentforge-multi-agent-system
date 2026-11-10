"""Tes langsung tools deterministik: csv_tools dan text_tools."""

import tempfile
import unittest
from pathlib import Path

from agentforge.config import PROJECT_ROOT
from agentforge.tools import csv_tools, text_tools

SAMPLES = PROJECT_ROOT / "data" / "samples"


class TestCsvTools(unittest.TestCase):
    def test_analyze_sample_csv(self):
        result = csv_tools.analyze_csv(SAMPLES / "penjualan_mingguan.csv")
        self.assertEqual(result["rows"], 18)
        self.assertEqual(
            result["columns"], ["minggu", "produk", "unit_terjual", "pendapatan"]
        )
        self.assertEqual(result["group_column"], "produk")
        top_group = next(iter(result["group_summary"].items()))
        self.assertEqual(top_group[0], "Soto Kecil")
        self.assertEqual(result["trend"]["column"], "pendapatan")
        self.assertEqual(result["trend"]["direction"], "naik")
        self.assertAlmostEqual(result["trend"]["change_pct"], 12.4, places=1)
        self.assertTrue(any("18 baris" in f for f in result["facts"]))

    def test_number_parsing_formats(self):
        self.assertEqual(csv_tools._to_number("2060000"), 2060000.0)
        self.assertEqual(csv_tools._to_number("1.5"), 1.5)
        self.assertEqual(csv_tools._to_number("1,5"), 1.5)
        self.assertEqual(csv_tools._to_number("2.500,75"), 2500.75)
        self.assertIsNone(csv_tools._to_number("bukan angka"))
        self.assertIsNone(csv_tools._to_number(""))

    def test_indonesian_decimal_comma_column_is_numeric(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.csv"
            # Desimal koma di dalam CSV wajib dikutip agar tidak
            # terbaca sebagai pemisah kolom.
            path.write_text('item,nilai\nA,"1,5"\nB,"2,5"\nC,"3,5"\nD,"4,5"\n', encoding="utf-8")
            result = csv_tools.analyze_csv(path)
        self.assertIn("nilai", result["numeric_summary"])
        self.assertAlmostEqual(result["numeric_summary"]["nilai"]["total"], 12.0)

    def test_missing_csv_raises_clear_errors(self):
        with self.assertRaises(ValueError):
            csv_tools.read_csv("")
        with self.assertRaises(FileNotFoundError):
            csv_tools.read_csv(SAMPLES / "tidak_ada.csv")


class TestTextTools(unittest.TestCase):
    def test_classify_billing_ticket(self):
        text = (SAMPLES / "tiket_support.txt").read_text(encoding="utf-8")
        result = text_tools.classify_ticket(text)
        self.assertEqual(result["category"], "tagihan")
        self.assertEqual(result["priority"], "tinggi")

    def test_extract_facts_and_points(self):
        text = (SAMPLES / "tiket_support.txt").read_text(encoding="utf-8")
        facts = text_tools.extract_facts(text)
        self.assertTrue(facts)
        self.assertTrue(all(any(ch.isdigit() for ch in f) for f in facts))
        points = text_tools.extract_points(text)
        self.assertGreaterEqual(len(points), 1)
        self.assertLessEqual(len(points), 6)

    def test_keywords_skip_stopwords(self):
        keywords = text_tools.extract_keywords(
            "Tagihan tagihan tagihan dan yang untuk pelanggan pelanggan"
        )
        self.assertIn("tagihan", keywords)
        self.assertNotIn("yang", keywords)
        self.assertNotIn("dan", keywords)


if __name__ == "__main__":
    unittest.main()

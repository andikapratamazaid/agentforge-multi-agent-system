"""Tes end-to-end tiga workflow dalam mode demo."""

import unittest

from agentforge.cli import sample_tasks
from agentforge.orchestrator import Orchestrator


class TestWorkflowsDemo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orch = Orchestrator(force_demo=True)
        cls.results = {t["workflow"]: cls.orch.run(t) for t in sample_tasks()}

    def test_konten_end_to_end(self):
        r = self.results["konten"]
        self.assertEqual(r["status"], "selesai")
        self.assertTrue(r["reviewer_passed"])
        self.assertGreaterEqual(r["reviewer_score"], 70)
        self.assertGreater(len(r["final_output"]), 100)
        self.assertGreaterEqual(r["step_count"], 4)
        self.assertGreater(r["total_cost_usd"], 0)

    def test_laporan_data_end_to_end(self):
        r = self.results["laporan_data"]
        self.assertEqual(r["status"], "selesai")
        self.assertTrue(r["reviewer_passed"])
        self.assertTrue(any("18 baris" in f for f in r["analysis_facts"]))
        self.assertIn("pendapatan", r["final_output"])

    def test_triase_support_end_to_end(self):
        r = self.results["triase_support"]
        self.assertEqual(r["status"], "selesai")
        self.assertTrue(r["reviewer_passed"])
        self.assertEqual(r["classification"]["category"], "tagihan")
        self.assertEqual(r["classification"]["priority"], "tinggi")

    def test_free_task_is_routed(self):
        r = self.orch.run({
            "title": "Artikel Kopi",
            "input_text": "Tulis artikel tentang manfaat kopi robusta untuk petani, target pembaca adalah petani muda, budidaya kopi memberi manfaat ekonomi yang penting dan utama bagi desa.",
        })
        self.assertEqual(r["workflow"], "konten")
        self.assertEqual(r["status"], "selesai")

    def test_all_steps_logged_with_models(self):
        for r in self.results.values():
            for step in r["steps"]:
                self.assertIn("model", step)
                self.assertIn("cost_usd", step)
                self.assertEqual(step["status"], "selesai")


if __name__ == "__main__":
    unittest.main()

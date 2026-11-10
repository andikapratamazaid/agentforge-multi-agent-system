"""Tes Conductor: perutean tugas dan validitas rencana langkah."""

import unittest

from agentforge.agents.conductor import WORKFLOWS, classify_task, validate_plan
from agentforge.orchestrator import Orchestrator


class TestClassifyTask(unittest.TestCase):
    def test_routing_laporan_data(self):
        self.assertEqual(
            classify_task("Tolong buat laporan data penjualan dari file csv mingguan ini"),
            "laporan_data",
        )

    def test_routing_triase_support(self):
        self.assertEqual(
            classify_task("Ada tiket keluhan pelanggan soal tagihan yang terpotong dua kali"),
            "triase_support",
        )

    def test_routing_konten_default(self):
        self.assertEqual(classify_task("Tulis artikel blog tentang kopi robusta Lampung"), "konten")


class TestPlan(unittest.TestCase):
    def setUp(self):
        self.orch = Orchestrator(force_demo=True)

    def test_all_workflow_plans_valid(self):
        for workflow in WORKFLOWS:
            plan = self.orch.conductor.plan({"workflow": workflow, "title": "Uji", "input_text": "isi"})
            self.assertEqual(validate_plan(plan["steps"]), [])
            ids = [s["id"] for s in plan["steps"]]
            self.assertEqual(ids[0], plan["steps"][0]["id"])
            self.assertIn("review", ids)
            self.assertEqual(plan["workflow"], workflow)

    def test_validate_plan_detects_bad_dependency(self):
        bad = [{"id": "draf", "agent": "writer", "action": "draft", "depends_on": ["riset"]}]
        problems = validate_plan(bad)
        self.assertTrue(any("riset" in p for p in problems))

    def test_validate_plan_detects_duplicate(self):
        dup = [
            {"id": "a", "agent": "research", "action": "structure", "depends_on": []},
            {"id": "a", "agent": "research", "action": "structure", "depends_on": []},
        ]
        self.assertTrue(any("duplikat" in p for p in validate_plan(dup)))

    def test_unknown_workflow_rejected(self):
        with self.assertRaises(ValueError):
            self.orch.conductor.plan({"workflow": "tidak_ada", "title": "x", "input_text": "y"})


if __name__ == "__main__":
    unittest.main()

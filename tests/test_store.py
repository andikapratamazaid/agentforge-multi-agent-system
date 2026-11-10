"""Tes penulisan riwayat run ke SQLite."""

import tempfile
import unittest
from pathlib import Path

from agentforge.cli import sample_tasks
from agentforge.orchestrator import Orchestrator
from agentforge.store import init_db, list_runs, list_steps, save_run


class TestStore(unittest.TestCase):
    def test_save_and_read_run(self):
        orch = Orchestrator(force_demo=True)
        task = [t for t in sample_tasks() if t["workflow"] == "konten"][0]
        result = orch.run(task)
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            conn = init_db(db_path)
            save_run(conn, result)
            runs = list_runs(conn)
            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0]["run_id"], result["run_id"])
            self.assertEqual(runs[0]["reviewer_score"], result["reviewer_score"])
            steps = list_steps(conn, result["run_id"])
            self.assertEqual(len(steps), result["step_count"])
            self.assertTrue(all(s["status"] == "selesai" for s in steps))
            conn.close()

    def test_schema_tables_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = init_db(Path(tmp) / "schema.db")
            names = {
                row[0]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            self.assertIn("runs", names)
            self.assertIn("run_steps", names)
            conn.close()


if __name__ == "__main__":
    unittest.main()

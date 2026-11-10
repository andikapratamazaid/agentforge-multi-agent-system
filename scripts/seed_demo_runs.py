"""Jalankan tiga workflow contoh dan simpan hasilnya ke:
- outputs/sample_runs.json     (hasil run lengkap)
- dashboard/data/runs.json     (data untuk dashboard statis)
- db/agentforge.db             (riwayat run SQLite sesuai schema.sql)

Seed selalu berjalan dalam mode demo (force_demo) agar datanya
deterministik dan bebas biaya, meskipun OPENROUTER_API_KEY terisi.

Jalankan dari root project:
    python scripts/seed_demo_runs.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agentforge.cli import sample_tasks  # noqa: E402
from agentforge.orchestrator import Orchestrator  # noqa: E402
from agentforge.store import init_db, save_run  # noqa: E402


def main() -> int:
    orch = Orchestrator(force_demo=True)
    results = [orch.run(task) for task in sample_tasks()]

    outputs_dir = PROJECT_ROOT / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    (outputs_dir / "sample_runs.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    dash_data = PROJECT_ROOT / "dashboard" / "data"
    dash_data.mkdir(parents=True, exist_ok=True)
    (dash_data / "runs.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    db_dir = PROJECT_ROOT / "db"
    db_dir.mkdir(exist_ok=True)
    conn = init_db(db_dir / "agentforge.db")
    for r in results:
        save_run(conn, r)
    conn.close()

    for r in results:
        print(f"{r['workflow']}: skor {r['reviewer_score']}, {r['step_count']} langkah, biaya ${r['total_cost_usd']}")
    print("Seed selesai: outputs/sample_runs.json, dashboard/data/runs.json, db/agentforge.db")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

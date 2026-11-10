"""Antarmuka baris perintah AgentForge.

Contoh:
  python -m agentforge run --workflow konten --title "Kasir Digital" \
      --input-file data/samples/brief_konten.txt
  python -m agentforge run --workflow laporan_data \
      --title "Penjualan Mingguan" --csv data/samples/penjualan_mingguan.csv
  python -m agentforge demo

Tanpa OPENROUTER_API_KEY, semua perintah berjalan dalam mode demo
deterministik. Hasil run dicetak sebagai JSON ringkas dan dapat
disimpan ke file dengan --out serta ke SQLite dengan --db.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import PROJECT_ROOT
from .orchestrator import Orchestrator
from .store import init_db, save_run


def _read_input(args) -> str:
    if getattr(args, "input_file", None):
        path = Path(args.input_file)
        if not path.is_file():
            raise FileNotFoundError(f"File input tidak ditemukan: {args.input_file}")
        return path.read_text(encoding="utf-8")
    return getattr(args, "input", "") or ""


def cmd_run(args) -> int:
    orch = Orchestrator()
    task = {
        "workflow": args.workflow,
        "title": args.title or "Tugas AgentForge",
        "input_text": _read_input(args),
        "audience": args.audience or "pembaca umum",
    }
    if args.csv:
        task["csv_path"] = args.csv
    result = orch.run(task)
    summary = {
        "run_id": result["run_id"],
        "workflow": result["workflow"],
        "status": result["status"],
        "mode": result["mode"],
        "reviewer_score": result["reviewer_score"],
        "reviewer_passed": result["reviewer_passed"],
        "revision_rounds": result["revision_rounds"],
        "total_tokens": result["total_tokens"],
        "total_cost_usd": result["total_cost_usd"],
        "final_output": result["final_output"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.out:
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.db:
        conn = init_db(args.db)
        save_run(conn, result)
        conn.close()
    return 0 if result["status"] == "selesai" else 1


def sample_tasks() -> list[dict]:
    """Tiga tugas contoh bawaan untuk perintah demo dan seed."""
    samples = PROJECT_ROOT / "data" / "samples"
    return [
        {
            "workflow": "konten",
            "title": "Manfaat Kasir Digital untuk Warung Makan",
            "input_text": (samples / "brief_konten.txt").read_text(encoding="utf-8"),
            "audience": "pemilik warung makan kecil",
        },
        {
            "workflow": "laporan_data",
            "title": "Laporan Penjualan Mingguan",
            "input_text": "Susun laporan data penjualan mingguan per produk dan bacakan tren pendapatannya.",
            "csv_path": str(samples / "penjualan_mingguan.csv"),
        },
        {
            "workflow": "triase_support",
            "title": "Tiket Tagihan Ganda",
            "input_text": (samples / "tiket_support.txt").read_text(encoding="utf-8"),
        },
    ]


def cmd_demo(args) -> int:
    orch = Orchestrator()
    results = [orch.run(task) for task in sample_tasks()]
    for r in results:
        print(
            f"{r['run_id']} | {r['workflow']} | skor reviewer {r['reviewer_score']} "
            f"| revisi {r['revision_rounds']} | token {r['total_tokens']} "
            f"| biaya ${r['total_cost_usd']}"
        )
    if args.out:
        Path(args.out).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.db:
        conn = init_db(args.db)
        for r in results:
            save_run(conn, r)
        conn.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentforge", description="AgentForge Multi-Agent Automation System")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Jalankan satu workflow")
    p_run.add_argument("--workflow", choices=["konten", "laporan_data", "triase_support"], default=None)
    p_run.add_argument("--title", default=None)
    p_run.add_argument("--input", default=None, help="Teks tugas atau brief")
    p_run.add_argument("--input-file", default=None, help="File teks tugas atau brief")
    p_run.add_argument("--csv", default=None, help="Path CSV untuk workflow laporan_data")
    p_run.add_argument("--audience", default=None)
    p_run.add_argument("--out", default=None, help="Simpan hasil run lengkap ke file JSON")
    p_run.add_argument("--db", default=None, help="Simpan run ke SQLite pada path ini")
    p_run.set_defaults(func=cmd_run)

    p_demo = sub.add_parser("demo", help="Jalankan tiga workflow contoh")
    p_demo.add_argument("--out", default=None)
    p_demo.add_argument("--db", default=None)
    p_demo.set_defaults(func=cmd_demo)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        # Kesalahan penggunaan yang umum (file tidak ada, CSV belum
        # diberikan, semua model gagal) ditampilkan sebagai pesan
        # singkat, bukan traceback.
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

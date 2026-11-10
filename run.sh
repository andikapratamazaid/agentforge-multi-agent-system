#!/usr/bin/env bash
# Alur pemeriksaan lengkap AgentForge: tes, seed demo, dan evaluasi.
set -e
cd "$(dirname "$0")"

echo "== Menjalankan test suite =="
python3 -m unittest discover -s tests -t . -v

echo
echo "== Membuat data demo (outputs, dashboard, SQLite) =="
python3 scripts/seed_demo_runs.py

echo
echo "== Menjalankan harness evaluasi =="
python3 evaluation/run_evaluation.py

echo
echo "Selesai. Dashboard: sajikan folder ini dengan 'python3 -m http.server'"
echo "lalu buka http://localhost:8000/dashboard/"

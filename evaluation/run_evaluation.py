"""Harness evaluasi AgentForge (Lapis 4).

Menjalankan semua tugas di evaluation/benchmark.json dalam mode
demo, lalu menilai setiap run dengan lima kriteria terukur:
1. plan_valid: rencana Conductor lolos validasi DAG.
2. all_steps_completed: semua langkah berstatus selesai.
3. reviewer_passed: skor Reviewer mencapai ambang setelah revisi.
4. required_elements_complete: seluruh elemen wajib jenis draf
   ditemukan pada draf final.
5. final_output_substantive: output final tidak kosong dan
   panjangnya memadai (lebih dari 150 karakter).

Hasil ditulis ke evaluation/results.json dan diringkas di layar.
Angka berasal dari run yang sebenarnya, bukan perkiraan.

Jalankan dari root project:
    python evaluation/run_evaluation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agentforge.agents.conductor import WORKFLOWS, validate_plan  # noqa: E402
from agentforge.orchestrator import Orchestrator  # noqa: E402
from agentforge.tools.rubric_tools import REQUIRED_ELEMENTS  # noqa: E402


def load_tasks() -> list[dict]:
    bench = json.loads((PROJECT_ROOT / "evaluation" / "benchmark.json").read_text(encoding="utf-8"))
    tasks = []
    for raw in bench["tasks"]:
        task = {"workflow": raw["workflow"], "title": raw["title"]}
        if "input_file" in raw:
            task["input_text"] = (PROJECT_ROOT / raw["input_file"]).read_text(encoding="utf-8")
        else:
            task["input_text"] = raw.get("input_text", "")
        if "csv_file" in raw:
            task["csv_path"] = str(PROJECT_ROOT / raw["csv_file"])
        if "audience" in raw:
            task["audience"] = raw["audience"]
        tasks.append((raw["id"], task))
    return tasks


def evaluate() -> dict:
    orch = Orchestrator(force_demo=True)
    per_task = []
    for task_id, task in load_tasks():
        plan = orch.conductor.plan(task)
        plan_valid = validate_plan(plan["steps"]) == []
        result = orch.run(task)
        kind = WORKFLOWS[task["workflow"]]["draft_kind"]
        required = REQUIRED_ELEMENTS.get(kind, [])
        # Elemen wajib dinilai dari komponen review terakhir pada draf final.
        from agentforge.tools.rubric_tools import score_draft

        source = task.get("input_text", "")
        final_review = score_draft(kind, source, result["draft"], source)
        elements_complete = len(final_review["missing_elements"]) == 0 if required else True
        criteria = {
            "plan_valid": plan_valid,
            "all_steps_completed": result["status"] == "selesai" and all(
                s["status"] == "selesai" for s in result["steps"]
            ),
            "reviewer_passed": bool(result["reviewer_passed"]),
            "required_elements_complete": elements_complete,
            "final_output_substantive": len(result["final_output"]) > 150,
        }
        per_task.append(
            {
                "task_id": task_id,
                "workflow": task["workflow"],
                "reviewer_score": result["reviewer_score"],
                "revision_rounds": result["revision_rounds"],
                "total_tokens": result["total_tokens"],
                "total_cost_usd": result["total_cost_usd"],
                "criteria": criteria,
                "passed_all": all(criteria.values()),
            }
        )

    per_workflow: dict[str, dict] = {}
    for row in per_task:
        wf = per_workflow.setdefault(row["workflow"], {"tasks": 0, "passed_all": 0, "avg_score": 0.0})
        wf["tasks"] += 1
        wf["passed_all"] += 1 if row["passed_all"] else 0
        wf["avg_score"] += row["reviewer_score"]
    for wf in per_workflow.values():
        wf["avg_score"] = round(wf["avg_score"] / wf["tasks"], 1)

    criteria_totals: dict[str, int] = {}
    for row in per_task:
        for name, ok in row["criteria"].items():
            criteria_totals[name] = criteria_totals.get(name, 0) + (1 if ok else 0)

    return {
        "mode": "demo",
        "task_count": len(per_task),
        "tasks_passed_all": sum(1 for r in per_task if r["passed_all"]),
        "criteria_passed": criteria_totals,
        "per_workflow": per_workflow,
        "per_task": per_task,
    }


def main() -> int:
    report = evaluate()
    out = PROJECT_ROOT / "evaluation" / "results.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Tugas: {report['task_count']}, lulus semua kriteria: {report['tasks_passed_all']}")
    for wf, s in report["per_workflow"].items():
        print(f"- {wf}: {s['passed_all']}/{s['tasks']} tugas, rata-rata skor reviewer {s['avg_score']}")
    print("Per kriteria:", report["criteria_passed"])
    print(f"Hasil ditulis ke {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

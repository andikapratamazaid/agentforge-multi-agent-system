"""Conductor: orchestrator AgentForge.

Tugasnya:
1. Mengklasifikasikan tugas bebas ke salah satu workflow.
2. Menyusun rencana langkah (DAG sederhana) dari template workflow.
3. Menyintesis hasil final dari draf yang sudah lulus review.

Template langkah memakai dependensi eksplisit agar Orchestration
Engine dapat memvalidasi urutan sebelum eksekusi.
"""

from __future__ import annotations

WORKFLOWS: dict[str, dict] = {
    "konten": {
        "label": "Pipeline Konten",
        "draft_kind": "artikel",
        "steps": [
            {"id": "riset", "agent": "research", "action": "structure", "depends_on": []},
            {"id": "draf", "agent": "writer", "action": "draft", "depends_on": ["riset"]},
            {"id": "review", "agent": "reviewer", "action": "review", "depends_on": ["draf"]},
        ],
    },
    "laporan_data": {
        "label": "Pipeline Laporan Data",
        "draft_kind": "laporan",
        "steps": [
            {"id": "analisis", "agent": "data", "action": "analyze", "depends_on": []},
            {"id": "draf", "agent": "writer", "action": "draft", "depends_on": ["analisis"]},
            {"id": "review", "agent": "reviewer", "action": "review", "depends_on": ["draf"]},
        ],
    },
    "triase_support": {
        "label": "Pipeline Triase Support",
        "draft_kind": "balasan",
        "steps": [
            {"id": "klasifikasi", "agent": "research", "action": "classify", "depends_on": []},
            {"id": "draf", "agent": "writer", "action": "draft", "depends_on": ["klasifikasi"]},
            {"id": "review", "agent": "reviewer", "action": "review", "depends_on": ["draf"]},
        ],
    },
}

DATA_KEYWORDS = ["csv", "data", "penjualan", "dataset", "laporan data", "statistik", "grafik"]
SUPPORT_KEYWORDS = ["tiket", "keluhan", "pelanggan", "support", "bantuan", "komplain", "cs "]


def classify_task(text: str) -> str:
    """Perutean deterministik untuk tugas tanpa workflow eksplisit."""
    low = " " + text.lower() + " "
    if any(kw in low for kw in DATA_KEYWORDS):
        return "laporan_data"
    if any(kw in low for kw in SUPPORT_KEYWORDS):
        return "triase_support"
    return "konten"


def validate_plan(steps: list[dict]) -> list[str]:
    """Kembalikan daftar masalah rencana; kosong berarti valid."""
    problems: list[str] = []
    seen: set[str] = set()
    for step in steps:
        if step["id"] in seen:
            problems.append(f"ID langkah duplikat: {step['id']}")
        for dep in step.get("depends_on", []):
            if dep not in seen:
                problems.append(f"Langkah {step['id']} bergantung pada {dep} yang belum ada sebelumnya")
        seen.add(step["id"])
    return problems


class Conductor:
    name = "conductor"
    system_prompt = (
        "Anda adalah Conductor, orchestrator sistem multi-agent. "
        "Pecah tugas menjadi langkah yang jelas, tugaskan ke agent "
        "spesialis, dan sintesis hasil akhirnya secara ringkas."
    )

    def __init__(self, router):
        self.router = router

    def plan(self, task: dict) -> dict:
        workflow = task.get("workflow") or classify_task(task.get("input_text", "") + " " + task.get("title", ""))
        if workflow not in WORKFLOWS:
            raise ValueError(f"Workflow tidak dikenal: {workflow}")
        spec = WORKFLOWS[workflow]
        steps = [dict(s) for s in spec["steps"]]
        problems = validate_plan(steps)
        if problems:
            raise ValueError("Rencana tidak valid: " + "; ".join(problems))
        return {"workflow": workflow, "label": spec["label"], "draft_kind": spec["draft_kind"], "steps": steps}

    def synthesize(self, workflow: str, final_draft: str, review: dict):
        payload = {
            "workflow": workflow,
            "parts": [final_draft, f"Skor reviewer akhir: {review['score']} dari 100."],
        }
        completion = self.router.complete(self.name, "synthesize", payload, self.system_prompt)
        return completion.text, completion

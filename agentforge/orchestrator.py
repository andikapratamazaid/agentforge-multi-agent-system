"""Orchestration Engine AgentForge (Lapis 1).

Menjalankan rencana Conductor langkah demi langkah sesuai
dependensi, dengan retry sederhana (satu kali pengulangan) untuk
langkah yang gagal. Setelah langkah review, engine menjalankan
siklus revisi: bila skor Reviewer di bawah ambang, Writer diminta
memperbaiki draf berdasarkan catatan, lalu Reviewer menilai ulang,
maksimal sesuai konfigurasi max_revisions.

Setiap langkah dicatat lengkap: id langkah, agent, aksi, model,
mode, token prompt/completion, biaya, status, dan jumlah percobaan.
Hasil run dapat disimpan ke SQLite melalui store.py.
"""

from __future__ import annotations

import time
import uuid

from .agents.conductor import Conductor
from .agents.data_agent import DataAgent
from .agents.research import ResearchAgent
from .agents.reviewer import ReviewerAgent
from .agents.writer import WriterAgent
from .config import load_config
from .router import Completion, ModelRouter


class Orchestrator:
    def __init__(self, cfg: dict | None = None, router: ModelRouter | None = None, force_demo: bool = False):
        self.cfg = cfg or load_config()
        self.router = router or ModelRouter(self.cfg, force_demo=force_demo)
        self.conductor = Conductor(self.router)
        self.research = ResearchAgent(self.router)
        self.data = DataAgent(self.router)
        self.writer = WriterAgent(self.router)
        self.reviewer = ReviewerAgent(self.router, threshold=int(self.cfg.get("review_threshold", 70)))
        self.max_revisions = int(self.cfg.get("max_revisions", 2))

    # ---------- utilitas log ----------
    @staticmethod
    def _log_entry(step_id: str, agent: str, action: str, completion: Completion | None, status: str, attempts: int, started: float) -> dict:
        entry = {
            "step_id": step_id,
            "agent": agent,
            "action": action,
            "status": status,
            "attempts": attempts,
            "duration_ms": int((time.time() - started) * 1000),
            "model": completion.model if completion else "deterministic-tool",
            "mode": completion.mode if completion else "tool",
            "prompt_tokens": completion.prompt_tokens if completion else 0,
            "completion_tokens": completion.completion_tokens if completion else 0,
            "cost_usd": round(completion.cost_usd, 6) if completion else 0.0,
        }
        return entry

    def _run_step(self, logs: list[dict], step_id: str, agent: str, action: str, fn):
        """Jalankan satu langkah dengan satu kali retry."""
        started = time.time()
        attempts = 0
        while True:
            attempts += 1
            try:
                output, completion = fn()
                logs.append(self._log_entry(step_id, agent, action, completion, "selesai", attempts, started))
                return output
            except Exception:
                if attempts >= 2:
                    logs.append(self._log_entry(step_id, agent, action, None, "gagal", attempts, started))
                    raise
                continue

    # ---------- siklus review dan revisi ----------
    def review_cycle(self, kind: str, brief: str, source_text: str, draft: str, revise_fn, logs: list[dict], step_prefix: str = "review"):
        """Nilai draf, revisi bila perlu, dan nilai ulang.

        Mengembalikan (draf_final, review_terakhir, jumlah_revisi).
        """
        review, _ = self._run_review(kind, brief, source_text, draft, logs, step_prefix)
        rounds = 0
        current = draft
        while not review["passed"] and rounds < self.max_revisions:
            rounds += 1
            started = time.time()
            current = revise_fn(current, review)
            logs.append(
                self._log_entry(f"{step_prefix}_revisi_{rounds}", "writer", "revise", None, "selesai", 1, started)
            )
            review, _ = self._run_review(kind, brief, source_text, current, logs, f"{step_prefix}_ulang_{rounds}")
        return current, review, rounds

    def _run_review(self, kind, brief, source_text, draft, logs, step_id):
        started = time.time()
        attempts = 0
        while True:
            attempts += 1
            try:
                result, completion = self.reviewer.review(kind, brief, draft, source_text)
                logs.append(self._log_entry(step_id, "reviewer", "review", completion, "selesai", attempts, started))
                return result, completion
            except Exception:
                if attempts >= 2:
                    logs.append(self._log_entry(step_id, "reviewer", "review", None, "gagal", attempts, started))
                    raise

    # ---------- eksekusi workflow ----------
    def run(self, task: dict) -> dict:
        run_id = "run-" + uuid.uuid4().hex[:8]
        logs: list[dict] = []
        plan = self.conductor.plan(task)
        workflow = plan["workflow"]
        kind = plan["draft_kind"]
        title = task.get("title", plan["label"])
        input_text = task.get("input_text", "")
        context: dict = {}

        for step in plan["steps"]:
            action = step["action"]
            agent = step["agent"]
            step_id = step["id"]

            if action == "structure":
                out = self._run_step(logs, step_id, agent, action, lambda: (self.research.structure(input_text), None))
                context["research"] = out
            elif action == "classify":
                out = self._run_step(logs, step_id, agent, action, lambda: (self.research.classify(input_text), None))
                context["classification"] = out
            elif action == "analyze":
                csv_path = task.get("csv_path", "")
                out = self._run_step(logs, step_id, agent, action, lambda: self.data.analyze(csv_path, title))
                context["analysis"] = out
            elif action == "draft":
                if workflow == "konten":
                    draft = self._run_step(
                        logs, step_id, agent, action,
                        lambda: self.writer.draft_article(title, context["research"], task.get("audience", "pembaca umum")),
                    )
                elif workflow == "laporan_data":
                    draft = self._run_step(
                        logs, step_id, agent, action,
                        lambda: self.writer.draft_report(title, context["analysis"]),
                    )
                else:
                    draft = self._run_step(
                        logs, step_id, agent, action,
                        lambda: self.writer.draft_reply(context["classification"]),
                    )
                context["draft"] = draft
            elif action == "review":
                if workflow == "konten":
                    source_text = input_text
                    brief_keywords = context["research"].get("keywords", [])
                elif workflow == "laporan_data":
                    source_text = " ".join(context["analysis"].get("facts", []))
                    brief_keywords = []
                else:
                    source_text = input_text
                    brief_keywords = context["classification"].get("keywords", [])

                def revise_fn(current, review, _kind=kind, _kw=brief_keywords):
                    return self.writer.revise(_kind, current, review, _kw)

                final_draft, review, rounds = self.review_cycle(
                    kind, input_text or title, source_text, context["draft"], revise_fn, logs
                )
                context["draft"] = final_draft
                context["review"] = review
                context["revision_rounds"] = rounds

        # Sintesis final oleh Conductor.
        final_text = self._run_step(
            logs, "sintesis", "conductor", "synthesize",
            lambda: self.conductor.synthesize(workflow, context["draft"], context["review"]),
        )

        total_cost = round(sum(e["cost_usd"] for e in logs), 6)
        total_tokens = sum(e["prompt_tokens"] + e["completion_tokens"] for e in logs)
        failed = any(e["status"] == "gagal" for e in logs)
        result = {
            "run_id": run_id,
            "workflow": workflow,
            "workflow_label": plan["label"],
            "title": title,
            "status": "gagal" if failed else "selesai",
            "mode": "live" if self.router.live else "demo",
            "steps": logs,
            "step_count": len(logs),
            "draft": context.get("draft", ""),
            "final_output": final_text,
            "reviewer_score": context["review"]["score"],
            "reviewer_passed": context["review"]["passed"],
            "reviewer_components": context["review"]["components"],
            "revision_rounds": context.get("revision_rounds", 0),
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
        }
        if workflow == "triase_support":
            result["classification"] = context.get("classification", {})
        if workflow == "laporan_data":
            result["analysis_facts"] = context.get("analysis", {}).get("facts", [])
        if workflow == "konten":
            result["research_points"] = context.get("research", {}).get("points", [])
        return result

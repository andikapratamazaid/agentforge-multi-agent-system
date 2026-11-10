"""Reviewer Agent.

Menilai draf terhadap brief dengan rubrik deterministik
(tools/rubric_tools): kelengkapan elemen wajib, kesesuaian brief,
kejelasan, dan ketepatan fakta. Skor rubrik adalah skor resmi di
kedua mode. Di mode live maupun demo, router dipakai untuk
merangkai catatan naratif dari temuan rubrik.
"""

from __future__ import annotations

from ..tools import rubric_tools


class ReviewerAgent:
    name = "reviewer"
    system_prompt = (
        "Anda adalah Reviewer Agent. Nilai draf secara ketat memakai "
        "rubrik: kelengkapan, kesesuaian brief, kejelasan, dan "
        "ketepatan fakta terhadap bahan sumber."
    )

    def __init__(self, router, threshold: int = 70):
        self.router = router
        self.threshold = threshold

    def review(self, kind: str, brief: str, draft: str, source_text: str = ""):
        result = rubric_tools.score_draft(kind, brief, draft, source_text)
        result["passed"] = result["score"] >= self.threshold
        result["threshold"] = self.threshold
        payload = {"score": result["score"], "notes": result["notes"]}
        completion = self.router.complete(self.name, "review_note", payload, self.system_prompt)
        result["narrative_note"] = completion.text
        return result, completion

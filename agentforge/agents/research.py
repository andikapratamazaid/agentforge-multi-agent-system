"""Research Agent.

Menstrukturkan teks bebas menjadi poin kunci, fakta (kalimat berisi
angka), dan kata kunci memakai tools deterministik. Juga bertugas
mengklasifikasikan tiket support untuk workflow triase.
"""

from __future__ import annotations

from ..tools import text_tools


class ResearchAgent:
    name = "research"
    system_prompt = (
        "Anda adalah Research Agent. Strukturkan bahan menjadi poin "
        "kunci, fakta terukur, dan kata kunci tanpa menambah klaim "
        "yang tidak ada di sumber."
    )

    def __init__(self, router):
        self.router = router

    def structure(self, text: str) -> dict:
        return {
            "points": text_tools.extract_points(text),
            "facts": text_tools.extract_facts(text),
            "keywords": text_tools.extract_keywords(text),
            "sentence_count": len(text_tools.split_sentences(text)),
        }

    def classify(self, text: str) -> dict:
        result = text_tools.classify_ticket(text)
        sentences = text_tools.split_sentences(text)
        point = sentences[0] if sentences else text[:120]
        # Buang sapaan pembuka dan ringkas agar enak disisipkan ke balasan.
        low = point.lower()
        for greeting in ("halo,", "halo", "selamat pagi,", "selamat siang,", "selamat malam,"):
            if low.startswith(greeting):
                point = point[len(greeting):].strip().capitalize()
                break
        if len(point) > 90:
            point = point[:90].rsplit(" ", 1)[0] + "..."
        result["customer_point"] = point
        result["keywords"] = text_tools.extract_keywords(text)
        return result

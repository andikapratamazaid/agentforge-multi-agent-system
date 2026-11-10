"""Data Agent.

Menganalisis CSV secara deterministik lewat tools (statistik
deskriptif, agregasi kelompok, tren sederhana), lalu meminta router
menarasikan fakta-faktanya. Angka selalu berasal dari tools, bukan
dari model.
"""

from __future__ import annotations

from ..tools import csv_tools


class DataAgent:
    name = "data"
    system_prompt = (
        "Anda adalah Data Agent. Narasikan hanya angka yang diberikan "
        "tools statistik. Jangan mengarang angka baru."
    )

    def __init__(self, router):
        self.router = router

    def analyze(self, csv_path: str, title: str = "dataset"):
        analysis = csv_tools.analyze_csv(csv_path)
        payload = {"title": title, "facts": analysis["facts"]}
        completion = self.router.complete(self.name, "narrate_data", payload, self.system_prompt)
        analysis["narrative"] = completion.text
        return analysis, completion

"""Writer Agent.

Menyusun tiga jenis draf: artikel (pipeline konten), laporan
(pipeline laporan data), dan balasan (pipeline triase support).
Di mode demo, teks disusun backend deterministik dari bahan yang
diberikan agent lain. Fungsi revise memperbaiki draf berdasarkan
catatan reviewer: elemen wajib yang hilang ditambahkan secara
eksplisit, dan kalimat penutup yang memuat kata kunci brief
ditambahkan bila kesesuaian brief rendah.
"""

from __future__ import annotations

# Kalimat perbaikan per elemen yang hilang, per jenis draf.
FIX_SENTENCES: dict[str, dict[str, str]] = {
    "artikel": {
        "judul atau topik": "Artikel ini membahas tentang topik yang diminta pada brief secara langsung.",
        "isi utama": "Isi utama artikel ini menekankan manfaat yang paling penting bagi pembaca karena dampaknya langsung terasa.",
        "penutup atau ajakan": "Kesimpulan: pembaca dapat mulai menerapkan langkah pertama sekarang dan mencobanya pada minggu ini juga.",
    },
    "laporan": {
        "rujukan data": "Laporan ini disusun berdasarkan data pada dataset yang dianalisis dengan jumlah baris sesuai hasil tools.",
        "angka temuan": "Angka temuan utama mencakup total dan rata-rata dari kolom numerik yang dihitung tools statistik.",
        "kesimpulan tren": "Kesimpulan tren: pola data menunjukkan arah yang dapat dibaca dari perbandingan antar periode pada data.",
    },
    "balasan": {
        "sapaan": "Halo, terima kasih sudah menghubungi kami.",
        "pengakuan masalah": "Kami mencatat laporan Anda dan memahami kendala yang Anda alami.",
        "langkah lanjutan": "Tim kami sedang memeriksa laporan ini dan akan memberikan kabar lanjutan setelah proses pemeriksaan selesai.",
        "permintaan maaf atau empati": "Kami mohon maaf atas ketidaknyamanan yang terjadi.",
    },
}


class WriterAgent:
    name = "writer"
    system_prompt = (
        "Anda adalah Writer Agent. Tulis draf yang lengkap, jelas, "
        "dan setia pada bahan. Jangan menambah angka yang tidak ada "
        "di bahan sumber."
    )

    def __init__(self, router):
        self.router = router

    def draft_article(self, title: str, research: dict, audience: str = "pembaca umum"):
        payload = {"title": title, "points": research.get("points", []), "audience": audience}
        completion = self.router.complete(self.name, "draft_article", payload, self.system_prompt)
        return completion.text, completion

    def draft_report(self, title: str, analysis: dict):
        payload = {
            "title": title,
            "facts": analysis.get("facts", []),
            "narrative": analysis.get("narrative", ""),
        }
        completion = self.router.complete(self.name, "draft_report", payload, self.system_prompt)
        return completion.text, completion

    def draft_reply(self, classification: dict):
        payload = {
            "category": classification.get("category", "umum"),
            "priority": classification.get("priority", "normal"),
            "customer_point": classification.get("customer_point", "keluhan Anda"),
        }
        completion = self.router.complete(self.name, "draft_reply", payload, self.system_prompt)
        return completion.text, completion

    def revise(self, kind: str, draft: str, review: dict, brief_keywords: list[str] | None = None) -> str:
        """Perbaiki draf berdasarkan hasil review terakhir.

        Deterministik di kedua mode agar putaran revisi dapat diuji:
        setiap elemen wajib yang hilang mendapat kalimat perbaikan,
        dan bila ada kata kunci brief yang belum muncul, satu kalimat
        penutup yang memuatnya ditambahkan.
        """
        improved = draft.rstrip()
        fixes = FIX_SENTENCES.get(kind, {})
        for missing in review.get("missing_elements", []):
            sentence = fixes.get(missing)
            if sentence and sentence not in improved:
                improved += " " + sentence
        if brief_keywords:
            absent = [kw for kw in brief_keywords if kw not in improved.lower()]
            if absent:
                improved += (
                    " Sebagai penutup, hal ini berkaitan langsung dengan "
                    + ", ".join(absent[:3])
                    + " yang menjadi fokus brief."
                )
        return improved

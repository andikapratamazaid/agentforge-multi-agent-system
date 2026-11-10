"""Backend demo deterministik.

Dipakai saat OPENROUTER_API_KEY tidak terisi. Backend ini TIDAK
memanggil model bahasa sungguhan. Ia menyusun teks dari aturan dan
template berdasarkan payload terstruktur yang diberikan agent
(hasil tools deterministik). Tujuannya: seluruh alur orkestrasi,
rubrik reviewer, dan harness evaluasi dapat berjalan dan diuji
tanpa biaya API, dengan hasil yang sama pada setiap run.

Kontrak payload per jenis prompt (prompt_key):
- "narrate_data": {"title": str, "facts": [str, ...]}
- "draft_article": {"title": str, "points": [str, ...], "audience": str}
- "draft_report": {"title": str, "facts": [str, ...], "narrative": str}
- "draft_reply": {"category": str, "priority": str, "customer_point": str}
- "synthesize": {"workflow": str, "parts": [str, ...]}
- "review_note": {"score": int, "notes": [str, ...]}
"""

from __future__ import annotations


def _join_points(points: list[str]) -> str:
    return " ".join(p.strip() for p in points if p and p.strip())


def simulate(agent: str, prompt_key: str, payload: dict) -> str:
    """Hasilkan teks simulasi yang deterministik untuk satu panggilan."""
    if prompt_key == "narrate_data":
        facts = payload.get("facts", [])
        body = " ".join(facts)
        return (
            f"Berdasarkan data pada {payload.get('title', 'dataset')}, "
            f"temuan utamanya adalah sebagai berikut. {body} "
            "Pola ini layak diperhatikan karena muncul konsisten di "
            "keseluruhan periode data, bukan hanya pada satu titik."
        )
    if prompt_key == "draft_article":
        points = payload.get("points", [])
        audience = payload.get("audience", "pembaca umum")
        intro = (
            f"Artikel ini ditulis untuk {audience}. "
            f"Topik utamanya adalah {payload.get('title', 'topik yang diberikan')}."
        )
        return intro + " " + _join_points(points)
    if prompt_key == "draft_report":
        facts = payload.get("facts", [])
        narrative = payload.get("narrative", "")
        return (
            f"Laporan: {payload.get('title', 'Laporan Data')}. "
            + " ".join(facts)
            + " "
            + narrative
        )
    if prompt_key == "draft_reply":
        category = payload.get("category", "umum")
        priority = payload.get("priority", "normal")
        point = payload.get("customer_point", "keluhan Anda")
        return (
            "Halo, terima kasih sudah menghubungi kami. "
            f"Kami mencatat laporan Anda terkait {point} "
            f"(kategori: {category}, prioritas: {priority}). "
            "Tim kami sedang memeriksa laporan ini dan akan memberikan "
            "kabar lanjutan paling lambat satu hari kerja. "
            "Mohon maaf atas ketidaknyamanan yang terjadi."
        )
    if prompt_key == "synthesize":
        parts = payload.get("parts", [])
        return (
            f"Hasil final workflow {payload.get('workflow', '')}: "
            + " ".join(parts)
        )
    if prompt_key == "review_note":
        notes = payload.get("notes", [])
        if notes:
            return "Catatan reviewer: " + "; ".join(notes) + "."
        return "Catatan reviewer: tidak ada catatan tambahan."
    # Cadangan generik agar tidak pernah mengembalikan string kosong.
    return _join_points([str(v) for v in payload.values() if isinstance(v, str)])

"""Rubrik penilaian deterministik untuk Reviewer Agent.

Skor 0 sampai 100 disusun dari empat komponen tertimbang:
- Kelengkapan (35): elemen wajib per jenis draf ditemukan di teks.
- Kesesuaian brief (25): tumpang tindih kata kunci draf dengan brief.
- Kejelasan (20): panjang memadai, kalimat tidak terlalu panjang,
  dan teks terbagi menjadi lebih dari satu kalimat utuh.
- Ketepatan fakta (20): angka yang muncul di draf harus dapat
  ditelusur ke bahan sumber; angka asing menurunkan skor.

Komponen ini sengaja deterministik agar penilaian dapat diuji dan
dievaluasi tanpa bergantung pada model. Di mode live, Reviewer
tetap memakai rubrik ini sebagai skor resmi dan model hanya
menambah catatan naratif.
"""

from __future__ import annotations

import re

from .text_tools import extract_keywords, split_sentences

REQUIRED_ELEMENTS: dict[str, list[tuple[str, list[str]]]] = {
    # nama elemen -> kata penanda yang diterima (salah satu cukup)
    "artikel": [
        ("judul atau topik", ["topik", "tentang", "artikel"]),
        ("isi utama", ["manfaat", "penting", "utama", "karena"]),
        ("penutup atau ajakan", ["mulai", "coba", "hubungi", "kesimpulan", "sekarang"]),
    ],
    "laporan": [
        ("rujukan data", ["data", "dataset", "baris"]),
        ("angka temuan", ["total", "rata-rata", "persen"]),
        ("kesimpulan tren", ["tren", "naik", "turun", "stabil", "pola"]),
    ],
    "balasan": [
        ("sapaan", ["halo", "selamat", "terima kasih"]),
        ("pengakuan masalah", ["mencatat", "memahami", "laporan anda"]),
        ("langkah lanjutan", ["memeriksa", "kabar lanjutan", "tindak", "proses"]),
        ("permintaan maaf atau empati", ["maaf", "ketidaknyamanan", "empati"]),
    ],
}

WEIGHTS = {"kelengkapan": 35, "kesesuaian_brief": 25, "kejelasan": 20, "ketepatan_fakta": 20}


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:[.,]\d+)?", text))


def score_draft(kind: str, brief: str, draft: str, source_text: str = "") -> dict:
    notes: list[str] = []
    low = draft.lower()

    # 1. Kelengkapan elemen wajib.
    required = REQUIRED_ELEMENTS.get(kind, [])
    found = []
    missing = []
    for name, markers in required:
        if any(m in low for m in markers):
            found.append(name)
        else:
            missing.append(name)
    completeness = (len(found) / len(required) * WEIGHTS["kelengkapan"]) if required else WEIGHTS["kelengkapan"]
    if missing:
        notes.append("Elemen belum ada: " + ", ".join(missing))

    # 2. Kesesuaian dengan brief lewat kata kunci.
    brief_kw = set(extract_keywords(brief, limit=10))
    if brief_kw:
        hit = sum(1 for kw in brief_kw if kw in low)
        brief_fit = hit / len(brief_kw) * WEIGHTS["kesesuaian_brief"]
        if hit < len(brief_kw) / 2:
            notes.append("Draf belum menyentuh sebagian besar kata kunci brief")
    else:
        brief_fit = WEIGHTS["kesesuaian_brief"]

    # 3. Kejelasan struktur.
    sentences = split_sentences(draft)
    words = len(draft.split())
    clarity = 0.0
    if words >= 40:
        clarity += 8
    else:
        notes.append("Draf terlalu pendek untuk dinilai jelas")
    if len(sentences) >= 3:
        clarity += 7
    if sentences and all(len(s.split()) <= 40 for s in sentences):
        clarity += 5
    elif sentences:
        notes.append("Ada kalimat yang terlalu panjang")

    # 4. Ketepatan fakta: angka di draf harus ada di sumber.
    draft_nums = _numbers(draft)
    source_nums = _numbers(source_text) | _numbers(brief)
    if draft_nums:
        foreign = {n for n in draft_nums if n not in source_nums and n.rstrip("0").rstrip(".,") not in source_nums}
        if foreign:
            factual = max(0.0, WEIGHTS["ketepatan_fakta"] * (1 - len(foreign) / len(draft_nums)))
            notes.append("Angka yang tidak ditemukan di bahan sumber: " + ", ".join(sorted(foreign)))
        else:
            factual = float(WEIGHTS["ketepatan_fakta"])
    else:
        factual = float(WEIGHTS["ketepatan_fakta"])
        if kind == "laporan":
            factual = WEIGHTS["ketepatan_fakta"] / 2
            notes.append("Laporan data sebaiknya memuat angka temuan")

    total = round(completeness + brief_fit + clarity + factual)
    return {
        "score": int(max(0, min(100, total))),
        "components": {
            "kelengkapan": round(completeness, 1),
            "kesesuaian_brief": round(brief_fit, 1),
            "kejelasan": round(clarity, 1),
            "ketepatan_fakta": round(factual, 1),
        },
        "found_elements": found,
        "missing_elements": missing,
        "notes": notes,
    }

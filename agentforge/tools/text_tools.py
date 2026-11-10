"""Tools teks deterministik untuk Research Agent.

Semua fungsi di sini murni aturan: pemecahan kalimat, pemilihan
kalimat berisi angka sebagai fakta, ekstraksi kata kunci berbasis
frekuensi, dan klasifikasi tiket support berbasis kata kunci.
Tidak ada panggilan model di lapisan ini.
"""

from __future__ import annotations

import re
from collections import Counter

STOPWORDS_ID = {
    "yang", "dan", "di", "ke", "dari", "untuk", "dengan", "pada", "adalah",
    "ini", "itu", "atau", "juga", "akan", "dalam", "tidak", "ada", "kami",
    "anda", "saya", "bisa", "lebih", "sebagai", "oleh", "telah", "saat",
    "agar", "karena", "mereka", "kita", "para", "setiap", "seperti",
    "sudah", "belum", "harus", "dapat", "antara", "selama", "setelah",
    "kepada", "yaitu", "yakni", "sangat", "paling", "tanpa", "hanya",
    "masih", "jika", "bila", "maka", "dia", "ia", "nya", "pun", "lah",
}

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[a-zA-Z][a-zA-Z\-]{2,}")


def split_sentences(text: str) -> list[str]:
    parts = [p.strip() for p in _SENTENCE_SPLIT.split(text.replace("\n", " "))]
    return [p for p in parts if len(p) >= 15]


def extract_facts(text: str) -> list[str]:
    """Kalimat yang memuat angka dianggap fakta terukur."""
    return [s for s in split_sentences(text) if re.search(r"\d", s)]


def extract_points(text: str, limit: int = 6) -> list[str]:
    """Poin kunci: kalimat awal dokumen dan kalimat berisi angka
    atau kata penanda penting, tanpa duplikasi."""
    sentences = split_sentences(text)
    points: list[str] = []
    for s in sentences:
        low = s.lower()
        if re.search(r"\d", s) or any(
            marker in low
            for marker in ("penting", "utama", "wajib", "harus", "target", "tujuan", "manfaat", "penutup")
        ):
            if s not in points:
                points.append(s)
        if len(points) >= limit:
            break
    if not points and sentences:
        points = sentences[: min(3, len(sentences))]
    return points


def extract_keywords(text: str, limit: int = 8) -> list[str]:
    words = [w.lower() for w in _WORD.findall(text)]
    freq = Counter(w for w in words if w not in STOPWORDS_ID and len(w) > 3)
    return [w for w, _ in freq.most_common(limit)]


# Aturan klasifikasi tiket support: kategori -> kata kunci pemicu.
TICKET_RULES: list[tuple[str, list[str]]] = [
    ("tagihan", ["tagihan", "tertagih", "dipotong", "saldo", "pembayaran", "refund", "kembalian"]),
    ("teknis", ["error", "gagal", "tidak bisa masuk", "login", "lambat", "lemot", "putus", "down", "bug"]),
    ("pengiriman", ["paket", "pengiriman", "kurir", "belum sampai", "terlambat", "resi"]),
    ("akun", ["akun", "kata sandi", "password", "verifikasi", "email", "nomor hp"]),
    ("produk", ["produk", "barang", "rusak", "cacat", "tidak sesuai", "ukuran"]),
]

PRIORITY_HIGH = ["darurat", "urgent", "segera", "tidak bisa sama sekali", "uang saya", "dobel", "ganda", "hilang"]
PRIORITY_LOW = ["bertanya", "sekadar", "kapan tersedia", "info", "informasi"]


def classify_ticket(text: str) -> dict:
    """Klasifikasi deterministik: kategori dan prioritas tiket."""
    low = text.lower()
    scores = {cat: sum(1 for kw in kws if kw in low) for cat, kws in TICKET_RULES}
    category = max(scores, key=scores.get) if max(scores.values()) > 0 else "umum"
    if any(kw in low for kw in PRIORITY_HIGH):
        priority = "tinggi"
    elif any(kw in low for kw in PRIORITY_LOW):
        priority = "rendah"
    else:
        priority = "normal"
    return {"category": category, "priority": priority, "scores": scores}

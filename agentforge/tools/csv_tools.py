"""Tools CSV deterministik untuk Data Agent.

Membaca CSV dengan modul csv standard library, menghitung statistik
deskriptif kolom numerik, agregasi per kelompok, dan tren sederhana
(kolom urutan pertama yang numerik dibandingkan awal dan akhir).
Hasilnya berupa dict terstruktur plus daftar kalimat fakta yang
siap dinarasikan.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path


def _to_number(value: str):
    """Uraikan angka teks. Mendukung format polos (2060000 atau 1.5),
    desimal koma (1,5), dan format Indonesia campuran dengan titik
    ribuan plus koma desimal (2.500,75)."""
    try:
        s = str(value).strip()
        if not s:
            return None
        if s.count(",") == 1 and s.count(".") >= 1:
            return float(s.replace(".", "").replace(",", "."))
        if s.count(",") == 1:
            return float(s.replace(",", "."))
        return float(s)
    except (ValueError, AttributeError):
        return None


def read_csv(path: str | Path) -> tuple[list[str], list[dict]]:
    if not str(path).strip():
        raise ValueError("Workflow laporan_data membutuhkan file CSV. Berikan path-nya lewat opsi --csv.")
    if not Path(path).is_file():
        raise FileNotFoundError(f"File CSV tidak ditemukan: {path}")
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = [dict(r) for r in reader]
        return list(reader.fieldnames or []), rows


def analyze_csv(path: str | Path) -> dict:
    columns, rows = read_csv(path)
    numeric: dict[str, list[float]] = {}
    for col in columns:
        values = []
        for row in rows:
            num = _to_number(str(row.get(col, "")).strip())
            if num is not None:
                values.append(num)
        if values and len(values) >= max(2, len(rows) // 2):
            numeric[col] = values

    summary: dict[str, dict] = {}
    for col, values in numeric.items():
        summary[col] = {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": round(statistics.fmean(values), 2),
            "median": round(statistics.median(values), 2),
            "total": round(sum(values), 2),
        }

    facts: list[str] = []
    facts.append(f"Dataset berisi {len(rows)} baris dan {len(columns)} kolom ({', '.join(columns)}).")
    for col, s in summary.items():
        facts.append(
            f"Kolom {col}: total {s['total']}, rata-rata {s['mean']}, "
            f"nilai tengah {s['median']}, rentang {s['min']} sampai {s['max']}."
        )

    # Tren sederhana: kolom numerik dengan total terbesar (biasanya
    # kolom nilai utama seperti pendapatan) dibandingkan antar paruh.
    trend = None
    if numeric:
        first_col = max(summary, key=lambda c: summary[c]["total"])
        values = numeric[first_col]
        if len(values) >= 4:
            half = len(values) // 2
            first_avg = statistics.fmean(values[:half])
            last_avg = statistics.fmean(values[half:])
            change = round((last_avg - first_avg) / first_avg * 100, 1) if first_avg else 0.0
            direction = "naik" if change > 0 else "turun" if change < 0 else "stabil"
            trend = {"column": first_col, "change_pct": change, "direction": direction}
            facts.append(
                f"Tren kolom {first_col}: rata-rata paruh kedua {direction} "
                f"{abs(change)} persen dibanding paruh pertama."
            )

    # Agregasi per kelompok: kolom teks pertama terhadap kolom numerik terbesar totalnya.
    group_summary: dict[str, float] = {}
    group_col = None
    if numeric and columns:
        value_col = max(summary, key=lambda c: summary[c]["total"])
        for col in columns:
            if col not in numeric:
                group_col = col
                break
        if group_col:
            totals: dict[str, float] = {}
            for row in rows:
                num = _to_number(str(row.get(value_col, "")).strip())
                if num is not None:
                    key = str(row.get(group_col, "")).strip() or "(kosong)"
                    totals[key] = totals.get(key, 0.0) + num
            group_summary = dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))
            if group_summary:
                top_key, top_val = next(iter(group_summary.items()))
                facts.append(
                    f"Berdasarkan kolom {group_col}, penyumbang terbesar adalah "
                    f"{top_key} dengan total {value_col} sebesar {round(top_val, 2)}."
                )

    return {
        "path": str(path),
        "rows": len(rows),
        "columns": columns,
        "numeric_summary": summary,
        "group_column": group_col,
        "group_summary": group_summary,
        "trend": trend,
        "facts": facts,
    }

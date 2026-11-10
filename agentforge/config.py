"""Konfigurasi AgentForge.

Sumber konfigurasi:
1. File config/models.json di root project (model per agent, rantai
   fallback, tabel harga, ambang skor reviewer).
2. Environment variable: OPENROUTER_API_KEY untuk mode live, dan
   AGENTFORGE_MODEL_<AGENT> untuk menimpa model utama satu agent
   tanpa mengubah file.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "models.json"


def load_config(path: Path | None = None) -> dict:
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    with open(cfg_path, "r", encoding="utf-8") as fh:
        cfg = json.load(fh)
    # Timpa model utama dari environment bila tersedia.
    for agent_name in cfg.get("agents", {}):
        env_key = f"AGENTFORGE_MODEL_{agent_name.upper()}"
        override = os.environ.get(env_key)
        if override:
            cfg["agents"][agent_name]["model"] = override
    return cfg


def agent_models(cfg: dict, agent_name: str) -> list[str]:
    """Urutan model yang dicoba untuk satu agent: utama lalu fallback."""
    spec = cfg["agents"][agent_name]
    chain = [spec["model"]] + list(spec.get("fallbacks", []))
    # Hilangkan duplikat sambil menjaga urutan.
    seen: list[str] = []
    for model in chain:
        if model not in seen:
            seen.append(model)
    return seen


def price_for(cfg: dict, model: str) -> dict:
    """Harga per 1 juta token. Model tak dikenal dianggap gratis agar
    perhitungan biaya tidak pernah meledak diam-diam; README mencatat
    bahwa tabel harga bersifat indikatif."""
    return cfg.get("prices_usd_per_1m_tokens", {}).get(
        model, {"prompt": 0.0, "completion": 0.0}
    )


def is_live_mode() -> bool:
    """Mode live hanya aktif bila OPENROUTER_API_KEY terisi."""
    return bool(os.environ.get("OPENROUTER_API_KEY", "").strip())

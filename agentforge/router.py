"""Model Router OpenRouter.

Satu-satunya pintu panggilan model di AgentForge.

Mode LIVE (OPENROUTER_API_KEY terisi):
- Mengirim POST ke https://openrouter.ai/api/v1/chat/completions
  memakai urllib dari standard library, dengan header standar
  OpenRouter (Authorization, HTTP-Referer, X-Title).
- Setiap agent punya model utama dan rantai fallback dari
  config/models.json. Bila model utama gagal (error HTTP, timeout,
  respons kosong), router mencoba model berikutnya secara berurutan.

Mode DEMO (tanpa API key, default):
- Tidak ada panggilan jaringan sama sekali. Teks dihasilkan oleh
  demo_backend.simulate secara deterministik.
- Token tetap diestimasi dari panjang teks agar perhitungan biaya
  dan log run tetap bermakna untuk keperluan demo dan evaluasi.

Biaya dihitung dari tabel harga per 1 juta token di config.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from . import demo_backend
from .config import agent_models, is_live_mode, price_for

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


@dataclass
class Completion:
    text: str
    model: str
    mode: str  # "live" atau "demo"
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    attempts: list[str] = field(default_factory=list)


def estimate_tokens(text: str) -> int:
    """Estimasi token kasar: sekitar 4 karakter per token."""
    if not text:
        return 0
    return max(1, round(len(text) / 4))


def compute_cost(cfg: dict, model: str, prompt_tokens: int, completion_tokens: int) -> float:
    price = price_for(cfg, model)
    return (
        prompt_tokens / 1_000_000 * price["prompt"]
        + completion_tokens / 1_000_000 * price["completion"]
    )


def _default_transport(model: str, messages: list[dict], temperature: float, api_key: str) -> tuple[str, int, int]:
    """Transport sungguhan ke OpenRouter. Mengembalikan
    (teks, prompt_tokens, completion_tokens) dari respons API."""
    body = json.dumps(
        {"model": model, "messages": messages, "temperature": temperature}
    ).encode("utf-8")
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/andikapratamazaid/agentforge-multi-agent-system",
            "X-Title": "AgentForge Multi-Agent Automation System",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    text = payload["choices"][0]["message"]["content"].strip()
    usage = payload.get("usage", {})
    prompt_tokens = int(usage.get("prompt_tokens", estimate_tokens(messages[-1]["content"])))
    completion_tokens = int(usage.get("completion_tokens", estimate_tokens(text)))
    if not text:
        raise ValueError("Respons model kosong")
    return text, prompt_tokens, completion_tokens


class ModelRouter:
    def __init__(self, cfg: dict, transport=None, force_demo: bool = False):
        self.cfg = cfg
        self.transport = transport or _default_transport
        self.live = is_live_mode() and not force_demo

    def complete(self, agent: str, prompt_key: str, payload: dict, system_prompt: str = "") -> Completion:
        """Selesaikan satu panggilan untuk satu agent.

        Di mode live, payload dirangkai menjadi pesan user JSON agar
        model menerima konteks terstruktur yang sama seperti demo.
        """
        chain = agent_models(self.cfg, agent)
        user_content = json.dumps({"task": prompt_key, "payload": payload}, ensure_ascii=False)

        if not self.live:
            model = chain[0]
            text = demo_backend.simulate(agent, prompt_key, payload)
            pt = estimate_tokens(system_prompt + user_content)
            ct = estimate_tokens(text)
            return Completion(
                text=text,
                model=model,
                mode="demo",
                prompt_tokens=pt,
                completion_tokens=ct,
                cost_usd=compute_cost(self.cfg, model, pt, ct),
                attempts=[model],
            )

        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        temperature = float(self.cfg["agents"][agent].get("temperature", 0.3))
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        attempts: list[str] = []
        last_error: Exception | None = None
        for model in chain:
            attempts.append(model)
            try:
                text, pt, ct = self.transport(model, messages, temperature, api_key)
                return Completion(
                    text=text,
                    model=model,
                    mode="live",
                    prompt_tokens=pt,
                    completion_tokens=ct,
                    cost_usd=compute_cost(self.cfg, model, pt, ct),
                    attempts=attempts,
                )
            except (urllib.error.URLError, ValueError, KeyError, TimeoutError) as exc:
                last_error = exc
                continue
        raise RuntimeError(
            f"Semua model untuk agent {agent} gagal: {attempts}. Error terakhir: {last_error}"
        )

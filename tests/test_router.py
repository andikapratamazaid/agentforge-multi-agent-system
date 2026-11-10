"""Tes Model Router: mode demo, hitungan biaya, dan rantai fallback."""

import os
import unittest
from unittest.mock import patch

from agentforge.config import load_config
from agentforge.router import ModelRouter, compute_cost


class TestDemoMode(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()

    def test_demo_completion_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            router = ModelRouter(self.cfg, force_demo=True)
            result = router.complete("writer", "draft_reply", {"category": "tagihan", "priority": "tinggi", "customer_point": "tagihan ganda"})
            self.assertEqual(result.mode, "demo")
            self.assertIn("tagihan", result.text)
            self.assertEqual(result.model, self.cfg["agents"]["writer"]["model"])
            self.assertEqual(result.attempts, [result.model])
            self.assertGreater(result.completion_tokens, 0)

    def test_cost_computation_known_values(self):
        # gpt-4o-mini: prompt 0.15 dan completion 0.60 per 1 juta token.
        cost = compute_cost(self.cfg, "openai/gpt-4o-mini", 1_000_000, 1_000_000)
        self.assertAlmostEqual(cost, 0.75, places=6)

    def test_cost_unknown_model_is_zero(self):
        self.assertEqual(compute_cost(self.cfg, "model/tidak-dikenal", 5000, 5000), 0.0)


class TestFallback(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()

    def test_fallback_to_second_model(self):
        calls = []

        def flaky_transport(model, messages, temperature, api_key):
            calls.append(model)
            if len(calls) == 1:
                raise ValueError("model utama gagal")
            return "hasil dari fallback", 100, 50

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            router = ModelRouter(self.cfg, transport=flaky_transport)
            self.assertTrue(router.live)
            result = router.complete("research", "synthesize", {"workflow": "konten", "parts": ["isi"]})
            chain = [self.cfg["agents"]["research"]["model"]] + self.cfg["agents"]["research"]["fallbacks"]
            self.assertEqual(result.model, chain[1])
            self.assertEqual(result.attempts, chain[:2])
            self.assertEqual(result.mode, "live")
            self.assertAlmostEqual(
                result.cost_usd,
                compute_cost(self.cfg, chain[1], 100, 50),
                places=8,
            )

    def test_all_models_fail_raises(self):
        def always_fail(model, messages, temperature, api_key):
            raise ValueError("gagal total")

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            router = ModelRouter(self.cfg, transport=always_fail)
            with self.assertRaises(RuntimeError):
                router.complete("research", "synthesize", {"workflow": "konten", "parts": ["isi"]})


if __name__ == "__main__":
    unittest.main()

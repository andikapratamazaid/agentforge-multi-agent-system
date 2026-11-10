"""Tes rubrik Reviewer: kasus lulus, kasus lemah, dan siklus revisi."""

import unittest

from agentforge.agents.writer import WriterAgent
from agentforge.orchestrator import Orchestrator
from agentforge.router import ModelRouter
from agentforge.tools import rubric_tools

BRIEF = "Balas tiket pelanggan tentang tagihan ganda dengan sopan dan beri langkah lanjutan yang jelas."
GOOD_REPLY = (
    "Halo, terima kasih sudah menghubungi kami. Kami mencatat laporan Anda tentang tagihan "
    "yang terpotong dua kali dan memahami kekhawatiran Anda. Tim kami sedang memeriksa "
    "riwayat tagihan akun Anda dan akan memberikan kabar lanjutan paling lambat satu hari "
    "kerja. Kami mohon maaf atas ketidaknyamanan yang terjadi dan akan memastikan hak "
    "Anda kembali seperti semula."
)
WEAK_REPLY = "Baik, nanti kami cek."


class TestRubric(unittest.TestCase):
    def test_good_reply_passes(self):
        result = rubric_tools.score_draft("balasan", BRIEF, GOOD_REPLY, BRIEF)
        self.assertGreaterEqual(result["score"], 70)
        self.assertEqual(result["missing_elements"], [])

    def test_weak_reply_fails_with_notes(self):
        result = rubric_tools.score_draft("balasan", BRIEF, WEAK_REPLY, BRIEF)
        self.assertLess(result["score"], 70)
        self.assertTrue(result["missing_elements"])
        self.assertTrue(result["notes"])

    def test_foreign_numbers_penalized(self):
        draft = GOOD_REPLY + " Anda mendapat kompensasi sebesar 999999 rupiah."
        result = rubric_tools.score_draft("balasan", BRIEF, draft, BRIEF)
        good = rubric_tools.score_draft("balasan", BRIEF, GOOD_REPLY, BRIEF)
        self.assertLess(result["components"]["ketepatan_fakta"], good["components"]["ketepatan_fakta"])


class TestRevisionCycle(unittest.TestCase):
    def test_revision_improves_weak_draft(self):
        orch = Orchestrator(force_demo=True)
        writer = orch.writer
        logs: list[dict] = []
        initial_review = rubric_tools.score_draft("balasan", BRIEF, WEAK_REPLY, BRIEF)
        self.assertLess(initial_review["score"], orch.reviewer.threshold)

        def revise_fn(current, review):
            return writer.revise("balasan", current, review, ["tagihan", "pelanggan"])

        final_draft, final_review, rounds = orch.review_cycle(
            "balasan", BRIEF, BRIEF, WEAK_REPLY, revise_fn, logs
        )
        self.assertGreaterEqual(rounds, 1)
        self.assertGreater(final_review["score"], initial_review["score"])
        self.assertTrue(final_review["passed"])
        self.assertGreater(len(final_draft), len(WEAK_REPLY))

    def test_writer_revise_adds_missing_elements(self):
        router = ModelRouter(orch_cfg(), force_demo=True)
        writer = WriterAgent(router)
        review = rubric_tools.score_draft("balasan", BRIEF, WEAK_REPLY, BRIEF)
        revised = writer.revise("balasan", WEAK_REPLY, review, [])
        for element in review["missing_elements"]:
            self.assertIn(element, rubric_tools.score_draft("balasan", BRIEF, revised, BRIEF)["found_elements"])


def orch_cfg():
    from agentforge.config import load_config

    return load_config()


if __name__ == "__main__":
    unittest.main()

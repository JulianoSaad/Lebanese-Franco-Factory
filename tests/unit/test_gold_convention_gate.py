"""Gold gate: normalize the spelling, drop only what normalizing cannot fix (MSA vocabulary).

Background: 24 of the 45 corrections recorded in feedback/human_feedback.jsonl rewrote Lebanese
into Modern Standard Arabic in Latin letters. Mechanical differences (the article, "shu"/"shou",
MSA case endings) are repaired and the row is kept; MSA *words* cannot be repaired, so those rows
are not gold. See docs/ARABIZI_CONVENTION.md.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from lebanese_franco_factory.factory.feedback import (
    apply_feedback_to_lexicon,
    gold_quality,
    gold_spelling,
)


class GoldQualityTests(unittest.TestCase):
    def test_lebanese_spellings_are_gold(self):
        for ok in ("sheghel", "bser3a", "jem3a", "ana mut3ab", "shou bet7eb?", "l internet bati2"):
            self.assertEqual(gold_quality(ok), [], ok)

    def test_mechanical_differences_are_normalized_not_dropped(self):
        self.assertEqual(gold_quality("al internet bati2"), [])
        self.assertEqual(gold_spelling("al internet bati2"), "l internet bati2")
        self.assertEqual(gold_quality("shu fi?"), [])
        self.assertEqual(gold_spelling("shu fi?"), "shou fi?")
        self.assertEqual(gold_spelling("ana mech fahem"), "ana mesh fahem")

    def test_msa_vocabulary_is_dropped(self):
        for msa in ("ayna anta?", "al touroukat mouzdahima", "alshare3 mughlaq bisabab albina2",
                    "kam almutabaqi?", "ana birkod fi alhadiqa", "ana mut3abaton"):
            self.assertTrue(gold_quality(msa), msa)

    def test_msa_hidden_behind_the_article_is_still_caught(self):
        # normalizing "alhadiqa" to "l hadiqa" must not hide the MSA word
        self.assertIn("alhadiqa", gold_quality("ana birkod fi alhadiqa"))

    def test_arabic_script_is_not_a_franco_spelling(self):
        self.assertIn("arabic_in_franco", gold_quality("كيفك؟"))


class ApplyFeedbackTests(unittest.TestCase):
    def test_gate_and_normalization_end_to_end(self):
        rows = [
            {"decision": "edit", "original": "شغل", "generated": "shighl", "corrected": "sheghel"},
            {"decision": "edit", "original": "الإنترنت بطيء", "generated": "al internet bat7i",
             "corrected": "al internet bati2"},                     # normalized, kept
            {"decision": "edit", "original": "أنا متعبة", "generated": "ana muta3ebat",
             "corrected": "ana mut3abaton"},                        # MSA word, dropped
            {"decision": "edit", "original": "الطرقات مزدحمة", "generated": "traktou 3alayha",
             "corrected": "al touroukat mouzdahima"},               # MSA words, dropped
            {"decision": "correct", "original": "مرحبا", "generated": "mar7aba"},
            {"decision": "correct", "original": "هلق", "generated": "halla2",
             "excluded_from_gold": True},                            # explicit flag, skipped
            {"decision": "reject", "original": "x", "generated": "y"},
        ]
        with TemporaryDirectory() as d:
            fb, lex = Path(d) / "fb.jsonl", Path(d) / "lex.json"
            fb.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
            lex.write_text("[]", encoding="utf-8")
            out = apply_feedback_to_lexicon(feedback_path=fb, lexicon_path=lex)
            written = {r["arabic"]: r["franco"] for r in json.loads(lex.read_text(encoding="utf-8"))}
        self.assertEqual(out["off_convention"], 2)
        self.assertEqual(out["skipped"], 2)  # reject + excluded_from_gold
        self.assertEqual(written, {"شغل": "sheghel", "الإنترنت بطيء": "l internet bati2",
                                   "مرحبا": "mar7aba"})

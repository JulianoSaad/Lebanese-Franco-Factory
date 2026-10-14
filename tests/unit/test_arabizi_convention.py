"""Arabizi spelling convention: the normalizer and the violation report.

Cases marked "native" are the corrections the native reviewer actually made in
feedback/human_feedback.jsonl — the normalizer must reproduce those exactly.
"""
from __future__ import annotations

import unittest

from lebanese_franco_factory.factory.cleaner.arabizi import (
    franco_violations,
    normalize_franco,
    strip_counters,
)


class NormalizerTests(unittest.TestCase):
    def test_native_reviewer_corrections(self):
        self.assertEqual(normalize_franco("shighl"), "sheghel")
        self.assertEqual(normalize_franco("b ser3a"), "bser3a")
        self.assertEqual(normalize_franco("jam3a"), "jem3a")

    def test_generator_counters_removed(self):
        self.assertEqual(normalize_franco("bye shu fi ma fi? #1"), "bye shou fi ma fi?")
        self.assertEqual(strip_counters("[8805] bade (3254)"), "bade")

    def test_article_is_l(self):
        self.assertEqual(normalize_franco("al internet bati2"), "l internet bati2")
        self.assertEqual(normalize_franco("el beit"), "l beit")
        self.assertEqual(normalize_franco("alshare3 msakkar"), "l share3 msakkar")

    def test_negation_and_shou(self):
        self.assertEqual(normalize_franco("ana ma7 fahem"), "ana mesh fahem")
        self.assertEqual(normalize_franco("ana mich fahem"), "ana mesh fahem")
        self.assertEqual(normalize_franco("sho fi?"), "shou fi?")

    def test_msa_ending_and_doubles_and_spacing(self):
        self.assertEqual(normalize_franco("ana mut3abaton"), "ana mut3ab")
        self.assertEqual(normalize_franco("kkifak?"), "kifak?")
        self.assertEqual(normalize_franco("  Kifak?   ya   zaki "), "kifak? ya zaki")

    def test_proper_nouns_keep_their_capital(self):
        self.assertEqual(normalize_franco("ana ma3ak fi beirut"), "ana ma3ak fi Beirut")
        self.assertEqual(normalize_franco("idm mnih"), "IDM mnih")  # acronyms stay upper
        self.assertEqual(normalize_franco("ana b jounieh"), "ana b Jounieh")  # no gluing onto a name
        self.assertEqual(normalize_franco("b l beit"), "b l beit")

    def test_already_clean_text_is_untouched(self):
        for text in ("kifak?", "shou fi ma fi?", "l internet bati2", "ana mesh fahem"):
            self.assertEqual(normalize_franco(text), text)


class ViolationTests(unittest.TestCase):
    def test_reports_without_changing(self):
        self.assertEqual(franco_violations("kifak?"), [])
        self.assertIn("counter_in_text", franco_violations("kifak? #3"))
        self.assertIn("msa_article", franco_violations("al beit"))
        self.assertIn("word_choice", franco_violations("ana ma7 fahem"))
        self.assertIn("detached_prefix", franco_violations("b ser3a"))
        self.assertIn("doubled_letter", franco_violations("kkifak"))
        self.assertIn("msa_ending", franco_violations("mut3abaton"))
        self.assertIn("arabic_in_franco", franco_violations("كيفك؟"))
        self.assertIn("spacing", franco_violations("kifak?  ya zaki"))

    def test_every_violation_a_normalizer_can_fix_is_fixed(self):
        for text in ("kifak? #3", "al beit", "ana ma7 fahem", "b ser3a", "kkifak", "mut3abaton"):
            self.assertNotEqual(normalize_franco(text), text, text)

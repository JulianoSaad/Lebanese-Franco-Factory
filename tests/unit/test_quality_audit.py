"""Validator rules: artifacts, identity pairs, scripts, duplicates, lexicon agreement."""
from __future__ import annotations

import unittest

from lebanese_franco_factory.factory.validator.quality import (
    check_scripts,
    check_text,
    classify,
    lexicon_verdict,
    normalize,
    strip_counters,
)
from lebanese_franco_factory.factory.validator.audit import row_fields, validate_rows

LEX = {"كيفك؟": {"kifak", "keefak"}}


class RuleTests(unittest.TestCase):
    def test_strip_injected_counters(self):
        # The generators injected these into the training text itself (2026-10 audit).
        self.assertEqual(strip_counters("[8805] بدي (3254)"), "بدي")
        self.assertEqual(strip_counters("bye shu fi ma fi? #1"), "bye shu fi ma fi?")
        self.assertEqual(normalize("Kifak?  #12"), "kifak?")

    def test_counter_artifact_and_identity(self):
        self.assertIn("counter_artifact", check_text("كيفك؟ #1", "kifak? #1"))
        self.assertIn("identity_pair", check_text("kifak?", "kifak?"))
        self.assertNotIn("identity_pair", check_text("kifak", "kifak", expect_identity=True))
        self.assertEqual(check_text("كيفك؟", "kifak?"), [])

    def test_empty_and_length(self):
        self.assertIn("empty_field", check_text("كيفك؟", ""))
        self.assertIn("length_ratio", check_text("hi", "a very long sentence indeed here"))

    def test_script_rules(self):
        self.assertEqual(check_scripts("arabic_to_franco", "كيفك؟", "kifak?"), [])
        self.assertIn("source_not_arabic", check_scripts("arabic_to_franco", "kifak?", "kifak?"))
        self.assertIn("target_has_arabic", check_scripts("arabic_to_franco", "كيفك؟", "كيفك؟"))

    def test_lexicon_and_classify(self):
        self.assertEqual(lexicon_verdict("كيفك؟", "KIFAK", LEX), "verified")
        self.assertEqual(lexicon_verdict("كيفك؟", "kifeek", LEX), "conflict")
        self.assertEqual(lexicon_verdict("شغل", "shighl", LEX), "unknown")
        self.assertEqual(classify(["counter_artifact"]), "reject")
        self.assertEqual(classify([], "verified"), "verified")
        self.assertEqual(classify([], "conflict"), "conflict")
        self.assertEqual(classify([], "unknown", duplicate=True), "duplicate")
        self.assertEqual(classify(["length_ratio"], "unknown"), "review")


class RunnerTests(unittest.TestCase):
    def test_row_fields_handles_each_family(self):
        self.assertEqual(row_fields({"direction": "arabic_to_franco", "source": "كيفك؟", "target": "kifak?"}),
                         ("arabic_to_franco", "arabic_to_franco", "كيفك؟", "kifak?"))
        d, ds, s, t = row_fields({"messages": [{"role": "user", "content": "hi"},
                                               {"role": "assistant", "content": "kifak?"}], "domain": "casual_chat"})
        self.assertEqual((ds, s, t), ("casual_chat", "hi", "kifak?"))
        d, ds, s, t = row_fields({"task": "rewrite", "input": "kifak?", "output": "kifek?"})
        self.assertEqual((ds, s, t), ("rewrite", "kifak?", "kifek?"))

    def test_duplicates_flagged_second_time_only(self):
        rows = [{"direction": "arabic_to_franco", "source": "كيفك؟", "target": "kifak?"},
                {"direction": "arabic_to_franco", "source": "كيفك؟ #2", "target": "kifak? #2"},
                {"direction": "arabic_to_franco", "source": "مرحبا", "target": "mar7aba"}]
        out = validate_rows(rows, LEX)
        # row 2 is the same pair once counters are stripped, but artifacts outrank duplication
        self.assertEqual([r["verdict"] for r in out], ["verified", "reject", "review"])

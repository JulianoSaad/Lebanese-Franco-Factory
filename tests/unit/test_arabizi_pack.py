"""Normalizer cases found by validating dictionary/lebanese_support_phrases.json."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from lebanese_franco_factory.core.paths import repo_root
from lebanese_franco_factory.factory.cleaner.arabizi import (
    franco_violations,
    msa_vocabulary,
    normalize_franco,
)


class PrepositionsAndVerbsTests(unittest.TestCase):
    def test_mn_keeps_its_space(self):
        # "mn" is a preposition; only the article-fused "mnl" attaches
        self.assertEqual(normalize_franco("dafa3et mn embare7"), "dafa3et mn embare7")
        self.assertEqual(normalize_franco("3am estanna mn sa3a"), "3am estanna mn sa3a")
        self.assertEqual(normalize_franco("jibo mnl beit"), "jibo mnl beit")

    def test_b_still_attaches_to_ordinary_words(self):
        self.assertEqual(normalize_franco("b ser3a"), "bser3a")
        self.assertEqual(normalize_franco("fi fiber b mant2atna"), "fi fiber bmant2atna")

    def test_prefix_before_a_name_keeps_its_space(self):
        self.assertEqual(normalize_franco("l esim 3am tzabbet b fransa"), "l esim 3am tzabbet b Fransa")
        self.assertEqual(franco_violations("l esim 3am tzabbet b Fransa"), [])

    def test_glued_article_is_not_split_off_a_verb(self):
        self.assertEqual(normalize_franco("3am el3ab"), "3am el3ab")
        self.assertEqual(normalize_franco("badde elghe l talab"), "badde elghe l talab")
        self.assertEqual(normalize_franco("alshare3 msakkar"), "l share3 msakkar")

    def test_acronyms_brands_and_loanwords(self):
        self.assertEqual(normalize_franco("dawa l los a7mar"), "dawa l LOS a7mar")
        self.assertEqual(normalize_franco("l vpn mesh 3am yetwasal"), "l VPN mesh 3am yetwasal")
        self.assertEqual(normalize_franco("calls l whatsapp"), "calls l WhatsApp")
        self.assertEqual(normalize_franco("ma fi wifi"), "ma fi wifi")       # loanword, lowercase
        self.assertEqual(normalize_franco("badde esim"), "badde esim")


class SeedPackTests(unittest.TestCase):
    """The shipped phrase pack must obey the convention it was written for."""

    def test_pack_is_convention_clean(self):
        pack = json.loads((repo_root() / "dictionary" / "lebanese_support_phrases.json")
                          .read_text(encoding="utf-8"))
        self.assertTrue(pack["needs_native_review"])
        self.assertGreaterEqual(len(pack["entries"]), 100)
        for entry in pack["entries"]:
            self.assertTrue(entry["arabic"] and entry["english"], entry["id"])
            for spelling in entry["franco"]:
                self.assertEqual(normalize_franco(spelling), spelling, entry["id"])
                self.assertEqual(franco_violations(spelling), [], entry["id"])
                self.assertEqual(msa_vocabulary(spelling), [], entry["id"])

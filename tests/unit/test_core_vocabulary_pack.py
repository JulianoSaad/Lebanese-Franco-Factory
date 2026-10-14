"""dictionary/lebanese_core_vocabulary.json: generated, convention-clean, and reproducible."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest

from lebanese_franco_factory.core.paths import repo_root
from lebanese_franco_factory.factory.cleaner.arabizi import (
    franco_violations,
    msa_vocabulary,
    normalize_franco,
)

PACK = repo_root() / "dictionary" / "lebanese_core_vocabulary.json"


class CoreVocabularyPackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = json.loads(PACK.read_text(encoding="utf-8"))
        cls.entries = cls.pack["entries"]

    def test_pack_shape_and_provenance(self):
        self.assertEqual(self.pack["pack"], "lebanese_core_vocabulary")
        self.assertTrue(self.pack["needs_native_review"])
        self.assertGreater(len(self.entries), 9000)
        ids = [e["id"] for e in self.entries]
        self.assertEqual(len(ids), len(set(ids)), "entry ids must be unique")
        for e in self.entries:
            self.assertTrue(e["franco"] and e["arabic"] and e["english"] and e["tags"], e["id"])

    def test_house_spellings_follow_the_convention(self):
        # franco[0] is the house spelling; the other spellings are recognition variants and may
        # deliberately break the convention (ch for sh, h for 7 ...).
        bad = [(e["id"], e["franco"][0], franco_violations(e["franco"][0])) for e in self.entries
               if franco_violations(e["franco"][0])]
        self.assertEqual(bad, [])
        changed = [(e["franco"][0], normalize_franco(e["franco"][0])) for e in self.entries
                   if normalize_franco(e["franco"][0]) != e["franco"][0]]
        self.assertEqual(changed, [])
        msa = [(e["id"], msa_vocabulary(sp)) for e in self.entries for sp in e["franco"] if msa_vocabulary(sp)]
        self.assertEqual(msa, [])

    def test_morphology_covers_the_shapes_customers_type(self):
        spellings = {sp for e in self.entries for sp in e["franco"]}
        for form in ("bektob", "btektbe", "mnektob", "katabet", "katabto", "2oullo", "2oulle", "3emlo", "esme",
                     "bshoufak", "beite", "sawtak", "lfatoura", "mnihe", "mesh mnih", "badde", "lezem"):
            self.assertIn(form, spellings, form)
        # recognition variants: the common respellings are present too
        for form in ("chou", "shu", "ktir", "kteer", "menshouf", "bishouf", "mech", "hayk"):
            self.assertIn(form, spellings, form)

    def test_generator_is_reproducible(self):
        script = repo_root() / "scripts" / "build_lebanese_core_pack.py"
        tmp = repo_root() / ".pytest_cache" / "core_pack_regen.json"
        tmp.parent.mkdir(exist_ok=True)
        subprocess.run([sys.executable, str(script), str(tmp)], check=True, capture_output=True)
        regen = json.loads(tmp.read_text(encoding="utf-8"))
        self.assertEqual(regen["entries"], self.entries, "committed pack is out of date: rerun the generator")


if __name__ == "__main__":
    unittest.main()

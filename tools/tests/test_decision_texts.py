"""Tests for the decision text that replaces Anbennar's placeholders ("TODO", "(WIP)", blank, or the decision's name).

    python -I -m unittest discover -s tools/tests -p "test_decision_texts*.py"
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pdx_script import ANBENNAR_CK3 as ANBENNAR, parse_blocks, strip_comments  # noqa: E402

SUBMOD = Path(__file__).resolve().parent.parent.parent

TEXT_FILE = "localization/replace/english/aov_decision_text_replace_l_english.yml"
OVERRIDE_FILE = "common/decisions/zz_aov_decision_overrides.txt"
# Decisions copied from Anbennar to fix one line: key -> (Anbennar's line, ours).
OVERRIDES = {
    "restore_reaver_kingdom_of_divenhal": ("desc = restore_reaver_kingdom_of_divenhal",
                                           "desc = restore_reaver_kingdom_of_divenhal_desc"),
}

# Decisions whose scripts work but whose text was unfinished.
DECISIONS = (
    "incorporate_carneter_decision", "reclaim_what_dameria_stole_decision", "old_damerian_resurgence_decision",
    "restore_western_marches_decision", "resurrect_the_high_kingdom_decision", "encourage_arbarani_decision",
    "consolidate_farranean_decision", "restore_havoric_kingdom_decision", "show_eaglecrest_its_place_decision",
    "the_moormen_kneel_decision", "bring_the_reach_into_the_fold_decision", "restore_reaver_kingdom_of_divenhal",
    "the_roots_of_our_dominion_decision", "into_the_silence_of_castans_fall_decision",
    "found_stonescepter_court_decision", "recite_skaldic_tale_decision",
)
SUFFIXES = ("_desc", "_tooltip", "_confirm")
# Real but one-line Anbennar text, rewritten anyway; and the blank opening of the Skaldic recitation event.
THIN = {"restore_havoric_kingdom_decision_desc", "found_stonescepter_court_decision_desc"}
EVENT_TEXT = {"anb_religious_decision.0501.desc.beginning"}


def _text(path):
    return path.read_bytes().decode("utf-8-sig") if path.is_file() else ""


def loc_values(text):
    return dict(re.findall(r'^\s*([\w.\-]+):\d*\s*"(.*)"\s*(?:#.*)?$', text, re.M))


def squash(body):
    return " ".join(strip_comments(body).split())


def decision_files():
    """Every decision file of Anbennar and the overhaul in load order (sorted by path under common/decisions)."""
    by_path = {}
    for root in (ANBENNAR, SUBMOD):
        folder = root / "common/decisions"
        for f in folder.rglob("*.txt"):
            by_path[f.relative_to(folder).as_posix()] = f
    return [by_path[p] for p in sorted(by_path)]


def is_placeholder(value, name=None):
    return (value is None or not value.strip() or value == name
            or re.search(r"TODO|\(WIP\)", value) is not None)


class DecisionTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = {}
        for f in (ANBENNAR / "localization/english").rglob("*.yml"):
            cls.base.update(loc_values(_text(f)))
        cls.placeholders = set(EVENT_TEXT)
        for key in DECISIONS:
            if is_placeholder(cls.base.get(key)):
                cls.placeholders.add(key)
            for suffix in SUFFIXES:
                if is_placeholder(cls.base.get(key + suffix), cls.base.get(key)):
                    cls.placeholders.add(key + suffix)
        cls.ours = loc_values(_text(SUBMOD / TEXT_FILE))

    def test_every_placeholder_replaced(self):
        self.assertEqual(self.placeholders - set(self.ours), set())

    def test_only_placeholders_replaced(self):
        self.assertLessEqual(set(self.ours), self.placeholders | THIN)

    def test_names_drop_wip(self):
        for key in DECISIONS:
            name = self.ours.get(key, self.base.get(key, ""))
            self.assertNotIn("(WIP)", name, key)

    def test_texts_are_real(self):
        for key, value in self.ours.items():
            self.assertFalse(is_placeholder(value), key)
            self.assertGreaterEqual(len(value), 100 if key.endswith(("_desc", ".beginning")) else 5, key)


class DecisionOverrideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ours = parse_blocks(_text(SUBMOD / OVERRIDE_FILE))
        cls.base = {}
        for f in (ANBENNAR / "common/decisions").rglob("*.txt"):
            cls.base.update(parse_blocks(_text(f)))

    def test_only_listed_decisions_overridden(self):
        self.assertEqual(set(self.ours), set(OVERRIDES))

    def test_overrides_match_anbennar_but_the_fixed_line(self):
        for key, (theirs, fixed) in OVERRIDES.items():
            self.assertRegex(squash(self.base[key]), re.escape(theirs) + r"(?!\w)",
                             f"{key}: Anbennar changed the line we fix")
            self.assertEqual(squash(self.ours[key]), squash(self.base[key]).replace(theirs, fixed, 1),
                             f"{key}: re-copy it from Anbennar")

    def test_our_definitions_win(self):
        effective = {}
        for f in decision_files():
            effective.update({key: f for key in parse_blocks(_text(f))})
        for key in OVERRIDES:
            self.assertEqual(effective[key].name, Path(OVERRIDE_FILE).name, key)


if __name__ == "__main__":
    unittest.main()

"""Tests for the four Anbennar cultural men-at-arms recruited by faith in the overhaul (Dercinges, Druids, Skalds,
Knights of the Spear) and the retired traditions that used to unlock them.

    python -I -m unittest discover -s tools/tests -p "test_faith_maa*.py"
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pdx_script import ANBENNAR_CK3 as ANBENNAR, parse_blocks  # noqa: E402
from test_cultural_maa import _text, base_blocks, blocks, maa_files, squash, without_blocks  # noqa: E402

MAA_FILE = "common/men_at_arms_types/zz_aov_faith_maa_overrides.txt"
BASE_MAA_FILE = "common/men_at_arms_types/anb_cultural_maa_types.txt"
TRADITION_FILE = "common/culture/traditions/zz_aov_faith_traditions.txt"
BASE_TRADITION_FILE = "common/culture/traditions/anb_maa_traditions.txt"
ON_ACTION_FILE = "common/on_action/aov_faith_maa_on_actions.txt"

DRUIDIC = "faith = { has_doctrine = tenet_druids_of_the_deruwren }"
ADEAN = ("faith = { OR = { has_doctrine = doctrine_patron_deity_adean "
         "has_doctrine = doctrine_patron_deity_the_dame_adean has_doctrine = doctrine_patron_deity_adean_minara } }")
GATES = {
    "dercinges": DRUIDIC,
    "druids": DRUIDIC,
    "skalds": ("faith = { has_doctrine = tenet_skaldic_tales } OR = { faith = { religion_tag = skaldhyrric_religion } "
               "culture = { has_cultural_pillar = heritage_gerudian } }"),
    "knights_of_the_spear": ADEAN,
}
RETIRED = tuple(f"tradition_test_maa_anb_{key}" for key in GATES)
DOCTRINES = ("tenet_druids_of_the_deruwren", "tenet_skaldic_tales", "doctrine_patron_deity_adean",
             "doctrine_patron_deity_the_dame_adean", "doctrine_patron_deity_adean_minara")


class FaithMaaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ours = blocks(MAA_FILE)
        cls.base = base_blocks(BASE_MAA_FILE)

    def test_only_the_four_units_are_overridden(self):
        self.assertEqual(set(self.ours), set(GATES))

    def test_units_regated_and_otherwise_anbennars(self):
        for key, gate in GATES.items():
            self.assertEqual(squash(parse_blocks(self.ours[key]).get("can_recruit", "")), gate, key)
            self.assertEqual(squash(without_blocks(self.ours[key], ("can_recruit",))),
                             squash(without_blocks(self.base[key], ("can_recruit",))), key)

    def test_our_definitions_win(self):
        effective = {}
        for f in maa_files():
            effective.update({key: f for key in parse_blocks(_text(f))})
        for key in GATES:
            self.assertEqual(effective[key].name, Path(MAA_FILE).name, key)

    def test_gate_doctrines_exist(self):
        text = "".join(_text(f) for f in (ANBENNAR / "common/religion/doctrine_types").glob("*.txt"))
        for doctrine in DOCTRINES:
            self.assertRegex(text, rf"(?m)^\s*{doctrine} = \{{", doctrine)


class FaithTraditionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ours = blocks(TRADITION_FILE)
        cls.base = base_blocks(BASE_TRADITION_FILE)
        cls.on_actions = blocks(ON_ACTION_FILE)

    def test_retired_traditions_hidden_and_unpickable(self):
        self.assertEqual(set(self.ours), set(RETIRED))
        for key in RETIRED:
            inner = parse_blocks(self.ours[key])
            self.assertEqual(squash(inner.get("is_shown", "")), "always = no", key)
            self.assertEqual(squash(inner.get("can_pick", "")), "always = no", key)

    def test_overrides_match_anbennar_elsewhere(self):
        for key in RETIRED:
            self.assertEqual(squash(without_blocks(self.ours[key], ("is_shown", "can_pick"))),
                             squash(without_blocks(self.base[key], ("is_shown", "can_pick"))), key)

    def test_game_start_removes_them(self):
        self.assertIn("aov_faith_maa_game_start", squash(self.on_actions.get("on_game_start", "")))
        effect = squash(self.on_actions.get("aov_faith_maa_game_start", ""))
        for key in RETIRED:
            self.assertRegex(effect, rf"every_culture_global = {{ limit = {{ has_cultural_tradition = {key} }} "
                                     rf"remove_culture_tradition = {key} }}")

    def test_no_other_tradition_unlocks_the_units(self):
        # Anbennar's debug tradition_test_maa (never shown) still lists every unlock parameter.
        for key, body in self.base.items():
            if key in RETIRED or key == "tradition_test_maa":
                continue
            for unit in GATES:
                self.assertNotRegex(body, rf"unlock_maa_anb_{unit}\b", key)


if __name__ == "__main__":
    unittest.main()

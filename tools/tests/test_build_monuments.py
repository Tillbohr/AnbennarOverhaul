import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_monuments as bm  # noqa: E402
from data.monuments.cannor import MONUMENTS  # noqa: E402

LIVE = bm.ANBENNAR_CK3.is_dir()
FILES = bm.render_all("cannor") if LIVE else {}
B = FILES.get("common/buildings/aov_monuments_cannor.txt", "")
H = FILES.get("history/provinces/aov_monuments_cannor.txt", "")
L = FILES.get("localization/english/aov_monuments_cannor_l_english.yml", "")


def block(text, key):
    m = re.search(rf"^{key} = \{{\n(.*?)^\}}", text, re.M | re.S)
    assert m, key
    return m.group(1)


def province_block(text, pid):
    m = re.search(rf"^{pid} = \{{\n(.*?)^\}}", text, re.M | re.S)
    assert m, pid
    return m.group(1)


def new_level_keys():
    known = bm.anbennar_keys()
    return [k for m in MONUMENTS for k in m["levels"] if k not in known]


def fake(**tier):
    t = {"province_modifier": {}, "county_modifier": {}, "character_modifier": {}, "on_complete": "",
         "cost": 100, "days": 900, "dropped": ["x: y"]}
    t.update(tier)
    return {"eu4_key": "x", "name": "X", "desc": "d", "levels": ["aov_monument_x_01"] * 3, "category": "castle",
            "gate": "", "gate_desc": "", "start_level": 0, "province": 1, "tiers": [t, t, t]}


@unittest.skipUnless(LIVE, "Anbennar CK3 not present")
class BuildMonumentTests(unittest.TestCase):
    def test_levels_chain(self):
        self.assertIn("next_building = aov_monument_toncodden_lighthouse_02", block(B, "aov_monument_toncodden_lighthouse_01"))
        self.assertNotIn("next_building", block(B, "aov_monument_toncodden_lighthouse_03"))

    def test_level_fields(self):
        lvl = block(B, "aov_monument_toncodden_lighthouse_01")
        for line in ("type = special", "cost_gold = ", "construction_time = ", 'type_icon = "'):
            self.assertIn(line, lvl)

    def test_gate_used_for_effects_and_building(self):
        lvl = block(B, "aov_monument_lorentaine_mage_academy_01")
        self.assertIn("is_enabled = {", lvl)
        self.assertIn("can_construct = {", lvl)
        self.assertIn("scope:holder = {", lvl)
        self.assertIn("text = aov_monument_lorentaine_mage_academy_gate", lvl)
        self.assertIn(" aov_monument_lorentaine_mage_academy_gate: \"Built and used by: ", L)

    def test_ungated_has_no_gate_blocks(self):
        lvl = block(B, "aov_monument_toncodden_lighthouse_01")
        self.assertNotIn("is_enabled", lvl)
        self.assertNotIn("can_construct = {", lvl)

    def test_level_without_modifiers_has_no_empty_blocks(self):
        text = bm.building(fake(), 1, "aov_monument_x_01", None)
        self.assertNotRegex(text, r"_modifier = \{\s*\}")
        self.assertNotIn("on_complete", text)
        self.assertNotIn("duchy_capital", B)

    def test_real_generated_file_is_well_formed(self):
        text = (bm.SUBMOD / "common/buildings/aov_monuments_cannor.txt").read_text(encoding="utf-8-sig")
        self.assertNotRegex(text, r"_modifier = \{\s*\}")
        self.assertEqual(text.count("{"), text.count("}"))
        self.assertEqual(text, B)

    def test_number_format(self):
        self.assertEqual(bm.num(0.05), "0.05")
        self.assertEqual(bm.num(2), "2")
        self.assertEqual(bm.num(0.12345), "0.123")

    def test_history_places_slots_and_level_one(self):
        known = bm.anbennar_keys()
        for m in MONUMENTS:
            first = m["levels"][0]
            if first in known:
                continue
            pb = province_block(H, m["province"])
            self.assertIn(f"special_building_slot = {first}", pb)
            self.assertEqual(f"special_building = {first}" in pb, m["start_level"] == 1)

    def test_loc_for_every_new_level(self):
        for key in new_level_keys():
            self.assertIn(f" building_{key}:", L)
            self.assertIn(f" building_{key}_desc:", L)
        self.assertIn(' building_castle_dameris_03: "Castle Dameris"', L)

    def test_slot_loc_for_new_monuments(self):
        known = bm.anbennar_keys()
        for m in MONUMENTS:
            if m["levels"][0] not in known:
                self.assertIn(f" building_type_{m['levels'][0]}:", L)
                self.assertIn(f" building_type_{m['levels'][0]}_desc:", L)

    def test_no_loc_for_anbennar_keys(self):
        for k in bm.anbennar_keys():
            self.assertNotIn(f" building_{k}:", L)

    def test_loc_values_have_no_inner_quotes(self):
        for line in L.splitlines()[1:]:
            m = re.fullmatch(r' [\w]+: "(.*)"', line)
            self.assertTrue(m, line)
            self.assertNotIn('"', m.group(1), line)


if __name__ == "__main__":
    unittest.main()

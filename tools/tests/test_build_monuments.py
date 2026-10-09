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


ANBENNAR = bm.ANBENNAR_CK3
OVR = "common/buildings/zz_aov_monument_overrides_cannor.txt"


def overrides():
    return FILES[OVR]


def body_lines(text):
    lines = text.splitlines()
    return [l for l in lines[1:-1] if l.strip()]


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


BASE_PLAIN = """x_01 = {
\tcost_gold = 1

\ttype = special
}
"""
BASE_ON_COMPLETE = """x_01 = {
\ton_complete = {
\t\tadd_gold = 1
\t}

\ttype = special
}
"""


@unittest.skipUnless(LIVE, "Anbennar CK3 not present")
class OverrideTests(unittest.TestCase):
    def test_override_keeps_every_anbennar_line(self):
        known = bm.anbennar_keys()
        for key in (k for m in MONUMENTS for k in m["levels"] if k in known):
            base = bm.anbennar_definition(ANBENNAR, key)
            ours = block(overrides(), key)
            our_keys = {l.split("=")[0].strip() for l in ours.splitlines() if "=" in l}
            for line in body_lines(base):
                if line.strip().startswith("next_building"):
                    continue
                if line in ours.splitlines() or line.strip() in (l.strip() for l in ours.splitlines()):
                    continue
                # a line the generator merged (summed) is compared by key
                self.assertIn(line.split("=")[0].strip(), our_keys, f"{key}: {line}")
                self.assertTrue(re.match(r"\t\t\w+ = ", line), f"{key}: only modifier lines may be merged: {line}")

    def test_no_override_block_repeats_a_modifier_key(self):
        known = bm.anbennar_keys()
        for key in (k for m in MONUMENTS for k in m["levels"] if k in known):
            ours = block(overrides(), key)
            for name in bm.BLOCKS:
                m = re.search(rf"^\t{name} = \{{\n(.*?)^\t\}}", ours, re.M | re.S)
                if m:
                    keys = re.findall(r"^\t\t(\w+) = ", m.group(1), re.M)
                    self.assertEqual(len(keys), len(set(keys)), f"{key} {name}: {keys}")

    def test_merge_sums_named_value(self):
        values = bm.parse_values("@base = 2\n@step = 2\n@t1 = @[base]\n@t3 = @[t1 + step + step]\n"
                                 "good_building_fort_level_tier_3 = @[t3]\n")
        base = "x_01 = {\n\tprovince_modifier = {\n\t\tfort_level = good_building_fort_level_tier_3\n\t}\n\n\ttype = special\n}\n"
        tier = {"province_modifier": {"fort_level": 1}, "county_modifier": {}, "character_modifier": {}, "on_complete": ""}
        out = bm.override(base, "x_01", tier, None, 1, values)
        self.assertEqual(out.count("fort_level"), 2)  # the summed line and its comment
        self.assertIn("\t\tfort_level = 7\n", out)
        self.assertNotIn("fort_level = good_building", out)
        self.assertIn("# Anbennar Overhaul: EU4 tier 1 (+1 to good_building_fort_level_tier_3 = 6)", out)

    def test_merge_sums_numeric_value(self):
        base = "x_01 = {\n\tcounty_modifier = {\n\t\ttax_mult = 0.2 # old\n\t}\n\n\ttype = special\n}\n"
        tier = {"province_modifier": {}, "county_modifier": {"tax_mult": 0.05, "development_growth": 0.1},
                "character_modifier": {}, "on_complete": ""}
        out = bm.override(base, "x_01", tier, None, 2, {})
        self.assertIn("\t\ttax_mult = 0.25\n", out)
        self.assertEqual(out.count("tax_mult ="), 1)
        self.assertIn("\t\tdevelopment_growth = 0.1\n", out)
        self.assertEqual(out.count("county_modifier = {"), 1)

    def test_unresolvable_value_keeps_anbennar_line(self):
        base = "x_01 = {\n\tprovince_modifier = {\n\t\tfort_level = mystery_value\n\t}\n\n\ttype = special\n}\n"
        tier = {"province_modifier": {"fort_level": 1}, "county_modifier": {}, "character_modifier": {}, "on_complete": ""}
        warnings = []
        out = bm.override(base, "x_01", tier, None, 3, {}, warnings)
        self.assertIn("\t\tfort_level = mystery_value\n", out)
        self.assertNotIn("fort_level = 1", out)
        self.assertIn("# Anbennar Overhaul: EU4 tier 3 fort_level mystery_value not added (unknown name mystery_value)", out)
        self.assertEqual(len(warnings), 1)

    def test_one_line_block_is_rejected(self):
        base = "x_01 = {\n\tprovince_modifier = { fort_level = 1 }\n\n\ttype = special\n}\n"
        tier = {"province_modifier": {"fort_level": 1}, "county_modifier": {}, "character_modifier": {}, "on_complete": ""}
        with self.assertRaises(bm.GeneratorError):
            bm.override(base, "x_01", tier, None, 1, {})

    def test_override_adds_tier_effects_and_extends_chain(self):
        ours = block(overrides(), "castanorian_citadel_bal_ouord_02")
        self.assertIn("# Anbennar Overhaul", ours)
        self.assertIn("next_building = aov_monument_bal_ouord_02", ours)
        self.assertIn("aov_monument_bal_ouord_03", bm.render_all("cannor")["common/buildings/aov_monuments_cannor.txt"])

    def test_existing_modifier_block_is_extended_not_duplicated(self):
        ours = block(overrides(), "castanorian_citadel_bal_ouord_02")
        self.assertEqual(ours.count("character_modifier = {"), 1)
        self.assertEqual(ours.count("province_modifier = {"), 1)

    def test_inserted_lines_are_inside_the_block(self):
        ours = block(overrides(), "castanorian_citadel_bal_ouord_02")
        m = re.search(r"^\tprovince_modifier = \{\n(.*?)^\t\}", ours, re.M | re.S)
        self.assertIn("garrison_size = 0.15", m.group(1))
        self.assertIn("defender_holding_advantage", m.group(1))

    def test_overrides_file_is_brace_balanced(self):
        code = "\n".join(l.split("#", 1)[0] for l in overrides().splitlines())
        self.assertEqual(code.count("{"), code.count("}"))
        for key in (k for m in MONUMENTS for k in m["levels"] if k in bm.anbennar_keys()):
            blk = block(overrides(), key)
            depth = 0
            for l in blk.splitlines():
                depth += l.split("#", 1)[0].count("{") - l.split("#", 1)[0].count("}")
                self.assertGreaterEqual(depth, 0, key)
            self.assertEqual(depth, 0, key)

    def test_ruins_stage_untouched(self):
        self.assertNotIn("castanorian_citadel_bal_ouord_01 = {", overrides())

    def test_missing_anbennar_key_errors(self):
        with self.assertRaises(bm.GeneratorError):
            bm.anbennar_definition(ANBENNAR, "castanorian_citadel_bal_nowhere_02")

    def test_castle_dameris_defined_fresh(self):
        files = bm.render_all("cannor")
        for k in ("castle_dameris_01", "castle_dameris_02", "castle_dameris_03"):
            self.assertTrue(any(re.search(rf"^{k} = \{{", t, re.M) for t in files.values()), k)
        self.assertNotIn("castle_dameris_01 = {", overrides())

    def test_every_anbennar_level_overridden_once(self):
        known = bm.anbennar_keys()
        expected = [k for m in MONUMENTS for k in m["levels"] if k in known]
        self.assertEqual(len(expected), 17)
        for k in expected:
            self.assertEqual(len(re.findall(rf"^{k} = \{{", overrides(), re.M)), 1, k)

    def test_next_building_replaced(self):
        ours = block(overrides(), "lake_palace_01")
        self.assertEqual(ours.count("next_building"), 1)
        self.assertIn("next_building = lake_palace_02", ours)
        self.assertIn("next_building = aov_monument_the_lake_palace_03", block(overrides(), "lake_palace_02"))

    def test_override_adds_missing_block_before_type(self):
        tier = {"province_modifier": {}, "county_modifier": {"development_growth": 0.1},
                "character_modifier": {}, "on_complete": "add_gold = 1"}
        out = bm.override(BASE_PLAIN, "x_01", tier, None, 2)
        self.assertLess(out.index("county_modifier"), out.index("type = special"))
        self.assertIn("# Anbennar Overhaul: EU4 tier 2", out)
        self.assertIn("on_complete = {", out)
        self.assertNotIn("next_building", out)

    def test_override_appends_inside_existing_on_complete(self):
        tier = {"province_modifier": {}, "county_modifier": {}, "character_modifier": {}, "on_complete": "add_gold = 2"}
        out = bm.override(BASE_ON_COMPLETE, "x_01", tier, None, 1)
        self.assertEqual(out.count("on_complete = {"), 1)
        self.assertIn("add_gold = 1", out)
        self.assertIn("add_gold = 2", out)
        self.assertLess(out.index("add_gold = 2"), out.index("type = special"))
        self.assertLess(out.index("add_gold = 2"), out.rindex("\t}"))

    def test_upper_chain_levels_use_tier_one_icon(self):
        self.assertIn('type_icon = "icon_structure_the_citadel_of_aleppo.dds"',
                      block(B, "aov_monument_bal_ouord_02"))


if __name__ == "__main__":
    unittest.main()

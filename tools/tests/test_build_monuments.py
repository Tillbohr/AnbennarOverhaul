import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_monuments as bm  # noqa: E402
import eu4_monuments  # noqa: E402
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


def modifiers(text):
    """(block, key) -> raw value of the depth-2 lines of every modifier block of a building body."""
    out = {}
    for name in bm.BLOCKS:
        m = re.search(rf"^\t{name} = \{{\n(.*?)^\t\}}", text, re.M | re.S)
        if m:
            for k, v in re.findall(r"^\t\t(\w+) = ([^\s#]+)", m.group(1), re.M):
                out[(name, k)] = v
    return out


def level_text(key):
    return block(overrides(), key) if key in bm.anbennar_keys() else block(B, key)


def override_chains():
    known = bm.anbennar_keys()
    return [(m, bm.chain_top(m, known)) for m in MONUMENTS if bm.chain_top(m, known)]


KEPT_LINES = re.compile(r"^\t(flag|type_icon|show_disabled|max_garrison) = |^\t(is_enabled|effect_desc) = \{")


@unittest.skipUnless(LIVE, "Anbennar CK3 not present")
class UpperLevelTests(unittest.TestCase):
    """Final review C1: upper levels of Anbennar chains copy the chain's top Anbennar level (an upgrade replaces the
    previous level's effects)."""

    def test_sixteen_chains(self):
        self.assertEqual(len(override_chains()), 16)

    def test_upper_levels_keep_anbennar_top_level_effects(self):
        values = bm.load_values()
        for m, top in override_chains():
            base = modifiers(bm.anbennar_definition(ANBENNAR, top))
            self.assertTrue(base, top)
            for key in m["levels"][1:]:
                ours = modifiers(level_text(key))
                for (name, k), raw in base.items():
                    self.assertIn((name, k), ours, f"{key} lost {name} {k}")
                    old, new = bm.resolve(raw, values), bm.resolve(ours[(name, k)], values)
                    if old >= 0:
                        self.assertGreaterEqual(new, old, f"{key} {name} {k}")
                    else:
                        self.assertLessEqual(new, old, f"{key} {name} {k}")

    def test_upper_levels_keep_flags_and_gates_of_anbennar(self):
        for m, top in override_chains():
            base = bm.anbennar_definition(ANBENNAR, top)
            kept = [l.rstrip() for l in base.splitlines() if KEPT_LINES.match(l)]
            for key in m["levels"][1:]:
                lines = [l.rstrip() for l in level_text(key).splitlines()]
                for line in kept:
                    self.assertIn(line, lines, f"{key}: {line}")

    def test_necropolis_upper_levels_keep_holy_site_gate(self):
        for key in ("aov_monument_the_necropolis_02", "aov_monument_the_necropolis_03"):
            text = block(B, key)
            self.assertIn("holy_site_pantheonic_or_holy_site_trigger", text)
            self.assertIn("flag = holy_building", text)
            self.assertIn("monthly_income = 3", text)

    def test_eu4_gate_only_in_can_construct(self):
        for m, top in override_chains():
            if not m["gate"]:
                continue
            for key in m["levels"][1:]:
                if key in bm.anbennar_keys():
                    continue
                text = block(B, key)
                cc = re.search(r"^\tcan_construct = \{.*?\n(.*?)^\t\}", text, re.M | re.S).group(1)
                self.assertIn(f"text = aov_monument_{m['eu4_key']}_gate", cc, key)
                self.assertEqual(text.count(f"aov_monument_{m['eu4_key']}_gate"), 1, key)
                self.assertEqual(text.count("can_construct = {"), 1, key)

    def test_existing_can_construct_is_extended(self):
        text = block(B, "aov_monument_bal_ouord_02")
        cc = re.search(r"^\tcan_construct = \{\n(.*?)^\t\}", text, re.M | re.S).group(1)
        self.assertIn("has_innovation = innovation_hoardings", cc)
        self.assertIn("aov_monument_bal_ouord_gate", cc)

    def test_cost_time_and_chain_from_tier(self):
        """Cost and time come from the tier, but never below the level upgraded from (follow-up to PR #3)."""
        values = bm.load_values()
        for m, top in override_chains():
            for i, key in enumerate(m["levels"]):
                if key in bm.anbennar_keys():
                    continue
                text, prev = block(B, key), level_text(m["levels"][i - 1])
                tier = m["tiers"][i]
                for name, field in bm.UPGRADE_FIELDS.items():
                    ours = bm.resolve(bm.line_value(f"x = {{\n{text}}}", name), values)
                    raw = bm.line_value(f"x = {{\n{prev}}}", name)  # None: a level with no cost or time line
                    before = bm.resolve(raw, values) if raw else 0
                    self.assertEqual(ours, max(float(tier[field]), before), f"{key} {name}")
                nxt = re.findall(r"(?m)^\tnext_building = (\w+)", text)
                self.assertEqual(nxt, m["levels"][i + 1:i + 2], key)

    def test_upgrades_cost_at_least_anbennar_level_one(self):
        for key in ("aov_monument_calascandar_02", "aov_monument_calascandar_03"):
            self.assertRegex(block(B, key), r"(?m)^\tcost_gold = 2000 ", key)
            self.assertRegex(block(B, key), r"(?m)^\tconstruction_time = very_slow_construction_time ", key)

    def test_necropolis_upper_levels_take_either_gate(self):
        """A holy-site holder of another faith may build level 1, so must be able to upgrade it: the EU4 gate is an
        alternative inside Anbennar's OR, not an extra requirement (follow-up to PR #3)."""
        gate = "\t\t\tscope:holder = {\n\t\t\t\tcustom_tooltip = {\n\t\t\t\t\ttext = aov_monument_the_necropolis_gate"
        for key in ("aov_monument_the_necropolis_02", "aov_monument_the_necropolis_03"):
            cc = re.search(r"^\tcan_construct = \{\n(.*?)^\t\}", block(B, key), re.M | re.S).group(1)
            code = [l for l in cc.splitlines() if l.split("#", 1)[0].strip()]
            self.assertEqual(code[0], "\t\tOR = {", key)
            self.assertEqual(code[-1], "\t\t}", key)
            self.assertFalse([l for l in code[1:-1] if re.match(r"\t\t\S", l)], key)  # the OR is the only statement
            self.assertIn("is_holy_site_of = scope:holder.faith", cc, key)
            self.assertIn(gate, cc, key)

    def test_other_gates_stay_requirements(self):
        cc = re.search(r"^\tcan_construct = \{\n(.*?)^\t\}", block(B, "aov_monument_bal_ouord_02"), re.M | re.S).group(1)
        self.assertIn("\t\tscope:holder = {\n\t\t\tcustom_tooltip = {\n\t\t\t\ttext = aov_monument_bal_ouord_gate", cc)

    def test_lake_palace_top_copies_level_two(self):
        text = block(B, "aov_monument_the_lake_palace_03")
        self.assertIn("legitimacy_gain_mult = 0.1", text)
        self.assertIn("flag = travel_point_of_interest_diplomatic", text)
        self.assertIn("culture_likely_to_fortify_modifier = yes", text)

    def test_chain_top_is_last_anbennar_level(self):
        known = {"x_01", "x_02"}
        self.assertEqual(bm.chain_top({"levels": ["x_01", "x_02", "aov_x_03"]}, known), "x_02")
        self.assertIsNone(bm.chain_top({"levels": ["y_01", "y_02", "y_03"]}, known))


ANB_TOP = """x_01 = { # Rebuilt
\tconstruction_time = very_slow_construction_time

\tcan_construct = {
\t\thas_x = yes
\t}

\tis_enabled = {
\t\thas_y = yes
\t}

\tcost_gold = 2000

\tprovince_modifier = {
\t\tfort_level = 6
\t}

\tai_value = {
\t\tbase = 100
\t}

\ttype = special

\tflag = holy_building
}
"""


class UpperLevelUnitTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "common" / "buildings").mkdir(parents=True)
        (self.root / "common" / "buildings" / "anb.txt").write_text(ANB_TOP, encoding="utf-8")
        self.m = fake(province_modifier={"fort_level": 2}, character_modifier={"diplomacy": 1}, cost=1000, days=3600)
        self.m.update(gate="culture = culture:x", eu4_key="x", levels=["x_01", "aov_x_02", "aov_x_03"])

    def tearDown(self):
        self.tmp.cleanup()

    def upper(self, level, key, nxt):
        return bm.upper_level(self.m, level, key, nxt, "x_01", self.root, {}, [])

    def test_copy_renamed_merged_and_chained(self):
        text = self.upper(2, "aov_x_02", "aov_x_03")
        body = block(text, "aov_x_02")
        self.assertIn("\t\tfort_level = 8\n", body)
        self.assertIn("\t\tdiplomacy = 1\n", body)
        self.assertIn("\tcost_gold = 2000 ", body)  # not below x_01's 2000
        self.assertIn("\tconstruction_time = 3600 ", body)  # x_01's very_slow_construction_time is unknown here
        self.assertIn("\tnext_building = aov_x_03 ", body)
        self.assertIn("\tflag = holy_building", body)
        self.assertNotIn("x_01 = {", text)

    def test_gate_goes_into_can_construct_only(self):
        body = block(self.upper(2, "aov_x_02", "aov_x_03"), "aov_x_02")
        cc = re.search(r"^\tcan_construct = \{\n(.*?)^\t\}", body, re.M | re.S).group(1)
        self.assertIn("has_x = yes", cc)
        self.assertIn("text = aov_monument_x_gate", cc)
        ie = re.search(r"^\tis_enabled = \{\n(.*?)^\t\}", body, re.M | re.S).group(1)
        self.assertNotIn("aov_monument_x_gate", ie)
        self.assertIn("has_y = yes", ie)

    def test_ai_guard_added_to_anbennar_ai_value(self):
        body = block(self.upper(3, "aov_x_03", None), "aov_x_03")
        ai = re.search(r"^\tai_value = \{\n(.*?)^\t\}", body, re.M | re.S).group(1)
        self.assertIn("base = 100", ai)
        self.assertIn("free_building_slots > 0", ai)
        self.assertNotIn("next_building", body)
        self.assertEqual(body.count("{"), body.count("}"))

    def test_upgrade_value_floor(self):
        values = {"very_slow_construction_time": "2190"}
        self.m["tiers"][2] = dict(self.m["tiers"][1], cost=3000, days=900)
        two = bm.upgrade_value(self.m, 2, "cost_gold", "x_01", self.root, values, [])
        self.assertEqual(two, ("2000", 2000.0, " (1000), not below x_01"))
        days = bm.upgrade_value(self.m, 2, "construction_time", "x_01", self.root, values, [])
        self.assertEqual(days, ("3600", 3600.0, ""))  # the tier is slower than x_01
        self.assertEqual(bm.upgrade_value(self.m, 3, "cost_gold", "x_01", self.root, values, [])[:2], ("3000", 3000.0))
        self.assertEqual(bm.upgrade_value(self.m, 3, "construction_time", "x_01", self.root, values, []),
                         ("3600", 3600.0, " (900), not below aov_x_02"))  # floored by the generated level 2

    def test_unresolvable_upgrade_floor_warns(self):
        warnings = []
        self.assertEqual(bm.upgrade_value(self.m, 2, "construction_time", "x_01", self.root, {}, warnings)[:2],
                         ("3600", 3600.0))
        self.assertEqual(len(warnings), 1)

    def test_gate_mode_or_wraps_plain_can_construct(self):
        self.m["gate_mode"] = "or"
        body = block(self.upper(2, "aov_x_02", "aov_x_03"), "aov_x_02")
        cc = re.search(r"^\tcan_construct = \{\n(.*?)^\t\}", body, re.M | re.S).group(1)
        self.assertRegex(cc, r"^\t\tOR = \{\n\t\t\tAND = \{\n\t\t\t\thas_x = yes\n\t\t\t\}\n")
        self.assertIn("\t\t\tscope:holder = {\n\t\t\t\tcustom_tooltip = {\n\t\t\t\t\ttext = aov_monument_x_gate", cc)
        self.assertEqual(body.count("{"), body.count("}"))

    def test_gate_mode_or_joins_existing_or(self):
        anb = ANB_TOP.replace("\t\thas_x = yes\n", "\t\tOR = {\n\t\t\thas_x = yes\n\t\t\thas_z = yes\n\t\t}\n\t\t# has_w = yes\n")
        (self.root / "common" / "buildings" / "anb.txt").write_text(anb, encoding="utf-8")
        self.m["gate_mode"] = "or"
        body = block(self.upper(2, "aov_x_02", "aov_x_03"), "aov_x_02")
        cc = re.search(r"^\tcan_construct = \{\n(.*?)^\t\}", body, re.M | re.S).group(1)
        self.assertIn("\t\t\thas_z = yes\n\t\t\t# Anbennar Overhaul: EU4 culture gate, an alternative to Anbennar's\n"
                      "\t\t\tscope:holder = {", cc)
        self.assertIn("\t\t\t}\n\t\t}\n\t\t# has_w = yes\n", cc)
        self.assertNotIn("AND", cc)

    def test_gate_mode_or_needs_can_construct(self):
        anb = re.sub(r"\tcan_construct = \{\n.*?\n\t\}\n", "", ANB_TOP, flags=re.S)
        (self.root / "common" / "buildings" / "anb.txt").write_text(anb, encoding="utf-8")
        self.m["gate_mode"] = "or"
        with self.assertRaises(bm.GeneratorError):
            self.upper(2, "aov_x_02", "aov_x_03")


class FortLevelCapTests(unittest.TestCase):
    """Follow-up to PR #3: merged fort levels stop at max(8, Anbennar's value); the rest becomes holding advantage."""
    VALUES = bm.parse_values("good_building_fort_level_tier_3 = 6\nadv = 6\n")
    TIER = {"province_modifier": {"fort_level": 4}, "county_modifier": {}, "character_modifier": {}, "on_complete": ""}

    def test_surplus_moves_to_existing_advantage(self):
        base = ("x_01 = {\n\tprovince_modifier = {\n\t\tdefender_holding_advantage = adv\n"
                "\t\tfort_level = good_building_fort_level_tier_3\n\t}\n\n\ttype = special\n}\n")
        out = bm.override(base, "x_01", self.TIER, None, 3, self.VALUES)
        self.assertIn("\t\tfort_level = 8\n", out)
        self.assertIn("\t\tdefender_holding_advantage = 8\n", out)
        self.assertIn("capped at 8; 2 moved to defender_holding_advantage", out)
        self.assertEqual(out.count("defender_holding_advantage ="), 1)

    def test_surplus_added_when_no_advantage(self):
        base = "x_01 = {\n\tprovince_modifier = {\n\t\tfort_level = 7\n\t}\n\n\ttype = special\n}\n"
        out = bm.override(base, "x_01", self.TIER, None, 3, {})
        self.assertIn("\t\tfort_level = 8\n", out)
        self.assertIn("\t\tdefender_holding_advantage = 3\n", out)
        self.assertLess(out.index("defender_holding_advantage"), out.index("type = special"))

    def test_anbennar_value_above_cap_is_kept(self):
        base = "x_01 = {\n\tprovince_modifier = {\n\t\tfort_level = 10\n\t}\n\n\ttype = special\n}\n"
        out = bm.override(base, "x_01", self.TIER, None, 3, {})
        self.assertIn("\t\tfort_level = 10\n", out)
        self.assertIn("\t\tdefender_holding_advantage = 4\n", out)

    def test_tier_advantage_sums_with_surplus(self):
        tier = dict(self.TIER, province_modifier={"defender_holding_advantage": 1, "fort_level": 4})
        base = "x_01 = {\n\tprovince_modifier = {\n\t\tfort_level = 6\n\t}\n\n\ttype = special\n}\n"
        out = bm.override(base, "x_01", tier, None, 3, {})
        self.assertEqual(out.count("defender_holding_advantage ="), 1)
        self.assertIn("\t\tdefender_holding_advantage = 3\n", out)

    @unittest.skipUnless(LIVE, "Anbennar CK3 not present")
    def test_generated_fort_levels_within_cap(self):
        """Every level in the written building files: resolved fort_level <= max(8, Anbennar's value for the level)."""
        values, known, checked = bm.load_values(), bm.anbennar_keys(), 0
        files = {rel: (bm.SUBMOD / rel).read_text(encoding="utf-8-sig") for rel in (
            "common/buildings/aov_monuments_cannor.txt", OVR)}
        for m in MONUMENTS:
            top = bm.chain_top(m, known)
            for key in m["levels"]:
                rel = OVR if key in known else "common/buildings/aov_monuments_cannor.txt"
                ours = modifiers(block(files[rel], key)).get(("province_modifier", "fort_level"))
                if ours is None:
                    continue
                source = key if key in known else top
                anb = modifiers(bm.anbennar_definition(ANBENNAR, source)).get(("province_modifier", "fort_level")) \
                    if source else None
                cap = max(bm.FORT_LEVEL_CAP, bm.resolve(anb, values) if anb else 0)
                self.assertLessEqual(bm.resolve(ours, values), cap, key)
                checked += 1
        self.assertGreater(checked, 40)
        self.assertRegex(block(files["common/buildings/aov_monuments_cannor.txt"], "aov_monument_calascandar_03"),
                         r"(?m)^\t\tfort_level = 8$")


@unittest.skipUnless(LIVE, "Anbennar CK3 not present")
class AiValueAndEffectTests(unittest.TestCase):
    def test_every_generated_level_has_vanilla_ai_guard(self):
        for key in new_level_keys():
            ai = re.search(r"^\tai_value = \{\n(.*?)^\t\}", block(B, key), re.M | re.S)
            self.assertTrue(ai, key)
            self.assertIn("free_building_slots > 0", ai.group(1), key)
            self.assertIn("factor = 0", ai.group(1), key)

    def test_preference_modifier_by_category(self):
        known = bm.anbennar_keys()
        for m in MONUMENTS:
            if bm.chain_top(m, known):
                continue
            ai = re.search(r"^\tai_value = \{\n(.*?)^\t\}", block(B, m["levels"][0]), re.M | re.S).group(1)
            wanted = bm.AI_PREFERENCE.get(m["category"])
            if wanted:
                self.assertIn(f"{wanted} = yes", ai, m["eu4_key"])
            else:
                self.assertNotIn("_modifier = yes", ai, m["eu4_key"])

    def test_overridden_anbennar_levels_keep_anbennar_ai_value(self):
        base = bm.anbennar_definition(ANBENNAR, "castanorian_citadel_bal_ouord_02")
        ai = re.search(r"^\tai_value = \{\n(.*?)^\t\}", base, re.M | re.S).group(0)
        self.assertIn(ai, block(overrides(), "castanorian_citadel_bal_ouord_02"))

    def test_every_level_has_an_effect(self):
        """Final review I2: no level of any monument is an empty building."""
        for text in (B, overrides()):
            for key, body in re.findall(r"^(\w+) = \{\n(.*?)^\}", text, re.M | re.S):
                self.assertRegex(body, r"(?m)^\t(province_modifier|county_modifier|character_modifier|on_complete) = \{",
                                 key)

    def test_palaces_have_effects(self):
        for key in ("castle_dameris_01", "castle_dameris_02", "castle_dameris_03",
                    "aov_monument_palace_of_unity_01", "aov_monument_palace_of_unity_03"):
            self.assertIn("character_modifier = {", block(B, key), key)
        self.assertIn("diplomacy = 2", block(B, "castle_dameris_03"))


class ValidationTests(unittest.TestCase):
    """Final review I5: render_all validates the data and names the monument."""

    def good(self, **fields):
        m = fake(county_modifier={"tax_mult": 0.1})
        m.update(barony="b_x", eu4_key="x")
        m.update(fields)
        return m

    def assertRejected(self, monuments, text):
        with self.assertRaises(bm.GeneratorError) as e:
            bm.validate(monuments, set())
        self.assertIn("monument x", str(e.exception))
        self.assertIn(text, str(e.exception))

    def test_good_data_passes(self):
        bm.validate([self.good()], set())

    def test_missing_barony_or_province(self):
        self.assertRejected([self.good(barony=None)], "no barony")
        self.assertRejected([self.good(province=None)], "no barony or province")

    def test_duplicate_province(self):
        other = self.good(eu4_key="y")
        self.assertRejected([other, self.good()], "province 1 already holds y")

    def test_empty_name_or_desc(self):
        self.assertRejected([self.good(name=" ")], "empty name")
        self.assertRejected([self.good(desc="")], "empty desc")

    def test_unknown_category(self):
        self.assertRejected([self.good(category="spaceport")], "category 'spaceport'")

    def test_unmapped_modifier_key(self):
        m = fake(county_modifier={"made_up_mult": 0.1})
        m.update(barony="b_x")
        self.assertRejected([m], "made_up_mult")
        bm.validate([m], set(), {"made_up_mult"})  # a hand key is accepted

    def test_level_without_effect(self):
        self.assertRejected([fake() | {"barony": "b_x"}], "level 1 has no effect")
        m = fake() | {"barony": "b_x", "levels": ["anb_01", "x_02", "x_03"]}
        bm.validate([m], {"anb_01"})  # Anbennar chains carry Anbennar's effects

    def test_on_complete_counts_as_effect(self):
        bm.validate([fake(on_complete="add_gold = 1") | {"barony": "b_x"}], set())

    @unittest.skipUnless(LIVE, "Anbennar CK3 not present")
    def test_render_all_validates(self):
        from unittest import mock
        bad = [self.good(barony=None)]
        with mock.patch.object(bm, "load_monuments", return_value=bad):
            with self.assertRaises(bm.GeneratorError):
                bm.render_all("cannor")

    def test_hand_keys(self):
        self.assertIn("vassal_opinion", bm.hand_keys("cannor"))
        self.assertEqual(bm.hand_keys("nowhere"), set())



@unittest.skipUnless(LIVE and eu4_monuments.EU4_ROOTS["anbennar"].is_dir(), "EU4 Anbennar art not installed")
class ArtTests(unittest.TestCase):
    def test_art_written_for_monuments_with_paintings(self):
        from build_spells import read_bgra
        files = bm.render_art("cannor")
        for m in MONUMENTS:
            if m["art"]:
                w, h, _ = read_bgra(files[f"gfx/interface/illustrations/aov_monuments/{m['eu4_key']}.dds"])
                self.assertEqual((w, h), (300, 150))

    def test_custom_loc_entry_per_monument_with_art(self):
        cl = bm.render_shared()["common/customizable_localization/aov_monument_illustration.txt"]
        self.assertIn("type = province", cl)
        for m in MONUMENTS:
            if m["art"]:
                self.assertIn(f"has_building_or_higher = {m['levels'][0]}", cl)
                self.assertIn(f"localization_key = aov_monument_art_{m['eu4_key']}", cl)
        self.assertIn("fallback = yes", cl)

    def test_art_loc_holds_texture_path(self):
        key = next(m["eu4_key"] for m in MONUMENTS if m["art"])
        self.assertIn(f' aov_monument_art_{key}: "gfx/interface/illustrations/aov_monuments/{key}.dds"', L)

@unittest.skipUnless(LIVE, "needs Anbennar CK3")
class RegionTests(unittest.TestCase):
    def test_regions(self):
        self.assertEqual(bm.REGIONS, ("cannor", "dwarovar"))

    def test_dwarovar_files(self):
        files = bm.render_all("dwarovar")
        self.assertIn("common/buildings/aov_monuments_dwarovar.txt", files)
        self.assertIn("history/provinces/aov_monuments_dwarovar.txt", files)
        self.assertIn("localization/english/aov_monuments_dwarovar_l_english.yml", files)
        self.assertNotIn("common/buildings/zz_aov_monument_overrides_dwarovar.txt", files)  # no Anbennar levels
        self.assertNotIn("common/customizable_localization/aov_monument_illustration.txt", files)  # shared
        self.assertIn("aov_monument_khugdihr_bank_03 = {", files["common/buildings/aov_monuments_dwarovar.txt"])

    def test_shared_illustration_covers_every_region(self):
        cl = bm.render_shared()["common/customizable_localization/aov_monument_illustration.txt"]
        for region in bm.REGIONS:
            for m in bm.load_monuments(region):
                if m["art"]:
                    self.assertIn(f"localization_key = aov_monument_art_{m['eu4_key']}", cl)
        self.assertEqual(cl.count("fallback = yes"), 1)

    def test_province_unique_across_regions(self):
        real = bm.load_monuments
        cannor = real("cannor")
        clash = [dict(real("dwarovar")[0], province=cannor[0]["province"])]
        bm.load_monuments = lambda r: cannor if r == "cannor" else clash
        try:
            with self.assertRaises(bm.GeneratorError):
                bm.render_shared()
        finally:
            bm.load_monuments = real

    def test_written_files_are_fresh(self):
        files = {**bm.render_all("dwarovar"), **bm.render_shared()}
        for rel, text in files.items():
            self.assertEqual((bm.SUBMOD / rel).read_bytes().decode("utf-8-sig"), text.replace("\r\n", "\n"), rel)



if __name__ == "__main__":
    unittest.main()

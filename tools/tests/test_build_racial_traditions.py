"""Tests for tools/build_racial_traditions.py: racial traditions, their units, costs, game-start grants and loc.

    python -I -m unittest discover -s tools/tests -p "test_build_racial_traditions*.py"
"""

import re
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_racial_traditions as brt  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
from data import racial_traditions as data  # noqa: E402
from pdx_script import parse_blocks  # noqa: E402

MOD = Path(__file__).resolve().parent.parent.parent
ON_ACTION_FILE = "common/on_action/aov_racial_traditions_on_actions.txt"
GATED_ELSEWHERE = {  # units of Anbennar or the overhaul unlocked by a tradition parameter, and their files
    "aov_unlock_maa_thorn_druids": "common/men_at_arms_types/zz_aov_faith_maa_overrides.txt",
}
GATED_ELSEWHERE.update({f"aov_unlock_maa_{u}": "common/men_at_arms_types/aov_dwarven_maa_types.txt" for u in (
    "grudgebearers", "silverforge_engineers", "tortoise_formation", "giantbane_crossbows", "uthojdihr_marines",
    "seg_band_gnollhunters", "golden_gate_guard", "clockwork_bows", "dauvek_veker", "copper_road_wardens",
    "brightbeard_hammers", "lens_crossbows", "lightflare_guard", "flint_forest_rangers", "orcrend_guard",
    "basalt_berserkers")})


def _text(rel):
    return (MOD / rel).read_bytes().decode("utf-8-sig")


def squash(text):
    return " ".join(text.split())


class GeneratedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = brt.build_all()
        cls.traditions = parse_blocks(cls.files[brt.TRADITION_FILE].decode("utf-8-sig"))
        cls.units = parse_blocks(cls.files[brt.MAA_FILE].decode("utf-8-sig"))
        cls.effects = cls.files[brt.EFFECT_FILE].decode("utf-8-sig")
        cls.loc = cls.files[brt.LOC_FILE].decode("utf-8-sig")

    def test_files_have_bom_and_lf(self):
        for rel, content in self.files.items():
            self.assertTrue(content.startswith(b"\xef\xbb\xbf"), rel)
            self.assertNotIn(b"\r", content, rel)

    def test_every_tradition_written(self):
        self.assertEqual(set(self.traditions), set(data.TRADITIONS))

    def test_traditions_gated_to_their_culture_and_descendants(self):
        for key, t in data.TRADITIONS.items():
            inner = parse_blocks(self.traditions[key])
            self.assertEqual(squash(inner["is_shown"]), f"has_cultural_pillar = {t['heritage']}", key)
            kind, value = t["gate"]
            want = (f"{value} = yes" if kind == "lineage" else
                    f"OR = {{ this = culture:{value} any_parent_culture_or_above = {{ this = culture:{value} }} }}")
            self.assertEqual(squash(inner["can_pick"]), want, key)

    def test_units_unlocked_by_their_tradition(self):
        for key, t in data.TRADITIONS.items():
            params = squash(parse_blocks(self.traditions[key]).get("parameters", ""))
            for unit in t.get("units", ()):
                self.assertIn(f"{brt.unit_parameter(unit)} = yes", params, key)
                gate = squash(parse_blocks(self.units[unit])["can_recruit"])
                self.assertEqual(gate, f"valid_for_maa_trigger = {{ PARAMETER = {brt.unit_parameter(unit)} }}", unit)

    def test_parameters_reach_their_units(self):
        """Every other parameter gates a unit in the overhaul's hand-written MAA files."""
        for t in data.TRADITIONS.values():
            for p in t.get("parameters", ()):
                self.assertIn(p, GATED_ELSEWHERE, p)
                self.assertIn(f"valid_for_maa_trigger = {{ PARAMETER = {p} }}", squash(_text(GATED_ELSEWHERE[p])), p)

    def test_unit_costs_follow_racial_pricing(self):
        values = dict(re.findall(r"^(\w+) = ([0-9.]+)$", self.files[brt.VALUES_FILE].decode("utf-8-sig"), re.M))
        for key, u in data.UNITS.items():
            vd, vt, vb, vu = data.VANILLA_ROLES[u["type"]]
            factor = ((u["stack"] * u["damage"] / vd) * (u["stack"] * u["toughness"] / vt)) ** 0.5
            buy, low, high = (float(values[f"{key}_{s}"]) for s in ("recruitment_cost", "low_maint_cost",
                                                                     "high_maint_cost"))
            self.assertAlmostEqual(buy, vb * factor, delta=vb * factor * 0.05, msg=key)
            self.assertAlmostEqual(low, vu * factor, delta=vu * factor * 0.05, msg=key)
            self.assertAlmostEqual(high, 3 * low, places=6, msg=key)

    def test_unit_art_copied(self):
        for key, u in data.UNITS.items():
            for folder in ("icons/regimenttypes", "illustrations/men_at_arms_big", "illustrations/men_at_arms_small"):
                self.assertTrue((MOD / "gfx/interface" / folder / f"aov_rie_{u['art']}.dds").is_file(),
                                f"{key} {folder}")

    def test_grants_at_game_start(self):
        blocks = parse_blocks(_text(ON_ACTION_FILE))
        self.assertIn("aov_racial_traditions_game_start", squash(blocks["on_game_start"]))
        self.assertIn("aov_racial_traditions_game_start_effect = yes", squash(blocks["aov_racial_traditions_game_start"]))
        for culture, traditions in data.GRANTS.items():
            for t in traditions:
                self.assertIn(f"if = {{ limit = {{ NOT = {{ has_cultural_tradition = {t} }} }} "
                              f"add_culture_tradition = {t} }}", squash(self.effects.split(f"culture:{culture} = {{")[1]
                                                                         .split("\n\t}")[0]), culture)

    def test_marble_keeps_masons_and_gets_whitestone(self):
        self.assertEqual(data.GRANTS["marble_dwarvish"],
                         ("tradition_masons_of_the_deep", "tradition_whitestone_council"))

    def test_serpentreach_cultures_granted(self):
        want = {"cobalt_dwarvish": "tradition_glasslords", "diamond_dwarvish": "tradition_aegis_of_the_serpentreach",
                "flint_dwarvish": "tradition_warding_gate", "garnet_dwarvish": "tradition_hold_where_love_lives",
                "basalt_dwarvish": "tradition_hearts_of_fire"}
        for culture, tradition in want.items():
            self.assertEqual(data.GRANTS[culture], (tradition,), culture)
            self.assertEqual(data.TRADITIONS[tradition]["gate"], ("culture", culture), tradition)

    def test_regional_elves_get_their_parents_tradition(self):
        for culture in ("redglader", "ibevari", "celmaldorian", "venaili"):
            self.assertIn("tradition_elven_high_culture", data.GRANTS[culture])
        for culture in ("lake", "mountain", "thorn", "bone", "hunter", "flower", "river", "arrow", "shadow"):
            self.assertIn("tradition_ranger_art", data.GRANTS[f"{culture}_elvish"])

    def test_localization_complete(self):
        keys = set(re.findall(r"^ (\S+):0 ", self.loc, re.M))
        for key in data.TRADITIONS:
            self.assertTrue({f"{key}_name", f"{key}_desc"} <= keys, key)
        for key in data.UNITS:
            self.assertTrue({key, f"{key}_flavor", f"culture_parameter_{brt.unit_parameter(key)}"} <= keys, key)
        for p in GATED_ELSEWHERE:
            self.assertIn(f"culture_parameter_{p}", keys)
        self.assertIn("GetMaA('druids')", self.loc)


class CheckTests(unittest.TestCase):
    def test_unknown_culture_errors(self):
        with mock.patch.dict(data.GRANTS, {"no_such_culture": ("tradition_ranger_art",)}):
            with self.assertRaisesRegex(GeneratorError, "no_such_culture"):
                brt.build_all()

    def test_unknown_tradition_errors(self):
        with mock.patch.dict(data.GRANTS, {"taric": ("tradition_no_such_thing",)}):
            with self.assertRaisesRegex(GeneratorError, "tradition_no_such_thing"):
                brt.build_all()

    def test_realms_in_exile_words_rejected(self):
        unit = dict(data.UNITS["aov_hearth_muster"], flavor="Hobbits of the Shire.")
        with mock.patch.dict(data.UNITS, {"aov_hearth_muster": unit}):
            with self.assertRaisesRegex(GeneratorError, "Realms in Exile word"):
                brt.build_all()

    def test_unit_without_tradition_errors(self):
        with mock.patch.dict(data.UNITS, {"aov_stray": dict(data.UNITS["aov_hearth_muster"])}):
            with self.assertRaisesRegex(GeneratorError, "exactly one tradition"):
                brt.build_all()


class FreshnessTests(unittest.TestCase):
    def test_generated_files_match_the_mod(self):
        stale = [rel for rel, content in brt.build_all().items()
                 if not (MOD / rel).is_file() or (MOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_racial_traditions.py")


if __name__ == "__main__":
    unittest.main()

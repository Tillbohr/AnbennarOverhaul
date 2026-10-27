"""Tests for tools/build_lich_maa.py and the Lich's raised dead.

    python -I -m unittest discover -s tools/tests -p test_build_lich_maa.py
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_lich_maa as blm  # noqa: E402
from build_hud_override import brace_delta  # noqa: E402

MOD = blm.SUBMOD
HAVE_REAL = blm.DEFAULT_ANBENNAR.is_dir() and blm.DEFAULT_GAME.is_dir()
LICH_MAA = "common/men_at_arms_types/aov_lich_maa_types.txt"
EFFECTS = "common/scripted_effects/aov_lich_maa_effects.txt"
VALUES = "common/script_values/aov_lich_maa_values.txt"

MAA = (
    "@maa_buy_cost = 150\n"
    "@provisions_cost_infantry_cheap = 3\n"
    "\n"
    "light_footmen = {\n"
    "\ttype = skirmishers\n"
    "\tcan_recruit = {\n"
    "\t\tNOR = { government_has_flag = government_is_nomadic }\n"
    "\t}\n"
    "\tprovision_cost = @provisions_cost_infantry_cheap\n"
    "}\n"
    "\n"
    "pikemen_militia = {\n"
    "\ttype = peasant_militia\n"
    "\tstack = 100\n"
    "}\n"
    "\n"
    "trebuchet = {\n"
    "\ttype = siege_weapon\n"
    "}\n"
)


def read(rel):
    return (MOD / rel).read_bytes().decode("utf-8-sig")


def block(text, name):
    m = re.search(rf"^{re.escape(name)} = \{{\n(.*?)\n^\}}", text, re.M | re.S)
    assert m, name
    return m.group(1)


class MaaTests(unittest.TestCase):
    def setUp(self):
        self.files = blm.build_maa(MAA, blm.MAA_SOURCE, submod=Path("does-not-exist"))
        self.maa = self.files[blm.MAA_FILE].decode("utf-8-sig")

    def test_gate_first_in_can_recruit(self):
        self.assertRegex(block(self.maa, "light_footmen"),
                         r"can_recruit = \{\n\t\tNOT = \{ has_trait = lich \}.*\n\t\tNOR = ")

    def test_new_can_recruit_when_missing(self):
        self.assertIn("\tcan_recruit = {\n\t\tNOT = { has_trait = lich }", block(self.maa, "pikemen_militia"))

    def test_siege_engines_stay_recruitable(self):
        self.assertNotIn("trebuchet", self.maa)
        trig = self.files[blm.TRIGGERS_FILE].decode("utf-8-sig")
        self.assertNotIn("trebuchet", trig)
        self.assertIn("is_maa_type = light_footmen", trig)
        self.assertIn("is_maa_type = pikemen_militia", trig)

    def test_only_used_variables_copied(self):
        self.assertIn("@provisions_cost_infantry_cheap = 3", self.maa)
        self.assertNotIn("@maa_buy_cost", self.maa)

    def test_refuses_keys_overridden_elsewhere(self):
        with self.assertRaises(blm.GeneratorError):
            blm.build_maa(MAA.replace("light_footmen", "aithchri"), blm.MAA_SOURCE)


TYPE_VIEW = (
    "widget = {\n"
    "\ttext_single = {\n"
    "\t\tname = \"men_at_arms_cost\"\n"
    "\t\ttext = \"[MenAtArmsType.GetCostString( GetPlayer )]\"\n"
    "\t}\n"
    "\tbutton_primary = {\n"
    "\t\tsize = { 200 40 }\n"
    "\t\ttext = \"[MenAtArmsTypeView.GetCostString( GetPlayer )]\"\n"
    "\t\tonclick = \"[MenAtArmsTypeView.Create]\"\n"
    "\t}\n"
    "}\n"
)

REGIMENT_VIEW = (
    "widget = {\n"
    "\tbutton_primary = {\n"
    "\t\tonclick = \"[MenAtArmsView.BuyMaa]\"\n"
    "\t\ttext_single = {\n"
    "\t\t\ttext = \"MAA_SIZE_CHANGE\"\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
)


class GuiTests(unittest.TestCase):
    def test_type_view_mana_price_and_pay(self):
        out = blm.patch_type_view(TYPE_VIEW)
        self.assertEqual(sum(brace_delta(l) for l in out.split("\n")), 0)
        self.assertIn(f'visible = "[Not( {blm.IS_ITEM} )]"', out)
        self.assertIn(f'visible = "[{blm.IS_ITEM}]"', out)
        ours = out[out.index(f'visible = "[{blm.IS_SELECTED}]"'):]
        # Create first, then pay for what it raised
        self.assertLess(ours.index("[MenAtArmsTypeView.Create]"), ours.index("aov_lich_maa_pay"))
        self.assertIn('text = "AOV_LICH_MAA_COST"', ours)
        vanilla = out[:out.index(f'visible = "[{blm.IS_SELECTED}]"')]
        self.assertIn(f'visible = "[Not( {blm.IS_SELECTED} )]"', vanilla)
        self.assertNotIn("aov_lich_maa_pay", vanilla)

    def test_regiment_view_pays_after_buying(self):
        out = blm.patch_regiment_view(REGIMENT_VIEW)
        self.assertLess(out.index("[MenAtArmsView.BuyMaa]"), out.index("aov_lich_maa_pay"))
        self.assertIn(f'visible = "[{blm.IS_REGIMENT}]"', out)
        self.assertEqual(sum(brace_delta(l) for l in out.split("\n")), 0)

    def test_refuses_patched_files(self):
        with self.assertRaises(blm.GeneratorError):
            blm.patch_type_view(blm.patch_type_view(TYPE_VIEW))
        with self.assertRaises(blm.GeneratorError):
            blm.patch_regiment_view(blm.patch_regiment_view(REGIMENT_VIEW))

    def test_missing_anchor(self):
        with self.assertRaises(blm.GeneratorError):
            blm.patch_type_view(TYPE_VIEW.replace("Create", "Make"))

    def test_icon_key_matches_the_raised_dead(self):
        maa = read(LICH_MAA)
        for key in ("aov_lich_skeletons", "aov_lich_skeleton_archers"):
            self.assertIn(f"\ticon = {blm.ICON_KEY}\n", block(maa, key) + "\n")


class RaisedDeadTests(unittest.TestCase):
    def test_no_gold_no_upkeep_no_provisions(self):
        maa = read(LICH_MAA)
        for key in ("aov_lich_skeletons", "aov_lich_skeleton_archers"):
            body = block(maa, key)
            for cost in ("buy_cost", "low_maintenance_cost", "high_maintenance_cost"):
                self.assertNotIn(cost, body)
            self.assertIn("provision_cost = 0", body)
            self.assertIn("aov_lich_maa_can_recruit = yes", body)

    def test_recruit_needs_lich_and_mana(self):
        trig = block(read("common/scripted_triggers/aov_lich_maa_triggers.txt"), "aov_lich_maa_can_recruit")
        self.assertIn("has_trait = lich", trig)
        self.assertIn("aov_mana >= aov_lich_maa_next_cost", trig)

    def test_payment_and_hooks(self):
        effects = read(EFFECTS)
        pay = block(effects, "aov_lich_maa_pay")
        self.assertIn("aov_mana_spend = { AMOUNT = aov_lich_maa_owed }", pay)
        self.assertIn("set_variable = { name = aov_lich_maa_paid value = aov_lich_maa_capacity }", pay)
        becoming = block(effects, "aov_lich_maa_on_becoming_lich")
        self.assertIn("aov_lich_maa_forbidden_regiment = yes", becoming)
        self.assertIn("destroy_maa_regiment = yes", becoming)
        self.assertIn("aov_lich_maa_on_becoming_lich = yes",
                      block(read("common/scripted_effects/aov_advancement_level_effects.txt"), "aov_adv_lich_ascend"))
        oa = read("common/on_action/aov_lich_maa_on_actions.txt")
        self.assertIn("aov_lich_maa_quarterly", block(oa, "quarterly_playable_pulse"))
        self.assertIn("aov_lich_maa_game_start", block(oa, "on_game_start_after_lobby"))
        sgui = block(read("common/scripted_guis/aov_lich_maa_sgui.txt"), "aov_lich_maa_pay")
        self.assertIn("aov_lich_maa_pay = yes", sgui)

    def test_capacity_counts_only_raised_dead(self):
        self.assertIn("aov_lich_maa_regiment = yes", block(read(VALUES), "aov_lich_maa_capacity"))

    def test_art_and_loc(self):
        for rel in (f"gfx/interface/icons/regimenttypes/{blm.ICON_KEY}.dds",
                    f"gfx/interface/illustrations/men_at_arms_big/{blm.ICON_KEY}.dds",
                    f"gfx/interface/illustrations/men_at_arms_small/{blm.ICON_KEY}.dds"):
            self.assertTrue((MOD / rel).is_file(), rel)
        loc = read("localization/english/aov_lich_maa_l_english.yml")
        for key in ("aov_lich_skeletons", "aov_lich_skeleton_archers", "aov_lich_maa_needs_mana",
                    "AOV_LICH_MAA_COST", "AOV_LICH_MAA_COST_TT"):
            self.assertRegex(loc, rf"(?m)^ {key}:")


@unittest.skipUnless(HAVE_REAL, "Anbennar and game needed")
class FreshnessTests(unittest.TestCase):
    def test_generated_files_match_the_mod(self):
        stale = [rel for rel, content in blm.build_all().items()
                 if not (MOD / rel).is_file() or (MOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_lich_maa.py")


if __name__ == "__main__":
    unittest.main()

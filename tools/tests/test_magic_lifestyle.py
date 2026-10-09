"""Static checks on the magic lifestyle (perks, traits, focuses, loc, mastery).

    python -I -m unittest discover -s tools/tests -v
"""

import re
import unittest
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent.parent
SCHOOLS = ("abjuration", "conjuration", "divination", "enchantment", "evocation", "illusion", "necromancy", "transmutation")

TREES = {
    "aov_arcane_scholar": [
        "aov_diviners_eye_perk", "aov_read_the_stars_perk", "aov_prescience_perk",
        "aov_warding_glyphs_perk", "aov_arcane_reservoir_perk", "aov_spellguard_perk",
        "aov_transmuters_craft_perk", "aov_ley_lines_perk", "aov_arcane_scholar_perk",
    ],
    "aov_battle_mage": [
        "aov_spark_of_battle_perk", "aov_overchannel_perk", "aov_firestorm_tactics_perk",
        "aov_summoners_circle_perk", "aov_conjured_provisions_perk", "aov_bound_elementals_perk",
        "aov_battle_meditation_perk", "aov_mage_knight_perk", "aov_battle_mage_perk",
    ],
    "aov_mindweaver": [
        "aov_silver_tongue_perk", "aov_hearts_desire_perk", "aov_lasting_charm_perk",
        "aov_veil_perk", "aov_mirror_image_perk", "aov_grand_illusion_perk",
        "aov_grave_whispers_perk", "aov_deathless_will_perk", "aov_mindweaver_perk",
    ],
}
TRAIT_OF = {"aov_arcane_scholar": "arcane_scholar", "aov_battle_mage": "battle_mage", "aov_mindweaver": "mindweaver"}
FINAL_PERKS = {keys[8] for keys in TREES.values()}
FOCUS_OF = {
    "divination": "magic_arcane_study_focus", "abjuration": "magic_arcane_study_focus", "transmutation": "magic_arcane_study_focus",
    "evocation": "magic_duelist_focus", "conjuration": "magic_duelist_focus", "necromancy": "magic_mindweaving_focus",
    "enchantment": "magic_mindweaving_focus", "illusion": "magic_mindweaving_focus",
}
STUDY_PERK = {
    "divination": "aov_diviners_eye_perk", "abjuration": "aov_warding_glyphs_perk", "transmutation": "aov_transmuters_craft_perk",
    "evocation": "aov_spark_of_battle_perk", "conjuration": "aov_summoners_circle_perk", "enchantment": "aov_silver_tongue_perk",
    "illusion": "aov_veil_perk", "necromancy": "aov_grave_whispers_perk",
}
COST_PERK = {
    "divination": "aov_read_the_stars_perk", "abjuration": "aov_spellguard_perk", "transmutation": "aov_ley_lines_perk",
    "evocation": "aov_overchannel_perk", "conjuration": "aov_conjured_provisions_perk", "enchantment": "aov_hearts_desire_perk",
    "illusion": "aov_mirror_image_perk", "necromancy": "aov_deathless_will_perk",
}
YEARS_PERK = {
    "divination": "aov_prescience_perk", "evocation": "aov_firestorm_tactics_perk", "conjuration": "aov_bound_elementals_perk",
    "enchantment": "aov_lasting_charm_perk", "illusion": "aov_grand_illusion_perk",
}
PERK_FILES = {
    "aov_arcane_scholar": "common/lifestyle_perks/aov_magic_arcane_scholar_perks.txt",
    "aov_battle_mage": "common/lifestyle_perks/aov_magic_battle_mage_perks.txt",
    "aov_mindweaver": "common/lifestyle_perks/aov_magic_mindweaver_perks.txt",
}
LAYOUT = [(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2), (1, 3), (1, 4), (1, 5)]
PARENTS = [[], [0], [1], [], [3], [4], [2, 5], [6], [7]]   # indices into the tree's perk list


def read(rel):
    return (MOD / rel).read_text(encoding="utf-8-sig")


def block(text, name):
    m = re.search(rf"^{re.escape(name)} = \{{\n(.*?)\n^\}}", text, re.M | re.S)
    assert m, name
    return m.group(1)


def all_perks():
    out = {}
    for rel in PERK_FILES.values():
        for m in re.finditer(r"^(\w+_perk) = \{\n(.*?)\n^\}", read(rel), re.M | re.S):
            out[m.group(1)] = m.group(2)
    return out


class PerkTests(unittest.TestCase):
    def test_three_trees_of_nine(self):
        perks = all_perks()
        self.assertEqual(len(perks), 27)
        for tree, keys in TREES.items():
            for k in keys:
                self.assertIn(f"tree = {tree}", perks[k])
                self.assertIn("lifestyle = magic_lifestyle", perks[k])

    def test_vanilla_layout_and_parents(self):
        for tree, keys in TREES.items():
            for i, k in enumerate(keys):
                body = all_perks()[k]
                x, y = LAYOUT[i]
                self.assertIn(f"position = {{ {x} {y} }}", body)
                self.assertEqual(sorted(re.findall(r"parent = (\w+)", body)), sorted(keys[p] for p in PARENTS[i]))

    def test_final_perk_grants_trait(self):
        for tree, keys in TREES.items():
            body = all_perks()[keys[8]]
            self.assertIn(f"trait = {TRAIT_OF[tree]}", body)
            self.assertIn(f"add_trait_force_tooltip = {TRAIT_OF[tree]}", body)
            self.assertIn(f"icon = trait_{TRAIT_OF[tree]}", body)

    def test_every_perk_syncs_mastery(self):
        for k, body in all_perks().items():
            self.assertIn("aov_magic_sync_mastery = yes", body, k)

    def test_root_perks_respect_new_tree_rule(self):
        for keys in TREES.values():
            for root in (keys[0], keys[3]):
                self.assertIn("can_start_new_lifestyle_tree_trigger = no", all_perks()[root])


TREE_SKILLS = {"aov_arcane_scholar": {"learning", "stewardship"}, "aov_battle_mage": {"martial", "prowess"}, "aov_mindweaver": {"diplomacy", "intrigue"}}
TREE_OF_FOCUS = {"magic_arcane_study_focus": "aov_arcane_scholar", "magic_duelist_focus": "aov_battle_mage", "magic_mindweaving_focus": "aov_mindweaver"}


def tree_schools(tree):
    return {s for s in SCHOOLS if FOCUS_OF[s] == {v: k for k, v in TREE_OF_FOCUS.items()}[tree]}


class AIWeightTests(unittest.TestCase):
    def check(self, body, tree, label):
        weight = body
        self.assertEqual(set(re.findall(r"aov_is_studying = \{ SCHOOL = (\w+) \}", weight)), tree_schools(tree), label)
        self.assertEqual(set(re.findall(r"highest_skill(?:_including_prowess)? = (\w+)", weight)), TREE_SKILLS[tree], label)
        # The engine rejects prowess in highest_skill (error.log): it needs highest_skill_including_prowess
        self.assertNotIn("highest_skill = prowess", weight, label)
        self.assertIn("NOT = { has_variable = aov_studying }", weight, label)
        self.assertIn("add = 1000", weight, label)

    def test_perk_weights(self):
        for tree, keys in TREES.items():
            for k in keys[:8]:
                self.check(all_perks()[k].split("character_modifier")[0].split("effect = {")[0], tree, k)

    def test_focus_weights(self):
        f = read("common/focuses/zz_aov_magic_focuses.txt")
        for focus, tree in TREE_OF_FOCUS.items():
            self.check(block(f, focus), tree, focus)
        self.assertIn("has_trait = brave", block(f, "magic_duelist_focus"))

    def test_root_rule_is_last(self):
        for keys in TREES.values():
            for r in (keys[0], keys[3]):
                w = all_perks()[r]
                self.assertLess(w.index("add = 1000"), w.index("multiply = 0"))


class TraitFocusTests(unittest.TestCase):
    def test_traits_are_lifestyle(self):
        t = read("common/traits/aov_magic_lifestyle_traits.txt")
        for k in ("arcane_scholar", "battle_mage", "mindweaver"):
            self.assertIn("category = lifestyle", block(t, k))

    def test_focuses(self):
        f = read("common/focuses/zz_aov_magic_focuses.txt")
        for k in ("magic_arcane_study_focus", "magic_duelist_focus", "magic_mindweaving_focus"):
            self.assertIn("lifestyle = magic_lifestyle", block(f, k))
        self.assertIn("prowess = 3", block(f, "magic_duelist_focus"))
        self.assertIn("martial = 1", block(f, "magic_duelist_focus"))


class LocTests(unittest.TestCase):
    def test_every_key_has_loc(self):
        loc = read("localization/english/aov_magic_lifestyle_l_english.yml")
        keys = [f"{p}_name" for p in all_perks()] + [f"{p}_effect" for p in all_perks() if p not in FINAL_PERKS]
        keys += [f"{t}_name" for t in TREES]
        keys += [f"trait_{t}" for t in TRAIT_OF.values()] + [f"trait_{t}_desc" for t in TRAIT_OF.values()]
        for f in ("magic_arcane_study_focus", "magic_mindweaving_focus"):
            keys += [f, f"{f}_desc", f"{f}_modifier"]
        keys += ["magic_arcane_study_focus_study_desc", "magic_arcane_study_focus_effect_desc",
                 "magic_mindweaving_focus_study_desc", "magic_mindweaving_focus_effect_desc", "magic_duelist_focus_study_desc"]
        for k in keys:
            self.assertRegex(loc, rf"(?m)^ {re.escape(k)}:", k)
        rep = read("localization/replace/english/aov_magic_lifestyle_replace_l_english.yml")
        self.assertIn(' magic_duelist_focus: "Battle Mage Focus"', rep)
        self.assertRegex(rep, r"(?m)^ magic_duelist_focus_effect_desc:")
        # Anbennar's placeholder lifestyle text is replaced
        self.assertRegex(rep, r'(?m)^ magic_lifestyle_desc: "Magic is a discipline before it is a gift\.')
        self.assertRegex(rep, r'(?m)^ game_concept_magic_lifestyle_desc: "The \$game_concept_magic_lifestyle\$ is open only')
        self.assertNotIn("all that you can", rep)


class MasteryTests(unittest.TestCase):
    def test_mastery_counts_perks(self):
        self.assertIn("add = magic_lifestyle_perks", block(read("common/script_values/aov_magic_values.txt"), "aov_magic_mastery_value"))
        b = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_magic_sync_mastery")
        self.assertIn("name = magic_lifestyle_total_points", b)


if __name__ == "__main__":
    unittest.main()


class BonusLayerTests(unittest.TestCase):
    def v(self):
        return read("common/script_values/aov_magic_lifestyle_values.txt")

    def test_school_values_name_their_perks(self):
        for s in SCHOOLS:
            self.assertIn(f"has_perk = {STUDY_PERK[s]}", block(self.v(), f"aov_study_mult_{s}"))
            self.assertIn(f"has_focus = {FOCUS_OF[s]}", block(self.v(), f"aov_study_mult_{s}"))
            self.assertIn("has_trait = arcane_scholar", block(self.v(), f"aov_study_mult_{s}"))
            self.assertIn(f"has_perk = {COST_PERK[s]}", block(self.v(), f"aov_cost_cut_{s}"))
            if s in YEARS_PERK:
                self.assertIn(f"has_perk = {YEARS_PERK[s]}", block(self.v(), f"aov_years_mult_{s}"))
            else:
                self.assertEqual(block(self.v(), f"aov_years_mult_{s}").strip(), "value = 1")

    def test_bonus_layer_reads_only_perks_traits_focuses(self):
        refs = set(re.findall(r"has_(?:perk|trait|focus) = (\w+)", self.v()))
        self.assertTrue(refs <= set(all_perks()) | set(TRAIT_OF.values()) | set(FOCUS_OF.values()))
        self.assertNotIn("var:", self.v())

    def test_mana_and_dark_magic(self):
        self.assertIn("has_perk = aov_arcane_reservoir_perk", block(self.v(), "aov_mana_max_bonus"))
        self.assertIn("has_trait = arcane_scholar", block(self.v(), "aov_mana_max_bonus"))
        b = block(self.v(), "aov_mana_refill_mult")
        self.assertIn("has_perk = aov_ley_lines_perk", b)
        self.assertIn("is_at_war = yes", b)
        self.assertIn("has_perk = aov_grave_whispers_perk", block(self.v(), "aov_dark_magic_mult"))
        self.assertIn("has_trait = battle_mage", block(self.v(), "aov_cost_cut_war"))
        self.assertIn("has_trait = mindweaver", block(self.v(), "aov_cost_cut_targeted"))


class WiringTests(unittest.TestCase):
    def test_values_use_layer(self):
        v = read("common/script_values/aov_magic_values.txt")
        self.assertIn("add = aov_mana_max_bonus", block(v, "aov_mana_max"))
        self.assertIn("multiply = aov_mana_refill_mult", block(v, "aov_mana_refill_month"))
        for s in SCHOOLS:
            self.assertIn(f"multiply = aov_study_mult_{s}", block(v, f"aov_study_gain_{s}_month"))

    def test_quarterly_uses_per_school_gain(self):
        b = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_magic_quarterly")
        for s in SCHOOLS:
            self.assertIn(f"aov_study_gain_{s}_month", b)

    def test_dark_magic_scaled(self):
        b = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_dark_magic_roll")
        self.assertEqual(b.count("multiply = aov_dark_magic_mult"), 2)

    def test_mana_spend_clamps(self):
        b = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_mana_spend")
        self.assertIn("subtract = $AMOUNT$", b)
        self.assertIn("min = 0", b)

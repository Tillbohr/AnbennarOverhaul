"""Tests for tools/data/advancements.py and tools/build_advancements.py.

    python -I -m unittest discover -s tools/tests -p "test_build_advancements.py"
"""

import copy
import importlib.util
import re
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
MOD = TOOLS.parent
sys.path.insert(0, str(TOOLS))


def load_data():
    spec = importlib.util.spec_from_file_location("aov_advancements_data", TOOLS / "data" / "advancements.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ADVANCEMENTS


ADVS = load_data()

import build_advancements as ba  # noqa: E402
from build_inventions import GeneratorError  # noqa: E402


class DataTests(unittest.TestCase):
    def test_one_advancement_per_school(self):
        self.assertEqual(sorted(a["school"] for a in ADVS), sorted(ba.SCHOOLS))
        self.assertEqual({a["school"]: a["key"] for a in ADVS}, ba.ADV_OF_SCHOOL)

    def test_three_levels_each(self):
        for a in ADVS:
            self.assertEqual(len(a["levels"]), 3, a["key"])
            self.assertTrue(all(lv["name"] and lv["desc"] for lv in a["levels"]), a["key"])

    def test_costs_and_durations_rise(self):
        for seq in (ba.GOLD, ba.MANA, ba.YEARS):
            self.assertEqual(list(seq), sorted(set(seq)))
        self.assertEqual((ba.GOLD, ba.MANA, ba.YEARS), ((100, 200, 400), (50, 75, 100), (2, 3, 4)))

    def test_possession_and_prisoner_requirements(self):
        req = {a["key"]: a["requires"] for a in ADVS}
        self.assertIn("aov_adv_can_craft_enchanted_artifact", req["enchanted_artifact"][1])
        for n in (2, 3):
            self.assertIn("aov_adv_owns_enchanted_artifact", req["enchanted_artifact"][n])
        self.assertIn("aov_adv_owns_phylactery", req["lichdom"][3])
        self.assertIn("aov_adv_has_sacrifice", req["lichdom"][3])
        self.assertIn("aov_adv_can_become_lich", req["lichdom"][3])


class ValidateTests(unittest.TestCase):
    def broken(self, change):
        advs = copy.deepcopy(ADVS)
        change(advs[0])
        with self.assertRaises(GeneratorError):
            ba.validate(advs)

    def test_real_data_valid(self):
        ba.validate(ADVS)

    def test_rejects_unknown_school(self):
        self.broken(lambda a: a.update(school="pyromancy"))

    def test_rejects_two_levels(self):
        self.broken(lambda a: a.update(levels=a["levels"][:2]))

    def test_rejects_double_quote(self):
        self.broken(lambda a: a["levels"][0].update(desc='a "quoted" word'))

    def test_rejects_bad_requires_level(self):
        self.broken(lambda a: a.update(requires={4: ["aov_adv_x"]}))

    def test_rejects_duplicate(self):
        advs = copy.deepcopy(ADVS)
        advs.append(copy.deepcopy(advs[0]))
        with self.assertRaises(GeneratorError):
            ba.validate(advs)


import build_hud_override  # noqa: E402  (brace_delta)

TRIG = "common/scripted_triggers/aov_advancement_triggers.txt"
VAL = "common/script_values/aov_advancement_values.txt"
EFF = "common/scripted_effects/aov_advancement_effects.txt"
SGUI = "common/scripted_guis/aov_advancement_sgui.txt"
GUI = "gui/aov_advancements_generated.gui"
LOC = "localization/english/aov_advancements_l_english.yml"


def balanced(text):
    depth = 0
    for line in text.split("\n"):
        depth += build_hud_override.brace_delta(line)
        if depth < 0:
            return False
    return depth == 0


def block(text, name):
    m = re.search(rf"^{re.escape(name)} = \{{\n(.*?)\n^\}}", text, re.M | re.S)
    assert m, name
    return m.group(1)


def branch(trigger_body, level):
    """The trigger_if / trigger_else_if body that applies when the advancement has `level` levels done."""
    m = re.search(rf"limit = \{{ aov_adv_\w+_level = {level} \}}\n(.*?)\n\t\}}", trigger_body, re.S)
    assert m, level
    return m.group(1)


try:
    FILES = ba.render_all(ADVS)
except AttributeError:
    FILES = {}


class GeneratedTests(unittest.TestCase):
    def test_render_all_paths(self):
        self.assertEqual(set(FILES), {TRIG, VAL, EFF, SGUI, GUI, LOC})

    def test_outputs_balanced_and_headed(self):
        for rel, text in FILES.items():
            self.assertTrue(balanced(text), rel)
            if rel != LOC:
                self.assertTrue(text.startswith(ba.HEADER), rel)

    def test_can_start_requires_landed_mage_and_not_committed(self):
        t = block(FILES[TRIG], "aov_adv_lichdom_can_start")
        self.assertIn("aov_adv_eligible = yes", t)
        self.assertIn("NOT = { aov_adv_is_committed = yes }", t)
        self.assertIn("text = AOV_ADV_REQ_NOT_COMMITTED", t)
        e = block(FILES[TRIG], "aov_adv_eligible")
        self.assertIn("is_landed = yes", e)
        self.assertIn("aov_is_mage = yes", e)

    def test_level_gate_uses_school_level(self):
        t = block(FILES[TRIG], "aov_adv_lichdom_can_start")
        for done in (0, 1, 2):
            self.assertIn(f"aov_school_level_at_least = {{ SCHOOL = necromancy LEVEL = {done + 1} }}", branch(t, done))

    def test_requires_triggers_in_their_level(self):
        t = block(FILES[TRIG], "aov_adv_lichdom_can_start")
        self.assertIn("aov_adv_owns_phylactery = yes", branch(t, 2))
        self.assertNotIn("aov_adv_owns_phylactery", branch(t, 0) + branch(t, 1))
        e = block(FILES[TRIG], "aov_adv_enchanted_artifact_can_start")
        self.assertIn("aov_adv_can_craft_enchanted_artifact = yes", branch(e, 0))
        self.assertIn("aov_adv_owns_enchanted_artifact = yes", branch(e, 1))

    def test_can_start_checks_gold_and_mana(self):
        t = block(FILES[TRIG], "aov_adv_homunculus_can_start")
        self.assertIn("gold >= aov_adv_homunculus_next_gold", t)
        self.assertIn("aov_mana >= aov_adv_homunculus_next_mana", t)

    def test_start_pays_and_clears_study(self):
        s = block(FILES[EFF], "aov_adv_mirror_image_start")
        self.assertIn("remove_short_term_gold = aov_adv_mirror_image_next_gold", s)
        self.assertIn("aov_mana_spend = { AMOUNT = aov_adv_mirror_image_next_mana }", s)
        self.assertIn("remove_variable = aov_studying", s)
        self.assertIn("set_variable = { name = aov_adv_committed value = flag:mirror_image }", s)
        self.assertIn("set_variable = { name = aov_adv_progress value = 0 }", s)

    def test_abandon_clears_state(self):
        a = block(FILES[EFF], "aov_adv_abandon")
        for v in ("aov_adv_committed", "aov_adv_working_level", "aov_adv_progress"):
            self.assertIn(f"remove_variable = {v}", a)
        self.assertNotIn("gold", a)

    def test_quarterly_abandons_when_ineligible(self):
        q = block(FILES[EFF], "aov_adv_quarterly")
        self.assertLess(q.index("aov_adv_eligible = no"), q.index("aov_adv_abandon = yes"))
        self.assertIn("change_variable = { name = aov_adv_progress add = 3 }", q)
        for k in ba.ADV_OF_SCHOOL.values():
            self.assertIn(f"aov_adv_working_on = {{ KEY = {k} }}", q)
            self.assertIn(f"aov_adv_{k}_complete = yes", q)

    def test_complete_calls_each_level_effect(self):
        for k in ba.ADV_OF_SCHOOL.values():
            c = block(FILES[EFF], f"aov_adv_{k}_complete")
            for n in (1, 2, 3):
                self.assertIn(f"aov_adv_{k}_{n}_effect = yes", c)
            self.assertIn(f"set_variable = {{ name = aov_adv_{k}_lvl value = var:aov_adv_working_level }}", c)
            self.assertIn("trigger_event = aov_advancement.1", c)
            self.assertLess(c.index("_effect = yes"), c.index("aov_adv_abandon = yes"))

    def test_months_needed(self):
        m = block(FILES[VAL], "aov_adv_months_needed")
        for months in (24, 36, 48):
            self.assertIn(str(months), m)

    def test_sguis(self):
        for k in ba.ADV_OF_SCHOOL.values():
            s = block(FILES[SGUI], f"aov_adv_{k}_start_sgui")
            self.assertIn(f"aov_adv_{k}_can_start = yes", s)
            self.assertIn(f"aov_adv_{k}_start = yes", s)
            self.assertIn(f"aov_adv_working_on = {{ KEY = {k} }}", block(FILES[SGUI], f"aov_adv_{k}_working_sgui"))
        self.assertIn("aov_adv_abandon = yes", block(FILES[SGUI], "aov_adv_abandon_sgui"))

    def test_gui_page_per_school(self):
        g = FILES[GUI]
        for c, k in ba.ADV_OF_SCHOOL.items():
            m = re.search(rf"type aov_advancement_{c} = vbox \{{(.*?)\n\t\}}\n", g, re.S)
            self.assertTrue(m, c)
            page = m.group(1)
            self.assertIn(f"aov_adv_{k}_start_sgui", page)
            self.assertIn("aov_adv_abandon_sgui", page)
            self.assertIn(f"ScriptValue( 'aov_adv_{k}_level' )", page)
            self.assertIn("aov_adv_progress_percent", page)

    def test_gui_warns_study_ends(self):
        self.assertEqual(FILES[GUI].count('text = "AOV_ADV_ENDS_STUDY"'), 8)
        self.assertIn("GetPlayer.MakeScope.Var( 'aov_studying' ).IsSet", FILES[GUI])

    def test_start_disabled_elsewhere_names_progress(self):
        for k in ba.ADV_OF_SCHOOL.values():
            self.assertIn("aov_adv_is_committed = yes", block(FILES[SGUI], f"aov_adv_{k}_elsewhere_sgui"))
        self.assertEqual(FILES[GUI].count('text = "AOV_ADV_IN_PROGRESS_ELSEWHERE"'), 8)

    def test_loc_keys(self):
        used = set(re.findall(r"\b(aov_adv_[a-z_0-9]+)", FILES[GUI] + FILES[TRIG] + FILES[EFF]))
        used = {u for u in used if not u.endswith(("_sgui", "_level", "_lvl", "_effect", "_start", "_complete",
                                                     "_can_start", "_next_gold", "_next_mana", "_next_years"))}
        defined = set(re.findall(r"^ (aov_adv_[a-z_0-9]+):", FILES[LOC], re.M))
        script_names = {"aov_adv_eligible", "aov_adv_is_committed", "aov_adv_working_on", "aov_adv_abandon",
                        "aov_adv_quarterly", "aov_adv_committed", "aov_adv_working_level", "aov_adv_progress",
                        "aov_adv_progress_percent", "aov_adv_months_needed", "aov_adv_months_left"}
        requires = {t for a in ADVS for ts in a["requires"].values() for t in ts}
        self.assertEqual(sorted(used - defined - script_names - requires), [])
        for k in ba.ADV_OF_SCHOOL.values():
            for key in (f"aov_adv_{k}", f"aov_adv_{k}_desc", *(f"aov_adv_{k}_{n}" for n in (1, 2, 3)),
                        *(f"aov_adv_{k}_{n}_desc" for n in (1, 2, 3))):
                self.assertIn(key, defined)


class FreshnessTests(unittest.TestCase):
    def test_generated_files_match_the_mod(self):
        stale = [rel for rel, text in FILES.items()
                 if not (MOD / rel).is_file()
                 or (MOD / rel).read_bytes() != b"\xef\xbb\xbf" + text.encode("utf-8")]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_advancements.py")


if __name__ == "__main__":
    unittest.main()

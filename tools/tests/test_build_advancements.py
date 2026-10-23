"""Tests for tools/data/advancements.py and tools/build_advancements.py.

    python -I -m unittest discover -s tools/tests -p "test_build_advancements.py"
"""

import copy
import importlib.util
import re
import sys
import tempfile
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
        for n in (2, 3):
            self.assertIn("aov_adv_owns_orb", req["orb_of_omniscience"][n])
        for n in (2, 3):
            self.assertIn("aov_adv_owns_phylactery", req["lichdom"][n])
        self.assertIn("aov_adv_can_become_lich", req["lichdom"][3])
        # The lich dies by their own potion: no prisoner is needed
        self.assertNotIn("aov_adv_has_sacrifice", str(req["lichdom"]))

    def test_only_lichdom_has_a_start_hook(self):
        hooks = {a["key"]: a["on_start"] for a in ADVS if a["on_start"]}
        self.assertEqual(hooks, {"lichdom": "aov_adv_lichdom_on_start"})


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

    def test_rejects_bad_on_start(self):
        self.broken(lambda a: a.update(on_start="aov adv x"))

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
    """The trigger_if / trigger_else_if / trigger_else body that applies when the advancement has `level` levels done
    (the last branch, for level 2, is the trigger_else)."""
    if level == 2:
        m = re.search(r"\ttrigger_else = \{\n(.*?)\n\t\}", trigger_body, re.S)
    else:
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

    def test_trigger_else_if_chain_ends_in_trigger_else(self):
        """The engine rejects a trigger_else_if with no trigger_else (error.log: 'trigger_else_if with no trigger_else')."""
        for k in ba.ADV_OF_SCHOOL.values():
            t = block(FILES[TRIG], f"aov_adv_{k}_can_start")
            self.assertIn("\ttrigger_else = {", t, k)
            self.assertLess(t.rindex("trigger_else_if"), t.index("\ttrigger_else = {"), k)

    def test_requires_triggers_in_their_level(self):
        t = block(FILES[TRIG], "aov_adv_lichdom_can_start")
        for done in (1, 2):
            self.assertIn("aov_adv_owns_phylactery = yes", branch(t, done))
        self.assertNotIn("aov_adv_owns_phylactery", branch(t, 0))
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

    def test_start_hook_runs_after_commitment(self):
        s = block(FILES[EFF], "aov_adv_lichdom_start")
        self.assertLess(s.index("set_variable = { name = aov_adv_progress value = 0 }"),
                        s.index("aov_adv_lichdom_on_start = yes"))
        self.assertNotIn("on_start", block(FILES[EFF], "aov_adv_mirror_image_start"))

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
            # The commitment ends before the level effect; the success event is skipped when the level fires its own
            # (a lost artifact, Lichdom's ascension)
            self.assertLess(c.index("aov_adv_abandon = yes"), c.index("_effect = yes"))
            self.assertIn("limit = { NOT = { exists = scope:aov_adv_own_event } }\n\t\ttrigger_event = aov_advancement.1", c)

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
            self.assertNotIn(f"aov_adv_{k}_elsewhere_sgui", FILES[SGUI])
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

    def pages(self):
        return {c: re.search(rf"type aov_advancement_{c} = vbox \{{(.*?)\n\t\}}\n", FILES[GUI], re.S).group(1)
                for c in ba.SCHOOLS}

    def test_gui_warns_which_study_ends(self):
        for c, page in self.pages().items():
            for s in ba.SCHOOLS:
                m = re.search(rf'text = "AOV_ADV_ENDS_STUDY_{s.upper()}"\n\s*visible = "\[(.*?)\]"', page)
                self.assertTrue(m, f"{c}: {s}")
                self.assertIn(f"aov_study_{s}_sgui').IsShown", m.group(1))
        for s in ba.SCHOOLS:
            self.assertIn(f"$AOV_SCHOOL_{s.upper()}$", re.search(rf'AOV_ADV_ENDS_STUDY_{s.upper()}: "(.*)"', FILES[LOC]).group(1))

    def test_elsewhere_line_names_the_advancement(self):
        for c, page in self.pages().items():
            own = ba.ADV_OF_SCHOOL[c]
            self.assertNotIn(f'text = "aov_adv_{own}_in_progress"', page)
            for k in ba.ADV_OF_SCHOOL.values():
                if k != own:
                    m = re.search(rf'text = "aov_adv_{k}_in_progress"\n\s*visible = "\[(.*?)\]"', page)
                    self.assertTrue(m, f"{c}: {k}")
                    self.assertIn(f"aov_adv_{k}_working_sgui').IsShown", m.group(1))
        for k in ba.ADV_OF_SCHOOL.values():
            self.assertIn(f"$aov_adv_{k}$", re.search(rf'aov_adv_{k}_in_progress: "(.*)"', FILES[LOC]).group(1))

    def test_loc_keys(self):
        gui = re.sub(r'name = "\w+"', "", FILES[GUI])  # widget names are not loc keys
        used = set(re.findall(r"\b(aov_adv_[a-z_0-9]+)", gui + FILES[TRIG] + FILES[EFF]))
        used = {u for u in used if not u.endswith(("_sgui", "_level", "_lvl", "_effect", "_start", "_complete",
                                                     "_can_start", "_next_gold", "_next_mana", "_next_years"))}
        defined = set(re.findall(r"^ (aov_adv_[a-z_0-9]+):", FILES[LOC], re.M))
        script_names = {"aov_adv_eligible", "aov_adv_is_committed", "aov_adv_working_on", "aov_adv_abandon",
                        "aov_adv_quarterly", "aov_adv_committed", "aov_adv_working_level", "aov_adv_progress",
                        "aov_adv_progress_percent", "aov_adv_months_needed", "aov_adv_months_left",
                        "aov_adv_ai_pick", "aov_adv_ai_yearly", "aov_adv_own_event",
                        "aov_adv_lichdom_on_start"}
        requires = {t for a in ADVS for ts in a["requires"].values() for t in ts}
        self.assertEqual(sorted(used - defined - script_names - requires), [])
        for k in ba.ADV_OF_SCHOOL.values():
            for key in (f"aov_adv_{k}", f"aov_adv_{k}_desc", *(f"aov_adv_{k}_{n}" for n in (1, 2, 3)),
                        *(f"aov_adv_{k}_{n}_desc" for n in (1, 2, 3))):
                self.assertIn(key, defined)


class AiTests(unittest.TestCase):
    def test_ai_pick_uses_can_start(self):
        pick = block(FILES[EFF], "aov_adv_ai_pick")
        options = pick.split("\t\t\t10 = {")[1:]
        self.assertEqual(len(options), 8)
        for k in ba.ADV_OF_SCHOOL.values():
            option = next(o for o in options if f"aov_adv_{k}_start = yes" in o)
            self.assertLess(option.index(f"aov_adv_{k}_can_start = yes"), option.index("modifier = {"))

    def test_ai_prefers_its_best_schools(self):
        pick = block(FILES[EFF], "aov_adv_ai_pick")
        for c in ba.SCHOOLS:
            self.assertIn(f"value = aov_school_{c}_level", pick)

    def test_ai_skips_lichdom_unless_dark(self):
        pick = block(FILES[EFF], "aov_adv_ai_pick")
        lich = pick[pick.index("aov_adv_lichdom_can_start"):pick.index("aov_adv_lichdom_start")]
        self.assertIn("has_trait = forbidden_magic_practitioner", lich)
        self.assertIn("aov_dark_magic_risky = no", lich)


class ArtTests(unittest.TestCase):
    def test_committed_art_exists(self):
        ba.check_art(MOD)

    def test_missing_art_stops_the_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(GeneratorError):
                ba.check_art(Path(tmp))

    def test_gui_uses_project_art(self):
        g = FILES[GUI]
        self.assertEqual(g.count(f'{ba.ART_DIR}/project_progress_full.dds'), 8)

    def test_begin_is_one_button(self):
        """The EU4 project plate behind the Begin button read as two overlapping buttons: no plate."""
        g = FILES[GUI]
        self.assertNotIn("project_button.dds", g)
        self.assertNotIn("project_button.dds", ba.ART)
        self.assertEqual(g.count('text = "AOV_ADV_START"'), 8)


class LevelListTests(unittest.TestCase):
    def page(self, c):
        return re.search(rf"type aov_advancement_{c} = vbox \{{(.*?)\n\t\}}\n", FILES[GUI], re.S).group(1)

    def test_levels_listed_vertically_with_effects(self):
        for c, k in ba.ADV_OF_SCHOOL.items():
            page = self.page(c)
            rows = [page.index(f'name = "aov_adv_{k}_level_{n}"') for n in (1, 2, 3)]
            self.assertEqual(rows, sorted(rows))
            track = page[page.index('name = "aov_adv_levels"'):]
            self.assertTrue(track.lstrip().startswith('name = "aov_adv_levels"'))
            self.assertIn("vbox = {\n", page[:page.index('name = "aov_adv_levels"')][-40:])
            for n in (1, 2, 3):
                self.assertIn(f'text = "aov_adv_{k}_{n}_desc"', page)

    def test_level_status(self):
        page = self.page("necromancy")
        for status, cmp in (("AOV_ADV_LEVEL_DONE", "GreaterThanOrEqualTo_CFixedPoint( GetPlayer.MakeScope.ScriptValue( 'aov_adv_lichdom_level' ), '(CFixedPoint)2' )"),
                            ("AOV_ADV_LEVEL_NEXT", "EqualTo_CFixedPoint( GetPlayer.MakeScope.ScriptValue( 'aov_adv_lichdom_level' ), '(CFixedPoint)1' )"),
                            ("AOV_ADV_LEVEL_LOCKED", "LessThan_CFixedPoint( GetPlayer.MakeScope.ScriptValue( 'aov_adv_lichdom_level' ), '(CFixedPoint)1' )")):
            m = re.search(rf'text = "{status}"\n\s*visible = "\[(.*?)\]"', page[page.index('name = "aov_adv_lichdom_level_2"'):])
            self.assertTrue(m, status)
            self.assertIn(cmp, m.group(1))

    def test_level_texts_say_what_they_give(self):
        """Every level description names a concrete effect: a number or a named unlock."""
        for a in ADVS:
            for lv in a["levels"]:
                self.assertRegex(lv["desc"], r"[+-]?\d|[A-Z][a-z]+ [A-Z]", f"{a['key']}: {lv['desc']}")
                self.assertNotIn("grows stronger", lv["desc"])
                self.assertNotIn("reaches its full power", lv["desc"])


class FreshnessTests(unittest.TestCase):
    def test_generated_files_match_the_mod(self):
        stale = [rel for rel, text in FILES.items()
                 if not (MOD / rel).is_file()
                 or (MOD / rel).read_bytes() != b"\xef\xbb\xbf" + text.encode("utf-8")]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_advancements.py")


if __name__ == "__main__":
    unittest.main()

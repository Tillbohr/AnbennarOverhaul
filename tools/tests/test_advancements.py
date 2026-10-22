"""Static checks on the hand-written magic advancement script (interlock, tick, level effects, content).

    python -I -m unittest discover -s tools/tests -p "test_advancements.py"
"""

import importlib.util
import re
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
MOD = TOOLS.parent
SCHOOLS = ("abjuration", "conjuration", "divination", "enchantment", "evocation", "illusion", "necromancy", "transmutation")


def load_data():
    spec = importlib.util.spec_from_file_location("aov_advancements_data", TOOLS / "data" / "advancements.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ADVANCEMENTS


ADVS = load_data()
ADV_KEYS = [a["key"] for a in ADVS]

LEVEL_EFFECTS = "common/scripted_effects/aov_advancement_level_effects.txt"
CONDITIONS = "common/scripted_triggers/aov_advancement_conditions.txt"
ON_ACTIONS = "common/on_action/aov_advancement_on_actions.txt"
EVENTS = "events/aov_advancement_events.txt"
CONTENT_LOC = "localization/english/aov_advancement_content_l_english.yml"
TUNING = "common/script_values/aov_advancement_tuning.txt"
MODIFIERS = "common/modifiers/aov_advancement_modifiers.txt"


def read(rel):
    return (MOD / rel).read_text(encoding="utf-8-sig")


def block(text, name):
    m = re.search(rf"^{re.escape(name)} = \{{\n(.*?)\n^\}}", text, re.M | re.S)
    assert m, name
    return m.group(1)


def loc_keys(rel):
    return set(re.findall(r"^ ([A-Za-z0-9_.]+):", read(rel), re.M))


class InterlockTests(unittest.TestCase):
    def test_study_button_blocked_while_committed(self):
        sg = read("common/scripted_guis/aov_spell_sgui.txt")
        for c in SCHOOLS:
            body = block(sg, f"aov_study_{c}_sgui")
            self.assertIn("text = AOV_ADV_REQ_NOT_COMMITTED", body)
            self.assertIn("NOT = { aov_adv_is_committed = yes }", body)

    def test_ai_does_not_restudy_while_committed(self):
        ai = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_magic_ai_quarterly")
        self.assertRegex(ai, r"NOT = \{ has_variable = aov_studying \}\s*\n\s*NOT = \{ has_variable = aov_adv_committed \}")

    def test_quarterly_pulse_runs_the_tick_for_mages(self):
        oa = read(ON_ACTIONS)
        self.assertIn("aov_adv_quarterly_pulse", block(oa, "quarterly_playable_pulse"))
        pulse = block(oa, "aov_adv_quarterly_pulse")
        self.assertIn("aov_is_mage = yes", pulse)
        self.assertIn("aov_adv_quarterly = yes", pulse)

    def test_every_level_effect_defined_once(self):
        eff = read(LEVEL_EFFECTS)
        for key in ADV_KEYS:
            for n in (1, 2, 3):
                self.assertEqual(len(re.findall(rf"^aov_adv_{key}_{n}_effect = \{{", eff, re.M)), 1, f"{key} {n}")

    def test_every_requires_trigger_defined(self):
        cond = read(CONDITIONS)
        for a in ADVS:
            for names in a["requires"].values():
                for t in names:
                    self.assertRegex(cond, rf"(?m)^{t} = \{{", t)

    def test_completion_event_exists(self):
        ev = read(EVENTS)
        self.assertTrue(ev.startswith("namespace = aov_advancement"))
        body = block(ev, "aov_advancement.1")
        for key in ADV_KEYS:
            self.assertIn(f"scope:aov_adv = flag:{key}", body)

    def test_ui_loc(self):
        keys = loc_keys(CONTENT_LOC)
        for k in ("AOV_ADV_REQ_ELIGIBLE", "AOV_ADV_REQ_NOT_COMMITTED", "AOV_ADV_REQ_NOT_DONE",
                  "AOV_ADV_IN_PROGRESS_ELSEWHERE", "AOV_ADV_START", "AOV_ADV_ABANDON", "AOV_ADV_ABANDON_TT",
                  "AOV_ADV_PROGRESS", "AOV_ADV_COMPLETE", "AOV_ADV_ENDS_STUDY",
                  "AOV_MAGIC_TAB_ADVANCEMENTS", "AOV_MAGIC_TAB_SPELLS", "aov_advancement.1.t", "aov_advancement.1.a"):
            self.assertIn(k, keys)
        for key in ADV_KEYS:
            self.assertIn(f"aov_advancement.1.desc.{key}", keys)


if __name__ == "__main__":
    unittest.main()

"""Static checks on the Delving Campaign events (dwarven hold digging).

    python -I -m unittest discover -s tools/tests -p test_hold_dig_events.py
"""

import re
import unittest
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent.parent
ON_ACTIONS = "common/on_action/aov_hold_dig_on_actions.txt"
EVENTS = "events/aov_hold_dig_events.txt"
LOC = "localization/english/aov_hold_dig_events_l_english.yml"
PULSES = {
    "aov_hold_dig_survey_pulse": {1, 2, 3},
    "aov_hold_dig_excavation_pulse": {4, 5, 6, 7, 8},
    "aov_hold_dig_shoring_pulse": {9, 10, 11},
}
SETBACKS = {2, 5, 6, 8, 9, 11}


def read(rel):
    return (MOD / rel).read_text(encoding="utf-8-sig")


def blocks(text):
    return {m.group(1): m.group(2) for m in re.finditer(r"^([\w.]+) = \{\n(.*?)^\}", text, re.M | re.S)}


def pulse_body(name):
    return blocks(read(ON_ACTIONS))[name]


def pulse_events(name):
    return {int(n) for n in re.findall(r"trigger_event = aov_hold_dig\.(\d+)", pulse_body(name))}


def pulse_entry(name, n):
    """The random_list entry (weight block) of event n inside a pulse."""
    for entry in re.findall(r"^\t\t\t\d+ = \{\n(.*?)^\t\t\t\}", pulse_body(name), re.M | re.S):
        if f"trigger_event = aov_hold_dig.{n}\n" in entry:
            return entry
    raise AssertionError((name, n))


class DigEventTests(unittest.TestCase):
    def test_every_event_has_loc_and_options(self):
        events, loc = read(EVENTS), read(LOC)
        for n in range(1, 12):
            self.assertIn(f"aov_hold_dig.{n} = {{", events)
            for key in (f"aov_hold_dig.{n}.t", f"aov_hold_dig.{n}.desc", f"aov_hold_dig.{n}.a"):
                self.assertIn(f" {key}:", loc)
        parsed = blocks(events)
        for n in range(1, 12):
            body = parsed[f"aov_hold_dig.{n}"]
            options = re.findall(r"^\toption = \{", body, re.M)
            self.assertIn(len(options), (2, 3), n)
            self.assertIn("involved_activity = { has_activity_type = activity_hold_dig }", body)
            self.assertIn("save_scope_as = activity", body)
            self.assertIn("save_scope_as = hold", body)
            for opt in re.findall(r"name = (aov_hold_dig\.\d+\.\w+)", body):
                self.assertIn(f" {opt}:", loc)

    def test_pulses_cover_phases(self):
        for name, expected in PULSES.items():
            self.assertEqual(pulse_events(name), expected, name)

    def test_setbacks_weighted_by_pace(self):
        for name, expected in PULSES.items():
            for n in expected:
                entry = pulse_entry(name, n)
                reckless = "category = aov_dig_pace option = aov_dig_pace_reckless"
                careful = "category = aov_dig_pace option = aov_dig_pace_careful"
                if n in SETBACKS:
                    for factor, cond in (("2", reckless), ("0.5", careful)):
                        pattern = (rf"modifier = \{{\n\t+factor = {re.escape(factor)}\n\t+involved_activity = "
                                   rf"\{{ has_activity_option = \{{ {cond} \}} \}}\n")
                        self.assertRegex(entry, pattern, n)
                else:
                    self.assertNotIn("aov_dig_pace", entry, n)

    def test_progress_changes_within_bounds(self):
        events = read(EVENTS)
        found = 0
        for m in re.finditer(r"change_variable = \{ name = aov_campaign_progress (add|subtract) = (-?\d+) \}", events):
            found += 1
            self.assertLessEqual(abs(int(m.group(2))), 20)
        self.assertGreater(found, 20)
        # Every change to the progress variable is a bounded literal one.
        self.assertEqual(found, len(re.findall(r"name = aov_campaign_progress", events)))
        # A progress reduction never leaves the campaign below 0.
        self.assertIn("aov_dig_floor_progress = yes", events)

    def test_floor_effect_defined(self):
        eff = blocks(read("common/scripted_effects/aov_hold_dig_event_effects.txt"))
        self.assertIn("aov_dig_floor_progress", eff)
        self.assertIn("var:aov_campaign_progress < 0", eff["aov_dig_floor_progress"])

    def test_something_in_the_deep_is_a_skill_check(self):
        body = blocks(read(EVENTS))["aov_hold_dig.8"]
        self.assertRegex(body, r"duel = \{\s*skill = prowess\s*value = \d+")
        self.assertRegex(body, r"duel = \{\s*skill = martial\s*value = \d+")
        self.assertEqual(len(re.findall(r"desc = aov_hold_dig\.8\.\w+\.(success|failure)", body)), 4)

    def test_costly_options_check_gold(self):
        for n, body in blocks(read(EVENTS)).items():
            for opt in re.findall(r"^\toption = \{\n(.*?)^\t\}", body, re.M | re.S):
                for gold in re.findall(r"remove_short_term_gold = (\d+)", opt):
                    self.assertRegex(opt, rf"gold >= {gold}\b", n)


if __name__ == "__main__":
    unittest.main()

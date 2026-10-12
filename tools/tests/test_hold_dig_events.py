"""Static checks on the dig events (dwarven hold digging, Delve Deeper).

    python -I -m unittest discover -s tools/tests -p test_hold_dig_events.py
"""

import re
import unittest
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent.parent
EVENTS = "events/aov_hold_dig_events.txt"
LOC = "localization/english/aov_hold_dig_events_l_english.yml"


def read(rel):
    return (MOD / rel).read_text(encoding="utf-8-sig")


def blocks(text):
    return {m.group(1): m.group(2) for m in re.finditer(r"^([\w.]+) = \{\n(.*?)^\}", text, re.M | re.S)}


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
            self.assertIn("exists = scope:hold", body)
            self.assertIn("scope:hold = { aov_hold_dig_running = yes }", body)
            for opt in re.findall(r"name = (aov_hold_dig\.\d+\.\w+)", body):
                self.assertIn(f" {opt}:", loc)

    def test_progress_changes_within_bounds(self):
        events = read(EVENTS)
        found = 0
        for m in re.finditer(r"scope:hold = \{ aov_hold_add_dig_progress_effect = \{ MONTHS = (-?\d+) \} \}", events):
            found += 1
            self.assertLessEqual(abs(int(m.group(1))), 20)
        self.assertGreater(found, 20)
        # Every change to the dig progress is a bounded literal one, through the effect that keeps it at 0 or above.
        self.assertEqual(found, events.count("aov_hold_add_dig_progress_effect"))
        self.assertNotIn("aov_dig_progress", events)

    def test_something_in_the_deep_is_a_skill_check(self):
        body = blocks(read(EVENTS))["aov_hold_dig.8"]
        self.assertRegex(body, r"duel = \{\s*skill = prowess\s*value = \d+")
        self.assertRegex(body, r"duel = \{\s*skill = martial\s*value = \d+")
        self.assertEqual(len(re.findall(r"desc = aov_hold_dig\.8\.\w+\.(success|failure)", body)), 4)

    def test_something_in_the_deep_failures_promise_no_wounds(self):
        # the failure branches only cost progress, so their text must not describe the character being hurt
        loc = read(LOC)
        for opt in ("a", "b"):
            line = re.search(rf"^ aov_hold_dig\.8\.{opt}\.failure:0 \"(.*)\"$", loc, re.M).group(1)
            self.assertNotRegex(line.lower(), r"wound|claw|injur|blood|armou?r|drag you", opt)
        self.assertNotIn("add_trait", blocks(read(EVENTS))["aov_hold_dig.8"])

    def test_costly_options_check_gold(self):
        for n, body in blocks(read(EVENTS)).items():
            for opt in re.findall(r"^\toption = \{\n(.*?)^\t\}", body, re.M | re.S):
                for gold in re.findall(r"remove_short_term_gold = (\d+)", opt):
                    self.assertRegex(opt, rf"gold >= {gold}\b", n)


if __name__ == "__main__":
    unittest.main()

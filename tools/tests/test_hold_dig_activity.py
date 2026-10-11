"""Static checks on the Delving Campaign activity (dwarven hold digging).

    python -I -m unittest discover -s tools/tests -p test_hold_dig_activity.py
"""

import re
import sys
import unittest
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(MOD / "tools" / "data"))
import holds  # noqa: E402

ACTIVITY = "common/activities/activity_types/aov_hold_dig.txt"
EFFECTS = "common/scripted_effects/aov_hold_effects.txt"
ON_ACTIONS = "common/on_action/aov_hold_dig_on_actions.txt"
EVENTS = "events/aov_hold_dig_events.txt"
LOC = "localization/english/aov_hold_dig_l_english.yml"
PHASES = ["survey", "excavation", "shoring", "breakthrough"]


def read(rel):
    return (MOD / rel).read_text(encoding="utf-8-sig")


def parse_blocks(text):
    """Top-level `name = {` ... `}` blocks, by name."""
    return {m.group(1): m.group(2) for m in re.finditer(r"^([\w.]+) = \{\n(.*?)^\}", text, re.M | re.S)}


def sub_block(body, name, depth):
    """The multi-line block `name = {` opened at `depth` tabs inside `body`."""
    tabs = "\t" * depth
    m = re.search(rf"^{tabs}{re.escape(name)} = \{{\n(.*?)^{tabs}\}}", body, re.M | re.S)
    assert m, f"{name} at depth {depth}"
    return m.group(1)


def child_names(body, depth):
    return re.findall(rf"^{chr(9) * depth}(\w+) = \{{$", body, re.M)


def phase_blocks(act):
    phases = sub_block(act, "phases", 1)
    return {name: sub_block(phases, name, 2) for name in child_names(phases, 2)}


def is_valid_block(act):
    return sub_block(act, "is_valid", 1)


def can_start_block(act):
    return sub_block(act, "can_start", 1)


def effect_block(name):
    return parse_blocks(read(EFFECTS))[name]


class DelvingCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.act = parse_blocks(read(ACTIVITY))["activity_hold_dig"]

    def test_four_predefined_phases_in_order(self):
        phases = phase_blocks(self.act)
        self.assertEqual(list(phases), [f"aov_dig_{p}" for p in PHASES])
        for order, (key, phase) in enumerate(zip(PHASES, phases.values()), 1):
            self.assertIn("is_predefined = yes", phase)
            self.assertIn(f"order = {order}", phase)
            months = holds.PHASE_MONTHS[key]
            self.assertIn(f"progress_activity_phase_after = {{ months = {months} }}", phase)
        self.assertEqual([holds.PHASE_MONTHS[p] for p in PHASES], [3, 12, 6, 1])

    def test_player_pulses_in_first_three_phases(self):
        phases = phase_blocks(self.act)
        for key in PHASES[:3]:
            phase = phases[f"aov_dig_{key}"]
            self.assertRegex(phase, rf"is_ai = no[\s\S]*on_action = aov_hold_dig_{key}_pulse days = \{{ 30 60 \}}")
        self.assertNotIn("on_action", phases["aov_dig_breakthrough"])
        self.assertIn("aov_hold_apply_campaign_effect = yes", phases["aov_dig_breakthrough"])
        on_actions = parse_blocks(read(ON_ACTIONS))
        for key in PHASES[:3]:
            self.assertIn(f"aov_hold_dig_{key}_pulse", on_actions)

    def test_war_does_not_invalidate(self):
        self.assertNotIn("is_at_war", is_valid_block(self.act))
        self.assertIn("is_at_war = no", can_start_block(self.act))

    def test_is_valid_ends_on_loss_ruin_or_siege(self):
        block = is_valid_block(self.act)
        for needle in ("is_alive = yes", "aov_hold_is_working = yes", "barony.holder = scope:host",
                       "is_occupied = no", "is_army_in_siege = yes"):
            self.assertIn(needle, block)

    def test_running_dig_checked_on_the_hold(self):
        trig = parse_blocks(read("common/scripted_triggers/aov_hold_triggers.txt"))["aov_can_dig_at"]
        digger = sub_block(trig, "scope:digger", 1)
        self.assertNotIn("aov_dig_in_progress", digger)
        self.assertRegex(trig, r"(?m)^\tNOT = \{ has_variable = aov_dig_in_progress \}$")
        # A running campaign must not fail its own validity because of its own flag.
        self.assertNotIn("aov_can_dig_at", is_valid_block(self.act))
        for phase in phase_blocks(self.act).values():
            self.assertNotIn("aov_can_dig_at", phase)
        for hook in ("on_invalidated", "on_host_death"):
            self.assertIn(f"\t{hook} = {{\n\t\tvar:aov_dig_hold ?= {{ remove_variable = aov_dig_in_progress }}\n\t}}",
                          self.act)

    def test_host_and_location(self):
        self.assertIn("is_dwarvish_culture = yes", sub_block(self.act, "is_shown", 1))
        self.assertIn("aov_can_dig_at = yes", can_start_block(self.act))
        self.assertIn("aov_dig_campaign_cost", can_start_block(self.act))
        loc = sub_block(self.act, "is_location_valid", 1)
        self.assertIn("aov_can_dig_at = yes", loc)
        self.assertIn("barony.holder = scope:host", loc)
        self.assertIn("province_filter = domain", self.act)
        self.assertIn("max_guests = 0", self.act)
        self.assertIn("allow_zero_guest_invites = yes", self.act)
        self.assertIn("aov_dig_campaign_cost", sub_block(self.act, "cost", 1))

    def test_on_start_stores_progress_and_hold(self):
        on_start = sub_block(self.act, "on_start", 1)
        self.assertIn("name = aov_campaign_progress value = scope:host.aov_dig_campaign_base", on_start)
        self.assertIn("name = aov_dig_hold value = activity_location", on_start)
        self.assertRegex(on_start, r"activity_location = \{\s*set_variable = aov_dig_in_progress")

    def test_progress_targets_activity_location(self):
        eff = effect_block("aov_hold_apply_campaign_effect")
        self.assertIn("var:aov_dig_hold", eff)
        self.assertNotIn("capital_province", eff)

    def test_level_up_carries_surplus_and_caps_at_ten(self):
        eff = effect_block("aov_hold_apply_campaign_effect")
        self.assertRegex(eff, r"aov_dig_progress[\s\S]*subtract[\s\S]*aov_dig_target")
        self.assertIn("aov_hold_level < 10", eff)
        self.assertEqual(eff.count("add_building"), 9)  # one guarded add per level 02..10
        for n in range(2, 11):
            self.assertIn(f"aov_hold_level = {n - 1} }}\n\t\t\t\tadd_building = dwarven_hold_{n:02d}", eff)
        self.assertIn("aov_hold_dig.100", eff)
        self.assertIn("aov_hold_dig.101", eff)
        self.assertIn("remove_variable = aov_dig_in_progress", eff)

    def test_options_match_data(self):
        opts = sub_block(self.act, "options", 1)
        self.assertEqual(child_names(opts, 2), ["aov_dig_pace", "aov_dig_investment"])
        pace = sub_block(opts, "aov_dig_pace", 2)
        inv = sub_block(opts, "aov_dig_investment", 2)
        self.assertEqual(child_names(pace, 3), [f"aov_dig_pace_{k}" for k in holds.PACE])
        self.assertEqual(child_names(inv, 3), [f"aov_dig_investment_{k}" for k in holds.INVESTMENT])
        self.assertEqual(list(holds.PACE), ["careful", "steady", "reckless"])
        self.assertEqual(list(holds.INVESTMENT), ["none", "generous", "lavish"])
        on_start = sub_block(self.act, "on_start", 1)
        factors = {f"aov_dig_pace_{k}": v for k, v in holds.PACE.items()}
        for key, (gold, factor) in holds.INVESTMENT.items():
            option = sub_block(inv, f"aov_dig_investment_{key}", 3)
            if gold:
                self.assertRegex(option, rf"cost = \{{\s*gold = \{{\s*add = \{{\s*value = {gold}\b")
            else:
                self.assertNotIn("cost", option)
            factors[f"aov_dig_investment_{key}"] = factor
        for option, factor in factors.items():
            category = option.rsplit("_", 1)[0]
            pattern = (rf"has_activity_option = \{{ category = {category} option = {option} \}}\s*\}}\s*"
                       rf"change_variable = \{{ name = aov_campaign_progress multiply = {factor:g} \}}")
            if factor == 1:
                self.assertNotRegex(on_start, pattern)
            else:
                self.assertRegex(on_start, pattern)

    def test_ai_does_not_drain_treasury(self):
        ai = sub_block(self.act, "ai_will_do", 1)
        self.assertIn("gold >= { value = aov_dig_campaign_cost multiply = 2 }", ai)
        for weight in ("stewardship", "has_trait = diligent", "has_trait = greedy"):
            self.assertIn(weight, ai)
        self.assertIn("ai_check_interval = 12", self.act)

    def test_end_campaign_extended_not_duplicated(self):
        text = read(EFFECTS)
        self.assertEqual(len(re.findall(r"^aov_hold_end_campaign_effect = \{", text, re.M)), 1)
        eff = effect_block("aov_hold_end_campaign_effect")
        self.assertIn("remove_variable = aov_dig_in_progress", eff)
        self.assertIn("has_activity_type = activity_hold_dig", eff)
        self.assertIn("invalidate_activity", eff)

    def test_events_and_loc(self):
        events = parse_blocks(read(EVENTS))
        self.assertIn("namespace = aov_hold_dig", read(EVENTS))
        self.assertIn("aov_hold_dig.100", events)
        self.assertIn("aov_hold_dig.101", events)
        ev100 = events["aov_hold_dig.100"]
        self.assertIn("multiply = 25", ev100)
        self.assertIn("modifier = aov_hold_rich_vein", ev100)
        self.assertIn("years = 10", ev100)
        self.assertIn("add_learning_lifestyle_xp = 500", ev100)
        loc = read(LOC)
        for key in ("activity_hold_dig", "aov_dig_pace", "aov_dig_investment", "aov_hold_dig.100.t",
                    "aov_hold_dig.101.t", *[f"aov_dig_{p}" for p in PHASES],
                    *[f"aov_dig_pace_{k}" for k in holds.PACE],
                    *[f"aov_dig_investment_{k}" for k in holds.INVESTMENT]):
            self.assertRegex(loc, rf"(?m)^ {re.escape(key)}:")


if __name__ == "__main__":
    unittest.main()

"""The hand-written tribal script: forming titles, raising vassals, and (Task 9) duels."""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import pdx_script  # noqa: E402
from data import dwarovar_tribes as dt  # noqa: E402

SUBMOD = Path(__file__).resolve().parents[2]
TIERS = {"duchy": "tier_county", "kingdom": "tier_duchy", "empire": "tier_kingdom"}


def read(rel: str) -> str:
    return (SUBMOD / rel).read_text(encoding="utf-8-sig")


def blocks(text: str) -> dict:
    return pdx_script.parse_blocks(pdx_script.strip_comments(text))


def section(body: str, name: str) -> str:
    """The block `name = { ... }` one tab into a top-level block."""
    return re.search(rf"(?m)^\t{name} = \{{\n(.*?)^\t\}}", body, re.S).group(1)


class FormDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decisions = blocks(read("common/decisions/aov_tribes_decisions.txt"))

    def decision(self, tier):
        return self.decisions[f"aov_form_tribal_{tier}_decision"]

    def test_form_decisions_tier_gates(self):
        for tier, below in TIERS.items():
            self.assertIn(f"highest_held_title_tier = {below}", section(self.decision(tier), "is_shown"), tier)

    def test_form_decisions_use_values(self):
        for tier in TIERS:
            body = self.decision(tier)
            self.assertIn(f"sub_realm_size >= aov_form_{tier}_counties", section(body, "is_valid"), tier)
            self.assertIn(f"prestige = aov_form_{tier}_prestige", section(body, "cost"), tier)

    def test_form_decisions_gate_on_government(self):
        for tier in TIERS:
            self.assertIn("government_has_flag = government_is_dwarovar_tribe",
                          section(self.decision(tier), "is_shown"), tier)

    def test_form_decisions_independent_or_not(self):
        # a vassal count may form a duchy; the tier gate and the county count are the only limits
        for tier in TIERS:
            self.assertNotIn("is_independent_ruler", self.decision(tier), tier)

    def test_form_decisions_need_a_free_title(self):
        for tier in TIERS:
            valid = section(self.decision(tier), "is_valid")
            self.assertRegex(valid, rf"custom_description = \{{\s*text = aov_tribe_no_free_title\s*"
                                    rf"aov_tribe_has_free_title_trigger = \{{ TIER = {tier} \}}", tier)

    def test_form_effect_transfers_the_saved_title(self):
        for tier in TIERS:
            effect = section(self.decision(tier), "effect")
            self.assertIn(f"aov_tribe_take_free_title_effect = {{ TIER = {tier} }}", effect, tier)
            self.assertIn("type = created", effect, tier)
            self.assertRegex(effect, r"scope:aov_new_title = \{\s*change_title_holder = \{\s*holder = root", tier)
            self.assertIn("resolve_title_and_vassal_change = scope:change", effect, tier)

    def test_ai_does_not_rush(self):
        for tier in TIERS:
            body = self.decision(tier)
            self.assertRegex(body, r"(?m)^\tai_check_interval = 60$", tier)
            self.assertRegex(section(body, "ai_will_do"), r"factor = 0", tier)


class RaiseVassalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body = blocks(read("common/character_interactions/aov_tribes_interactions.txt"))[
            "aov_raise_tribal_vassal_interaction"]

    def test_raise_tier_rules(self):
        shown = section(self.body, "is_shown")
        self.assertIn("scope:recipient = {", shown)
        self.assertIn("liege = scope:actor", shown)
        self.assertEqual(shown.count("government_has_flag = government_is_dwarovar_tribe"), 2)
        self.assertRegex(shown, r"scope:actor = \{ highest_held_title_tier = tier_kingdom \}\s*"
                                r"scope:recipient = \{ highest_held_title_tier <= tier_county \}")
        self.assertRegex(shown, r"scope:actor = \{ highest_held_title_tier = tier_empire \}\s*"
                                r"scope:recipient = \{ highest_held_title_tier <= tier_duchy \}")

    def test_grants_one_tier_below_the_actor(self):
        accept = section(self.body, "on_accept")
        self.assertRegex(accept, r"highest_held_title_tier = tier_kingdom \}\s*\}\s*scope:recipient = \{\s*"
                                 r"aov_tribe_take_free_title_effect = \{ TIER = duchy \}")
        self.assertRegex(accept, r"scope:recipient = \{\s*aov_tribe_take_free_title_effect = \{ TIER = kingdom \}")
        self.assertRegex(accept, r"change_title_holder = \{\s*holder = scope:recipient")

    def test_duke_cannot_raise(self):
        shown = section(self.body, "is_shown")
        self.assertRegex(shown, r"scope:actor = \{[^}]*highest_held_title_tier >= tier_kingdom", re.S)

    def test_cost_and_auto_accept(self):
        self.assertRegex(self.body, r"(?m)^\tauto_accept = yes$")
        self.assertIn("prestige = aov_raise_prestige", section(self.body, "cost"))

    def test_needs_a_free_title(self):
        valid = section(self.body, "is_valid_showing_failures_only")
        self.assertIn("text = aov_tribe_no_free_title", valid)
        self.assertIn("aov_tribe_has_free_title_trigger = { TIER = duchy }", valid)
        self.assertIn("aov_tribe_has_free_title_trigger = { TIER = kingdom }", valid)


class LocTests(unittest.TestCase):
    def test_loc_complete(self):
        loc = read("localization/english/aov_tribes_decisions_l_english.yml")
        keys = ["aov_raise_tribal_vassal_interaction", "aov_raise_tribal_vassal_interaction_desc",
                "aov_tribe_no_free_title"]
        for tier in TIERS:
            base = f"aov_form_tribal_{tier}_decision"
            keys += [base, f"{base}_desc", f"{base}_tooltip", f"{base}_confirm"]
        self.assertEqual([k for k in keys if not re.search(rf'(?m)^ {k}:\d* ?"', loc)], [])


class DuelDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body = blocks(read("common/decisions/aov_tribes_decisions.txt"))["aov_challenge_warlord_decision"]
        cls.shown = section(cls.body, "is_shown")
        cls.valid = section(cls.body, "is_valid_showing_failures_only")

    def test_challenger_must_be_orc(self):
        self.assertIn("has_trait = race_orc", self.shown)
        self.assertNotIn("race_goblin", self.body)

    def test_liege_must_be_top_warband(self):
        self.assertRegex(self.shown, r"liege \?= \{\s*this != root\s*is_independent_ruler = yes\s*"
                                     r"government_has_flag = government_is_orcish_warband")
        self.assertIn("is_landed = yes", self.shown)

    def test_no_goblin_ruler_can_be_challenged(self):
        self.assertNotIn("government_is_dwarovar_tribe", self.shown)
        self.assertNotIn("government_is_goblin_chiefdom", self.shown)

    def test_limits(self):
        self.assertIn("is_adult = yes", self.valid)
        self.assertIn("is_imprisoned = no", self.shown)
        self.assertIn("is_at_war = no", self.valid)
        self.assertRegex(self.valid, r"liege = \{[^}]*is_adult = yes[^}]*is_imprisoned = no[^}]*is_at_war = no", re.S)
        self.assertRegex(self.body, rf"(?m)^\tcooldown = \{{ years = {dt.CHALLENGE_COOLDOWN_YEARS} \}}$")

    def test_a_ruler_who_cannot_fight_cannot_be_challenged(self):
        self.assertRegex(self.valid, r"liege = \{[^}]*can_start_single_combat_trigger = yes", re.S)

    def test_ai_weaker_never_challenges(self):
        ai = section(self.body, "ai_will_do")
        self.assertRegex(ai, r"factor = 0\s*prowess < liege\.prowess")
        self.assertIn("has_trait = ambitious", section(self.body, "ai_potential"))

    def test_vanilla_challenge_blocked(self):
        override = blocks(read("common/decisions/zz_aov_dwarovar_tribes_overrides.txt"))["tribal_challenge_ruler_decision"]
        self.assertIn("NOT = { government_has_flag = government_is_dwarovar_tribe }", section(override, "is_shown"))


class DuelEventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = read("events/aov_tribes_duel_events.txt")
        cls.received = cls.event("aov_tribe_duel.1")
        cls.outcome = cls.event("aov_tribe_duel.2")
        cls.invalid = cls.event("aov_tribe_duel.3")

    @classmethod
    def event(cls, key):
        return re.search(rf"(?ms)^{re.escape(key)} = \{{\n(.*?)^\}}", cls.events).group(1)

    def test_accept_uses_vanilla_combat(self):
        accept = re.search(r"(?ms)^\toption = \{\n\t\tname = aov_tribe_duel\.1\.a\n(.*?)^\t\}", self.received).group(1)
        for line in ("configure_start_single_combat_effect = {", "SC_INITIATOR = scope:challenger",
                     "SC_ATTACKER = scope:challenger", "SC_DEFENDER = root", "FATALITY = no",
                     "OUTPUT_EVENT = aov_tribe_duel.2", "INVALIDATION_EVENT = aov_tribe_duel.3"):
            self.assertIn(line, accept)

    def test_refuse_penalties(self):
        refuse = re.search(r"(?ms)^\toption = \{\n\t\tname = aov_tribe_duel\.1\.b\n(.*?)^\t\}", self.received).group(1)
        self.assertIn("add_prestige_level = -5", refuse)
        modifier = re.search(r"add_character_modifier = \{(.*?)\}", refuse, re.S).group(1)
        self.assertIn("modifier = aov_refused_challenge", modifier)
        self.assertNotRegex(modifier, r"years|days|months")
        self.assertNotIn("configure_start_single_combat_effect", refuse)

    def test_both_options_tell_the_challenger(self):
        for name in "ab":
            option = re.search(rf"(?ms)^\toption = \{{\n\t\tname = aov_tribe_duel\.1\.{name}\n(.*?)^\t\}}", self.received).group(1)
            self.assertRegex(option, r"scope:challenger = \{\s*send_interface_toast")

    def test_event_revalidates(self):
        trigger = section(self.received, "trigger")
        for line in ("is_alive = yes", "is_imprisoned = no", "is_at_war = no", "can_start_single_combat_trigger = yes"):
            self.assertEqual(trigger.count(line), 2, line)  # the ruler's and the challenger's
        self.assertIn("liege = root", trigger)

    def test_outcome_order(self):
        win = self.outcome[self.outcome.index("scope:sc_victor = scope:challenger"):]
        win = win[:win.index("else = {")]
        self.assertLess(win.index("aov_tribe_duel_winner_takes_all_effect = yes"), win.index("death = {"))
        self.assertLess(win.index("aov_tribe_duel_winner_takes_all_effect = yes"), win.index("aov_tribe_title_sync_effect = yes"))
        self.assertIn("death_reason = death_duel", win)
        self.assertRegex(win, r"scope:ruler = \{\s*death = \{\s*death_reason = death_duel\s*killer = scope:sc_victor")

    def test_ruler_win_kills_challenger(self):
        lose = self.outcome[self.outcome.rindex("else = {"):]
        self.assertRegex(lose, r"scope:challenger = \{\s*death = \{\s*death_reason = death_duel\s*killer = scope:sc_victor")
        self.assertNotIn("winner_takes_all", lose)

    def test_invalidated_duel_has_no_consequence(self):
        for gone in ("death =", "change_title_holder", "winner_takes_all", "add_prestige"):
            self.assertNotIn(gone, self.invalid)
        self.assertIn("send_interface_toast", self.invalid)

    def test_winner_takes_every_title_and_vassal(self):
        effect = blocks(read("common/scripted_effects/aov_tribes_effects.txt"))["aov_tribe_duel_winner_takes_all_effect"]
        self.assertIn("type = usurped", effect)
        self.assertIn("add_claim_on_loss = no", effect)
        self.assertRegex(effect, r"every_held_title = \{\s*change_title_holder = \{\s*holder = scope:challenger")
        self.assertRegex(effect, r"every_vassal = \{\s*limit = \{ this != scope:challenger \}\s*change_liege")
        self.assertIn("resolve_title_and_vassal_change = scope:change", effect)
        self.assertRegex(effect, r"scope:challenger = \{\s*becomes_independent = \{ change = scope:change \}")

    def test_duel_loc_complete(self):
        loc = read("localization/english/aov_tribes_duel_l_english.yml")
        keys = ["aov_challenge_warlord_decision", "aov_challenge_warlord_decision_desc",
                "aov_challenge_warlord_decision_tooltip", "aov_challenge_warlord_decision_confirm",
                "aov_challenge_warlord_effect_tooltip", "aov_tribe_duel.1.t", "aov_tribe_duel.1.desc", "aov_tribe_duel.1.a",
                "aov_tribe_duel.1.b", "aov_tribe_duel.1.accepted", "aov_tribe_duel.1.refused", "aov_tribe_duel.2.won",
                "aov_tribe_duel.2.lost", "aov_tribe_duel.3.invalid"]
        self.assertEqual([k for k in keys if not re.search(rf'(?m)^ {re.escape(k)}:\d* ?"', loc)], [])


if __name__ == "__main__":
    unittest.main()

"""Static checks on the artificer factions (titles, influence, elections, Factions tab).

    python -I -m unittest discover -s tools/tests -v
"""

import re
import unittest
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent.parent
FACTIONS = ("brillites", "mechanists", "technomancers")
LEVELS = ("hostile", "displeased", "favored", "exalted")


def read(rel):
    return (MOD / rel).read_text(encoding="utf-8-sig")


def block(text, name):
    m = re.search(rf"^{re.escape(name)} = \{{\n(.*?)\n^\}}", text, re.M | re.S)
    assert m, name
    return m.group(1)


class TitleTests(unittest.TestCase):
    def test_three_landless_duchies(self):
        text = read("common/landed_titles/aov_artificer_faction_titles.txt")
        for f in FACTIONS:
            b = block(text, f"d_{f}")
            for line in ("landless = yes", "definite_form = yes", "ruler_uses_title_name = no",
                         "no_automatic_claims = yes", "can_use_nomadic_naming = no", "capital = c_nimscodd"):
                self.assertIn(line, b)
            self.assertNotIn("always_follows_primary_heir", b)

    def test_coats_of_arms_use_cogs(self):
        text = read("common/coat_of_arms/coat_of_arms/aov_artificer_factions.txt")
        self.assertIn("ce_anb_cog", block(text, "d_brillites"))
        self.assertIn("ce_anb_crystal_magic", block(text, "d_brillites"))
        self.assertIn("pattern_checkers_01", block(text, "d_mechanists"))
        self.assertEqual(block(text, "d_mechanists").count("ce_anb_cog.dds"), 2)
        self.assertIn("ce_anb_cog_02", block(text, "d_technomancers"))

    def test_revoke_override_keeps_anbennar_and_excludes_faction_titles(self):
        ours = block(read("common/scripted_triggers/zz_aov_interaction_triggers.txt"), "title_revocation_standard_can_pick_title_trigger")
        base = (MOD.parent / "anbennar-ck3-dev-master/common/scripted_triggers/00_interaction_triggers.txt").read_text(encoding="utf-8-sig")
        for line in block(base, "title_revocation_standard_can_pick_title_trigger").splitlines():
            self.assertIn(line, ours)
        self.assertIn("aov_is_artificer_faction_title = no", ours)

    def test_faction_title_trigger(self):
        b = block(read("common/scripted_triggers/aov_artificer_faction_triggers.txt"), "aov_is_artificer_faction_title")
        for f in FACTIONS:
            self.assertIn(f"this = title:d_{f}", b)


class InfluenceTests(unittest.TestCase):
    def test_twelve_modifiers(self):
        text = read("common/modifiers/aov_artificer_faction_modifiers.txt")
        for f in FACTIONS:
            for lv in LEVELS:
                block(text, f"aov_{f}_{lv}")
        self.assertIn("domain_tax_mult = 0.1", block(text, "aov_mechanists_exalted"))
        self.assertIn("domain_tax_mult = -0.1", block(text, "aov_mechanists_hostile"))
        self.assertIn("learning = 2", block(text, "aov_brillites_exalted"))
        self.assertIn("advantage = -5", block(text, "aov_technomancers_hostile"))

    def test_level_thresholds(self):
        b = block(read("common/script_values/aov_artificer_faction_values.txt"), "aov_influence_level_brillites")
        for n in ("15", "30", "60", "85"):
            self.assertIn(f">= {n}", b)

    def test_costs_and_quarters(self):
        text = read("common/script_values/aov_artificer_faction_values.txt")
        cost = block(text, "aov_research_cost_mechanists")
        for v in ("100", "75", "50", "38", "25"):
            self.assertIn(f"value = {v}", cost)
        q = block(text, "aov_research_quarters_technomancers")
        for v in ("75", "60", "45"):
            self.assertIn(f"value = {v}", q)

    def test_change_influence_clamps(self):
        b = block(read("common/scripted_effects/aov_artificer_faction_effects.txt"), "aov_faction_change_influence")
        self.assertIn("min = 0", b)
        self.assertIn("max = 100", b)
        self.assertIn("aov_faction_refresh_modifiers = yes", b)


class ResearchCostTests(unittest.TestCase):
    def test_common_start_pays_scaled_cost_and_shifts_influence(self):
        b = block(read("common/scripted_effects/aov_artificery_research_effects.txt"), "aov_artificery_start_research_common")
        self.assertIn("set_variable = { name = aov_research_paid value = aov_research_cost_$SPONSOR$ }", b)
        self.assertIn("value = aov_research_quarters_$SPONSOR$", b)
        self.assertIn("aov_faction_sponsor_shift_$SPONSOR$ = yes", b)
        self.assertIn("custom_tooltip = aov_sponsor_influence_$SPONSOR$_tt", b)

    def test_sponsor_shift_is_plus_twenty_minus_ten(self):
        text = read("common/scripted_effects/aov_artificer_faction_effects.txt")
        for f in FACTIONS:
            b = block(text, f"aov_faction_sponsor_shift_{f}")
            self.assertIn(f"aov_faction_change_influence = {{ FACTION = {f} AMOUNT = 20 }}", b)
            for o in FACTIONS:
                if o != f:
                    self.assertIn(f"aov_faction_change_influence = {{ FACTION = {o} AMOUNT = -10 }}", b)

    def test_refund_uses_paid_amount(self):
        b = block(read("common/scripted_effects/aov_artificery_research_effects.txt"), "aov_artificery_complete_research")
        self.assertIn("add_gold = var:aov_research_paid", b)
        self.assertNotIn("add_gold = aov_research_cost", b)

    def test_sponsor_sguis_check_their_faction(self):
        text = read("common/scripted_guis/aov_artificery_research_sgui.txt")
        self.assertIn("aov_artificery_can_sponsor = { FACTION = brillites }", block(text, "aov_research_brillites_sgui"))
        for c in ("economic", "military", "society"):
            self.assertIn("FACTION = mechanists", block(text, f"aov_research_mechanists_{c}_sgui"))
            self.assertIn("FACTION = technomancers", block(text, f"aov_research_technomancers_{c}_sgui"))
        gen = read("common/scripted_guis/aov_invention_sgui.txt")
        self.assertIn("aov_artificery_can_sponsor = { FACTION = technomancers }", block(gen, "aov_inv_sparkdrive_rifles_research_sgui"))


class DriftTests(unittest.TestCase):
    def test_quarterly_applies_running_fade_and_opinion(self):
        b = block(read("common/scripted_effects/aov_artificer_faction_effects.txt"), "aov_factions_quarterly")
        for f in FACTIONS:
            self.assertIn(f"var:aov_research_sponsor = flag:{f}", b)
            self.assertIn(f"var:aov_influence_{f} > 40", b)
            self.assertIn(f"AMOUNT = aov_opinion_drift_{f}", b)

    def test_opinion_drift_bands(self):
        b = block(read("common/script_values/aov_artificer_faction_values.txt"), "aov_opinion_drift_brillites")
        self.assertIn("exists = title:d_brillites.holder", b)
        for cond in ("value >= 50", "value >= 20", "value <= -20", "value <= -50"):
            self.assertIn(f"opinion = {{ target = root {cond} }}", b)

    def test_dormancy_and_inheritance_hooked(self):
        eff = read("common/scripted_effects/aov_artificery_research_effects.txt")
        self.assertIn("aov_faction_remove_modifiers = yes", block(eff, "aov_artificery_update_dormancy"))
        self.assertIn("aov_faction_refresh_modifiers = yes", block(eff, "aov_artificery_update_dormancy"))
        self.assertIn("aov_factions_inherit = yes", block(eff, "aov_artificery_inherit"))

    def test_quarterly_on_action(self):
        text = read("common/on_action/aov_artificer_faction_on_actions.txt")
        self.assertIn("quarterly_playable_pulse = {\n\ton_actions = { aov_artificer_factions_quarterly }", text)

    def test_ai_makes_amends_when_hostile_and_rich(self):
        b = block(read("common/scripted_effects/aov_artificery_research_effects.txt"), "aov_artificery_ai_quarterly")
        for f in FACTIONS:
            self.assertIn(f"aov_faction_make_amends = {{ FACTION = {f} }}", b)
        self.assertIn("gold > 300", b)


class ElectionTests(unittest.TestCase):
    def eff(self, name):
        return block(read("common/scripted_effects/aov_artificer_election_effects.txt"), name)

    def test_open_picks_exactly_three_with_world_fallback(self):
        b = self.eff("aov_election_open")
        self.assertIn("aov_election_clear = { FACTION = $FACTION$ }", b)
        self.assertIn("clear_global_variable_list = aov_candidates_$FACTION$", self.eff("aov_election_clear"))
        self.assertIn("max = 3", b)
        self.assertIn("order_by = aov_candidate_score_$FACTION$", b)
        self.assertIn("every_living_character", b)          # top-up from anywhere
        self.assertIn("name = aov_election_running_$FACTION$ days = 30", b)
        self.assertIn("trigger_event = aov_artificer_factions.1", b)

    def test_vote_adds_weight_and_marks_voter(self):
        b = self.eff("aov_election_cast_vote")
        self.assertIn("save_temporary_scope_value_as = { name = aov_vote_weight value = aov_vote_weight_$FACTION$ }", b)
        self.assertIn("add = scope:aov_vote_weight", b)
        self.assertIn("set_variable = aov_voted_$FACTION$", b)

    def test_resolve_skips_dead_candidates(self):
        self.assertIn("is_alive = yes", self.eff("aov_election_resolve"))

    def test_resolve_skips_current_holders(self):
        self.assertIn("aov_faction_candidate_trigger = yes", self.eff("aov_election_resolve"))
        b = block(read("common/scripted_triggers/aov_artificer_faction_triggers.txt"), "aov_faction_candidate_trigger")
        self.assertIn("any_held_title = { aov_is_artificer_faction_title = yes }", b)

    def test_auto_votes_only_for_living_eligible_voters(self):
        b = self.eff("aov_election_resolve")
        self.assertRegex(b, r"every_ruler = \{\s*limit = \{\s*aov_artificer_nation_trigger = yes\s*NOT = \{ has_variable = aov_voted_\$FACTION\$ \}")

    def test_vote_event_shows_three_candidates_and_highlights(self):
        ev = read("events/aov_artificer_faction_events.txt")
        b = block(ev, "aov_artificer_factions.1")
        for slot in ("lower_left_portrait", "lower_center_portrait", "lower_right_portrait"):
            self.assertIn(slot, b)
        for n in (1, 2, 3):
            self.assertIn(f"highlight_portrait = scope:aov_candidate_{n}", b)
        self.assertIn("theme = aov_artificery", b)

    def test_on_death_and_game_start(self):
        text = read("common/on_action/aov_artificer_faction_on_actions.txt")
        self.assertIn("on_death = {\n\ton_actions = { aov_artificer_factions_on_death }", text)
        self.assertIn("on_game_start_after_lobby = {\n\ton_actions = { aov_artificer_factions_game_start }", text)
        self.assertIn("yearly_global_pulse = {\n\ton_actions = { aov_artificer_factions_yearly }", text)

    def test_grant_uses_title_change(self):
        b = self.eff("aov_faction_grant_title")
        self.assertIn("create_title_and_vassal_change", b)
        self.assertIn("change_title_holder = { holder = $WINNER$ change = scope:aov_change }", b)
        self.assertIn("resolve_title_and_vassal_change = scope:aov_change", b)


class FactionsTabTests(unittest.TestCase):
    def test_make_amends_caps_at_forty(self):
        b = block(read("common/scripted_effects/aov_artificer_faction_effects.txt"), "aov_faction_make_amends")
        self.assertIn("remove_short_term_gold = 100", b)
        self.assertIn("max = 40", b)

    def test_make_amends_sgui_only_below_forty_with_gold(self):
        text = read("common/scripted_guis/aov_artificer_faction_sgui.txt")
        for f in FACTIONS:
            b = block(text, f"aov_make_amends_{f}_sgui")
            self.assertIn(f"aov_influence_{f} < 40", b)
            self.assertIn("gold >= 100", b)
            self.assertIn(f"aov_faction_make_amends = {{ FACTION = {f} }}", b)

    def test_tab_has_three_cards(self):
        win = read("gui/aov_window_artificery.gui")
        self.assertNotIn("AOV_ARTIFICERY_FACTIONS_PLACEHOLDER", win)
        self.assertEqual(win.count("aov_faction_card = {"), 3)
        for f in FACTIONS:
            self.assertIn(f"GetTitleByKey('d_{f}')", win)
            self.assertIn(f"aov_make_amends_{f}_sgui", win)

    def test_bar_markers_at_thresholds(self):
        gui = read("gui/aov_artificer_factions.gui")
        self.assertIn("type aov_influence_bar", gui)
        self.assertEqual(gui.count("widget_level_marker = {"), 4)
        for x in ("15%", "30%", "60%", "85%"):
            self.assertIn(x, gui)


class ReviewFixTests(unittest.TestCase):
    """Findings of the final branch review."""

    def eff(self, name):
        return block(read("common/scripted_effects/aov_artificer_election_effects.txt"), name)

    def test_ai_vote_uses_the_voter_not_root(self):
        b = self.eff("aov_election_ai_vote")
        self.assertIn("save_scope_as = aov_voter", b)
        self.assertIn("is_courtier_of = scope:aov_voter", b)
        self.assertNotIn("is_courtier_of = root", b)
        self.assertIn("clear_saved_scope = aov_ai_choice", b)

    def test_heir_inherits_the_paid_amount(self):
        b = block(read("common/scripted_effects/aov_artificery_research_effects.txt"), "aov_artificery_inherit")
        self.assertIn("set_variable = { name = aov_research_paid value = scope:aov_predecessor.var:aov_research_paid }", b)

    def test_yearly_counts_overdue_elections_and_dying_leader_is_not_the_counter(self):
        yearly = block(read("common/on_action/aov_artificer_faction_on_actions.txt"), "aov_artificer_factions_yearly")
        self.assertIn("aov_elections_resolve_overdue = yes", yearly)
        overdue = self.eff("aov_elections_resolve_overdue")
        for f in FACTIONS:
            self.assertIn(f"aov_election_resolve = {{ FACTION = {f} }}", overdue)
        self.assertRegex(self.eff("aov_election_open"),
                         r"ordered_ruler = \{\s*limit = \{\s*aov_artificer_nation_trigger = yes\s*NOT = \{ has_character_flag = aov_dying_faction_leader \}")

    def test_grant_keeps_the_winner_under_their_liege(self):
        b = self.eff("aov_faction_grant_title")
        self.assertIn("save_scope_as = aov_winner_liege", b)
        self.assertIn("change_liege = { liege = scope:aov_winner_liege change = scope:aov_liege_change }", b)

    def test_title_given_away_reopens_the_election(self):
        text = read("common/on_action/aov_artificer_faction_on_actions.txt")
        self.assertIn("on_title_gain = {\n\ton_actions = { aov_artificer_factions_on_title_gain }", text)
        b = block(text, "aov_artificer_factions_on_title_gain")
        self.assertIn("var:aov_elected_holder = root", b)
        self.assertIn("destroy_title = scope:title", b)
        self.assertIn("set_variable = { name = aov_elected_holder value = $WINNER$ }", self.eff("aov_faction_grant_title"))

    def test_one_gnome_cannot_win_two_titles(self):
        b = self.eff("aov_election_open")
        self.assertIn("aov_court_pool_$FACTION$", b)
        self.assertIn("aov_world_pool_$FACTION$", b)
        grant = b.split("NOT = { any_ruler = { aov_artificer_nation_trigger = yes } }")[1]
        self.assertIn("limit = { aov_faction_candidate_trigger = yes }", grant.split("aov_faction_grant_title")[0])
        # User rule: a single gnome holds at most one faction title, whatever path gives it
        g = self.eff("aov_faction_grant_title")
        self.assertIn("NOT = { any_held_title = { aov_is_artificer_faction_title = yes } }", g)
        # Reopened through a hidden event: aov_election_open itself calls the grant, and scripted effects cannot recurse
        self.assertIn("trigger_event = { id = aov_artificer_factions.4 days = 1 }", g)
        self.assertNotIn("aov_election_open = { FACTION = $FACTION$ }", g)

    def test_stale_votes_cleared_and_late_votes_refused(self):
        b = self.eff("aov_election_open")
        self.assertRegex(b, r"every_in_global_list = \{\s*variable = aov_candidates_\$FACTION\$\s*remove_variable = aov_votes_\$FACTION\$")
        ev = block(read("events/aov_artificer_faction_events.txt"), "aov_artificer_factions.1")
        self.assertEqual(ev.count("aov_election_is_open_trigger = yes"), 3)

    def test_card_rows_fit_the_factions_tab(self):
        # Width inside a card: main tab 655 - Window_Margins 80 - body margin 20 - Scrollbox_Margins 35
        # - content margin 12 - card margin 28 = 480. Wider rows get clipped (no horizontal scrolling).
        budget = 480
        gui = read("gui/aov_artificer_factions.gui")
        card = gui.split("type aov_faction_card = vbox {")[1]
        header, footer = card.split("aov_influence_bar = {")
        text_width = max(int(w) for w in re.findall(r"max_width = (\d+)", header))
        self.assertLessEqual(72 + 10 + 110 + 10 + text_width, budget)      # coat of arms, portrait, text column
        status = int(re.search(r"max_width = (\d+)", footer).group(1))
        button = int(re.search(r"size = \{ (\d+) \d+ \}", footer).group(1))
        self.assertLessEqual(status + 8 + button, budget)                 # status text, Make Amends

    def test_portrait_slot_fits_portrait_head(self):
        gui = read("gui/aov_artificer_factions.gui")
        self.assertIn("size = { 110 120 }", gui)


if __name__ == "__main__":
    unittest.main()

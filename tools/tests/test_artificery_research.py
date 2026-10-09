"""Static checks on the hand-written research files.

    python -I -m unittest discover -s tools/tests -v
"""

import re
import unittest
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent.parent


def read(rel):
    return (MOD / rel).read_text(encoding="utf-8-sig")


def block(text, name):
    m = re.search(rf"^{name} = \{{\n(.*?)\n^\}}", text, re.M | re.S)
    assert m, name
    return m.group(1)


class ResearchTests(unittest.TestCase):
    def test_complete_research_refunds_when_nothing_discovered(self):
        b = block(read("common/scripted_effects/aov_artificery_research_effects.txt"), "aov_artificery_complete_research")
        self.assertIn("remove_variable = aov_last_discovered", b)
        self.assertRegex(b, r"else = \{\s*add_gold = var:aov_research_paid\s*trigger_event = aov_artificery\.2")

    def test_sponsor_durations(self):
        text = read("common/scripted_effects/aov_artificery_research_effects.txt")
        # Durations are per faction and influence: common/script_values/aov_artificer_faction_values.txt
        for f in ("brillites", "mechanists", "technomancers"):
            self.assertIn(f"aov_artificery_start_research_common = {{ SPONSOR = {f} }}", text)
        self.assertIn("value = aov_research_quarters_$SPONSOR$", text)

    def test_technomancer_category_sgui_rolls_only_once(self):
        text = read("common/scripted_guis/aov_artificery_research_sgui.txt")
        for c in ("economic", "military", "society"):
            b = block(text, f"aov_research_technomancers_{c}_sgui")
            self.assertIn(f"NOT = {{ has_variable = aov_tech_offers_rolled_{c} }}", b)
            self.assertIn(f"aov_inventions_roll_offers_{c} = yes", b)

    def test_cooldowns_cover_five_slots(self):
        b = block(read("common/scripted_effects/aov_artificery_research_effects.txt"), "aov_artificery_start_slot_cooldown")
        for n in range(1, 6):
            self.assertIn(f"set_variable = {{ name = aov_slot_cd_{n} years = 1 }}", b)

    def test_on_actions_hook_quarterly_and_death(self):
        text = read("common/on_action/aov_inventions_on_actions.txt")
        self.assertIn("quarterly_playable_pulse = {\n\ton_actions = { aov_artificery_quarterly }", text)
        self.assertIn("on_death = {\n\ton_actions = { aov_artificery_on_death }", text)

    def test_maa_gated_on_active_invention(self):
        text = read("common/men_at_arms_types/aov_invention_maa_types.txt")
        for maa, inv in (("aov_prototype_tanks", "prototype_tanks"), ("aov_war_golems", "war_golems"),
                         ("aov_damestear_megacannon", "damestear_reactor_megacannon")):
            b = block(text, maa)
            self.assertIn(f"aov_invention_{inv}_active = yes", b)

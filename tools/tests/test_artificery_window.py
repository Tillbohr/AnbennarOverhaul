"""Static checks on gui/aov_window_artificery.gui.

    python -I -m unittest discover -s tools/tests -v
"""

import unittest
from pathlib import Path

WINDOW = Path(__file__).resolve().parent.parent.parent / "gui" / "aov_window_artificery.gui"


class ArtificeryWindowTests(unittest.TestCase):
    def test_window_draws_its_own_background(self):
        # Vanilla main-tab windows get their background from sidebar_background_right in
        # hud_sidebars.gui, which only shows while IsRightWindowOpen; this window is not a game view
        text = WINDOW.read_text(encoding="utf-8-sig")
        self.assertIn("using = Window_Background", text)

    def test_inventions_tab_has_tier_tabs_and_tier_grids(self):
        text = WINDOW.read_text(encoding="utf-8-sig")
        self.assertNotIn("AOV_ARTIFICERY_INVENTIONS_PLACEHOLDER", text)
        self.assertNotIn("aov_filter_hide_", text)
        for t in (1, 2, 3):
            self.assertIn(f"aov_inventions_tier_{t} = {{", text)
            self.assertIn(f'text = "AOV_INVENTIONS_TAB_TIER_{t}"', text)
        for t in (2, 3):
            self.assertIn(f"GetVariableSystem.Set( 'aov_inventions_tier', '{t}' )", text)
            self.assertIn(f"aov_inventions_tier_{t}_unlocked_sgui", text)

    def test_research_popup_is_an_event_style_window(self):
        root = WINDOW.parent
        reg = (root / "scripted_widgets" / "aov_scripted_widgets.txt").read_text(encoding="utf-8-sig")
        self.assertIn("gui/aov_window_artificery_research.gui = aov_artificery_research_window", reg)
        popup = (root / "aov_window_artificery_research.gui").read_text(encoding="utf-8-sig")
        self.assertIn("gfx/interface/illustrations/event_scenes/", popup)
        self.assertIn("gfx/interface/icons/event_types/type_inspiration.dds", popup)
        self.assertEqual(popup.count("aov_research_leader = {"), 3)
        for f in ("brillites", "mechanists", "technomancers"):
            self.assertIn(f'text = "AOV_RESEARCH_LEADER_{f.upper()}"', popup)
        for c in ("economic", "military", "society"):
            self.assertIn(f"aov_inventions_offers_{c} = {{}}", popup)
            self.assertIn(f"aov_research_mechanists_{c}_sgui", popup)
            self.assertIn(f"aov_research_technomancers_{c}_sgui", popup)
        self.assertIn("aov_research_brillites_sgui", popup)
        self.assertEqual(popup.count("{"), popup.count("}"))

    def test_research_popup_uses_title_holders_and_faction_costs(self):
        popup = (WINDOW.parent / "aov_window_artificery_research.gui").read_text(encoding="utf-8-sig")
        self.assertNotIn('datacontext = "[GetPlayer]"', popup)
        for f in ("brillites", "mechanists", "technomancers"):
            self.assertIn(f"GetTitleByKey('d_{f}').GetHolder", popup)
            self.assertIn(f"AOV_RESEARCH_COST_{f.upper()}", popup)
        gen = (WINDOW.parent / "aov_inventions_generated.gui").read_text(encoding="utf-8-sig")
        self.assertIn("AOV_RESEARCH_COST_TECHNOMANCERS", gen)
        self.assertNotIn('"AOV_RESEARCH_COST"', gen)


if __name__ == "__main__":
    unittest.main()

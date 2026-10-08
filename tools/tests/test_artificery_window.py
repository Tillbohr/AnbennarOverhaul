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

    def test_inventions_tab_has_list_and_no_placeholder(self):
        text = WINDOW.read_text(encoding="utf-8-sig")
        self.assertIn("aov_inventions_list = {", text)
        self.assertNotIn("AOV_ARTIFICERY_INVENTIONS_PLACEHOLDER", text)
        for c in ("economic", "military", "society"):
            self.assertIn(f"GetVariableSystem.Toggle( 'aov_filter_hide_{c}' )", text)

    def test_research_popup_registered_and_offers_per_category(self):
        root = WINDOW.parent
        reg = (root / "scripted_widgets" / "aov_scripted_widgets.txt").read_text(encoding="utf-8-sig")
        self.assertIn("gui/aov_window_artificery_research.gui = aov_artificery_research_window", reg)
        popup = (root / "aov_window_artificery_research.gui").read_text(encoding="utf-8-sig")
        for c in ("economic", "military", "society"):
            self.assertIn(f"aov_inventions_offers_{c} = {{", popup)
            self.assertIn(f"aov_research_mechanists_{c}_sgui", popup)
            self.assertIn(f"aov_research_technomancers_{c}_sgui", popup)
        self.assertIn("aov_research_brillites_sgui", popup)


if __name__ == "__main__":
    unittest.main()

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


if __name__ == "__main__":
    unittest.main()

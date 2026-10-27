"""Tests for tools/build_hud_override.py.

    python -I -m unittest discover -s tools/tests -v
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_hud_override as bho  # noqa: E402

HUD = (
    "widget = {\n"
    "\tvbox = {\n"
    "\t\twidget_hud_main_tab = {\n"
    "\t\t\tname = \"tab_activities\"\n"
    "\t\t}\n"
    "\n"
    "\t\twidget_hud_main_tab = {\n"
    "\t\t\tname = \"tab_situation\"\n"
    "\t\t\tblockoverride \"maintab_button\"\n"
    "\t\t\t{\n"
    "\t\t\t\tonclick = \"[ToggleGameView( 'situations' )]\"\n"
    "\t\t\t}\n"
    "\t\t}\n"
    "\n"
    "\t\twidget_hud_main_tab = {\n"
    "\t\t\tname = \"royal_court_button_tutorial_uses_this\"\n"
    "\t\t}\n"
    "\t}\n"
    "\thbox = {\n"
    "\t\tname = \"tutorial_highlight_resources_bar\"\n"
    "\n"
    "\t\twidget = {\n"
    "\t\t\tname = \"gold\"\n"
    "\t\t\tsize = { 144 70 }\n"
    "\n"
    "\t\t\tbackground = {\n"
    "\t\t\t\ttexture = \"gfx/interface/skinned/resource_panel_start.dds\"\n"
    "\t\t\t}\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
)


class BraceDeltaTests(unittest.TestCase):
    def test_counts_braces(self):
        self.assertEqual(bho.brace_delta("a = { b = {"), 2)
        self.assertEqual(bho.brace_delta("}"), -1)

    def test_ignores_braces_in_strings_and_comments(self):
        self.assertEqual(bho.brace_delta('text = "{ not a brace }" # { nor }'), 0)
        self.assertEqual(bho.brace_delta('x = { # }'), 1)


class InsertTabTests(unittest.TestCase):
    def test_inserts_after_situation_tab(self):
        out = bho.insert_tab(HUD)
        sit_end = out.index('name = "tab_situation"')
        ours = out.index('name = "tab_aov_artificery"')
        court = out.index('name = "royal_court_button_tutorial_uses_this"')
        self.assertLess(sit_end, ours)
        self.assertLess(ours, court)

    def test_only_adds_the_marked_block(self):
        out = bho.insert_tab(HUD)
        lines = out.split("\n")
        begin = lines.index("\t\t" + bho.BEGIN)
        end = lines.index("\t\t" + bho.END)
        stripped = lines[:begin] + lines[end + 1:]
        # the block is inserted as: blank line, BEGIN ... END, directly after the closing brace
        self.assertEqual(lines[begin - 1], "")
        self.assertEqual("\n".join(stripped[:begin - 1] + stripped[begin:]), HUD)

    def test_block_uses_tab_indentation_of_siblings(self):
        out = bho.insert_tab(HUD)
        self.assertIn('\t\twidget_hud_main_tab = {\n\t\t\tname = "tab_aov_artificery"', out)

    def test_button_wiring(self):
        out = bho.insert_tab(HUD)
        self.assertIn("GetScriptedGui('aov_artificery_available').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )", out)
        self.assertIn("GetVariableSystem.Toggle( 'aov_artificery_window' )", out)
        self.assertIn("GetVariableSystem.Exists( 'aov_artificery_window' )", out)
        self.assertIn('tooltip = "AOV_ARTIFICERY_BUTTON"', out)
        self.assertIn(bho.TEXTURE, out)

    def test_button_closes_open_main_tab_before_toggling(self):
        # Toggling then closing a vanilla game view closes whichever main tab is open (PoD's pattern),
        # so the Artificery window is not left hidden behind Not( IsRightWindowOpen )
        out = bho.insert_tab(HUD)
        toggle_view = out.index("onclick = \"[ToggleGameView( 'decisions' )]\"", out.index("tab_aov_artificery"))
        close_view = out.index("onclick = \"[CloseGameView( 'decisions' )]\"", toggle_view)
        toggle_var = out.index("GetVariableSystem.Toggle( 'aov_artificery_window' )", close_view)
        self.assertLess(toggle_view, close_view)
        self.assertLess(close_view, toggle_var)

    def test_icon_is_the_shipped_eu4_artificery_icon(self):
        # Frame 1 (tier 1 emblem) of EU4 Anbennar's artifice_tier_emblems_strip.dds, shipped in the submod
        self.assertEqual(bho.TEXTURE, "gfx/interface/skinned/hud_maintab/aov_maintab_artificery.dds")
        self.assertTrue((bho.SUBMOD / bho.TEXTURE).is_file())

    def test_magic_tab_after_artificery(self):
        out = bho.insert_tab(HUD)
        art, magic = out.index('name = "tab_aov_artificery"'), out.index('name = "tab_aov_magic"')
        self.assertLess(art, magic)
        self.assertLess(magic, out.index(bho.END))
        self.assertIn("GetScriptedGui('aov_magic_available').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )", out)
        self.assertIn("GetVariableSystem.Toggle( 'aov_magic_window' )", out)
        self.assertIn('tooltip = "AOV_MAGIC_BUTTON"', out)
        self.assertEqual(bho.MAGIC_TEXTURE, "gfx/interface/skinned/hud_maintab/aov_maintab_magic.dds")
        self.assertTrue((bho.SUBMOD / bho.MAGIC_TEXTURE).is_file())

    def test_tabs_close_each_other(self):
        out = bho.insert_tab(HUD)
        art = out[out.index('name = "tab_aov_artificery"'):out.index('name = "tab_aov_magic"')]
        magic = out[out.index('name = "tab_aov_magic"'):out.index(bho.END)]
        self.assertIn("GetVariableSystem.Clear( 'aov_magic_window' )", art)
        self.assertIn("GetVariableSystem.Clear( 'aov_artificery_window' )", magic)

    def test_block_braces_balance(self):
        self.assertEqual(sum(bho.brace_delta(l) for l in bho.insert_tab(HUD).split("\n")), 0)

    def test_missing_anchor(self):
        with self.assertRaises(bho.GeneratorError):
            bho.insert_tab(HUD.replace("tab_situation", "tab_renamed"))

    def test_refuses_when_already_present(self):
        with self.assertRaises(bho.GeneratorError):
            bho.insert_tab(bho.insert_tab(HUD))

    def test_unbalanced_braces(self):
        # file ends before the Situations widget closes
        broken = HUD[:HUD.index("\t\t\t}\n\t\t}\n\n\t\twidget_hud_main_tab = {\n\t\t\tname = \"royal")]
        with self.assertRaises(bho.GeneratorError):
            bho.insert_tab(broken)


class InsertManaTests(unittest.TestCase):
    """A mage's mana sits left of gold in the resource bar, as in Godherja; gold then loses the bar's end cap."""

    def test_mana_widget_before_gold(self):
        out = bho.insert_mana(HUD)
        self.assertLess(out.index('name = "aov_mana"'), out.index('name = "gold"'))
        # Indented like its sibling
        self.assertIn('\t\twidget = {\n\t\t\tname = "aov_mana"', out)

    def test_mana_shows_for_mages(self):
        out = bho.insert_mana(HUD)
        mana = out[out.index(bho.MANA_BEGIN):out.index(bho.MANA_END)]
        self.assertIn(f'visible = "{bho.MAGE}"', mana)
        self.assertIn("GetScriptedGui('aov_magic_available')", bho.MAGE)
        self.assertIn("ScriptValue( 'aov_mana' )", mana)
        self.assertIn("ScriptValue( 'aov_mana_refill_month' )", mana)
        self.assertIn('tooltip = "AOV_HUD_MANA_TT"', mana)
        self.assertIn("gfx/interface/skinned/resource_panel_start.dds", mana)
        self.assertIn(bho.MANA_ICON, mana)
        self.assertTrue((bho.SUBMOD / bho.MANA_ICON).is_file())

    def test_gold_keeps_end_cap_only_without_mana(self):
        out = bho.insert_mana(HUD)
        gold = out[out.index('name = "gold"'):]
        start = gold.index("resource_panel_start.dds")
        self.assertIn(f'visible = "[Not( {bho.MAGE[1:-1]} )]"', gold[start:start + 300])
        piece = gold.index("resource_panel_piece.dds")
        self.assertIn(f'visible = "{bho.MAGE}"', gold[piece:piece + 300])

    def test_braces_balance(self):
        self.assertEqual(sum(bho.brace_delta(l) for l in bho.insert_mana(HUD).split("\n")), 0)

    def test_missing_gold(self):
        with self.assertRaises(bho.GeneratorError):
            bho.insert_mana(HUD.replace('name = "gold"', 'name = "renamed"'))

    def test_refuses_when_already_present(self):
        with self.assertRaises(bho.GeneratorError):
            bho.insert_mana(bho.insert_mana(HUD))

    def test_build_adds_tabs_and_mana(self):
        out = bho.build(HUD.encode("utf-8")).decode("utf-8")
        self.assertIn('name = "tab_aov_magic"', out)
        self.assertIn('name = "aov_mana"', out)


class BuildTests(unittest.TestCase):
    def test_build_preserves_bom_and_crlf(self):
        raw = b"\xef\xbb\xbf" + HUD.replace("\n", "\r\n").encode("utf-8")
        out = bho.build(raw)
        self.assertTrue(out.startswith(b"\xef\xbb\xbf# Anbennar Overhaul: generated"))
        body = out[3:].decode("utf-8")
        self.assertNotIn("\n", body.replace("\r\n", ""))

    def test_build_lf_without_bom(self):
        out = bho.build(HUD.encode("utf-8"))
        self.assertFalse(out.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r\n", out)
        self.assertTrue(out.decode("utf-8").endswith("\t\t}\n\t}\n}\n"))


class FindSourceTests(unittest.TestCase):
    def test_prefers_anbennar(self):
        with tempfile.TemporaryDirectory() as tmp:
            anb, game = Path(tmp, "anb"), Path(tmp, "game")
            for root in (anb, game):
                (root / "gui").mkdir(parents=True)
                (root / "gui" / "hud.gui").write_text("x")
            self.assertEqual(bho.find_source(anb, game), anb / "gui" / "hud.gui")

    def test_falls_back_to_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            anb, game = Path(tmp, "anb"), Path(tmp, "game")
            (game / "gui").mkdir(parents=True)
            (game / "gui" / "hud.gui").write_text("x")
            self.assertEqual(bho.find_source(anb, game), game / "gui" / "hud.gui")

    def test_neither_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(bho.GeneratorError):
                bho.find_source(Path(tmp, "a"), Path(tmp, "b"))


if __name__ == "__main__":
    unittest.main()

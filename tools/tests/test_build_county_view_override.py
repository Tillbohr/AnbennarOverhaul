import difflib
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_county_view_override as cvo  # noqa: E402
import build_monuments as bm  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402

FIXTURE = """window = {
\twidget = {
\t\tbackground = {
\t\t\tvisible = "[HoldingView.HasHolding]"
\t\t\ttexture = "[HoldingView.GetHolding.GetIllustration]"
\t\t\talpha = 0.8

\t\t\tmodify_texture = {
\t\t\t\ttexture = "gfx/mask.dds"
\t\t\t\tblend_mode = alphamultiply
\t\t\t}
\t\t}

\t\tbackground = {
\t\t\ttexture = "[HoldingView.GetProvince.GetTerrain.GetIllustration]"
\t\t}

\t\t### TOP LEFT
\t\thbox = {
\t\t\tlayoutpolicy_horizontal = expanding

\t\t\tvbox = {
\t\t\t\tlayoutpolicy_horizontal = expanding
\t\t\t\ttext_single = { text = "NAME" }
\t\t\t}

\t\t\t### HOLDING STATS
\t\t\tvbox = {
\t\t\t\tminimumsize = { 171 0 }
\t\t\t}
\t\t}

\t\t### CONSTRUCT NEW HOLDING & CONSTRUCTING PROGRESS
\t\tvbox = {
\t\t\thbox = {
\t\t\t\tvisible = "[HoldingView.IsBeingConstructed]"
\t\t\t\tmargin_bottom = 30

\t\t\t\tvbox = {
\t\t\t\t\tname = "constructing_holding"
\t\t\t\t\tprogressbar_standard = { value = "[HoldingView.GetConstructionProgressForSlot('(int32)0')]" }
\t\t\t\t}
\t\t\t}
\t\t}
\t}
}
"""


def name_vbox(out):
    """The text of the first vbox inside the TOP LEFT hbox (the area left of the holding stats; no paintings)."""
    start = out.index("\t\t\tvbox = {")
    return out[start:out.index("\n\t\t\t}\n", start)]


class CountyViewTests(unittest.TestCase):
    def test_paintings_cover_the_holding_panel(self):
        """The painting covers the holding panel like the vanilla holding art: inline backgrounds right after the
        vanilla illustration (drawn above the panel's dark background; never a `using` template, whose backgrounds
        draw beneath inline ones), not only the area left of the stats. Top-aligned (fittype start), so the top of
        the painting is never trimmed."""
        out = cvo.insert(FIXTURE)
        self.assertNotIn("using = AovMonumentPaintings", out)
        painted = len([m for m in bm.all_monuments() if m["art"]])
        self.assertEqual(out.count("aov_monuments/"), painted)
        self.assertEqual(name_vbox(out).count("aov_monuments/"), 0)
        self.assertLess(out.index("HoldingView.GetHolding.GetIllustration"), out.index("aov_monuments/"))
        self.assertLess(out.rindex("aov_monuments/"), out.index("GetTerrain"))
        self.assertEqual(out.count("fittype = start"),
                         painted + len([a for a in bm.EXTRA_ART if a["style"] == "painting"]))
        self.assertEqual(out.count("{"), out.count("}"))

    def test_no_texture_from_custom_loc(self):
        # a texture path taken from localized text is not loaded by CK3 (the first version showed vanilla art)
        self.assertIsNone(re.search(r'texture = "\[[^"]*Custom', cvo.insert(FIXTURE)))

    def test_vanilla_illustration_hidden_under_a_monument(self):
        # the vanilla holding art is switched off in provinces with a monument painting, so the two never blend
        out = cvo.insert(FIXTURE)
        self.assertNotIn(cvo.VANILLA_VISIBLE, out)
        block = out[out.index("background = {"):out.index("GetHolding.GetIllustration")]
        self.assertIn(f'visible = "{cvo.HIDDEN_UNDER_MONUMENT}"', block)

    def test_errors_without_vanilla_visible_line(self):
        with self.assertRaises(GeneratorError):
            cvo.insert(FIXTURE.replace(f'visible = "{cvo.VANILLA_VISIBLE}"', 'visible = "[Something.Else]"'))

    def test_errors_without_anchor(self):
        with self.assertRaises(GeneratorError):
            cvo.insert(FIXTURE.replace("HoldingView.GetHolding.GetIllustration", "x"))

    def test_dig_progress_bar_after_holding_construction(self):
        """A running dig shows a large progress bar where vanilla shows a barony's construction (a hold is never
        under construction), bound to the hold's dig variables."""
        out = cvo.insert(FIXTURE)
        self.assertEqual(out.count(cvo.MARKER + ": hold dig progress"), 1)
        self.assertLess(out.index('name = "constructing_holding"'), out.index('name = "aov_hold_dig_progress"'))
        dig = out[out.index(cvo.MARKER + ": hold dig progress"):]
        self.assertIn('''visible = "[HoldingView.GetProvince.MakeScope.Var('aov_dig_target_level').IsSet]"''', dig)
        self.assertIn("ScriptValue('aov_dig_percent')", dig)
        self.assertIn('text = "AOV_HOLD_DIG_PROGRESS"', dig)
        self.assertIn('tooltip = "AOV_HOLD_DIG_PROGRESS_TT"', dig)
        # a sibling of vanilla's construction hbox, in the same vbox
        before = out[:out.index(cvo.MARKER + ": hold dig progress")]
        self.assertEqual(before.rstrip().split("\n")[-1].strip(), "}")
        self.assertEqual(out.count("{"), out.count("}"))

    def test_errors_without_construction_anchor(self):
        with self.assertRaises(GeneratorError):
            cvo.insert(FIXTURE.replace('name = "constructing_holding"', 'name = "x"'))

    def test_dig_loc_and_values_exist(self):
        """The bar's loc keys and the script values they read are defined, and the loc's tick matches the data."""
        sys.path.insert(0, str(cvo.SUBMOD / "tools" / "data"))
        import holds  # noqa: E402
        loc = (cvo.SUBMOD / "localization/english/aov_hold_view_l_english.yml").read_text(encoding="utf-8-sig")
        self.assertIn(" AOV_HOLD_DIG_PROGRESS:0 ", loc)
        self.assertIn(" AOV_HOLD_DIG_PROGRESS_TT:0 ", loc)
        self.assertIn(f"{holds.TICK_MONTHS} months each quarter", loc)
        values = (cvo.SUBMOD / "common/script_values/aov_hold_view_values.txt").read_text(encoding="utf-8-sig")
        self.assertRegex(values, r"(?m)^aov_dig_percent = \{")
        self.assertRegex(values, r"(?m)^aov_dig_years_left = \{")
        self.assertIn("ScriptValue('aov_dig_years_left')", loc)

    def test_errors_if_already_generated(self):
        with self.assertRaises(GeneratorError):
            cvo.insert(cvo.insert(FIXTURE))

    def test_build_adds_header_and_keeps_bom(self):
        out = cvo.build(b"\xef\xbb\xbf" + FIXTURE.encode()).decode("utf-8-sig")
        self.assertTrue(out.startswith("# Anbennar Overhaul: generated by tools/build_county_view_override.py"))


class GeneratedFileTests(unittest.TestCase):
    @unittest.skipUnless((cvo.DEFAULT_ANBENNAR / cvo.REL_PATH).is_file() and (cvo.SUBMOD / cvo.REL_PATH).is_file(),
                         "needs Anbennar and the generated file")
    def test_generated_differs_from_source_only_by_header_and_block(self):
        src = (cvo.DEFAULT_ANBENNAR / cvo.REL_PATH).read_bytes().decode("utf-8-sig").replace("\r\n", "\n")
        out = (cvo.SUBMOD / cvo.REL_PATH).read_bytes().decode("utf-8-sig").replace("\r\n", "\n")
        lines = out.split("\n")
        self.assertTrue(lines[0].startswith(cvo.MARKER + ": generated by tools/build_county_view_override.py"))
        self.assertTrue(lines[1].startswith(cvo.MARKER + ": do not edit"))
        start = next(i for i, l in enumerate(lines) if l.strip() == cvo.MARKER + ": monument painting")
        block = cvo.block()  # also fails when the monument data changed and the county view was not rebuilt
        end = start + len(block)
        self.assertEqual([l.strip() for l in lines[start:end]], [l.strip() for l in block])
        dig_start = next(i for i, l in enumerate(lines) if l.strip() == cvo.MARKER + ": hold dig progress")
        dig_end = dig_start + len(cvo.dig_block())
        self.assertEqual([l.strip() for l in lines[dig_start:dig_end]], [l.strip() for l in cvo.dig_block()])
        self.assertLess(end, dig_start)
        # Drop the header, the blank lines before the blocks and the blocks: what is left is Anbennar's file, byte for
        # byte. The vanilla holding illustration's visible line is the one other change.
        self.assertEqual(lines[start - 1], "")
        self.assertEqual(lines[dig_start - 1], "")
        rest = "\n".join(lines[2:start - 1] + lines[end:dig_start - 1] + lines[dig_end:])
        self.assertEqual(rest.count(cvo.HIDDEN_UNDER_MONUMENT), 1)
        self.assertEqual(rest.replace(cvo.HIDDEN_UNDER_MONUMENT, cvo.VANILLA_VISIBLE), src)
        self.assertEqual(out.count(cvo.MARKER + ": monument painting"), 1)
        self.assertEqual(out.count(cvo.MARKER + ": hold dig progress"), 1)

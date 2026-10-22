"""Tests for tools/build_knight_icons.py (race knight badges).

    python -I -m unittest discover -s tools/tests -p "test_build_knight_icons*.py"
"""

import re
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_knight_icons as bki  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
from data.knight_icons import GUI_TARGETS, ICON_DIR, ICON_SIZE, RACES, SOURCE_SIZE, VANILLA_ICON  # noqa: E402

REAL = bki.Roots.default()
HAVE_REAL = REAL.anbennar.is_dir() and REAL.game.is_dir()
BADGE = 'texture = "gfx/interface/icons/icon_knight_small.dds"'


class DataTests(unittest.TestCase):
    def test_the_six_races_with_unique_keys(self):
        keys = [row[0] for row in RACES]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(set(keys), {"moon_elven", "sun_elven", "wood_elven", "dwarven", "gnomish", "kobold"})

    def test_masks_stay_inside_the_icon(self):
        for key, _name, frame, _group, _cond, mask in RACES:
            self.assertTrue(1 <= frame <= 72, key)
            for y, last in mask.items():
                self.assertTrue(0 <= y < SOURCE_SIZE and 0 <= last < SOURCE_SIZE, (key, y))


class CutTests(unittest.TestCase):
    def test_cut_icon_clears_masked_pixels_only(self):
        width = SOURCE_SIZE * 2
        strip = bytes([10, 20, 30, 255]) * (width * SOURCE_SIZE)
        px = bki.cut_icon(strip, width, 2, {0: 3, 5: 0})
        alpha = lambda x, y: px[(y * SOURCE_SIZE + x) * 4 + 3]  # noqa: E731
        self.assertEqual([alpha(x, 0) for x in range(5)], [0, 0, 0, 0, 255])
        self.assertEqual([alpha(0, 5), alpha(1, 5), alpha(0, 6)], [0, 255, 255])

    def test_masked_area_stays_fully_transparent_after_resizing(self):
        px = bytearray(bytes([200, 200, 200, 255]) * (SOURCE_SIZE * SOURCE_SIZE))
        mask = {y: 19 for y in range(SOURCE_SIZE)}  # left half cleared
        for y, last in mask.items():
            for x in range(last + 1):
                px[(y * SOURCE_SIZE + x) * 4 + 3] = 0
        data = bki.icon_dds(bytes(px), mask)
        alphas = [data[128 + (y * ICON_SIZE + x) * 4 + 3] for y in range(ICON_SIZE) for x in range(ICON_SIZE)
                  if (x + 0.5) * SOURCE_SIZE / ICON_SIZE < 19.5]
        self.assertEqual(max(alphas), 0)

    def test_icon_dds_has_no_mip_chain_like_the_vanilla_badge(self):
        # the first build wrote a 6-level mip chain on the 50 px icon and every race badge showed blank in game;
        # vanilla's icon_knight_small.dds is one uncompressed A8R8G8B8 level
        data = bki.icon_dds(bytes([0, 0, 0, 255]) * (SOURCE_SIZE * SOURCE_SIZE))
        self.assertLessEqual(struct.unpack("<I", data[28:32])[0], 1)  # mip map count
        self.assertEqual(struct.unpack("<I", data[108:112])[0], 0x1000)  # caps: texture only
        self.assertEqual(len(data), 128 + ICON_SIZE * ICON_SIZE * 4)

    def test_icon_dds_is_icon_size(self):
        px = bytes([0, 0, 0, 255]) * (SOURCE_SIZE * SOURCE_SIZE)
        data = bki.icon_dds(px)
        self.assertEqual(struct.unpack("<II", data[12:20]), (ICON_SIZE, ICON_SIZE))


class CommittedIconTests(unittest.TestCase):
    def test_every_race_has_its_icon(self):
        for key, *_ in RACES:
            path = bki.SUBMOD / ICON_DIR / f"{key}.dds"
            self.assertTrue(path.is_file(), f"missing {path}: run build_knight_icons.py --import {key}")
            data = path.read_bytes()
            self.assertEqual(struct.unpack("<II", data[12:20]), (ICON_SIZE, ICON_SIZE), key)
            # the gear's left edge (4, 11 in the 38 px source) is masked in every race and transparent in the icon
            mask = next(row[5] for row in RACES if row[0] == key)
            self.assertGreaterEqual(mask.get(11, -1), 4, key)
            gx, gy = int(4 * ICON_SIZE / SOURCE_SIZE), int(11 * ICON_SIZE / SOURCE_SIZE)
            self.assertEqual(data[128 + (gy * ICON_SIZE + gx) * 4 + 3], 0, key)


class ScriptTests(unittest.TestCase):
    def test_custom_loc_lists_races_in_order_then_vanilla(self):
        text = bki.custom_loc_file()
        found = re.findall(r"aov_knight_icon_ruler_trigger = \{ TRIGGER = (\w+) VALUE = (\w+) \} \} "
                           r"localization_key = aov_knight_badge_(\w+) \}", text)
        self.assertEqual(found, [(cond[0], cond[1], key) for key, _n, _f, _g, cond, _m in RACES])
        self.assertRegex(text, r"text = \{ localization_key = aov_knight_badge_default \}\n\}\n$")

    def test_ruler_trigger_uses_self_for_rulers_else_court_owner(self):
        text = " ".join(bki.triggers_file().split())
        self.assertIn("trigger_if = { limit = { is_ruler = yes } culture = { $TRIGGER$ = $VALUE$ } }", text)
        self.assertIn("trigger_else_if = { limit = { exists = court_owner } court_owner.culture = { $TRIGGER$ = $VALUE$ } }",
                      text)

    def test_loc_gives_each_badge_its_innovation(self):
        # a texture cannot take a loc string as a path, so the custom loc names a hidden innovation holding the icon
        loc = bki.loc_file().decode("utf-8-sig")
        for key in [row[0] for row in RACES] + ["default"]:
            self.assertIn(f' aov_knight_badge_{key}:0 "aov_knight_icon_{key}"', loc)

    def test_hidden_innovations_hold_the_icons(self):
        found = re.findall(r"^(\w+) = \{(.*?)^\}", bki.innovations_file(), re.M | re.S)
        blocks = {key: " ".join(body.split()) for key, body in found}
        paths = {f"aov_knight_icon_{row[0]}": f"{ICON_DIR}/{row[0]}.dds" for row in RACES}
        paths["aov_knight_icon_default"] = VANILLA_ICON
        self.assertEqual(set(blocks), set(paths))
        for key, path in paths.items():
            self.assertIn(f'icon = "{path}"', blocks[key])
            self.assertIn("potential = { always = no }", blocks[key])


class GuiTests(unittest.TestCase):
    def test_badges_replaced_with_the_race_badge(self):
        text = f"a\n\t\t{BADGE}\n\tb\n\t\t{BADGE}\n"
        out = bki.gui_override(text, "Army.GetOwner", 2)
        self.assertNotIn(BADGE, out)
        self.assertEqual(out.count('texture = "[GetCultureInnovationType(Army.GetOwner.Custom(\'aov_knight_icon\'))'
                                   '.GetIcon]" # Anbennar Overhaul'), 2)

    def test_unexpected_badge_count_stops(self):
        with self.assertRaises(GeneratorError):
            bki.gui_override(f"{BADGE}\n", "Character", 2)

    @unittest.skipUnless(HAVE_REAL, "needs Anbennar and the CK3 install")
    def test_overrides_are_base_files_plus_the_badge_only(self):
        files = bki.build_all(REAL)
        for rel, (scope, count) in GUI_TARGETS.items():
            base = bki.base_gui(REAL, rel)
            ours = files[rel].decode("utf-8-sig")
            self.assertEqual(ours.count(f"[GetCultureInnovationType({scope}.Custom('aov_knight_icon')).GetIcon]"),
                             count, rel)
            self.assertEqual(re.sub(r"texture = \"\[GetCultureInnovationType\([\w.]+\.Custom\('aov_knight_icon'\)\)"
                                    r"\.GetIcon\]\" # Anbennar Overhaul: [^\r\n]*",
                                    BADGE, ours), base, rel)


@unittest.skipUnless(HAVE_REAL, "needs Anbennar and the CK3 install")
class FreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = bki.build_all(REAL)

    def test_generated_files_match_the_mod(self):
        stale = [rel for rel, content in self.files.items()
                 if not (bki.SUBMOD / rel).is_file() or (bki.SUBMOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_knight_icons.py")


if __name__ == "__main__":
    unittest.main()

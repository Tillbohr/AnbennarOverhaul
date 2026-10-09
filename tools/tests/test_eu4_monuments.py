import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import eu4_monuments as em  # noqa: E402

TIER = """\
	tier_{n} = {{
		upgrade_time = {{ months = {months} }}
		cost_to_upgrade = {{ factor = {factor} }}
		province_modifiers = {{
			local_defensiveness = 0.1
			local_development_cost = -0.05
		}}
		area_modifier = {{ }}
		country_modifiers = {{
			prestige = 1
		}}
		on_upgraded = {{
			owner = {{ add_prestige = 5 }}
		}}
	}}
"""


def project(key, start, factor):
    tiers = "".join(TIER.format(n=n, months=120 * n, factor=factor if n == 1 else 0) for n in (0, 1, 2))
    return (f"{key} = {{\n\tstart = {start}\n\tdate = 01.01.01\n\tstarting_tier = 1\n\ttype = monument\n"
            f"\tcan_use_modifiers_trigger = {{ culture = elf }}\n{tiers}}}\n")


def write(path, text, enc="latin-1"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode(enc))


def fixture_roots():
    base = Path(tempfile.mkdtemp())
    roots = {}
    for name in ("anbennar", "cannorian", "dwarven"):
        roots[name] = base / name
        roots[name].mkdir()
    write(roots["anbennar"] / "common/great_projects/a.txt", project("proj", 67, 1000) + project("dup", 5, 1))
    write(roots["cannorian"] / "common/great_projects/c.txt", project("dup", 5, 2))
    return roots


def dds_dxt1_header(w, h):
    header = bytearray(128)
    header[0:4] = b"DDS "
    struct.pack_into("<I", header, 4, 124)
    struct.pack_into("<II", header, 12, h, w)
    struct.pack_into("<I", header, 76, 32)
    header[84:88] = b"DXT1"
    return bytes(header)


class Eu4MonumentsTests(unittest.TestCase):
    def test_parse_blocks_handles_nesting_and_comments(self):
        t = "a = { x = { y = 1 } } # c = {\nb = { }\n"
        self.assertEqual(set(em.parse_blocks(t)), {"a", "b"})

    def test_project_tiers(self):
        p = em.load_projects(fixture_roots())["proj"]
        self.assertEqual((p.start, p.year, p.starting_tier, p.type), (67, 1, 1, "monument"))
        self.assertEqual((p.tiers[0].cost_factor, p.tiers[0].months), (1000, 120))
        self.assertEqual(p.tiers[0].province, {"local_defensiveness": 0.1, "local_development_cost": -0.05})
        self.assertEqual(p.tiers[0].country, {"prestige": 1.0})
        self.assertIn("add_prestige = 5", p.tiers[0].on_upgraded)
        self.assertIn("culture = elf", p.gate)
        self.assertEqual(len(p.tiers), 3)
        self.assertEqual((p.tiers[1].cost_factor, p.tiers[1].months), (0, 240))
        self.assertEqual((p.tiers[2].cost_factor, p.tiers[2].months), (0, 0))

    def test_missing_tier_is_empty(self):
        p = em.load_projects(fixture_roots())["proj"]
        self.assertEqual(len(p.tiers), 3)
        roots = fixture_roots()
        write(roots["anbennar"] / "common/great_projects/b.txt", "bare = { start = 1 date = 01.01.01 type = canal }\n")
        b = em.load_projects(roots)["bare"]
        self.assertEqual((b.tiers[2].cost_factor, b.tiers[2].months, b.tiers[2].province), (0, 0, {}))
        self.assertEqual(b.gate, "")

    def test_submod_precedence(self):
        roots = fixture_roots()
        self.assertEqual(em.load_projects(roots)["dup"].tiers[0].cost_factor, 2)
        self.assertEqual(em.load_projects(roots)["dup"].source, "cannorian")

    def test_province_names_and_regions(self):
        a = fixture_roots()["anbennar"]
        write(a / "localisation/prov_names_l_english.yml", ' l_english:\n PROV67:0 "Lorentainé"\n', "utf-8-sig")
        write(a / "map/area.txt", "x_area = { 67 68 }\ny_area = { #4\n color = { 1 2 3 }\n 70 }\n")
        write(a / "map/region.txt", "x_region = {\n areas = {\n x_area\n }\n monsoon = { 00.01 }\n}\ny_region = { areas = { y_area } }\n")
        write(a / "map/superregion.txt", "s_superregion = {\n x_region\n}\nt_superregion = { y_region }\n")
        self.assertEqual(em.province_names(a), {67: "Lorentainé"})
        sup = em.province_superregions(a)
        self.assertEqual((sup[67], sup[68], sup[70]), ("s_superregion", "s_superregion", "t_superregion"))
        self.assertNotIn(1, sup)

    def test_loc_and_art_precedence(self):
        roots = fixture_roots()
        write(roots["anbennar"] / "localisation/x_l_english.yml", ' l_english:\n k:0 "A"\n only_a:0 "Z"\n', "utf-8-sig")
        write(roots["cannorian"] / "localisation/y_l_english.yml", ' l_english:\n k:0 "C"\n', "utf-8-sig")
        loc = em.eu4_loc(roots)
        self.assertEqual((loc["k"], loc["only_a"]), ("C", "Z"))
        for r in ("anbennar", "dwarven"):
            write(roots[r] / "gfx/interface/great_projects/great_project_p.dds", "x")
        self.assertEqual(em.art_file(roots, "p"), roots["dwarven"] / "gfx/interface/great_projects/great_project_p.dds")
        self.assertIsNone(em.art_file(roots, "none"))

    def test_decode_dxt1_block(self):
        data = dds_dxt1_header(4, 4) + bytes([0x00, 0xF8, 0x00, 0x00, 0, 0, 0, 0])
        w, h, px = em.decode_dxt1(data)
        self.assertEqual((w, h), (4, 4))
        self.assertEqual(px[:4], bytes([0, 0, 255, 255]))

    def test_decode_dxt1_transparent_mode(self):
        # color0 < color1 -> 3 colours; index 3 is transparent black. Row 0 indices: 3 in pixel 0.
        data = dds_dxt1_header(4, 4) + bytes([0x00, 0x00, 0x00, 0xF8, 0x03, 0, 0, 0])
        _, _, px = em.decode_dxt1(data)
        self.assertEqual(px[:4], bytes([0, 0, 0, 0]))

    @unittest.skipUnless(em.EU4_ROOTS["anbennar"].is_dir(), "needs EU4 Anbennar")
    def test_cannor_projects(self):
        projects = em.load_projects(em.EU4_ROOTS)
        sup = em.province_superregions(em.EU4_ROOTS["anbennar"])
        cannor = [p for p in projects.values() if sup.get(p.start) in em.CANNOR]
        # The brief expected 82; the data gives 77 by province. Palace of Unity has no start (commented out
        # as 8, Anbenncost) and is the spec's 78th. See task-1-report.md.
        self.assertEqual(len(cannor), 77)
        self.assertEqual([p.key for p in cannor if p.type == "canal"], ["marrhold_dwarovar_tunnel"])


if __name__ == "__main__":
    unittest.main()

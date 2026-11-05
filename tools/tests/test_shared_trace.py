"""Tests for the trace cache: a changed input must force a fresh trace.

    python -I -m unittest discover -s tools/tests -p test_shared_trace.py
"""

import pickle
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import shared_trace as st


def make_tree(root: Path) -> tuple:
    """A small (anbennar, eu4, tools) holding every kind of cache input."""
    anbennar, eu4, tools = root / "anbennar", root / "eu4", root / "tools"
    files = [anbennar / "map_data" / name for name in st.ANBENNAR_MAP]
    files += [anbennar / "common/landed_titles/titles.txt"]
    files += [eu4 / "map" / name for name in st.EU4_MAP]
    files += [eu4 / "localisation/a_l_english.yml", eu4 / "localisation/replace/b_l_english.yml"]
    for path in files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(path.name.encode())
    (tools / "data").mkdir(parents=True)
    (tools / "build_serpentreach.py").write_text("import serpentreach_layout\nfrom data import serpentreach\n")
    (tools / "serpentreach_layout.py").write_text("def later():\n    import terrain_fill\n")
    (tools / "terrain_fill.py").write_text("x = 1\n")
    (tools / "data/serpentreach.py").write_text("from data import segbandal\nfrom data import west_dwarovar\n")
    (tools / "data/segbandal.py").write_text("x = 1\n")
    (tools / "data/west_dwarovar.py").write_text("x = 1\n")
    (tools / "build_spells.py").write_text("x = 1\n")  # imported by nothing the trace uses
    return anbennar, eu4, tools


class TreeCase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        self.anbennar, self.eu4, self.tools = make_tree(self.root)
        self.folder = self.root / "cache"
        self.traces = 0

    def trace(self, anbennar, eu4):
        self.traces += 1
        return {"trace number": self.traces}

    def load(self, trace=None):
        return st.load_or_trace(self.anbennar, self.eu4, self.folder, trace or self.trace, self.tools)


class InvalidationTests(TreeCase):
    def test_same_inputs_reuse_the_trace(self):
        first = self.load()
        self.assertEqual(self.load(), first)
        self.assertEqual(self.traces, 1)

    def test_changing_any_input_forces_a_fresh_trace(self):
        inputs = st.data_files(self.anbennar, self.eu4) + st.code_files(self.tools)
        self.assertGreater(len(inputs), 15)
        self.load()
        for count, path in enumerate(inputs, 2):
            with self.subTest(path=path.relative_to(self.root).as_posix()):
                path.write_bytes(path.read_bytes() + b"\n# changed\n")
                self.assertEqual(self.load(), {"trace number": count})

    def test_every_named_input_is_hashed(self):
        names = {p.relative_to(self.root).as_posix() for p in
                 st.data_files(self.anbennar, self.eu4) + st.code_files(self.tools)}
        self.assertLessEqual({
            "anbennar/map_data/provinces.png", "anbennar/map_data/definition.csv", "anbennar/map_data/default.map",
            "anbennar/common/landed_titles/titles.txt", "eu4/map/provinces.bmp", "eu4/map/region.txt",
            "eu4/localisation/replace/b_l_english.yml", "tools/build_serpentreach.py", "tools/serpentreach_layout.py",
            "tools/terrain_fill.py", "tools/data/serpentreach.py", "tools/data/segbandal.py",
            "tools/data/west_dwarovar.py"}, names)

    def test_a_new_or_removed_file_forces_a_fresh_trace(self):
        self.load()
        new = self.eu4 / "localisation/c_l_english.yml"
        new.write_bytes(b"new")
        self.assertEqual(self.load(), {"trace number": 2})
        new.unlink()
        self.assertEqual(self.load(), {"trace number": 1}, "the older trace of these inputs is still good")
        (self.anbennar / "map_data/default.map").unlink()
        self.assertEqual(self.load(), {"trace number": 3})

    def test_a_tool_outside_the_trace_keeps_the_trace(self):
        self.load()
        (self.tools / "build_spells.py").write_text("x = 2\n")
        self.load()
        self.assertEqual(self.traces, 1)

    def test_another_python_forces_a_fresh_trace(self):
        self.load()
        with mock.patch.object(st.sys, "version", "another python"):
            self.assertEqual(self.load(), {"trace number": 2})

    def test_an_unreadable_cache_is_traced_again(self):
        self.load()
        for path in self.folder.glob("*.pickle"):
            path.write_bytes(b"\x80\x05 not a pickle")
        self.assertEqual(self.load(), {"trace number": 2})
        for path in self.folder.glob("*.pickle"):
            path.write_bytes(pickle.dumps({"a": 1})[:3])
        self.assertEqual(self.load(), {"trace number": 3})

    def test_an_input_changed_during_the_trace_is_not_stored(self):
        def changes_an_input(anbennar, eu4):
            (anbennar / "map_data/default.map").write_bytes(b"edited mid-trace")
            return self.trace(anbennar, eu4)
        self.load(changes_an_input)
        self.assertEqual(list(self.folder.glob("*.pickle")), [])

    def test_old_traces_are_dropped(self):
        for number in range(st.KEEP + 2):
            (self.eu4 / "map/region.txt").write_text(str(number))
            self.load()
        self.assertEqual(len(list(self.folder.glob("*.pickle"))), st.KEEP)
        self.assertEqual(list(self.folder.glob("*.tmp")), [])


class WatchTests(TreeCase):
    def test_reading_an_unhashed_file_stops_the_trace(self):
        secret = self.eu4 / "map/not_in_the_key.txt"
        secret.write_text("x")

        def reads_it(anbennar, eu4):
            secret.read_text()
            return {}
        with self.assertRaisesRegex(st.TraceInputError, "not_in_the_key"):
            self.load(reads_it)
        self.assertEqual(list(self.folder.glob("*.pickle")) if self.folder.exists() else [], [])

    def test_reading_the_inputs_is_allowed(self):
        def reads_inputs(anbennar, eu4):
            return (anbennar / "map_data/provinces.png").read_bytes()
        self.assertEqual(self.load(reads_inputs), b"provinces.png")


class SeedTests(unittest.TestCase):
    def test_map_graphics_asks_the_tracer_for_the_same_layouts(self):
        """seed_map_graphics stands in for build_map_graphics's own traces, which must match build_serpentreach's."""
        import build_map_graphics as bmg
        import build_serpentreach as bs
        import dwarven_mountains as dm
        import serpentreach_layout as sl

        def fake_layout(first_id, colour):
            county = sl.County(f"c_{first_id}", first_id, "Name", "area", "cavern", [first_id])
            province = sl.Province(first_id, colour, county.key, 0, [(first_id, 0)], (first_id, 0))
            return sl.Layout(9999, 1, [county], {first_id: province}, {(first_id, 0): first_id}, [], {}, [])
        fakes = [fake_layout(7000, (1, 1, 1)), fake_layout(7100, (2, 2, 2)), fake_layout(7200, (3, 3, 3))]
        calls = []

        def layout(*args, **options):
            calls.append((args, options))
            return fakes[len(calls) - 1]
        definition = "0;0;0;0;x;x\n"
        pm, water, impassable = dm.ProvinceMap(1, 1, [0]), {1}, {2}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "map_data").mkdir()
            (root / "map_data/definition.csv").write_bytes(definition.encode())
            with mock.patch.object(sl, "layout", layout):
                bs.layouts(root, root, (pm, definition, water, impassable))
                by_generator = list(calls)
                calls.clear()
                bmg.west_dwarovar_layout(bmg.Roots(rie=root, anbennar=root, game=root, eu4=root),
                                         (pm, water, impassable))
        self.assertEqual(len(by_generator), 3)
        self.assertEqual(calls, by_generator)

    def test_generators_never_use_the_cache(self):
        users = [p.name for p in st.TOOLS.glob("*.py") if "shared_trace" in p.read_text(encoding="utf-8")]
        self.assertEqual(users, ["run_tests.py"])


class CodeFileTests(unittest.TestCase):
    def test_the_tracer_and_its_regions_are_inputs(self):
        names = {p.relative_to(st.TOOLS).as_posix() for p in st.code_files()}
        self.assertLessEqual({"build_serpentreach.py", "serpentreach_layout.py", "dwarven_mountains.py",
                              "eu4_import.py", "pngio.py", "terrain_fill.py", "heightpack.py",
                              "data/serpentreach.py", "data/segbandal.py", "data/west_dwarovar.py",
                              "data/map_graphics.py"}, names)


if __name__ == "__main__":
    unittest.main()

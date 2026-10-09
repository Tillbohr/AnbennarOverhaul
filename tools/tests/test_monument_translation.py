import re
import sys
import unittest
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import eu4_monuments as em  # noqa: E402
from data.monuments import translation as tr  # noqa: E402
from eu4_monuments import gate_atoms  # noqa: E402

GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game")
ANBENNAR = Path(__file__).resolve().parents[3] / "anbennar-ck3-dev-master"
EU4_PRESENT = all(root.is_dir() for root in em.EU4_ROOTS.values())
CK3_PRESENT = (GAME / "common").is_dir() and (ANBENNAR / "common").is_dir()

_MODIFIER_BLOCK = re.compile(r"\b(\w*_modifier)\s*=\s*\{")


def _read(path):
    return re.sub(r"#[^\n]*", "", path.read_bytes().decode("utf-8-sig", errors="replace")).replace("\r", "")


def _top_level_keys(body):
    depth, flat = 0, []
    for ch in body:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif depth == 0:
            flat.append(ch)
    return re.findall(r"(?:^|\s)([a-z_][a-z0-9_]*)\s*=", "".join(flat))


@lru_cache(maxsize=None)
def modifier_keys_by_block(*roots):
    """`*_modifier` block name -> keys used as `<key> =` directly inside such blocks under roots."""
    blocks = {}
    for root in roots:
        for path in root.rglob("*.txt"):
            text = _read(path)
            for m in _MODIFIER_BLOCK.finditer(text):
                end = em._balanced(text, m.end() - 1)
                keys = blocks.setdefault(m.group(1), set())
                keys.update(_top_level_keys(text[m.end():end - 1]))
    return blocks


def modifier_keys_in(*roots):
    """Every key that appears as `<key> =` in some `*_modifier` block under roots."""
    return set().union(*modifier_keys_by_block(*roots).values())


def _top_level_names(folder):
    names = set()
    for path in folder.glob("*.txt"):
        names.update(re.findall(r"(?m)^([A-Za-z0-9_]+)\s*=\s*\{", _read(path)))
    return names


def _nested_names(folder, depth):
    names = set()
    for path in folder.glob("*.txt"):
        names.update(re.findall(rf"(?m)^\t{{{depth}}}([A-Za-z0-9_]+)\s*=\s*\{{", _read(path)))
    return names


ANBENNAR_CULTURES = _top_level_names(ANBENNAR / "common/culture/cultures")
ANBENNAR_HERITAGES = {n for n in _top_level_names(ANBENNAR / "common/culture/pillars") if n.startswith("heritage_")}
ANBENNAR_RELIGIONS = _top_level_names(ANBENNAR / "common/religion/religion_types")
ANBENNAR_FAITHS = _nested_names(ANBENNAR / "common/religion/religion_types", 2)


def integer(value):
    """INTEGER rounding as the module docstring defines it: half away from zero, never 0 for a nonzero value."""
    if value == 0:
        return 0
    rounded = max(1, int(abs(value) + 0.5))
    return rounded if value > 0 else -rounded


def top_level_statements(text):
    """`key = value` / `key = { ... }` statements at the top level of a script snippet."""
    statements, pos = [], 0
    for m in re.finditer(r"[A-Za-z0-9_.:]+\s*=\s*", text):
        if m.start() < pos:
            continue
        end = em._balanced(text, m.end()) if text[m.end():m.end() + 1] == "{" else m.end() + len(text[m.end():].split()[0])
        statements.append(text[m.start():end])
        pos = end
    return statements


def cannor_projects():
    supers = em.province_superregions(em.EU4_ROOTS["anbennar"])
    return [p for p in em.load_projects(em.EU4_ROOTS).values() if supers.get(p.start) in em.CANNOR]


class GateAtomsTests(unittest.TestCase):
    def test_atoms_are_typed_and_deduplicated(self):
        body = """owner = { OR = { primary_culture = vertesker accepted_culture = vertesker tag = A30
                   culture_group = lencori religion_group = cannorian religion = the_thought
                   has_country_flag = semi_monstrous has_owner_religion = yes culture_is_elven = yes } }"""
        self.assertEqual(gate_atoms(body), [
            "culture:vertesker", "tag:A30", "culture_group:lencori", "religion_group:cannorian",
            "religion:the_thought", "flag:semi_monstrous",
        ])

    def test_comments_are_ignored(self):
        self.assertEqual(gate_atoms("culture = esmari # culture = moon_elf"), ["culture:esmari"])


class TranslationTableTests(unittest.TestCase):
    def test_rows_are_well_formed(self):
        for k, r in tr.MODIFIERS.items():
            self.assertIsInstance(r, (tr.Row, tr.Drop), k)
            if isinstance(r, tr.Row):
                self.assertIn(r.scope, ("province", "county"), k)
                self.assertNotEqual(r.mult, 0, k)
            else:
                self.assertTrue(r.reason, k)

    @unittest.skipUnless(CK3_PRESENT, "needs CK3 and Anbennar CK3")
    def test_ck3_keys_are_used_by_vanilla_or_anbennar(self):  # the key appears as `<key> =` in some *_modifier
        known = modifier_keys_in(GAME / "common", ANBENNAR / "common")
        for k, r in tr.MODIFIERS.items():
            if isinstance(r, tr.Row):
                self.assertTrue(r.ck3 in known, f"{k} -> {r.ck3}")
        for key in tr.INTEGER:
            self.assertTrue(key in known, key)

    @unittest.skipUnless(CK3_PRESENT, "needs CK3")
    def test_icons_exist(self):
        for cat, icon in tr.ICONS.items():
            self.assertTrue((GAME / "gfx/interface/icons/building_types" / icon).is_file(), cat)

    def test_icon_categories(self):
        self.assertEqual(set(tr.ICONS), {
            "fortress", "castle", "palace", "temple", "academy", "library", "port", "market", "guild", "foundry",
            "mine", "tomb", "monument", "theatre", "lighthouse", "bath", "forest"})

    @unittest.skipUnless(CK3_PRESENT, "needs Anbennar CK3")
    def test_culture_targets_exist(self):  # every `culture:x` / `has_cultural_pillar = heritage_x` named in a
        for k, trig in tr.CULTURES.items():  # mapped trigger exists in Anbennar's culture / pillar files
            for c in re.findall(r"culture:(\w+)", trig or ""):
                self.assertTrue(c in ANBENNAR_CULTURES, f"{k}: culture {c}")
            for h in re.findall(r"heritage_\w+", trig or ""):
                self.assertTrue(h in ANBENNAR_HERITAGES, f"{k}: {h}")
            for r in re.findall(r"religion:(\w+)", trig or ""):
                self.assertTrue(r in ANBENNAR_RELIGIONS, f"{k}: religion {r}")
            for f in re.findall(r"faith:(\w+)", trig or ""):
                self.assertTrue(f in ANBENNAR_FAITHS, f"{k}: faith {f}")

    def test_culture_rules(self):
        for k, trig in tr.CULTURES.items():
            if k.startswith(("tag:", "flag:")):
                self.assertIsNone(trig, k)
            if trig is not None:
                self.assertEqual(trig.count("{"), trig.count("}"), k)

    def test_one_off_has_no_character_root_values(self):
        for pattern, effect in tr.ONE_OFF:
            self.assertNotIn("root_faith", effect or "", pattern)

    def test_one_off_patterns_compile_and_scale(self):
        for pattern, effect in tr.ONE_OFF:
            re.compile(pattern)
            if effect is not None:
                self.assertEqual(effect.count("{"), effect.count("}"), pattern)

        def effect_of(statement):
            for pattern, effect in tr.ONE_OFF:
                if re.search(pattern, statement):
                    return effect
            return "unmatched"

        self.assertIsNone(effect_of("add_building_construction = { building = mage_tower speed = 0.1 cost = 0 }"))
        self.assertIsNone(effect_of("add_base_production = 2"))
        self.assertIsNone(effect_of("owner = { add_country_modifier = { name = x duration = 7300 } }"))
        mage = effect_of("define_advisor = { type = court_mage skill = 3 culture = root location = 67 }")
        self.assertIn("create_character", mage)
        self.assertIn("education_learning", mage)
        loyalty = effect_of("owner = { add_estate_loyalty = { estate = estate_mages loyalty = 15 } }")
        self.assertIn("add_prestige = 150", loyalty)  # 50 x loyalty / 5

    def test_integer_keys_are_mapped(self):
        targets = {r.ck3 for r in tr.MODIFIERS.values() if isinstance(r, tr.Row)}
        self.assertIn("fort_level", tr.INTEGER)
        self.assertLessEqual(tr.INTEGER, targets)

    def test_local_defensiveness_scales_to_fort_levels(self):
        row = tr.MODIFIERS["local_defensiveness"]
        self.assertEqual((row.ck3, row.scope), ("fort_level", "province"))
        self.assertEqual([integer(v * row.mult) for v in (0.05, 0.1, 0.25, 0.33, 1.0)], [1, 1, 2, 2, 6])

    def test_no_row_targets_a_cultural_head_modifier(self):  # cultural_head_* only works for the cultural head
        for k, r in tr.MODIFIERS.items():
            if isinstance(r, tr.Row):
                self.assertFalse(r.ck3.startswith("cultural_head_"), f"{k} -> {r.ck3}")

    def test_each_culture_value_is_one_trigger(self):
        for k, trig in tr.CULTURES.items():
            if trig is not None:
                self.assertEqual(len(top_level_statements(trig)), 1, f"{k}: {trig}")

    def test_costs(self):
        self.assertEqual([round(f * tr.COST) for f in (1000, 2500, 5000)], [400, 1000, 2000])
        self.assertEqual(120 * tr.DAYS_PER_MONTH, 1800)

    @unittest.skipUnless(EU4_PRESENT, "needs EU4 mods")
    def test_every_cannor_key_is_covered(self):
        for p in cannor_projects():
            for t in p.tiers:
                for k in (*t.province, *t.area, *t.country):
                    self.assertTrue(k in tr.MODIFIERS, f"{p.key}: {k}")
            for atom in gate_atoms(p.gate):  # "culture:castanorian", "tag:A80", ...
                self.assertTrue(atom in tr.CULTURES, f"{p.key}: {atom}")

    @unittest.skipUnless(EU4_PRESENT and CK3_PRESENT, "needs EU4 mods, CK3 and Anbennar CK3")
    def test_ck3_keys_fit_the_block_they_land_in(self):
        """province rows -> province_/county_modifier, area -> county_modifier, country -> character_modifier.

        Area rows must fit county_modifier: duchy_capital_county_modifier is for duchy_capital buildings only."""
        used = modifier_keys_by_block(GAME / "common", ANBENNAR / "common")
        for p in cannor_projects():
            for t in p.tiers:
                for blocks, keys in ((("province",), t.province), (("area",), t.area), (("country",), t.country)):
                    for k in keys:
                        r = tr.MODIFIERS.get(k)
                        if not isinstance(r, tr.Row):
                            continue
                        if blocks == ("province",):
                            allowed = used[f"{r.scope}_modifier"]
                        elif blocks == ("area",):
                            allowed = used["county_modifier"]
                        else:
                            allowed = used["character_modifier"]
                        self.assertTrue(r.ck3 in allowed, f"{p.key} {blocks[0]}: {k} -> {r.ck3}")


if __name__ == "__main__":
    unittest.main()

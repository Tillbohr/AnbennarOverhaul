"""The placeholder orc and goblin cultures and faiths."""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_dynasty_names as bdn  # noqa: E402
import eu4_import as ei  # noqa: E402
import pdx_script  # noqa: E402
import shared_trace  # noqa: E402
from data import dwarovar_tribes as dt  # noqa: E402

SUBMOD = Path(__file__).resolve().parents[2]
ANBENNAR = SUBMOD.parent / "anbennar-ck3-dev-master"
GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game")
ROOTS = (SUBMOD, ANBENNAR, GAME)
CULTURES = ("black_orc", "cave_goblin")
RELIGIONS = {"aov_dookan_religion": ("old_dookan", "orc"), "aov_goblin_shamanism_religion": ("goblinic_shamanism", "goblin")}
HERITAGES = ("heritage_orcish", "heritage_goblinoid")
LANGUAGES = ("language_orcish", "language_goblin")


def read(rel: str) -> str:
    return (SUBMOD / rel).read_text(encoding="utf-8-sig")


def blocks(rel: str) -> dict:
    return pdx_script.parse_blocks(pdx_script.strip_comments(read(rel)))


def defined(folder: str, key: str) -> bool:
    """A top-level `key = {` in any .txt of folder in the overhaul, Anbennar or the game."""
    pattern = re.compile(rf"(?m)^{re.escape(key)}\s*=\s*\{{")
    return any(pattern.search(p.read_text(encoding="utf-8-sig", errors="replace"))
               for root in ROOTS for p in (root / folder).glob("*.txt"))


LOC = read("localization/english/aov_tribes_cultures_l_english.yml") if (
    SUBMOD / "localization/english/aov_tribes_cultures_l_english.yml").is_file() else ""


def has_loc(key: str) -> bool:
    return re.search(rf'(?m)^ {re.escape(key)}:\d* ?"', LOC) is not None


class CultureTests(unittest.TestCase):
    def test_cultures_have_fields(self):
        cultures = blocks("common/culture/cultures/aov_tribes_cultures.txt")
        self.assertEqual(set(cultures), set(CULTURES))
        for key, body in cultures.items():
            for field in ("color", "ethos", "heritage", "language", "martial_custom", "head_determination", "traditions",
                          "name_list", "coa_gfx", "building_gfx", "clothing_gfx", "unit_gfx", "ethnicities"):
                self.assertRegex(body, rf"(?m)^\s*{field} =", f"{key} {field}")
        self.assertIn("heritage = heritage_orcish", cultures["black_orc"])
        self.assertIn("language = language_orcish", cultures["black_orc"])
        self.assertIn("name_list = name_list_black_orc", cultures["black_orc"])
        self.assertIn("heritage = heritage_goblinoid", cultures["cave_goblin"])
        self.assertIn("language = language_goblin", cultures["cave_goblin"])
        self.assertIn("name_list = name_list_cave_goblin", cultures["cave_goblin"])

    def test_traditions_exist(self):
        cultures = blocks("common/culture/cultures/aov_tribes_cultures.txt")
        for key, body in cultures.items():
            traditions = re.search(r"traditions = \{(.*?)\}", body, re.S).group(1).split()
            self.assertEqual(len(traditions), 3, key)
            for tradition in traditions:
                self.assertTrue(defined("common/culture/traditions", tradition), tradition)

    def test_ethos_and_gfx_exist(self):
        for key, body in blocks("common/culture/cultures/aov_tribes_cultures.txt").items():
            ethos = re.search(r"ethos = (\w+)", body).group(1)
            self.assertTrue(defined("common/culture/pillars", ethos), ethos)

    def test_name_lists(self):
        lists = blocks("common/culture/name_lists/aov_tribes.txt")
        self.assertEqual(set(lists), {f"name_list_{c}" for c in CULTURES})
        for key, body in lists.items():
            self.assertIn("house_based_map_names = yes", body, key)
            for field in ("dynasty_names", "male_names", "female_names"):
                inner = re.search(rf"\b{field} = \{{(.*?)\}}", body, re.S)
                self.assertTrue(inner and inner.group(1).split(), f"{key} {field}")

    def test_names_come_from_eu4(self):
        names = ei.culture_dynasty_names()
        lists = blocks("common/culture/name_lists/aov_tribes.txt")
        self.assertEqual(len(re.findall(r'"dynn_\w+"', lists["name_list_black_orc"])), len(set(names["orcish"])))
        self.assertEqual(len(re.findall(r'"dynn_\w+"', lists["name_list_cave_goblin"])), len(set(names["goblin"])))

    def test_every_name_has_loc(self):
        """A name list's names need loc, or the engine logs an error for each. A key may be one Anbennar already has."""
        known = LOC + "".join(p.read_text(encoding="utf-8-sig", errors="replace")
                              for root in (ANBENNAR, GAME) for p in (root / "localization/english").rglob("*.yml")
                              if "name" in p.name or "dynast" in p.name)
        dynasties = bdn.dynasty_loc(list(ROOTS))
        for key, body in blocks("common/culture/name_lists/aov_tribes.txt").items():
            for name in re.search(r"\bdynasty_names = \{(.*?)\}", body, re.S).group(1).replace('"', " ").split():
                self.assertIn(name, dynasties, key)
            for field in ("male_names", "female_names"):
                for name in re.search(rf"\b{field} = \{{(.*?)\}}", body, re.S).group(1).split():
                    self.assertRegex(known, rf'(?m)^ {re.escape(name)}:\d* ?"', f"{key} {name}")
            self.assertTrue(has_loc(key), key)

    def test_collective_nouns(self):
        self.assertRegex(LOC, r'(?m)^ black_orc_collective_noun:0 "Orcs"$')
        self.assertRegex(LOC, r'(?m)^ cave_goblin_collective_noun:0 "Goblins"$')

    def test_every_pillar_and_faith_has_loc(self):
        keys = [f"{h}_name" for h in HERITAGES + LANGUAGES] + [f"{h}_collective_noun" for h in HERITAGES]
        for culture in CULTURES:
            keys += [culture, f"{culture}_prefix", f"{culture}_collective_noun"]
        for religion, (faith, _race) in RELIGIONS.items():
            for base in (religion, faith):
                keys += [base, f"{base}_adj", f"{base}_adherent", f"{base}_adherent_plural", f"{base}_desc"]
        keys.append("rf_aov_serpentspine_tribes")
        self.assertEqual([k for k in keys if not has_loc(k)], [])

    def test_heritage_history_files(self):
        for heritage in HERITAGES:
            text = read(f"history/cultures/{heritage}.txt")
            self.assertIn("discover_innovation = innovation_barracks", text, heritage)
            self.assertNotIn("innovation_war_camels", text.replace("# discover", ""), heritage)


class FaithTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.religions = blocks("common/religion/religion_types/aov_tribes_religions.txt")

    def test_religions_and_family(self):
        self.assertEqual(set(self.religions), set(RELIGIONS))
        for key, (faith, _race) in RELIGIONS.items():
            self.assertIn("family = rf_aov_serpentspine_tribes", self.religions[key], key)
            self.assertRegex(self.religions[key], rf"(?m)^\s*{faith} = \{{", key)
        self.assertIn("rf_aov_serpentspine_tribes",
                      blocks("common/religion/religion_family_types/aov_tribes.txt"))

    def test_doctrines_exist(self):
        for key, body in self.religions.items():
            for doctrine in re.findall(r"\bdoctrine = (\w+)", body):
                self.assertTrue(defined("common/religion/doctrine_types", doctrine), f"{key} {doctrine}")

    def test_race_is_no_sin(self):
        for key, body in self.religions.items():
            self.assertNotIn("race_orc", body, key)
            self.assertNotIn("race_goblin", body, key)

    def test_every_localization_key_has_text(self):
        for key, body in self.religions.items():
            section = re.search(r"\blocalization = \{(.*)\n\t\}\n\n\tfaiths", body, re.S).group(1)
            used = set(re.findall(r"= (aov_\w+)", section)) | set(re.findall(r"^\s+(aov_\w+)\s*$", section, re.M))
            self.assertGreater(len(used), 30, key)
            self.assertEqual(sorted(k for k in used if not has_loc(k)), [], key)

    def test_holy_sites_are_tribe_counties(self):
        (serp, seg, wd), _ck3 = shared_trace.layouts()
        area_of = ei.province_areas()
        race_of = {}
        for lay in (serp, seg, wd):
            for c in lay.counties:
                tribe = dt.tribe_of(c.eu4_id, area_of.get(c.eu4_id))
                race_of[c.key] = tribe.race if tribe else None
        sites = blocks("common/religion/holy_site_types/aov_tribes_holy_sites.txt")
        for key, (faith, race) in RELIGIONS.items():
            listed = re.findall(r"\bholy_site = (\w+)", self.religions[key])
            self.assertEqual(len(listed), 5, key)
            for site in listed:
                county = re.search(r"county = (\w+)", sites[site]).group(1)
                self.assertEqual(race_of.get(county), race, f"{key} {site} {county}")
                self.assertTrue(has_loc(f"holy_site_{site}_name"), site)
                self.assertTrue(has_loc(f"holy_site_{site}_effect_name"), site)


if __name__ == "__main__":
    unittest.main()

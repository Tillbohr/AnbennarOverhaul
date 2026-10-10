import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import eu4_monuments as em  # noqa: E402
import import_eu4_monuments as imp  # noqa: E402
from eu4_monuments import Tier  # noqa: E402

ANBENNAR_CK3 = Path(__file__).resolve().parents[3] / "anbennar-ck3-dev-master"
LIVE = ANBENNAR_CK3.is_dir() and all(p.is_dir() for p in em.EU4_ROOTS.values())

TITLES = """\
e_a = {
	k_a = {
		d_a = {
			c_x = {
				b_1 = { province = 11 }
				b_2 = {
					province = 12
				}
				b_3 = { province = 13 }
			}
			c_y = {
				cultural_names = { name_list_x = cn_y }
				b_y1 = { province = 21 }
			}
			c_mid = {
				b_mid = { province = 31 } # a barony named like its county
			}
		}
	}
}
"""
LOC = (' c_x:0 "Xland"\n c_x_adj:0 "Xish"\n b_1:0 "Firstbarony"\n c_y:0 "Ytown"\n b_y1:0 "Ybarony"\n'
       ' c_mid:0 "Midton"\n b_mid:0 "Midton"\n')
HISTORY = """\
11 = {
	holding = castle_holding
}
12 = {
	# special_building = ignored_comment
	holding = city_holding
	1000.1.1 = {
		special_building_slot = some_anbennar_building_01
		special_building = some_anbennar_building_01
	}
}
"""


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(("﻿" + text).encode("utf-8"))


def fixture_root():
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    write(root / "common/landed_titles/anb_landed_titles.txt", TITLES)
    write(root / "localization/english/anb_titles_l_english.yml", "l_english:\n" + LOC)
    write(root / "history/provinces/anb_k_a.txt", HISTORY)
    return tmp, root


def fixture_titles():
    tmp, root = fixture_root()
    with tmp:
        return imp.ck3_titles(root)


def two_monuments_in(county):
    name = {"c_x": "Xland", "c_y": "Ytown"}[county]
    return [{"eu4_key": f"m{i}", "place": name, "barony": None, "province": None} for i in (1, 2)]


class PlacementTests(unittest.TestCase):
    def test_name_matching_ignores_accents_and_punctuation(self):
        titles = {"lorentaine": "c_lorentaine", "humacsrest": "c_humacs_rest"}
        self.assertEqual(imp.match_title("Lorentainé", titles), "c_lorentaine")
        self.assertEqual(imp.match_title("Humac's Rest", titles), "c_humacs_rest")
        self.assertIsNone(imp.match_title("Nowhere", titles))

    def test_ck3_titles_reads_nested_blocks(self):
        names, provinces, county_baronies, capitals = fixture_titles()
        self.assertEqual(names["xland"], "c_x")
        self.assertEqual(names["firstbarony"], "b_1")
        self.assertEqual(names["midton"], "c_mid")  # a county wins over a barony of the same name
        self.assertNotIn("xish", names)  # _adj keys are not names
        self.assertEqual(provinces["b_2"], 12)
        self.assertEqual(county_baronies["c_x"], ["b_1", "b_2", "b_3"])
        self.assertEqual(county_baronies["c_y"], ["b_y1"])
        self.assertEqual(capitals["c_x"], "b_1")

    def test_anbennar_slots_ignore_comments_and_read_dated_blocks(self):
        tmp, root = fixture_root()
        with tmp:
            self.assertEqual(imp.anbennar_slots(root), {12: "some_anbennar_building_01"})

    def test_shared_county_takes_next_free_barony(self):
        ms = two_monuments_in("c_x")
        imp.place(ms, fixture_titles(), slots={})
        self.assertEqual([m["barony"] for m in ms], ["b_1", "b_2"])
        self.assertEqual([m["province"] for m in ms], [11, 12])

    def test_existing_anbennar_slot_is_skipped(self):
        ms = two_monuments_in("c_x")[:1]
        imp.place(ms, fixture_titles(), slots={11: "some_anbennar_building_01"})
        self.assertEqual(ms[0]["barony"], "b_2")

    def test_shared_county_without_free_barony_is_reported(self):
        ms = two_monuments_in("c_y")
        report = imp.place(ms, fixture_titles(), slots={})
        self.assertEqual(ms[0]["barony"], "b_y1")
        self.assertIsNone(ms[1]["barony"])
        self.assertTrue(any("c_y" in line for line in report))

    def test_unmatched_name_is_reported(self):
        ms = [{"eu4_key": "lost", "place": "Nowhere", "barony": None, "province": None}]
        report = imp.place(ms, fixture_titles(), slots={})
        self.assertIsNone(ms[0]["barony"])
        self.assertTrue(any("lost" in line for line in report))

    def test_hand_placed_barony_is_reserved_and_gets_its_province(self):
        ms = two_monuments_in("c_x")
        ms[1]["barony"] = "b_1"
        imp.place(ms, fixture_titles(), slots={})
        self.assertEqual((ms[1]["barony"], ms[1]["province"]), ("b_1", 11))
        self.assertEqual(ms[0]["barony"], "b_2")

    def test_chain_takes_anbennar_barony(self):
        ms = [{"eu4_key": "the_lake_palace", "place": "Nowhere", "barony": None, "province": None}]
        report = imp.place(ms, fixture_titles(), slots={12: "lake_palace_02"})
        self.assertEqual((ms[0]["barony"], ms[0]["province"]), ("b_2", 12))
        self.assertEqual(report, [])

    def test_unbuilt_monument_prefers_barony_with_holding(self):  # final review 8
        ms = [{"eu4_key": "m", "place": "Firstbarony", "barony": None, "province": None, "start_level": 0}]
        report = imp.place(ms, fixture_titles(), slots={}, holdings={12, 13})
        self.assertEqual(ms[0]["barony"], "b_2")
        self.assertTrue(any("b_1 has no holding" in line and "took b_2" in line for line in report))

    def test_built_monument_keeps_its_barony_without_holding(self):
        ms = [{"eu4_key": "m", "place": "Firstbarony", "barony": None, "province": None, "start_level": 1}]
        imp.place(ms, fixture_titles(), slots={}, holdings={12})
        self.assertEqual(ms[0]["barony"], "b_1")

    def test_county_without_holding_keeps_choice_and_reports(self):
        ms = [{"eu4_key": "m", "place": "Ytown", "barony": None, "province": None, "start_level": 0}]
        report = imp.place(ms, fixture_titles(), slots={}, holdings=set())
        self.assertEqual(ms[0]["barony"], "b_y1")
        self.assertTrue(any("kept" in line for line in report))

    def test_anbennar_holdings(self):
        tmp, root = fixture_root()
        with tmp:
            (root / "history/provinces/anb_k_b.txt").write_bytes(
                "13 = {\n\tholding = none\n}\n14 = { holding = city_holding }\n".encode("utf-8"))
            self.assertEqual(imp.anbennar_holdings(root), {11, 12, 14})

    def test_ck3_loc_reads_nested_folders(self):
        tmp, root = fixture_root()
        with tmp:
            write(root / "localization/english/culture/anb_cultures_l_english.yml",
                  'l_english:\n moon_elvish: "Moon Elvish"\n')
            loc = imp.ck3_loc(root)
            self.assertEqual(loc["moon_elvish"], "Moon Elvish")
            self.assertEqual(loc["c_x"], "Xland")

    def test_county_overrides(self):
        titles = fixture_titles()
        ms = [{"eu4_key": k, "place": "Nowhere", "barony": None, "province": None}
              for k in ("the_dragonhoard", "kobildzan_kobildzex_guild_of_trapsmiths")]
        names, provinces, county_baronies, capitals = titles
        county_baronies["c_soxun_kobildzex"] = ["b_s1", "b_s2"]
        capitals["c_soxun_kobildzex"] = "b_s1"
        provinces.update(b_s1=1, b_s2=2)
        imp.place(ms, titles, slots={})
        self.assertEqual({m["barony"] for m in ms}, {"b_s1", "b_s2"})


class ConversionTests(unittest.TestCase):
    def test_start_level(self):
        self.assertEqual(imp.start_level(starting_tier=1, year=1), 1)
        self.assertEqual(imp.start_level(starting_tier=1, year=1300), 0)
        self.assertEqual(imp.start_level(starting_tier=0, year=1), 0)
        self.assertEqual(imp.start_level(starting_tier=1, year=1021), 1)
        self.assertEqual(imp.start_level(starting_tier=1, year=1022), 0)
        self.assertEqual(imp.start_level(starting_tier=2, year=1022), 0)

    def test_levels_for_kinds(self):
        self.assertEqual(imp.default_levels("toncodden_lighthouse"), [
            "aov_monument_toncodden_lighthouse_01", "aov_monument_toncodden_lighthouse_02",
            "aov_monument_toncodden_lighthouse_03"])
        self.assertEqual(len(imp.CHAINS), 17)
        self.assertEqual(imp.CHAINS["imperial_palace_anbenncost"],
                         ["castle_dameris_01", "castle_dameris_02", "castle_dameris_03"])
        self.assertEqual(imp.CHAINS["bal_ouord"], [
            "castanorian_citadel_bal_ouord_02", "aov_monument_bal_ouord_02", "aov_monument_bal_ouord_03"])
        self.assertEqual(imp.CHAINS["the_lake_palace"],
                         ["lake_palace_01", "lake_palace_02", "aov_monument_the_lake_palace_03"])

    def test_hand_fields_win_and_survive_reimport(self):
        out = imp.merge({"eu4_key": "k", "barony": None, "category": "monument"}, {"k": {"barony": "b_9"}})
        self.assertEqual(out["barony"], "b_9")
        self.assertEqual(out["category"], "monument")

    def test_hand_tiers_merge_key_by_key(self):
        base = {"eu4_key": "k", "tiers": [
            {"province_modifier": {"fort_level": 1, "monthly_income": 2}, "cost": 400},
            {"province_modifier": {}, "cost": 1000}, {"province_modifier": {}, "cost": 2000}]}
        hand = {"k": {"tiers": [{"province_modifier": {"fort_level": None, "tax_mult": 0.1}}, {}, {"cost": 5}]}}
        out = imp.merge(base, hand)
        self.assertEqual(out["tiers"][0]["province_modifier"], {"monthly_income": 2, "tax_mult": 0.1})
        self.assertEqual(out["tiers"][0]["cost"], 400)
        self.assertEqual(out["tiers"][2]["cost"], 5)
        self.assertEqual(base["tiers"][0]["province_modifier"], {"fort_level": 1, "monthly_income": 2})

    def test_translate_tier(self):
        t = imp.translate_tier(Tier(1000, 120, {"local_defensiveness": 0.1}, {}, {"mages_loyalty_modifier": 0.025}, ""))
        self.assertEqual(t["province_modifier"], {"fort_level": 1})
        self.assertEqual((t["cost"], t["days"]), (400, 1800))

    def test_translate_tier_scopes_sums_and_drops(self):
        t = imp.translate_tier(Tier(
            0, 0,
            {"local_tax_modifier": 0.2, "local_production_efficiency": 0.1, "local_unrest": -0.01, "merchants": 1},
            {"local_defensiveness": 0.25, "totally_unknown": 1},
            {"prestige": 0.5, "legitimacy": 1}, ""))
        self.assertEqual(t["county_modifier"]["tax_mult"], 0.13)
        self.assertEqual(t["county_modifier"]["fort_level"], 2)  # area modifiers land in the county block
        self.assertEqual(t["county_modifier"]["county_opinion_add"], 1)  # 0.02 never rounds to 0
        self.assertEqual(t["character_modifier"], {"monthly_prestige": 0.5, "monthly_legitimacy_add": 0.25})
        self.assertEqual(t["province_modifier"], {})
        self.assertNotIn("duchy_capital_county_modifier", t)
        self.assertEqual(len(t["dropped"]), 2)
        self.assertTrue(any("merchants" in d for d in t["dropped"]))
        self.assertTrue(any("totally_unknown" in d for d in t["dropped"]))

    def test_integer_rounding_half_away_from_zero(self):
        self.assertEqual(imp.to_integer(2.5), 3)
        self.assertEqual(imp.to_integer(-2.5), -3)
        self.assertEqual(imp.to_integer(0.3), 1)
        self.assertEqual(imp.to_integer(-0.3), -1)
        self.assertEqual(imp.to_integer(0), 0)

    def test_one_off_effects(self):
        t = imp.translate_tier(Tier(0, 0, {}, {}, {}, (
            "owner = { add_estate_loyalty = { estate = estate_church loyalty = 5 } }\n"
            "add_base_production = 2\n"
            "custom_tooltip = something_tt")))
        self.assertIn("add_piety = 50", t["on_complete"])
        self.assertEqual(len(t["dropped"]), 2)

    def test_scope_blocks_are_split_into_effects(self):
        t = imp.translate_tier(Tier(0, 0, {}, {}, {}, (
            "owner = { add_estate_loyalty = { estate = estate_mages loyalty = 5 } add_prestige = 10 }\n"
            "if = { hidden_effect = { owner = { add_treasury = 100 set_country_flag = f } } }")))
        self.assertIn("add_prestige = 50", t["on_complete"])
        self.assertIn("add_prestige = 100", t["on_complete"])
        self.assertIn("add_gold = 40", t["on_complete"])
        self.assertEqual(t["dropped"], ["on_upgraded: set_country_flag = f"])

    def test_gated_effects_are_dropped_with_their_condition(self):  # Bal Dostan tier 1
        t = imp.translate_tier(Tier(0, 0, {}, {}, {}, (
            "owner = { add_estate_loyalty = { estate = estate_nobles loyalty = 5 }\n"
            "if = { limit = { has_estate = estate_castonath_patricians } "
            "add_estate_loyalty = { estate = estate_castonath_patricians loyalty = 15 } }\n"
            "if = { limit = { has_estate = estate_vampires } "
            "add_estate_loyalty = { estate = estate_vampires loyalty = 5 } }\n"
            "if = { limit = { has_x = yes } add_prestige = 10 } else = { add_prestige = 15 } }")))
        self.assertEqual(t["on_complete"], "barony.holder = { add_prestige = 50 }")
        self.assertEqual(len(t["dropped"]), 4)
        self.assertTrue(t["dropped"][0].startswith("on_upgraded: if has_estate = estate_castonath_patricians: add_estate"))
        self.assertTrue(t["dropped"][1].startswith("on_upgraded: if has_estate = estate_vampires: add_estate"))
        self.assertTrue(t["dropped"][3].startswith("on_upgraded: else: add_prestige = 15"))

    def test_dropped_text_is_not_truncated(self):
        long = "custom_tooltip = " + "x" * 200
        t = imp.translate_tier(Tier(0, 0, {}, {}, {}, long))
        self.assertEqual(t["dropped"], ["on_upgraded: " + long])

    def test_gate_translation(self):
        gate, desc, notes = imp.translate_gate(
            "culture = castanorian\nculture_group = lencori\ntag = A80", {"castanorian": "Castanorian"})
        self.assertEqual(gate.split()[0], "OR")
        self.assertIn("culture = culture:castanorian", gate)
        self.assertEqual(desc, "Castanorian, lencori")
        self.assertTrue(any("tag:A80" in n for n in notes))
        self.assertEqual(imp.translate_gate("tag = A80", {}),
                         ("", "", ["gate atom tag:A80 ignored (no CK3 equivalent)"]))
        self.assertEqual(imp.translate_gate("", {}), ("", "", []))
        self.assertEqual(imp.translate_gate("culture = castanorian", {})[0], "culture = culture:castanorian")

    def test_negated_gate_atoms_are_not_mapped(self):  # final review I4
        body = "OR = { culture = castanorian NOT = { culture_group = lencori } }"
        gate, desc, notes = imp.translate_gate(body, {})
        self.assertEqual(gate, "culture = culture:castanorian")
        self.assertNotIn("lencori", gate)
        self.assertIn("gate atom culture_group:lencori not mapped (negated in EU4: NOT/NOR)", notes)
        gate, desc, notes = imp.translate_gate("NOR = { culture = castanorian religion = the_thought }", {})
        self.assertEqual((gate, desc), ("", ""))
        self.assertEqual(len(notes), 2)
        self.assertTrue(all("negated" in n for n in notes))

    def test_scripted_gates_expand_to_atoms(self):
        # Dwarven Monuments gate through its own scripted triggers: the culture one expands to its atoms; the dig
        # level one has no CK3 equivalent yet (hold digging) and is noted
        body = """AND = { custom_trigger_tooltip = { dwarven_monuments_has_dig_level_2_or_higher = yes }
                  custom_trigger_tooltip = { dwarven_monuments_has_acceptable_culture_or_race = yes } }"""
        gate, desc, notes = imp.translate_gate(body, {})
        self.assertEqual(gate, "OR = { culture = { has_cultural_pillar = heritage_dwarven } "
                               "culture = { has_cultural_pillar = heritage_kobold } }")
        self.assertIn("gate atom culture_group:goblin ignored (no CK3 equivalent)", notes)
        self.assertTrue(any("dig level" in n for n in notes), notes)
        self.assertFalse([n for n in notes if n.endswith("not in the translation table")], notes)

    def test_gate_desc_uses_ck3_names(self):  # final review 6
        ck3 = {"moon_elvish": "Moon Elvish", "heritage_damesheader_name": "Damesheader",
               "cannorian_pantheon_religion": "Cannorian Pantheon", "blue_reachman": "Blue Reachman",
               "white_reachman": "White Reachman", "moorman": "Moorman"}
        eu4 = {"moon_elf": "Moon Elf", "anbennarian": "Anbennarian", "cannorian": "Cannorian", "alenic": "Alenic"}
        body = ("culture = moon_elf culture_group = anbennarian religion_group = cannorian culture_group = reachman "
                "culture_group = alenic culture = white_reachman")
        _, desc, _ = imp.translate_gate(body, eu4, ck3)
        self.assertEqual(desc, "Moon Elvish, Damesheader, Cannorian Pantheon, Blue Reachman, White Reachman, "
                               "Moorman, Alenic")  # Alenic: no CK3 loc in the fixture, EU4 name kept

    def test_ck3_name(self):
        self.assertEqual(imp.ck3_name("faith = faith:elikhetist", {"elikhetist": "Elikhetist"}), "Elikhetist")
        self.assertIsNone(imp.ck3_name("culture = culture:x", {}))
        self.assertIsNone(imp.ck3_name("culture = culture:x", {"x": "$y$"}))

    def test_category_guess(self):
        self.assertEqual(imp.guess_category("bal_ouord", "Bal Ouord"), "fortress")
        self.assertEqual(imp.guess_category("ara_temple", "Ara Temple"), "temple")
        self.assertEqual(imp.guess_category("rubyhold_academy", "Rubyhold Academy"), "academy")
        self.assertEqual(imp.guess_category("mystery", "Mystery"), "monument")


@unittest.skipUnless(LIVE, "needs EU4 and Anbennar CK3")
class LiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = imp.run("cannor")

    def test_cannor_import_places_everything(self):
        data = self.data
        self.assertEqual(len(data["MONUMENTS"]) + len(data["EXCLUDED"]), 82)
        self.assertEqual(data["EXCLUDED"], {"marrhold_dwarovar_tunnel": "canal: no CK3 canal mechanic"})
        soxun_baronies = set(imp.ck3_titles(ANBENNAR_CK3)[2]["c_soxun_kobildzex"])
        soxun = {m["eu4_key"]: m["barony"] for m in data["MONUMENTS"]
                 if m["eu4_key"] in ("kobildzan_kobildzex_guild_of_trapsmiths", "the_dragonhoard")}
        self.assertEqual(len(soxun), 2)
        self.assertTrue(all(b and b in soxun_baronies for b in soxun.values()))
        placed = [m["barony"] for m in data["MONUMENTS"] if m["barony"]]
        self.assertEqual(len(set(placed)), len(placed))
        unplaced = {m["eu4_key"] for m in data["MONUMENTS"] if not m["barony"]}
        reported = {line.split(":")[0] for line in data["REPORT"]
                    if "has no free barony" in line or "no CK3 title" in line or "is not free" in line}
        self.assertEqual(unplaced, reported)

    def test_new_buildings_avoid_anbennar_slots(self):
        slots = imp.anbennar_slots(ANBENNAR_CK3)
        for m in self.data["MONUMENTS"]:
            if m["barony"] and m["eu4_key"] not in imp.CHAINS:
                self.assertNotIn(m["province"], slots, m["eu4_key"])

    def test_mission_monuments_are_present(self):
        keys = {m["eu4_key"] for m in self.data["MONUMENTS"]}
        self.assertTrue({"palace_of_unity", "ravioli_bastion", "imperial_palace_anbenncost"} <= keys)

    def test_dameris_and_unity_share_anbenncost(self):
        by = {m["eu4_key"]: m for m in self.data["MONUMENTS"]}
        self.assertEqual(by["imperial_palace_anbenncost"]["barony"], "b_castle_dameris")
        self.assertEqual(by["palace_of_unity"]["barony"], "b_elvendocks")  # b_the_bilge has no holding
        self.assertEqual(by["imperial_palace_anbenncost"]["name"], "Castle Dameris")

    def test_monument_shape(self):
        for m in self.data["MONUMENTS"]:
            self.assertEqual(len(m["levels"]), 3, m["eu4_key"])
            self.assertEqual(len(m["tiers"]), 3, m["eu4_key"])
            self.assertIn(m["start_level"], (0, 1))
            for t in m["tiers"]:
                self.assertEqual(set(t), {"province_modifier", "county_modifier", "character_modifier",
                                          "on_complete", "cost", "days", "dropped"})



class RegionTests(unittest.TestCase):
    """Which EU4 projects a region builds, and why the others are left out."""

    def proj(self, key, file="dwarven.txt", type_="monument"):
        return em.Project(key=key, source="dwarven", file=file, start=1, year=1, type=type_, starting_tier=1,
                          gate="", tiers=[em.Tier(), em.Tier(), em.Tier()])

    def test_regions(self):
        self.assertEqual(imp.REGIONS["cannor"]["superregions"], em.CANNOR)
        self.assertEqual(imp.REGIONS["dwarovar"]["superregions"],
                         ("west_serpentspine_superregion", "east_serpentspine_superregion"))

    def test_dwarovar_exclusions(self):
        titles = {"seghdihr": "c_seghdihr"}
        classify = lambda p, name: imp.exclusion(p, "dwarovar", name, titles)  # noqa: E731
        self.assertIsNone(classify(self.proj("seghdihr_home"), "Seghdihr"))
        self.assertEqual(classify(self.proj("dd_x", file=imp.DUNGEON_FILE), "Seghdihr"), imp.DUNGEON)
        self.assertEqual(classify(self.proj("t", type_="canal"), "Seghdihr"), imp.CANAL)
        self.assertEqual(classify(self.proj("amlharaz_assembly"), "Amlharaz"), imp.OFF_MAP)

    def test_mission_monument_on_shared_placeholder_is_excluded(self):
        # EU4's Insyaa mission monuments all carry `# start = 2864`, a placeholder, not a location
        p = self.proj("fires_beneath")
        p.mission, p.start = True, 2864
        self.assertEqual(imp.exclusion(p, "dwarovar", "Dwarovrod | 1 |", {"dwarovrod1": "c_dwarovrod1"},
                                       placeholder_starts={2864}), imp.PLACEHOLDER)
        self.assertEqual(imp.placeholder_starts([p, p]), {2864})
        self.assertEqual(imp.placeholder_starts([p]), set())

    def test_cannor_keeps_unmatched_projects(self):
        # Cannor places unmatched projects through COUNTY_OVERRIDES / hand baronies, so it never excludes them
        self.assertIsNone(imp.exclusion(self.proj("the_dragonhoard"), "cannor", "Deeb Kobilderd", {}))


@unittest.skipUnless(LIVE, "needs EU4 and Anbennar CK3")
class DwarovarLiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = imp.run("dwarovar")

    def test_five_hold_monuments(self):
        self.assertEqual({m["eu4_key"] for m in self.data["MONUMENTS"]}, {
            "seghdihr_home_of_the_seg_band", "verkal_gulan_golden_delve", "hehodovar_school_of_architecture",
            "gor_ozumbrog_the_topaz_throne", "khugdihr_bank"})

    def test_every_serpentspine_project_accounted_for(self):
        supers = em.province_superregions(em.EU4_ROOTS["anbennar"])
        region = {k for k, p in em.load_projects(em.EU4_ROOTS).items()
                  if supers.get(p.start) in imp.REGIONS["dwarovar"]["superregions"]}
        self.assertEqual({m["eu4_key"] for m in self.data["MONUMENTS"]} | set(self.data["EXCLUDED"]), region)
        reasons = set(self.data["EXCLUDED"].values())
        self.assertTrue(reasons <= {imp.DUNGEON, imp.CANAL, imp.OFF_MAP, imp.PLACEHOLDER}, reasons)
        for key in ("deepest", "fires_beneath", "fluvial_waterworks", "grasswhirlpool"):
            self.assertEqual(self.data["EXCLUDED"][key], imp.PLACEHOLDER, key)
        self.assertTrue(all(v == imp.DUNGEON for k, v in self.data["EXCLUDED"].items() if k.startswith("dd_")))

    def test_placed_on_free_baronies(self):
        slots = imp.anbennar_slots(ANBENNAR_CK3)
        provinces = [m["province"] for m in self.data["MONUMENTS"]]
        self.assertTrue(all(provinces))
        self.assertEqual(len(set(provinces)), len(provinces))
        self.assertFalse(set(provinces) & set(slots))

if __name__ == "__main__":
    unittest.main()

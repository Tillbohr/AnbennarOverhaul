"""The Dwarovar tribes generator: governments, title pool, decision overrides, and the script that uses them."""

import re
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_dwarovar_tribes as bdt  # noqa: E402
import eu4_import as ei  # noqa: E402
import pdx_script  # noqa: E402
import shared_trace  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
from data import dwarovar_tribes as dt  # noqa: E402

SUBMOD = bdt.SUBMOD
GOVERNMENTS = ("orcish_warband_government", "goblin_chiefdom_government")


def read(rel: str) -> str:
    return (SUBMOD / rel).read_text(encoding="utf-8-sig")


def blocks(text: str) -> dict:
    return pdx_script.parse_blocks(pdx_script.strip_comments(text))


def test_titles(text: str) -> list:
    """(key, own text without child titles) for every title of a nested landed titles text."""
    out = []
    for m in re.finditer(r"(?m)^(\t*)([dke]_\w+) = \{\n", text):
        tabs, depth, i = m.group(1), 1, m.end()
        while depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        out.append((m.group(2), re.sub(rf"(?ms)^{tabs}\t[dk]_\w+ = \{{\n.*?^{tabs}\t\}}\n", "", text[m.end():i])))
    return out


class GovernmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = read("common/governments/00_government_types.txt")
        cls.governments = blocks(bdt.render_governments(cls.source))

    def test_governments_copy_tribal(self):
        self.assertEqual(set(self.governments), set(GOVERNMENTS))
        for key, body in self.governments.items():
            for line in ("primary_holding = tribal_holding", "vassal_contract_group = tribal_vassal",
                         "government_is_tribal", "use_prestige_to_buy_maa", "government_can_raid_rule"):
                self.assertIn(line, body, key)

    def test_governments_add_rules(self):
        for key, body in self.governments.items():
            rules = re.search(r"government_rules = \{(.*?)\}", body, re.S).group(1)
            for rule in ("government_ignores_rightful_liege_penalties", "sticky_government", "use_as_base_on_landed",
                         "use_as_base_on_rank_up", "dynasty_named_realms"):
                self.assertIn(f"{rule} = yes", rules, key)
            self.assertIn("government_is_dwarovar_tribe", body, key)
        orc, goblin = self.governments[GOVERNMENTS[0]], self.governments[GOVERNMENTS[1]]
        self.assertIn("has_trait = race_orc", orc)
        self.assertNotIn("race_goblin", orc)
        self.assertIn("has_trait = race_goblin", goblin)
        self.assertNotIn("race_orc", goblin)
        self.assertIn("government_is_orcish_warband", orc)
        self.assertIn("government_is_goblin_chiefdom", goblin)

    def test_valid_holdings_include_holds(self):
        for key, body in self.governments.items():
            holdings = re.search(r"valid_holdings = \{(.*?)\}", body).group(1).split()
            self.assertIn("dwarven_hold_holding", holdings, key)
            self.assertIn("elven_holding", holdings, key)

    def test_missing_source_stops(self):
        with self.assertRaisesRegex(GeneratorError, "tribal_government"):
            bdt.render_governments("feudal_government = {\n}\n")

    def test_governments_have_loc(self):
        loc = bdt.render_loc()
        for key in GOVERNMENTS:
            for suffix in ("", "_adj", "_adjective", "_realm", "_desc"):
                self.assertRegex(loc, rf'(?m)^ {key}{suffix}:0 "')


class PoolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = bdt.render_pool_titles()
        cls.titles = blocks(cls.text)

    def test_pool_counts(self):
        count = lambda prefix: sum(1 for k in self.titles if k.startswith(prefix))
        self.assertEqual([count(p) for p in ("d_aov_warband_", "k_aov_warband_", "e_aov_warband_")], [40, 20, 6])
        self.assertEqual([count(p) for p in ("d_aov_chiefdom_", "k_aov_chiefdom_", "e_aov_chiefdom_")], [40, 15, 4])
        self.assertIn("d_aov_warband_01", self.titles)
        self.assertIn("e_aov_chiefdom_04", self.titles)
        self.assertEqual(len(self.titles), len(bdt.pool_keys()))

    def test_pool_fields(self):
        for key, body in self.titles.items():
            for line in ("de_jure_drift_disabled = yes", "no_automatic_claims = yes",
                         "ignore_titularity_for_title_weighting = yes", "definite_form = yes"):
                self.assertIn(line, body, key)
            self.assertRegex(body, r"can_create = \{\s*always = no\s*\}", key)
            self.assertRegex(body, r"color = \{ \d+ \d+ \d+ \}", key)
            self.assertRegex(body, r"capital = c_\w+", key)
            self.assertNotRegex(body, r"(?m)^\s*[bcdke]_\w+ = \{", key)

    def test_pool_colours_differ(self):
        colours = [re.search(r"color = \{ (\d+ \d+ \d+) \}", b).group(1) for b in self.titles.values()]
        self.assertEqual(len(colours), len(set(colours)))

    def test_placeholder_capitals_exist(self):
        titles = read("common/landed_titles/aov_serpentreach.txt")
        for county in set(re.findall(r"capital = (c_\w+)", self.text)):
            self.assertRegex(titles, rf"(?m)^\s*{county} = \{{", county)

    def test_names_read_the_dynasty(self):
        loc = bdt.render_loc()
        for key, word in (("d_aov_warband_01", "Warband"), ("k_aov_warband_01", "Warhost"), ("e_aov_warband_01", "Horde"),
                          ("d_aov_chiefdom_01", "Chiefdom"), ("k_aov_chiefdom_01", "High Chiefdom"),
                          ("e_aov_chiefdom_01", "Swarm")):
            self.assertIn(f""" {key}:0 "[GetTitleByKey('{key}').GetHolder.GetDynasty.GetName] {word}"\n""", loc)
            self.assertIn(f""" {key}_adj:0 "[GetTitleByKey('{key}').GetHolder.GetDynasty.GetName]"\n""", loc)

    def test_pool_trigger_lists_every_title(self):
        trigger = blocks(bdt.render_pool_triggers())["aov_is_pool_title_trigger"]
        self.assertEqual(set(re.findall(r"this = title:(\w+)", trigger)), set(self.titles))

    def test_free_title_chain_walks_the_pool_in_order(self):
        effects = blocks(bdt.render_pool_effects())
        chain = effects["aov_tribe_free_orc_duchy_effect"]
        found = re.findall(r"title:(\w+) = \{ NOT = \{ exists = holder \} \}", chain)
        self.assertEqual(found, [f"d_aov_warband_{n:02d}" for n in range(1, 41)])
        self.assertEqual(chain.count("else_if"), 39)
        self.assertEqual({f"aov_tribe_free_{r}_{t}_effect" for r in dt.POOL for t in dt.POOL[r]} - set(effects), set())

    def test_take_and_has_free_dispatch_on_race(self):
        take = blocks(bdt.render_pool_effects())["aov_tribe_take_free_title_effect"]
        has = blocks(bdt.render_pool_triggers())["aov_tribe_has_free_title_trigger"]
        for text, suffix in ((take, "effect"), (has, "trigger")):
            self.assertIn("has_trait = race_orc", text)
            self.assertIn("has_trait = race_goblin", text)
            self.assertIn(f"aov_tribe_free_orc_$TIER$_{suffix} = yes", text)
            self.assertIn(f"aov_tribe_free_goblin_$TIER$_{suffix} = yes", text)

    def test_reused_title_resets_capital_and_arms(self):
        take = blocks(bdt.render_pool_effects())["aov_tribe_take_free_title_effect"]
        self.assertIn("set_capital_county = scope:aov_title_taker.capital_county", take)
        gain = blocks(read("common/on_action/aov_tribes_on_actions.txt"))["aov_tribe_title_gain"]
        self.assertIn("aov_is_pool_title_trigger = yes", gain)
        self.assertIn("aov_tribe_title_sync_effect = yes", gain)

    def test_sync_all_covers_the_pool(self):
        sync = blocks(bdt.render_pool_effects())["aov_tribe_sync_all_pool_titles_effect"]
        self.assertEqual(set(re.findall(r"title:(\w+) = \{", sync)), set(bdt.pool_keys()))
        self.assertIn("set_capital_county = holder.capital_county", sync)
        start = blocks(read("common/on_action/aov_tribes_on_actions.txt"))["aov_tribe_game_start"]
        self.assertIn("aov_tribe_sync_all_pool_titles_effect = yes", start)


class ValueTests(unittest.TestCase):
    def test_values_come_from_data(self):
        values = bdt.render_values()
        for tier, (counties, prestige) in dt.FORM.items():
            self.assertIn(f"aov_form_{tier}_counties = {counties}\n", values)
            self.assertIn(f"aov_form_{tier}_prestige = {prestige}\n", values)
        self.assertIn(f"aov_raise_prestige = {dt.RAISE_PRESTIGE}\n", values)

    def test_refusal_modifier(self):
        modifier = blocks(bdt.render_modifiers())["aov_refused_challenge"]
        self.assertIn(f"general_opinion = {dt.REFUSAL_OPINION}", modifier)
        self.assertIn(" aov_refused_challenge:0 ", bdt.render_loc())
        self.assertIn(" aov_refused_challenge_desc:0 ", bdt.render_loc())


class OverrideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = bdt.render_decision_overrides(bdt.ANBENNAR, bdt.GAME)
        cls.decisions = blocks(cls.text)

    def test_overrides_copy_and_block(self):
        self.assertEqual(set(self.decisions), {"convert_to_feudalism_liege_converted_decision",
                                               "convert_whole_realm_to_feudalism_decision",
                                               "tribal_challenge_ruler_decision", "found_duchy_decision",
                                               "found_kingdom_decision", "found_empire_decision"})
        for key, body in self.decisions.items():
            shown = re.search(r"(?m)^\tis_shown = \{\n(.*)", body, re.S).group(1)
            self.assertTrue(shown.startswith("\t\tNOT = { government_has_flag = government_is_dwarovar_tribe }"), key)

    def test_rest_of_the_decision_is_unchanged(self):
        source = (bdt.ANBENNAR / "common/decisions/80_major_decisions.txt").read_text(encoding="utf-8-sig")
        restored = re.sub(r"\t\tNOT = \{ government_has_flag = government_is_dwarovar_tribe \}[^\n]*\n", "", self.text)
        for key, body in blocks(restored).items():
            self.assertEqual(body, blocks(source)[key], key)

    def test_west_african_decision_is_not_loaded(self):
        """Anbennar's 80_major_decisions.txt replaces the game's, and leaves this one out, so it needs no block. If
        Anbennar brings it back, add it to DECISION_KEYS."""
        self.assertTrue((bdt.ANBENNAR / "common/decisions/80_major_decisions.txt").is_file())
        with mock.patch.object(bdt, "DECISION_KEYS", ("convert_whole_realm_to_feudalism_west_african_pagan_decision",)):
            with self.assertRaises(GeneratorError):
                bdt.render_decision_overrides(bdt.ANBENNAR, bdt.GAME)

    def test_missing_override_key_stops(self):
        with mock.patch.object(bdt, "DECISION_KEYS", ("no_such_decision",)):
            with self.assertRaisesRegex(GeneratorError, "no_such_decision"):
                bdt.render_decision_overrides(bdt.ANBENNAR, bdt.GAME)


class ScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actions = read("common/on_action/aov_tribes_on_actions.txt")
        cls.gain = blocks(cls.actions)["aov_tribe_title_gain"]

    def test_hooked_on_vanilla_on_actions(self):
        self.assertRegex(self.actions, r"on_title_gain = \{\s*on_actions = \{ aov_tribe_title_gain \}")
        self.assertRegex(self.actions, r"on_game_start = \{\s*on_actions = \{ aov_tribe_game_start \}")

    def test_non_tribal_holder_destroys_title(self):
        before_sync = self.gain[:self.gain.index("aov_tribe_title_sync_effect")]
        self.assertIn("destroy_title = scope:title", before_sync)
        branch = before_sync[before_sync.index("aov_is_pool_title_trigger"):before_sync.index("destroy_title")]
        self.assertIn("has_trait = race_orc", branch)
        self.assertIn("has_trait = race_goblin", branch)
        self.assertIn("NOT", branch)

    def test_sync_guards_missing_dynasty(self):
        sync = blocks(read("common/scripted_effects/aov_tribes_effects.txt"))["aov_tribe_title_sync_effect"]
        self.assertLess(sync.index("exists = holder.dynasty"), sync.index("set_coa = holder.dynasty"))

    def test_gov_changes_on_title_gain(self):
        self.assertIn("top_liege = { government_has_flag = government_is_dwarovar_tribe }", self.gain)
        self.assertRegex(self.gain, r"has_trait = race_orc\s+NOT = \{ government_has_flag = "
                                    r"government_is_orcish_warband \}\s+\}\s+change_government = orcish_warband_government")
        self.assertRegex(self.gain, r"has_trait = race_goblin\s+NOT = \{ government_has_flag = "
                                    r"government_is_goblin_chiefdom \}\s+\}\s+change_government = goblin_chiefdom_government")
        self.assertGreater(self.gain.index("change_government"), self.gain.index("aov_tribe_title_sync_effect"))


class OnTheMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lays = shared_trace.layouts()[0]
        cls.people = bdt.TribePeople(cls.lays)
        cls.history = bdt.render_title_history(cls.people)
        cls.characters = bdt.render_characters(cls.people)
        cls.dynasties = bdt.render_dynasties(cls.people)
        cls.arms = bdt.render_arms(cls.people)

    def test_chief_holds_pool_title_and_seat(self):
        first = self.people.tribes["masked_butcher"]
        self.assertEqual(first["pool_title"], "d_aov_warband_01")
        self.assertEqual(first["chief"], "aov_tr_masked_butcher_chief_1")
        self.assertEqual(self.people.tribes["skomdihr_goblins"]["pool_title"], "d_aov_chiefdom_01")
        self.assertIn("d_aov_warband_01 = {\n\t980.1.1 = { holder = aov_tr_masked_butcher_chief_1 "
                      "government = orcish_warband_government }", self.history)
        self.assertIn("c_gor_burad = {\n\t980.1.1 = { holder = aov_tr_moltenbrand_chief_1 "
                      "government = orcish_warband_government }", self.history)

    def test_sub_chiefs_are_vassals(self):
        tribe = self.people.tribes["amldihr_orcs"]
        self.assertEqual(set(tribe["sub_chiefs"]), {"royal_terrace_area", "common_terrace_area",
                                                    "assembly_terrace_area", "castle_hill_area"})
        pool = tribe["pool_title"]
        self.assertRegex(self.history, rf"holder = aov_tr_amldihr_orcs_royal_terrace_area_1 "
                                       rf"government = orcish_warband_government liege = {pool} \}}")

    def test_sub_chiefs_have_their_own_dynasties(self):
        """A duel only changes a realm's name and arms if the winner is of another dynasty."""
        ids = {}
        for m in re.finditer(r"(?m)^(aov_tr_\w+) = \{\n\tname = \"\w+\"\n\tdynasty = (\w+)", self.characters):
            ids[m.group(1)] = m.group(2)
        self.assertNotEqual(ids["aov_tr_amldihr_orcs_chief_1"], ids["aov_tr_amldihr_orcs_royal_terrace_area_1"])
        self.assertEqual(ids["aov_tr_amldihr_orcs_chief_1"], ids["aov_tr_amldihr_orcs_chief_2"])

    def test_no_tribe_holds_a_dwarven_title(self):
        keys = set(re.findall(r"(?m)^([dke]_\w+) = \{", self.history))
        self.assertEqual({k for k in keys if "_aov_" not in k}, set())
        self.assertLessEqual({k for k in keys}, set(bdt.pool_keys()))

    def test_every_tribe_county_is_held(self):
        area_of = ei.province_areas()
        for lay in self.lays:
            for c in lay.counties:
                tribe = dt.tribe_of(c.eu4_id, area_of.get(c.eu4_id))
                if tribe:
                    self.assertRegex(self.history, rf"(?m)^{c.key} = \{{\n\t980\.1\.1 = \{{ holder = aov_tr_", c.key)

    def test_ten_dynasties_have_flags(self):
        for slug, tribe in dt.TRIBES.items():
            if tribe.tag:
                self.assertIn(f'texture = "aov_tribe_{slug}.dds"', self.arms, slug)
                self.assertTrue((SUBMOD / f"gfx/coat_of_arms/textured_emblems/aov_tribe_{slug}.dds").is_file(), slug)
        self.assertEqual(self.arms.count("textured_emblem"), 10)
        self.assertEqual(re.findall(r"(?m)^aov_tr_dynasty_\w+", self.arms), re.findall(r"(?m)^aov_tr_dynasty_\w+", self.dynasties))
        self.assertIn('name = "dynn_aov_tr_masked_butcher"', self.dynasties)
        self.assertIn(' dynn_aov_tr_masked_butcher:0 "Masked Butcher"', bdt.render_loc())

    def test_dynasty_names_are_all_different(self):
        names = re.findall(r'name = "(\w+)"', self.dynasties)
        self.assertEqual(len(names), len(set(names)))

    def test_race_traits(self):
        for name, body in re.findall(r"(?ms)^(aov_tr_\w+) = \{\n(.*?)^\}", self.characters):
            slug = next(s for s in dt.TRIBES if name.startswith(f"aov_tr_{s}_"))
            race = dt.TRIBES[slug].race
            self.assertIn(f"trait = race_{race}", body, name)
            self.assertIn(f'culture = "{dt.CULTURE[race]}"', body, name)
            self.assertIn(f'religion = "{dt.FAITH[race]}"', body, name)

    def test_missing_area_stops(self):
        with self.assertRaisesRegex(GeneratorError, "north_altar_area"):
            bdt.check_tribes([type(lay)(**{**lay._asdict(), "counties": [c for c in lay.counties
                                                                       if c.area != "north_altar_area"]})
                              for lay in self.lays])

    def test_missing_seat_stops(self):
        with self.assertRaisesRegex(GeneratorError, "4033"):
            bdt.check_tribes([type(lay)(**{**lay._asdict(), "counties": [c for c in lay.counties if c.eu4_id != 4033]})
                              for lay in self.lays])


class AnbennarTitleOverrideTests(unittest.TestCase):
    """Test round 4: redefining a title clears its own fields, so the override repeats them, nested as in Anbennar."""

    @classmethod
    def setUpClass(cls):
        cls.text = bdt.render_title_override(bdt.ANBENNAR)
        cls.base = (bdt.ANBENNAR / "common/landed_titles/anb_landed_titles.txt").read_text(encoding="utf-8-sig")

    def test_nested_in_the_real_parent(self):
        self.assertEqual(re.findall(r"(?m)^([ekd]_\w+) = \{", self.text), ["e_middle_dwarovar"])
        self.assertEqual(set(re.findall(r"(?m)^\t(k_\w+) = \{", self.text)),
                         {"k_seghdihr", "k_hehodovar", "k_verkal_gulan", "k_gor_ozumbrog"})
        self.assertRegex(self.text, r"(?m)^\t\td_seghdihr = \{")

    def test_no_county_or_barony_is_repeated(self):
        self.assertNotRegex(self.text, r"(?m)^\s*[cb]_\w+ = \{")

    def test_own_fields_repeated(self):
        self.assertIn("color =  { 36 96 143 }", self.text)
        self.assertIn("name_list_dwarven = cn_segbandal", self.text)
        self.assertIn("capital = c_hehodovar", self.text)
        self.assertIn("color =  { 15 82 186 }", self.text)
        self.assertIn("@correct_culture_primary_score = 100", self.text)

    def test_every_title_refuses_tribes(self):
        for key, block in test_titles(self.text):
            self.assertIn("government_has_flag = government_is_dwarovar_tribe", block, key)
            if key[0] in "ke":
                self.assertIn("de_jure_drift_disabled = yes", block, key)

    def test_existing_can_create_stops(self):
        with self.assertRaisesRegex(GeneratorError, "can_create"):
            bdt.title_override_text(self.base.replace("e_middle_dwarovar = {\n",
                                                      "e_middle_dwarovar = {\n\tcan_create = { always = yes }\n", 1))


class FreshnessTests(unittest.TestCase):
    def test_written_files_are_fresh(self):
        for rel, data in bdt.build_all(lays=shared_trace.layouts()[0]).items():
            self.assertEqual((SUBMOD / rel).read_bytes(), data, rel)


if __name__ == "__main__":
    unittest.main()

"""Static checks on the Dwarven Expedition activity (RiE's mining activity for dwarf rulers).

    python -I -m unittest discover -s tools/tests -p test_dwarven_expedition.py -v
"""

import re
import sys
import unittest
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent.parent
ACTIVITY = "common/activities/activity_types/aov_dwarven_expedition.txt"
ON_ACTIONS = "common/on_action/aov_dwarven_expedition_on_actions.txt"
VALUES = "common/script_values/aov_expedition_values.txt"
EFFECTS = "common/scripted_effects/aov_expedition_effects.txt"
LOC = "localization/english/aov_dwarven_expedition_l_english.yml"
WIDGET = "gui/activity_window_widgets/aov_expedition_success_chance.gui"
FILES = (ACTIVITY, ON_ACTIONS, VALUES, EFFECTS, LOC, WIDGET)

KEY = "activity_dwarven_expedition"
TYPE_CATEGORY = "aov_expedition_type"
TYPES = ("aov_expedition_mining", "aov_expedition_archaeology")
CREW_CATEGORY = "aov_expedition_crew"
CREWS = ("aov_expedition_crew_local", "aov_expedition_crew_skilled", "aov_expedition_crew_master")
PHASE = "aov_expedition_phase"

sys.path.insert(0, str(MOD / "tools"))  # python -I does not add the tools folder
from data import rie_dwarves  # noqa: E402


def read(rel):
    return (MOD / rel).read_text(encoding="utf-8-sig")


def strip_comments(text):
    return re.sub(r"#[^\n]*", "", text)


def block(text, key):
    """Body of the first `key = { ... }` in text (comments removed), by brace matching."""
    text = strip_comments(text)
    m = re.search(rf"(?<![\w.:]){re.escape(key)} = \{{", text)
    if not m:
        raise AssertionError(f"no block {key}")
    depth, i = 1, m.end()
    while depth:
        c = text[i]
        depth += c == "{"
        depth -= c == "}"
        i += 1
    return text[m.end():i - 1]


def activity():
    return block(read(ACTIVITY), KEY)


def option(name):
    return block(block(block(activity(), "options"), TYPE_CATEGORY if name in TYPES else CREW_CATEGORY), name)


def squash(text):
    return re.sub(r"\s+", " ", text)


def loc_keys():
    return set(re.findall(r"^ ([\w.]+):\d* \"", read(LOC), re.M))


class ActivityTests(unittest.TestCase):
    def test_host_must_be_dwarf_ruler(self):
        shown = block(activity(), "is_shown")
        self.assertIn("is_dwarvish_culture = yes", shown)
        self.assertIn("highest_held_title_tier > tier_barony", shown)
        self.assertIn("is_playable_character = yes", shown)
        self.assertIn("is_available_adult = yes", block(activity(), "can_start_showing_failures_only"))
        ai = squash(block(shown, "trigger_if"))
        self.assertIn("is_ai = yes", ai)
        self.assertIn("is_at_war = no", ai)
        self.assertIn("short_term_gold >= aov_expedition_base_cost", ai)

    def test_location_is_mountain_or_dwarven(self):
        body = activity()
        self.assertIn("aov_rie_mountain_terrain_trigger = yes", block(body, "is_location_valid"))
        self.assertRegex(body, r"(?m)^\tprovince_filter = domicile_realm$")
        self.assertRegex(body, r"(?m)^\tai_province_filter = domicile_domain$")
        self.assertRegex(body, r"(?m)^\tis_single_location = yes$")
        self.assertIn("aov_rie_mountain_terrain_trigger = yes", block(body, "can_start"))

    def test_mining_needs_province_without_deposit(self):
        # A province with a deposit never gets a second one: the Mining option and location exclude it, and so
        # does a second Mining expedition already running at the same place.
        self.assertIn("NOT = { aov_rie_has_deposit_trigger = yes }", squash(block(option("aov_expedition_mining"), "is_valid")))
        location = squash(block(activity(), "is_location_valid"))
        mining = squash(block(location, "trigger_if"))
        self.assertIn("scope:special_option ?= flag:aov_expedition_mining", mining)
        self.assertIn("NOT = { aov_rie_has_deposit_trigger = yes }", mining)
        self.assertIn(f"has_activity_type = {KEY}", mining)
        self.assertIn("activity_location = prev", mining)
        # The roll effect itself also refuses a province that has a deposit (Task 3).
        self.assertIn("NOT = { aov_rie_has_deposit_trigger = yes }",
                      squash(read("common/scripted_effects/aov_rie_deposit_effects.txt")))

    def test_archaeology_needs_dwarven_terrain(self):
        valid = block(option("aov_expedition_archaeology"), "is_valid")
        self.assertEqual(set(re.findall(r"terrain = (\w+)", valid)), set(rie_dwarves.DWARVEN_TERRAINS))
        location = block(activity(), "is_location_valid")
        archaeology = block(location, "trigger_else")
        self.assertEqual(set(re.findall(r"terrain = (\w+)", archaeology)), set(rie_dwarves.DWARVEN_TERRAINS))

    def test_option_ai_prefers_mining(self):
        mining = squash(block(option("aov_expedition_mining"), "ai_will_do"))
        self.assertIn("value = 100", mining)
        self.assertIn("NOT = { aov_rie_has_deposit_trigger = yes }", mining)
        self.assertEqual(squash(block(option("aov_expedition_archaeology"), "ai_will_do")).strip(), "value = 0")

    def test_phase_schedule(self):
        phase = squash(block(block(block(activity(), "phases"), PHASE), "on_phase_active"))
        self.assertIn("is_predefined = yes", squash(block(block(activity(), "phases"), PHASE)))
        self.assertIn("progress_activity_phase_after = { months = 8 }", phase)
        self.assertEqual(sorted(re.findall(r"on_action = aov_expedition_random_pulse months = (\d+)", phase)),
                         ["2", "4", "6"])
        self.assertEqual(re.findall(r"on_action = aov_expedition_outcome months = (\d+)", phase), ["7"])
        self.assertIn("on_action = aov_expedition_start_events", phase)
        self.assertIn("is_ai = no", phase)  # AI guests get no pulse events

    def test_success_chance_formula(self):
        value = squash(block(read(VALUES), "aov_expedition_success_chance_value"))
        self.assertTrue(value.strip().startswith("value = 30"), value)
        self.assertRegex(value, r"add = \{ value = stewardship divide = 4 (ceiling = yes )?max = 10")
        self.assertRegex(value, r"option = aov_expedition_crew_skilled \} \} add = \{ value = 10")
        self.assertRegex(value, r"option = aov_expedition_crew_master \} \} add = \{ value = 20")
        self.assertRegex(value, r"aov_rie_hold_province_trigger = yes \} \} add = \{ value = 10")
        self.assertRegex(value, r"max = 90 min = 0\s*$")
        start = squash(block(activity(), "on_start"))
        self.assertIn("set_variable = { name = aov_expedition_success_chance value = aov_expedition_success_chance_value }",
                      start)

    def test_values(self):
        values = read(VALUES)
        self.assertRegex(values, r"(?m)^aov_expedition_success_minor_value = 3$")
        self.assertRegex(values, r"(?m)^aov_expedition_success_medium_value = 5$")
        self.assertRegex(values, r"(?m)^aov_expedition_success_major_value = 10$")
        self.assertRegex(values, r"(?m)^aov_expedition_cooldown_years = 4$")
        for name, amount in (("skilled", 10), ("master", 35)):
            self.assertEqual(squash(block(values, f"aov_expedition_crew_{name}_cost")).strip(),
                             f"value = {amount} multiply = activity_cost_scale_by_tier multiply = activity_cost_scale_by_era")
        base = squash(block(values, "aov_expedition_base_cost"))
        self.assertIn("value = standard_activity_base_cost multiply = activity_cost_scale_by_era", base)
        body = activity()
        self.assertIn("years = aov_expedition_cooldown_years", squash(block(body, "cooldown")))
        self.assertRegex(body, r"(?m)^\tmax_guests = 10$")
        self.assertRegex(body, r"(?m)^\tallow_zero_guest_invites = yes$")
        self.assertRegex(body, r"(?m)^\tai_check_interval = 60$")
        self.assertIn("multiply = 0.5", squash(block(option("aov_expedition_mining"), "cost")))
        self.assertIn("aov_expedition_crew_skilled_cost", block(option("aov_expedition_crew_skilled"), "cost"))
        self.assertIn("aov_expedition_crew_master_cost", block(option("aov_expedition_crew_master"), "cost"))

    def test_change_success_effect_clamps(self):
        effect = squash(block(read(EFFECTS), "aov_expedition_change_success_effect"))
        self.assertIn("add = $AMOUNT$", effect)
        self.assertIn("aov_expedition_success_chance > 90", effect)
        self.assertIn("aov_expedition_success_chance < 0", effect)

    def test_archaeology_is_a_placeholder(self):
        text = read(EFFECTS)
        self.assertRegex(text, r"(?i)placeholder")
        effect = squash(block(text, "aov_expedition_archaeology_outcome_effect"))
        self.assertIn("add_prestige", effect)
        self.assertIn("key = aov_expedition_archaeology_log", effect)
        self.assertTrue({"aov_expedition_archaeology_log", "aov_expedition_archaeology_log_title"} <= loc_keys())

    def test_activity_stays_valid_without_guests(self):
        valid = squash(block(activity(), "is_valid"))
        self.assertNotIn("has_attending_activity_guests", valid)
        for check in ("is_alive = yes", "is_imprisoned = no", "is_incapable = yes", "is_vassal_or_below_of = scope:host"):
            self.assertIn(check, valid)

    def test_on_actions_defined(self):
        text = read(ON_ACTIONS)
        for name in ("aov_expedition_start_events", "aov_expedition_random_pulse", "aov_expedition_outcome"):
            block(text, name)
        events = "".join(p.read_text(encoding="utf-8-sig") for p in sorted((MOD / "events").glob("*.txt")))
        for event in sorted(set(re.findall(r"\b(aov_expedition\.\d+)\b", strip_comments(text)))):
            self.assertRegex(events, rf"(?m)^{re.escape(event)} = \{{", event)

    def test_backgrounds(self):
        body = read(ACTIVITY)
        textures = re.findall(r'texture = "([^"]+)"', body)
        self.assertEqual(textures, [
            "gfx/interface/illustrations/event_scenes/lotr_dwarven_gate.dds",
            "gfx/interface/illustrations/event_scenes/lotr_halls.dds",
            "gfx/interface/illustrations/activity_backgrounds/lotr_cave_interior.dds",
        ])
        for texture in textures:
            self.assertTrue((MOD / texture).is_file(), texture)
        halls = squash(re.findall(r"background = \{(.*?)texture", strip_comments(body), re.S)[1])
        for check in ("aov_rie_hold_province_trigger = yes", "terrain = cavern", "terrain = dwarven_road"):
            self.assertIn(check, halls)
        self.assertIn('map_entity = "building_special_mines_entity"', body)
        self.assertIn('aov_expedition_success_chance = "activity_plugin_widgets_summary"',
                      block(activity(), "activity_window_widgets"))
        self.assertIn("'aov_expedition_success_chance'", read(WIDGET))

    def test_every_option_category_and_phase_has_loc_and_icon(self):
        keys = loc_keys()
        icons = MOD / "gfx/interface/icons"
        need = {KEY, f"{KEY}_desc", f"{KEY}_name", f"{KEY}_owner", f"{KEY}_predicted_cost", f"{KEY}_guest_desc",
                f"TRAVEL_NAME_FOR_{KEY}", f"{KEY}_selection_tooltip", f"{KEY}_destination_selection",
                f"{KEY}_guest_help_text", f"{KEY}_host_desc", f"{KEY}_province_desc", f"{KEY}_conclusion_desc",
                TYPE_CATEGORY, CREW_CATEGORY, PHASE, f"{PHASE}_desc", "aov_expedition_success_bar"}
        for name in TYPES + CREWS:
            need |= {name, f"{name}_desc"}
        self.assertEqual(sorted(need - keys), [])
        # every desc = / text = key in the script files has loc (game keys excepted)
        game = {"activity_cost_scale_by_era_desc"}
        script = strip_comments(read(ACTIVITY) + read(VALUES) + read(EFFECTS))
        used = set(re.findall(r"\b(?:desc|text) = (\w+)", script)) - game
        self.assertEqual(sorted(used - keys), [])
        for rel in (f"activities/{KEY}.dds", f"activities/{KEY}_header.dds", f"activity_phases/{PHASE}.dds",
                    f"activity_option_categories/{TYPE_CATEGORY}.dds",
                    f"activity_option_categories/{CREW_CATEGORY}.dds",
                    *(f"activity_types/{name}_icon.dds" for name in TYPES)):
            self.assertTrue((icons / rel).is_file(), rel)
        illustrations = MOD / "gfx/interface/illustrations"
        for rel in (f"activity_header_backgrounds/{KEY}.dds", *(f"activity_types/{name}.dds" for name in TYPES)):
            self.assertTrue((illustrations / rel).is_file(), rel)
        body = activity()
        self.assertRegex(body, rf"(?m)^\tspecial_option_category = {TYPE_CATEGORY}$")
        self.assertIn(PHASE, block(body, "phases"))

    def test_no_rie_branches(self):
        text = strip_comments("".join(read(rel) for rel in FILES))  # comments may cite RiE's source files
        for word in ("lotr_", "is_dwarf ", "is_dwarf=", "overseer_of_the_mines", "stone_singer", "murder", "struggle",
                     "is_landless_adventurer", "mining_type_", "can_mine_trigger", "is_elf", "activity_invite_rule_miners"):
            self.assertNotIn(word, text.replace("lotr_cave_interior", "").replace("lotr_halls", "")
                             .replace("lotr_dwarven_gate", ""), word)

    def test_file_format(self):
        for rel in FILES:
            raw = (MOD / rel).read_bytes()
            if rel.endswith((".txt", ".yml")):
                self.assertTrue(raw.startswith(b"\xef\xbb\xbf"), rel)
            self.assertNotIn(b"\r", raw, rel)
            if not rel.endswith(".yml"):  # script indented with tabs
                self.assertNotRegex(raw.decode("utf-8-sig"), r"(?m)^ ", rel)


if __name__ == "__main__":
    unittest.main()

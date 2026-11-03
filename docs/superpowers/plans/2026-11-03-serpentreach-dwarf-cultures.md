# Serpentreach Dwarf Cultures Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Five new Serpentreach dwarf cultures (cobalt, diamond, flint, garnet, basalt) with their own language, set on
every county and character of their hold's kingdom. Each gets its own tradition and clan unit. Marble gets a second
tradition (the Whitestone Council), and six duchy dynasties take EU4 names.

**Architecture:** The language and cultures are hand-written files, tested against `stone_dwarvish` in the overhaul's
generated `anb_dwarf.txt`. `build_serpentreach.py` takes a kingdom → culture map and a duchy → dynasty name map from
its data file. The clan units are hand-written beside the 11 existing ones. The traditions and game-start grants are
rows in `tools/data/racial_traditions.py`, rebuilt by `build_racial_traditions.py`.

**Tech Stack:** CK3 1.19 script (UTF-8 BOM, LF, tabs), Python 3 generators and `unittest` in `tools/`.

**Spec:** `docs/superpowers/specs/2026-11-03-serpentreach-dwarf-cultures-draft.md`

## Global Constraints

- New script and loc files: UTF-8 with BOM, LF line endings, tabs; loc files start `l_english:`.
- Never edit `../anbennar-ck3-dev-master`. Never hand-edit generated files: change `tools/data/*.py` and rerun.
- New file names carry the `aov_` prefix; culture and tradition keys are unprefixed (`cobalt_dwarvish`).
- Run Python as `python -I`; tests with `python -I -m unittest discover -s tools/tests -p "test_<name>*.py"`.
- Every culture: `heritage_dwarven`, `language_serpentreach_dwarven` (marble keeps `language_segbandalic_dwarven`),
  no `parents`, no `created`.
- Clan unit costs: role's vanilla buy and low upkeep × √(regiment damage ratio × regiment toughness ratio), high
  upkeep = 3 × low (`racial-armies.md`); `PricingTests` allows 5%.
- Validate with `python -I tools/validate.py` (new reports only). A clean pass is not proof; list what needs an
  in-game test.

## Review Focus

1. **A new culture missing the overhaul's RiE gfx keys** shows Anbennar's plain buildings, clothes and armies. Task 1's
   `test_copies_stone_dwarvish_fields` pins all three gfx lines to `stone_dwarvish`'s.
2. **A Serpentreach county still on `stone_dwarvish`**, or a character whose culture differs from their county's.
   Task 2's `test_every_county_and_character_has_its_kingdom_culture` covers counties, characters and dynasties.
3. **A renamed dynasty that still shows "az-"**, or a duplicate dynasty name. Task 2's
   `test_eu4_dynasty_names_without_prefix` checks both.
4. **A clan unit nobody can recruit** because its parameter is in no tradition, or a tradition whose unit is missing.
   Task 4's tests (the existing `test_parameters_reach_their_units`, extended through `GATED_ELSEWHERE`) cover this.
5. **Marble losing Masons of the Deep** when its grant row becomes two traditions. Task 4's
   `test_marble_keeps_masons_and_gets_whitestone` pins both.

---

### Task 1: Serpentreach Dwarven language and the five cultures

**Files:**
- Create: `common/culture/pillars/aov_serpentreach_language.txt`
- Create: `common/culture/cultures/aov_serpentreach_cultures.txt`
- Create: `localization/english/aov_serpentreach_cultures_l_english.yml`
- Test: `tools/tests/test_serpentreach_cultures.py` (new)
- Modify: `docs/systems/serpentreach.md` (Serpentreach cultures section), `CLAUDE.md` (Serpentreach row: mention the cultures)

**Interfaces:**
- Produces: culture keys `cobalt_dwarvish`, `diamond_dwarvish`, `flint_dwarvish`, `garnet_dwarvish`,
  `basalt_dwarvish`; pillar `language_serpentreach_dwarven`. Tasks 2 and 4 use these keys.

- [ ] **Step 1: Write the failing tests** in `tools/tests/test_serpentreach_cultures.py`. Copy the module setup
  (path insert, `parse_blocks`, `strip_comments`, `SUBMOD`) from `test_elven_cultures.py`.

```python
CULTURES = {  # key -> (color, ethos, traditions in file order)
    "cobalt_dwarvish": ("0 71 171", "ethos_bureaucratic",
                        ("tradition_mountain_homes", "tradition_philosopher_culture", "tradition_music_theory")),
    "diamond_dwarvish": ("185 225 240", "ethos_courtly",
                         ("tradition_mountain_homes", "tradition_ancient_miners", "tradition_hereditary_hierarchy")),
    "flint_dwarvish": ("55 144 90", "ethos_spiritual",
                       ("tradition_mountain_homes", "tradition_forest_fighters", "tradition_medicinal_plants")),
    "garnet_dwarvish": ("247 179 215", "ethos_communal",
                        ("tradition_mountain_homes", "tradition_wedding_ceremonies",
                         "tradition_distinguished_winemakers")),
    "basalt_dwarvish": ("240 72 72", "ethos_bellicose",
                        ("tradition_mountain_homes", "tradition_stand_and_fight", "tradition_metal_craftsmanship")),
}
DLC_ARTISANS = ("cobalt_dwarvish", "diamond_dwarvish")  # dlc_tradition artisans / royal_court, as stone_dwarvish
COPIED = ("heritage", "martial_custom", "head_determination", "name_list", "coa_gfx", "building_gfx",
          "clothing_gfx", "unit_gfx", "ethnicities")  # equal to stone_dwarvish in the overhaul's anb_dwarf.txt
```

  Tests:
  - `test_files_have_bom_and_lf`: the three new files.
  - `test_language_pillar`: the block `language_serpentreach_dwarven` has `type = language`, and its `is_shown` calls
    `language_is_shown_trigger` with `LANGUAGE = language_serpentreach_dwarven`. Its `ai_will_do` matches
    `language_segbandalic_dwarven`'s in Anbennar's `anb_language.txt` with the key swapped (squashed compare).
  - `test_cultures_have_spec_fields`: the culture file defines exactly `CULTURES`. For each culture, `color` and
    `ethos` match, the `traditions` keys equal the tuple in order, and `language = language_serpentreach_dwarven`.
    It has no `parents` and no `created`. `dlc_tradition` is `trait = tradition_artisans` with
    `requires_dlc_flag = royal_court` for `DLC_ARTISANS` and absent for the others.
  - `test_copies_stone_dwarvish_fields`: every field in `COPIED` (squashed) equals `stone_dwarvish`'s in
    `common/culture/cultures/anb_dwarf.txt` of this mod.
  - `test_colors_distinct`: no colour equals another new culture's or any culture's in this mod's `anb_dwarf.txt`.
  - `test_localization_complete`: for each culture `<key>`, `<key>_prefix` and `<key>_collective_noun`, and
    `language_serpentreach_dwarven_name`.

- [ ] **Step 2: Run the tests to make sure they fail**

  Run: `python -I -m unittest discover -s tools/tests -p "test_serpentreach_cultures*.py"`
  Expected: errors, because the culture file does not exist.

- [ ] **Step 3: Write the three files**
  - The pillar: copy Anbennar's `language_segbandalic_dwarven` block with the key replaced and
    `color = { 176 120 64 }`. Add a `# Anbennar Overhaul: Serpentreach cultures (docs/systems/serpentreach.md)` header.
  - The cultures: same layout as `stone_dwarvish`, with the `COPIED` lines copied from the overhaul's
    `anb_dwarf.txt` (they keep their `# Anbennar Overhaul` comments). Put a one-line comment on each tradition naming
    the EU4 idea from the spec table (Guntîrhug, Glass and Trumpets, clast shafts, …).
  - Loc: `Cobalt Dwarven` / `Cobalt Dwarf` / `Cobalt Dwarves` (Anbennar's style, as `marble_dwarvish`), and likewise
    for the others; `language_serpentreach_dwarven_name:0 "Serpentreach Dwarven"`.

- [ ] **Step 4: Run the tests to make sure they pass**

  Run: the command from Step 2. Expected: `OK`.

- [ ] **Step 5: Document.** In `docs/systems/serpentreach.md`, add a "Cultures" bullet: the five cultures, their file,
  language and per-kingdom placement (Task 2), marble unchanged in Anbennar. Point to the spec for the rationale.
  Mention the cultures in the CLAUDE.md Serpentreach row.

- [ ] **Step 6: Commit**

```bash
git add common/culture/pillars/aov_serpentreach_language.txt common/culture/cultures/aov_serpentreach_cultures.txt localization/english/aov_serpentreach_cultures_l_english.yml tools/tests/test_serpentreach_cultures.py docs/systems/serpentreach.md CLAUDE.md docs/superpowers/specs/2026-11-03-serpentreach-dwarf-cultures-draft.md docs/superpowers/plans/2026-11-03-serpentreach-dwarf-cultures.md
git commit -m "Serpentreach: five dwarf cultures and the Serpentreach Dwarven language"
```

### Task 2: Kingdom cultures and EU4 dynasty names in the Serpentreach build

**Files:**
- Modify: `tools/data/serpentreach.py:101` (replace `CULTURE`)
- Modify: `tools/build_serpentreach.py` (`Realm`, `render_province_history`, `People`, `render_dynasties`, `render_characters`)
- Test: `tools/tests/test_serpentreach.py` (`BuildTests`)
- Regenerate: the Serpentreach generated files (`docs/systems/serpentreach.md` table)
- Modify: `docs/systems/serpentreach.md` ("People" bullet)

**Interfaces:**
- Consumes: the five culture keys from Task 1, plus `marble_dwarvish`.
- Produces: `data.KINGDOM_CULTURES: dict[str, str]` (kingdom → culture);
  `data.DYNASTY_NAMES: dict[str, str]` (duchy → display name, shown with no prefix);
  `Realm.culture_of(dkey: str) -> str` (the culture of a duchy's kingdom).

- [ ] **Step 1: Write the failing tests** in `BuildTests`:

```python
    def test_every_county_and_character_has_its_kingdom_culture(self):
        import re
        from data import serpentreach as data
        self.assertEqual(data.KINGDOM_CULTURES, {
            "k_orlghelovar": "cobalt_dwarvish", "k_shazstundihr": "marble_dwarvish",
            "k_arg_ordstun": "diamond_dwarvish", "k_verkal_skomdihr": "flint_dwarvish",
            "k_ovdal_lodhum": "garnet_dwarvish", "k_gor_burad": "basalt_dwarvish"})
        history = self.files["history/provinces/aov_serpentreach.txt"].decode("utf-8-sig")
        self.assertNotIn("stone_dwarvish", history)
        titles = self.files["common/landed_titles/aov_serpentreach.txt"].decode("utf-8-sig")
        for block in re.split(r"(?m)^\t(?=k_)", titles)[1:]:
            kkey = block.split(" ", 1)[0]
            for pid in re.findall(r"province = (\d+)", block):
                self.assertRegex(history, rf"(?m)^{pid} = \{{\t# .*\n\tculture = {data.KINGDOM_CULTURES[kkey]}\n")
        characters = self.files["history/characters/aov_serpentreach.txt"].decode("utf-8-sig")
        self.assertIn('aov_sr_emperor_1 = {', characters)
        self.assertRegex(characters, r'aov_sr_emperor_1 = \{[^}]*culture = "diamond_dwarvish"')
        self.assertRegex(characters, r'aov_sr_zarn_1 = \{[^}]*culture = "basalt_dwarvish"')
        dynasties = self.files[self.bs.DYNASTIES].decode("utf-8-sig")
        self.assertRegex(dynasties, r"aov_dynasty_still_caverns = \{[^}]*culture = garnet_dwarvish")
```

```python
    def test_eu4_dynasty_names_without_prefix(self):
        import re
        want = {"d_arg_ordstun": "Whiteforged", "d_kings_caverns": "Stormheart", "d_ovdal_lodhum": "Garnetpick",
                "d_still_caverns": "Slatecutter", "d_shazstundihr": "Whitebeard", "d_south_altar": "Brightbeard"}
        dynasties = self.files[self.bs.DYNASTIES].decode("utf-8-sig")
        loc = self.files["localization/english/aov_serpentreach_l_english.yml"].decode("utf-8-sig")
        for dkey, name in want.items():
            block = re.search(rf"(?ms)^aov_dynasty_{dkey[2:]} = \{{.*?^\}}", dynasties).group(0)
            self.assertNotIn("prefix", block, dkey)
            self.assertIn(f' dynn_aov_{dkey[2:]}:0 "{name}"', loc)
        self.assertEqual(dynasties.count('prefix = "dynnp_az"'), 19 - len(want))
        names = re.findall(r'(?m)^ dynn_aov_\w+:0 "([^"]*)"', loc)
        self.assertEqual(len(names), len(set(names)))
```

  `OutputTests`: `test_kingdom_cultures_must_cover_every_kingdom`. Patch `data.KINGDOM_CULTURES` without
  `k_gor_burad`, and building the `Realm` raises `GeneratorError` mentioning `KINGDOM_CULTURES`. Do the same for a
  `DYNASTY_NAMES` key that is not a duchy.

- [ ] **Step 2: Run them to make sure they fail**

  Run: `python -I -m unittest discover -s tools/tests -p "test_serpentreach*.py"`
  Expected: the new tests fail (`KINGDOM_CULTURES` is missing, and the history has `stone_dwarvish`).

- [ ] **Step 3: Implement.**
  - In `tools/data/serpentreach.py`, replace `CULTURE` with `KINGDOM_CULTURES` (the test's dict, with a comment: the
    EU4 hold cultures, spec link) and `DYNASTY_NAMES` (the test's `want`; comment: EU4 1444 rulers H76 Whiteforged and
    H77 Garnetpick, the rest from EU4 culture dynasty lists).
  - In `Realm.__init__`, extend the table check loop so `KINGDOM_CULTURES` must list exactly the kingdoms. Check that
    every `DYNASTY_NAMES` key is a duchy, else raise `GeneratorError`. Add `culture_of(dkey)`.
  - In `render_province_history`, write `realm.culture_of(realm.duchy_of[c.key])`.
  - In `People`, store each line's `culture`. Its `dyn_name` is `DYNASTY_NAMES.get(dkey)` when set, else today's
    rule. Add the EU4 names to `used` first, so a generated name never repeats one.
  - In `render_dynasties`, use the line's culture and omit the `prefix` line for `DYNASTY_NAMES` duchies; in
    `render_characters`, use the line's culture.

- [ ] **Step 4: Regenerate and run the tests**

  Run: `python -I tools/build_serpentreach.py`, then
  `python -I -m unittest discover -s tools/tests -p "test_serpentreach*.py"`. Expected: `OK`.
  Then run `python -I -m unittest discover -s tools/tests -p "test_build_holds*.py"` and
  `... -p "test_build_map_graphics*.py"`. Expected: `OK`, since they read nothing that changed. If one is stale, rerun
  that generator as `docs/systems/updating.md` says.

- [ ] **Step 5: Document.** Rewrite the "People" bullet of `serpentreach.md`: each kingdom's hold culture
  (`KINGDOM_CULTURES`), and the six EU4 dynasty names with no prefix.

- [ ] **Step 6: Commit**

```bash
git add tools/data/serpentreach.py tools/build_serpentreach.py tools/tests/test_serpentreach.py history/ common/dynasties/aov_serpentreach_dynasties.txt localization/english/aov_serpentreach_l_english.yml docs/systems/serpentreach.md
git commit -m "Serpentreach: hold cultures per kingdom, EU4 dynasty names"
```

### Task 3: Five clan units

**Files:**
- Modify: `common/men_at_arms_types/aov_dwarven_maa_types.txt` (append under `### Clan signature units`)
- Modify: `common/script_values/aov_racial_maa_values.txt`
- Modify: `localization/english/aov_racial_armies_l_english.yml`
- Copy (once, from RiE `gfx/interface/{icons/regimenttypes,illustrations/men_at_arms_big,illustrations/men_at_arms_small}/<art>.dds`): `aov_rie_<art>.dds` into the same three folders of this mod
- Test: `tools/tests/test_racial_armies.py` (`ROSTER`, `EXPECTED`, `DWARF_EXTRA`, `test_signature_counters`)
- Modify: `docs/systems/racial-armies.md` (Dwarf clans row; art table)

**Interfaces:**
- Produces: units, each gated by `valid_for_maa_trigger = { PARAMETER = aov_unlock_maa_<key without aov_> }`. Task 4
  sets these parameters.

| Unit key | Name | Type (pricing role) | Men | Dmg/tough per man | Pursuit/screen | Counters | Extra terrain | Buy / low / high | RiE art |
|---|---|---|---|---|---|---|---|---|---|
| `aov_lens_crossbows` | Lens Crossbows | archers (crossbow) | 80 | 70/32 | 0/0 | heavy_infantry 1, heavy_cavalry 1, archer_cavalry 0.5 | none | 121 / 0.41 / 1.23 | `ironfist_crossbowmen` |
| `aov_lightflare_guard` | Lightflare Guard | heavy_infantry | 50 | 75/150 | 0/0 | pikemen 1, peasant_militia 2 | cavern 1.0 | 180 / 0.8 / 2.4 | `broadbeam_heavy_infantry` |
| `aov_flint_forest_rangers` | Flint Forest Rangers | skirmishers | 80 | 32/45 | 0/0 | heavy_infantry 1 | forest 0.5, taiga 0.5 | 108 / 0.36 / 1.08 | `stiffbeard_skirmishers` |
| `aov_orcrend_guard` | Orcrend Guard | pikemen | 80 | 42/62 | 0/0 | light_cavalry 1, heavy_cavalry 1, camel_cavalry 1, elephant_cavalry 1 | none | 133 / 0.53 / 1.59 | `broadbeam_pikemen` |
| `aov_basalt_berserkers` | Basalt Berserkers | heavy_infantry | 50 | 130/55 | 0/0 | pikemen 1, skirmishers 1 | none | 143 / 0.64 / 1.92 | `firebeard_heavy_infantry` |

Terrain bonus = `DWARF_TERRAIN` (with `DWARF_EXTRA` replacing a key) × the per-man damage and toughness, rounded, as
`aov_brightbeard_hammers` does. Flavor text (`#F …#!`) comes from the spec's EU4 ideas:
- Lens Crossbows: Guntîrhug lenses and cobalt-glass sights.
- Lightflare Guard: diamond-studded armour that blinds cave ambushers.
- Flint Forest Rangers: wardens of the Deepwoods, and the first handheld flintlocks.
- Orcrend Guard: Gerin Orcrend's doctrine against the orcs.
- Basalt Berserkers: the berserker rage and the Borbordûz fire duel.
Every unit has `ai_quality = { value = @cultural_maa_extra_ai_score }` and `allowed_in_hired_troops = no`.

- [ ] **Step 1: Write the failing tests.** Add the five rows to `ROSTER` (role, men, dmg, tough) and to `EXPECTED`
  (type, men, dmg, tough, pursuit, screen, `"PARAM:aov_unlock_maa_<…>"`). Add `DWARF_EXTRA` rows for
  `aov_lightflare_guard` and `aov_flint_forest_rangers`. Add to `test_signature_counters`:
  `"aov_lightflare_guard": {"peasant_militia": "2"}, "aov_basalt_berserkers": {"skirmishers": "1"},
  "aov_orcrend_guard": {"camel_cavalry": "1"}`. Add `test_clan_unit_art_copied`: for each of the five, its `icon`
  file exists in all three art folders.

- [ ] **Step 2: Run them to make sure they fail**

  Run: `python -I -m unittest discover -s tools/tests -p "test_racial_armies*.py"`
  Expected: failures naming the five new keys.

- [ ] **Step 3: Implement.** Copy the 15 art files. Write the five unit blocks after `aov_brightbeard_hammers`,
  shaped like it. Add the 15 cost values from the table, and the name and flavor loc.

- [ ] **Step 4: Run the tests to make sure they pass**

  Run: the command from Step 2. Expected: `OK`.

- [ ] **Step 5: Document.** In `racial-armies.md`, add the five units to the "Dwarf clans" row. Add art rows: the
  Ironfist, Broadbeam, Stiffbeard and Firebeard sets are used only by the Serpentreach clans, unlike every other dwarf
  unit, which uses Longbeard.

- [ ] **Step 6: Commit**

```bash
git add common/men_at_arms_types/aov_dwarven_maa_types.txt common/script_values/aov_racial_maa_values.txt localization/english/aov_racial_armies_l_english.yml gfx/interface/icons/regimenttypes gfx/interface/illustrations tools/tests/test_racial_armies.py docs/systems/racial-armies.md
git commit -m "Racial armies: five Serpentreach clan units"
```

### Task 4: Six traditions and their game-start grants

**Files:**
- Modify: `tools/data/racial_traditions.py` (`TRADITIONS` dwarf section, `GRANTS`)
- Regenerate: `build_racial_traditions.py` outputs, then `build_racial_levies.py`
- Test: `tools/tests/test_build_racial_traditions.py` (`GATED_ELSEWHERE`, grants)
- Modify: `docs/systems/racial-traditions.md` (Traditions table, intro count)

**Interfaces:**
- Consumes: Task 1's culture keys; Task 3's unit parameters.

| Tradition key | Name | Gate | Category | Layers | Character / county | Parameter |
|---|---|---|---|---|---|---|
| `tradition_glasslords` | The Glasslords | cobalt_dwarvish | societal | learning, western, philosopher.dds | `domain_tax_mult` 0.1, `learning` 1; county `development_growth_factor` 0.1 | `aov_unlock_maa_lens_crossbows` |
| `tradition_aegis_of_the_serpentreach` | The Aegis of the Serpentreach | diamond_dwarvish | realm | diplo, western, king.dds | `monthly_prestige_gain_mult` 0.1, `diplomacy` 1, `vassal_opinion` 5 | `aov_unlock_maa_lightflare_guard` |
| `tradition_warding_gate` | The Warding Gate | flint_dwarvish | combat | martial, western, runestone.dds | `defender_advantage` 4, `enemy_hostile_scheme_success_chance_add` −10, `hostile_county_attrition` 0.1 | `aov_unlock_maa_flint_forest_rangers` |
| `tradition_hold_where_love_lives` | The Hold Where Love Lives | garnet_dwarvish | societal | diplo, western, ceremony.dds | `fertility` 0.15, `spouse_opinion` 15; county `county_opinion_add` 5 | `aov_unlock_maa_orcrend_guard` |
| `tradition_hearts_of_fire` | Hearts of Fire | basalt_dwarvish | combat | martial, western, fight.dds | `prowess` 2, `heavy_infantry_damage_mult` 0.15, `hostile_county_attrition` 0.1 | `aov_unlock_maa_basalt_berserkers` |
| `tradition_whitestone_council` | The Whitestone Council | marble_dwarvish | realm | diplo, western, council.dds | `powerful_vassal_opinion` 10, `councillor_opinion` 10, `monthly_piety_gain_mult` 0.1 | none |

`heritage="heritage_dwarven"`, `gate=culture(<key>)`, and an `eu4=` naming the ideas from the spec. Each `desc` is
two sentences of EU4 lore, with no Realms in Exile words: *Hearts of Fire* names Borbordûz, and *The Warding Gate*
names Kekig's labyrinth.

- [ ] **Step 1: Write the failing tests.** Add the five unit parameters to `GATED_ELSEWHERE` (`aov_dwarven_maa_types.txt`).
  Add `test_marble_keeps_masons_and_gets_whitestone`:
  `data.GRANTS["marble_dwarvish"] == ("tradition_masons_of_the_deep", "tradition_whitestone_council")`. Add
  `test_serpentreach_cultures_granted`: each of the five cultures is granted exactly its tradition from the table.

  Every modifier key in the table appears in the game's `common/` (checked 2026-11-03: `spouse_opinion` 38 uses,
  `fertility` 146, `heavy_infantry_damage_mult` 35, `vassal_opinion` 145, and so on), or is already used in
  `racial_traditions.py`.

- [ ] **Step 2: Run the tests to make sure they fail**

  Run: `python -I -m unittest discover -s tools/tests -p "test_build_racial_traditions*.py"`
  Expected: failures, because the grants are missing.

- [ ] **Step 3: Implement.** Add the six `TRADITIONS` entries after `tradition_masons_of_the_deep`. Add five `GRANTS`
  rows, and make marble's row the pair. Run `python -I tools/build_racial_traditions.py`.

- [ ] **Step 4: Run the tests to make sure they pass**

  Run: `... -p "test_build_racial_traditions*.py"`, `... -p "test_racial_armies*.py"`, and
  `... -p "test_build_racial_levies*.py"`. Expected: `OK`. No new tradition has a levy modifier, so the levies stay
  fresh. If `FreshnessTests` says otherwise, run `python -I tools/build_racial_levies.py` and add its four outputs
  (`racial-armies.md`) to the commit.

- [ ] **Step 5: Document.** In `racial-traditions.md`, add the six rows to the Traditions table. Update the intro and
  the CLAUDE.md Racial traditions row: 40 traditions, and the five new clans. The "17 units" count covers only
  `UNITS`, so it stays.

- [ ] **Step 6: Commit**

```bash
git add tools/data/racial_traditions.py tools/tests/test_build_racial_traditions.py common/culture/traditions/aov_racial_traditions.txt common/scripted_effects/aov_racial_traditions_effects.txt localization/english/aov_racial_traditions_l_english.yml docs/systems/racial-traditions.md CLAUDE.md
git commit -m "Racial traditions: Serpentreach clan traditions and the Whitestone Council"
```

### Task 5: Validation and in-game checklist

**Files:**
- Modify: `docs/systems/serpentreach.md` ("Needs an in-game test")

- [ ] **Step 1: Run all tool tests**

  Run: `python -I -m unittest discover -s tools/tests`. Expected: `OK`.

- [ ] **Step 2: Run tiger**

  Run: `python -I tools/validate.py`. Expected: no new report naming the new files or keys. Fix any that do. Do not
  baseline them.

- [ ] **Step 3: Write the in-game checklist** in `serpentreach.md`:
  1. Each Serpentreach kingdom's counties show its hold culture, and the culture window shows Serpentreach Dwarven.
  2. Rulers' dynasties read Whiteforged, Garnetpick and so on, with no "az-".
  3. The cultures have their base and clan traditions at game start, and Marble has both of its own.
  4. Each clan unit can be recruited by its culture only, and shows its RiE art.
  5. Dwarven buildings, clothes and armies use the RiE assets.

- [ ] **Step 4: Commit**

```bash
git add docs/systems/serpentreach.md
git commit -m "Serpentreach cultures: validation notes and in-game checklist"
```

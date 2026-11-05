# West Dwarovar Dwarf Cultures Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eight West Dwarovar dwarf cultures with their own language replace the `silver_dwarvish` stand-in. Each gets
its own tradition, seven get a clan unit, and ten duchy dynasties take EU4 names.

**Architecture:** The language and cultures are hand-written files, tested against `stone_dwarvish` in the overhaul's
generated `anb_dwarf.txt`. `build_west_dwarovar.py` already reads `KINGDOM_CULTURES` and `DYNASTY_NAMES` from its data
file, so only that data changes. The clan units are hand-written beside the existing ones. The traditions and
game-start grants are rows in `tools/data/racial_traditions.py`, rebuilt by `build_racial_traditions.py`.

**Tech Stack:** CK3 1.19 script (UTF-8 BOM, LF, tabs), Python 3 generators and `unittest` in `tools/`.

**Spec:** `docs/superpowers/specs/2026-11-05-west-dwarovar-dwarf-cultures-design.md`. Its tables hold every unit stat,
cost, modifier and art source. Read it with this plan; this plan does not repeat what the spec pins unless a test needs
it.

## Global Constraints

- Work on a branch `west-dwarovar-cultures` cut from `main`. Merging or pushing is a separate decision for the user.
- New script and loc files: UTF-8 with BOM, LF line endings, tabs; loc files start `l_english:`.
- Never edit `../anbennar-ck3-dev-master`. Never hand-edit generated files: change `tools/data/*.py` and rerun.
- New file names carry the `aov_` prefix; culture and tradition keys are unprefixed (`kronium_dwarvish`).
- Run Python as `python -I`; tests with `python -I -m unittest discover -s tools/tests -p "test_<name>*.py"`.
- Every culture: `heritage_dwarven`, `language_west_dwarovar_dwarven`, no `parents`, no `created`.
- Unit costs are the spec's table. `PricingTests` allows 5%; high upkeep is exactly 3 × low.
- Tests that build West Dwarovar take minutes. Run them with a 10-minute timeout, in the background if needed.
- Validate with `python -I tools/validate.py` (new reports only). A clean pass is not proof; list what needs an
  in-game test. Never baseline a report from these keys.

## Review Focus

1. **A West Dwarovar county, character or dynasty still on `silver_dwarvish`**, or a character whose culture differs
   from their county's. Task 2's `test_every_county_and_character_has_its_kingdom_culture` covers all three.
2. **Khugdihr losing its kobolds** when the stand-in map becomes explicit. The same test pins
   `"k_khugdihr": "darkscale"`, and the existing `test_khugdihr_untouched` still runs.
3. **A new culture missing the overhaul's RiE gfx keys**, which would show Anbennar's plain buildings, clothes and
   armies. Task 1's `test_copies_stone_dwarvish_fields` pins them to `stone_dwarvish`'s.
4. **A mixed-art unit showing the wrong picture, or a non-square icon drawn stretched or clipped**. The game finds
   pictures by icon name, so a wrong copy looks fine in tests that only check existence. Task 3's
   `test_west_dwarovar_art_sources` and `test_west_dwarovar_icons_are_120_square` pin both.
5. **A renamed dynasty still showing "az-", or a duplicate dynasty name**. Task 2's
   `test_eu4_dynasty_names_without_prefix` checks both.

---

### Task 1: West Dwarovar Dwarven language and the eight cultures

**Files:**
- Create: `common/culture/pillars/aov_west_dwarovar_language.txt`
- Create: `common/culture/cultures/aov_west_dwarovar_cultures.txt`
- Create: `localization/english/aov_west_dwarovar_cultures_l_english.yml`
- Test: `tools/tests/test_west_dwarovar_cultures.py` (new)

**Interfaces:**
- Produces: culture keys `kronium_dwarvish`, `platinum_dwarvish`, `mithril_dwarvish`, `dagrite_dwarvish`,
  `opal_dwarvish`, `lead_dwarvish`, `ramsteel_dwarvish`, `sapphire_dwarvish`; pillar
  `language_west_dwarovar_dwarven`. Tasks 2 and 4 use these keys.

- [ ] **Step 1: Write the failing tests.** Model the module on `tools/tests/test_serpentreach_cultures.py` (same
  imports, `FileTests`, `LanguageTests`, `CultureTests`, `LocalizationTests`, with the new file paths, and
  `LANGUAGE = "language_west_dwarovar_dwarven"`). Use these tables:

```python
CULTURES = {  # key -> (color, ethos, traditions in file order)
    "kronium_dwarvish": ("60 40 80", "ethos_bureaucratic",
                         ("tradition_mountain_homes", "tradition_legalistic", "tradition_agrarian")),
    "platinum_dwarvish": ("74 80 97", "ethos_courtly",
                          ("tradition_mountain_homes", "tradition_ruling_caste", "tradition_castle_keepers")),
    "mithril_dwarvish": ("81 231 213", "ethos_stoic",
                         ("tradition_mountain_homes", "tradition_loyal_soldiers", "tradition_storytellers")),
    "dagrite_dwarvish": ("147 191 155", "ethos_egalitarian",
                         ("tradition_mountain_homes", "tradition_caravaneers", "tradition_swords_for_hire")),
    "opal_dwarvish": ("255 228 216", "ethos_spiritual",
                      ("tradition_mountain_homes", "tradition_battlefield_looters", "tradition_life_is_just_a_joke")),
    "lead_dwarvish": ("160 114 158", "ethos_communal",
                      ("tradition_mountain_homes", "tradition_city_keepers", "tradition_sorcerous_metallurgy")),
    "ramsteel_dwarvish": ("74 111 121", "ethos_bellicose",
                          ("tradition_mountain_homes", "tradition_horse_breeder", "tradition_culinary_art")),
    "sapphire_dwarvish": ("0 25 119", "ethos_bureaucratic",
                          ("tradition_mountain_homes", "tradition_philosopher_culture", "tradition_astute_diplomats")),
}
DLC_ARTISANS = ("platinum_dwarvish",)
```

  In `test_colors_distinct`, also compare against the colours in `aov_serpentreach_cultures.txt`. In
  `test_localization_complete`, require `language_west_dwarovar_dwarven_name:0 "West Dwarovar Dwarven"` and the display
  names `"Kronium Dwarven"`, `"Kronium Dwarf"`, `"Kronium Dwarves"` (and likewise for each culture).

- [ ] **Step 2: Run the tests to make sure they fail**

  Run: `python -I -m unittest discover -s tools/tests -p "test_west_dwarovar_cultures*.py"`
  Expected: errors, because the culture file does not exist.

- [ ] **Step 3: Write the three files.**
  - Pillar: `language_serpentreach_dwarven`'s block with the key replaced and `color = { 96 72 128 }`, plus a
    `# Anbennar Overhaul: West Dwarovar cultures (docs/systems/west-dwarovar.md)` header.
  - Cultures: same layout as `aov_serpentreach_cultures.txt`, with its `COPIED` lines unchanged. Comment each culture
    with its hold, and each tradition with its EU4 idea from the spec's source table.
  - Loc: the names from Step 1 and the language name.

- [ ] **Step 4: Run the tests to make sure they pass**

  Run: the command from Step 2. Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add common/culture/pillars/aov_west_dwarovar_language.txt common/culture/cultures/aov_west_dwarovar_cultures.txt localization/english/aov_west_dwarovar_cultures_l_english.yml tools/tests/test_west_dwarovar_cultures.py docs/superpowers/specs/2026-11-05-west-dwarovar-dwarf-cultures-design.md docs/superpowers/plans/2026-11-05-west-dwarovar-dwarf-cultures.md
git commit -m "West Dwarovar: eight dwarf cultures and the West Dwarovar Dwarven language"
```

### Task 2: Kingdom cultures and EU4 dynasty names

**Files:**
- Modify: `tools/data/west_dwarovar.py:107-111` (`KINGDOM_CULTURES`) and `:119` (`DYNASTY_NAMES`)
- Test: `tools/tests/test_west_dwarovar.py`
- Regenerate: `python -I tools/build_west_dwarovar.py` (`history/provinces`, `history/characters`, `common/dynasties`,
  `localization/english/aov_west_dwarovar_l_english.yml`)

**Interfaces:**
- Consumes: the culture keys from Task 1. `Realm` already requires `KINGDOM_CULTURES` to list exactly the kingdoms and
  `DYNASTY_NAMES` keys to be duchies. `People` already drops the `az` prefix for a `DYNASTY_NAMES` duchy. No generator
  code changes.

- [ ] **Step 1: Write the failing tests.** Change the regex at `test_west_dwarovar.py:343` to
  `culture = kronium_dwarvish`, because the Vale's terraces are all in `k_amldihr`. Add to the same class (the one
  with `test_khugdihr_untouched`):

```python
    def test_every_county_and_character_has_its_kingdom_culture(self):
        want = {"k_khugdihr": "darkscale", "k_amldihr": "kronium_dwarvish", "k_haraz_orldhum": "platinum_dwarvish",
                "k_mithradhum": "mithril_dwarvish", "k_er_natvir": "dagrite_dwarvish",
                "k_verkal_kozenad": "opal_dwarvish", "k_hul_jorkad": "lead_dwarvish",
                "k_orlazam_az_dihr": "ramsteel_dwarvish", "k_dur_vazhatun": "sapphire_dwarvish"}
        self.assertEqual(data.KINGDOM_CULTURES, want)
        characters = self.files[self.bwd.CHARACTERS].decode("utf-8-sig")
        dynasties = self.files[self.bwd.DYNASTIES].decode("utf-8-sig")
        for text in (self.provinces, characters, dynasties):
            self.assertNotIn("silver_dwarvish", text)
        for kkey, (_, kareas) in data.KINGDOMS.items():
            for c in (c for c in self.lay.counties if c.area in kareas):
                for pid in c.baronies:
                    self.assertRegex(self.provinces, rf"(?m)^{pid} = \{{\t# .*\n\tculture = {want[kkey]}\n")
        self.assertRegex(characters, r'aov_wd_emperor_1 = \{[^}]*culture = "kronium_dwarvish"')
        self.assertRegex(characters, r'aov_wd_orlazam_1 = \{[^}]*culture = "ramsteel_dwarvish"')
        self.assertRegex(dynasties, r"aov_wd_dynasty_riftway = \{[^}]*culture = mithril_dwarvish")

    def test_eu4_dynasty_names_without_prefix(self):
        want = {"d_mithradhum": "Strongbellow", "d_riftway": "Goldbeard", "d_dwarovrod_7_9": "Goblinslayer",
                "d_the_railyard": "Ironhelm", "d_stunad_kozenad": "Forktongue", "d_zokkorna_caverns": "Ringbeard",
                "d_westnest": "Kezdori", "d_jorkad_junction": "Leadpipe", "d_orlazam": "Fourfoot",
                "d_vazhatun": "Melmarn"}
        self.assertEqual(data.DYNASTY_NAMES, want)
        dynasties = self.files[self.bwd.DYNASTIES].decode("utf-8-sig")
        loc = self.files[self.bwd.LOC].decode("utf-8-sig")
        for dkey, name in want.items():
            block = re.search(rf"(?ms)^aov_wd_dynasty_{dkey[2:]} = \{{.*?^\}}", dynasties).group(0)
            self.assertNotIn("prefix", block, dkey)
            self.assertIn(f' dynn_aov_wd_{dkey[2:]}:0 "{name}"', loc)
        self.assertEqual(dynasties.count('prefix = "dynnp_az"'), 35 - len(want))
        names = re.findall(r'(?m)^ dynn_aov_wd_\w+:0 "([^"]*)"', loc)
        self.assertEqual(len(names), len(set(names)))
```

- [ ] **Step 2: Run them to make sure they fail**

  Run: `python -I -m unittest discover -s tools/tests -p "test_west_dwarovar.py"`
  Expected: the changed test and both new tests fail, because the data and files are still on `silver_dwarvish`.

- [ ] **Step 3: Implement.** In `tools/data/west_dwarovar.py`, replace the stand-in comment and map with the test's
  `want` dict, with a comment naming the spec. Set `DYNASTY_NAMES` to the second test's `want`, with a comment:
  Forktongue and Leadpipe are from EU4's culture lists, and the rest are figures in each hold's idea texts. Run
  `python -I tools/build_west_dwarovar.py`.

- [ ] **Step 4: Run the tests to make sure they pass**

  Run: the command from Step 2, then `python -I -m unittest discover -s tools/tests -p "test_build_holds*.py"`.
  Expected: `OK`. If a `FreshnessTests` reports another generator stale, rerun it as `docs/systems/updating.md` says and
  add its files to the commit.

- [ ] **Step 5: Commit**

```bash
git add tools/data/west_dwarovar.py tools/tests/test_west_dwarovar.py history/provinces/aov_west_dwarovar.txt history/characters/aov_west_dwarovar.txt common/dynasties/aov_west_dwarovar_dynasties.txt localization/english/aov_west_dwarovar_l_english.yml
git commit -m "West Dwarovar: hold cultures per kingdom, EU4 dynasty names"
```

### Task 3: Seven clan units

**Files:**
- Modify: `common/men_at_arms_types/aov_dwarven_maa_types.txt` (a new `### West Dwarovar clans` section after
  `aov_basalt_berserkers`, before the `# Silver dwarves` block at line 543)
- Modify: `common/script_values/aov_racial_maa_values.txt` (a `# West Dwarovar clans` section after line 122)
- Modify: `localization/english/aov_racial_armies_l_english.yml` (after line 52)
- Copy: 18 art files (Step 3)
- Test: `tools/tests/test_racial_armies.py`

**Interfaces:**
- Produces: seven units, each gated by `valid_for_maa_trigger = { PARAMETER = aov_unlock_maa_<key without aov_> }`.
  Task 4 sets these parameters.

Unit stats, terrain extras, costs and art are the spec's tables. Shape each block like `aov_basalt_berserkers`. Counters:
heavy infantry `pikemen = 1`; skirmishers `heavy_infantry = 1`; heavy cavalry `archers = 1` and `gunpowder = 1`.

Flavor text is `#F …#!`, in our own words:

| Unit | What the flavor says |
|---|---|
| Amldavhad Guard | The clanless Shields of the Assembly, sworn to no clan so they cannot be turned in its plots |
| Platinum Warsuits | Armour said to hold the strength of the mountain; few suits exist, because Orldhûm guards the secret even from its own |
| Warchanters of Mithradhûm | They chant their forerunners' names with every blow, which unnerves foes |
| Er-Natvir Mercenary Guards | Paid by Er-Natvir's merchants to guard caravans and rails, and good enough to stop Opal bandits |
| Opal Railway Robbers | Bandits of the Dwarovar rail lines, famous for a stolen train of gold tithe |
| Hul-Jorkad Sewer Wardens | Soldiers come of age in the tunnels under the hold, clearing skitterers and worse from the pipes |
| Fourfoot Chargers | Heirs of Tednur Fourfoot, whose ram charge broke one of the largest goblin hordes |

- [ ] **Step 1: Write the failing tests.** In `test_racial_armies.py`:
  - Add to `ROSTER`:
    `"aov_amldavhad_guard": ("heavy_infantry", 50, 90, 130)`, `"aov_platinum_warsuits": ("heavy_infantry", 25, 180, 320)`,
    `"aov_mithril_warchanters": ("heavy_infantry", 50, 105, 105)`, `"aov_mercenary_guards": ("heavy_infantry", 50, 90, 95)`,
    `"aov_railway_robbers": ("skirmishers", 80, 38, 38)`, `"aov_sewer_wardens": ("skirmishers", 80, 30, 52)`,
    `"aov_fourfoot_chargers": ("heavy_cavalry", 50, 150, 90)`.
  - Add to `EXPECTED` the same rows with pursuit and screen (`0, 0`, except Railway Robbers and Fourfoot Chargers
    `40, 0`) and `"PARAM:aov_unlock_maa_<key without aov_>"`.
  - Add to `DWARF_EXTRA`: `"aov_mercenary_guards": {"dwarven_road": 1.0}`, `"aov_railway_robbers": {"dwarven_road": 1.0}`,
    `"aov_sewer_wardens": {"dwarven_hold": 1.0, "cavern": 1.0}`, `"aov_fourfoot_chargers": {"plains": 0.5, "farmlands": 0.5}`.
  - Add the seven keys to the tuple in `test_clan_unit_art_copied`.
  - Add to `MaaTests`:

```python
    WEST_DWAROVAR_ICONS = {"aov_amldavhad_guard": "aov_amldavhad_guard",
                           "aov_platinum_warsuits": "aov_rie_undying_of_khazad_dum",
                           "aov_mithril_warchanters": "aov_mithril_warchanters",
                           "aov_mercenary_guards": "aov_rie_blacklock_mercenaries",
                           "aov_railway_robbers": "aov_railway_robbers",
                           "aov_sewer_wardens": "aov_rie_blacklock_engineers",
                           "aov_fourfoot_chargers": "aov_rie_longbeard_cavalry"}

    def test_west_dwarovar_icons_are_120_square(self):
        for key, icon in self.WEST_DWAROVAR_ICONS.items():
            self.assertEqual(field(self.unit(key), "icon"), icon, key)
            data = (SUBMOD / "gfx/interface/icons/regimenttypes" / f"{icon}.dds").read_bytes()
            self.assertEqual(struct.unpack_from("<II", data, 12), (120, 120), icon)

    def test_west_dwarovar_art_sources(self):
        """The game finds pictures by icon name, so pin what each copied file came from."""
        anbennar = ANBENNAR / "gfx/interface/icons/regimenttypes"
        ours = SUBMOD / "gfx/interface"
        for icon, source in (("aov_mithril_warchanters", "paladins"), ("aov_railway_robbers", "rogues")):
            self.assertEqual((ours / "icons/regimenttypes" / f"{icon}.dds").read_bytes(),
                             (anbennar / f"{source}.dds").read_bytes(), icon)
        rie = Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/1158310/2291024373/gfx/interface")
        if not rie.is_dir():
            self.skipTest("Realms in Exile is not installed")
        for icon, source in (("aov_amldavhad_guard", "blacklock_heavy_infantry"),
                             ("aov_mithril_warchanters", "stiffbeard_heavy_infantry"),
                             ("aov_railway_robbers", "blacklock_skirmishers"),
                             ("aov_rie_undying_of_khazad_dum", "undying_of_khazad_dum"),
                             ("aov_rie_blacklock_mercenaries", "blacklock_mercenaries"),
                             ("aov_rie_blacklock_engineers", "Blacklock_engineers")):
            for folder in ("men_at_arms_big", "men_at_arms_small"):
                self.assertEqual((ours / "illustrations" / folder / f"{icon}.dds").read_bytes(),
                                 (rie / "illustrations" / folder / f"{source}.dds").read_bytes(), f"{icon} {folder}")
```

  Add `import struct` to the module's imports; it already has `ANBENNAR` and `SUBMOD`.

- [ ] **Step 2: Run them to make sure they fail**

  Run: `python -I -m unittest discover -s tools/tests -p "test_racial_armies*.py"`
  Expected: failures naming the seven keys.

- [ ] **Step 3: Copy the art.** With `R` the Realms in Exile `gfx/interface` folder above, and `A` Anbennar's
  `gfx/interface`. Fourfoot Chargers reuse the art already in the mod.

  | New file name | Icon (`icons/regimenttypes`) | Big and small (`illustrations/men_at_arms_{big,small}`) |
  |---|---|---|
  | `aov_amldavhad_guard.dds` | copy `R/…/house_guard_dwarf.dds` | copy `R/…/blacklock_heavy_infantry.dds` |
  | `aov_rie_undying_of_khazad_dum.dds` | copy `R/…/undying_of_khazad_dum.dds` | copy `R/…/undying_of_khazad_dum.dds` |
  | `aov_mithril_warchanters.dds` | copy `A/…/paladins.dds` | copy `R/…/stiffbeard_heavy_infantry.dds` |
  | `aov_rie_blacklock_mercenaries.dds` | convert `R/…/blacklock_mercenaries.dds` | copy `R/…/blacklock_mercenaries.dds` |
  | `aov_railway_robbers.dds` | copy `A/…/rogues.dds` | copy `R/…/blacklock_skirmishers.dds` |
  | `aov_rie_blacklock_engineers.dds` | convert `R/…/Blacklock_engineers.dds` | copy `R/…/Blacklock_engineers.dds` |

  "Convert" means `python -I tools/eu4_import.py convert "<absolute src>" gfx/interface/icons/regimenttypes/<new file name> --resize 120x120`.

- [ ] **Step 4: Implement.** Write the seven unit blocks, the 21 cost values from the spec's table, and the name and
  `_flavor` loc.

- [ ] **Step 5: Run the tests to make sure they pass**

  Run: the command from Step 2. Expected: `OK`.

- [ ] **Step 6: Commit**

```bash
git add common/men_at_arms_types/aov_dwarven_maa_types.txt common/script_values/aov_racial_maa_values.txt localization/english/aov_racial_armies_l_english.yml gfx/interface/icons/regimenttypes gfx/interface/illustrations tools/tests/test_racial_armies.py
git commit -m "Racial armies: seven West Dwarovar clan units"
```

### Task 4: Eight traditions and their game-start grants

**Files:**
- Modify: `tools/data/racial_traditions.py` (`TRADITIONS` after `tradition_hearts_of_fire`; `GRANTS` after the
  `basalt_dwarvish` row at line 466)
- Regenerate: `python -I tools/build_racial_traditions.py`
- Test: `tools/tests/test_build_racial_traditions.py`

**Interfaces:**
- Consumes: Task 1's culture keys; Task 3's unit parameters. The generator writes each parameter's tooltip line as
  `GetMaA('aov_<name>')`, so `aov_unlock_maa_<name>` must match the unit key `aov_<name>`.

Keys, names, categories, layers (add `.dds` to the third item), modifiers, parameters and `eu4` lines are the spec's
"Own traditions" tables. Each entry has `heritage="heritage_dwarven"` and `gate=culture(<key>)`. A `culture` block goes
through `culture={...}` and a county block through `county={...}`.

Each `desc` is two sentences of EU4 lore in our own words, with none of `FORBIDDEN_LORE`:

| Tradition | What the description says |
|---|---|
| The High Assembly | Amldihr means the Gates of the Assembly; here Udrek the Consolidator made the warring holds one empire, ruling with conscience and a heavy hand |
| Reign of the Highlord | The Highlord of Haraz Orldhûm was first among the kings of the Dwarovar; outposts carved into the caverns turned every approach into a killing field |
| The Vow of Honesty | Every Mithril child swears a lifelong vow of honesty on coming of age; the Goblinslayer Academy teaches the same honour to soldiers |
| All Roads Lead to Er-Natvir | The rail hub connects every hold in the Serpentspine; its markets drew every dwarf culture, and its supply lines never missed a delivery |
| Spymasters of Aul-Dwarov | Opal dwarves held the empire's posts of intrigue, despite their famous bad luck; those who were not spies robbed the rail lines |
| Dwarven Plumbing | Hul-Jorkad's engineers cleared millennia of sludge from the pipes and gave the hold the finest water in the Serpentspine; its shot towers use the same lead |
| Stewards of the Vale | Ramsteel herders bred the first war rams and guarded the Vale's terraces for the High Kings; no dwarf is as at home in open country |
| The Setzunkhûpa | Dwarves distrust the sky, but the Sapphire dwarves built the great Sky Dome to study it; their scholars were famous across Aul-Dwarov |

- [ ] **Step 1: Write the failing tests.** Add the seven names to `GATED_ELSEWHERE`: `amldavhad_guard`,
  `platinum_warsuits`, `mithril_warchanters`, `mercenary_guards`, `railway_robbers`, `sewer_wardens`,
  `fourfoot_chargers`. Add:

```python
    def test_west_dwarovar_cultures_granted(self):
        want = {"kronium_dwarvish": "tradition_high_assembly", "platinum_dwarvish": "tradition_reign_of_the_highlord",
                "mithril_dwarvish": "tradition_vow_of_honesty",
                "dagrite_dwarvish": "tradition_all_roads_lead_to_er_natvir",
                "opal_dwarvish": "tradition_spymasters_of_aul_dwarov", "lead_dwarvish": "tradition_dwarven_plumbing",
                "ramsteel_dwarvish": "tradition_stewards_of_the_vale", "sapphire_dwarvish": "tradition_setzunkhupa"}
        for culture, tradition in want.items():
            self.assertEqual(data.GRANTS[culture], (tradition,), culture)
            self.assertEqual(data.TRADITIONS[tradition]["gate"], ("culture", culture), tradition)
        self.assertNotIn("parameters", data.TRADITIONS["tradition_setzunkhupa"])
```

- [ ] **Step 2: Run the tests to make sure they fail**

  Run: `python -I -m unittest discover -s tools/tests -p "test_build_racial_traditions*.py"`
  Expected: failures, because the grants are missing.

- [ ] **Step 3: Implement.** Add the eight `TRADITIONS` entries and eight `GRANTS` rows, then run
  `python -I tools/build_racial_traditions.py`.

- [ ] **Step 4: Run the tests to make sure they pass**

  Run: the command from Step 2, then `... -p "test_racial_armies*.py"` and `... -p "test_build_racial_levies*.py"`.
  Expected: `OK`. No new tradition has a levy modifier, so the levies stay fresh. If `FreshnessTests` says otherwise, run
  `python -I tools/build_racial_levies.py` and add its files to the commit.

- [ ] **Step 5: Commit**

```bash
git add tools/data/racial_traditions.py tools/tests/test_build_racial_traditions.py common/culture/traditions/aov_racial_traditions.txt common/scripted_effects/aov_racial_traditions_effects.txt localization/english/aov_racial_traditions_l_english.yml
git commit -m "Racial traditions: West Dwarovar clan traditions"
```

### Task 5: Docs, validation and in-game checklist

**Files:**
- Modify: `docs/systems/west-dwarovar.md`, `docs/systems/racial-traditions.md`, `docs/systems/racial-armies.md`,
  `CLAUDE.md`

- [ ] **Step 1: Update the docs.**
  - `west-dwarovar.md`: in "People", replace the `silver_dwarvish` sentence with the per-kingdom cultures and the ten
    dynasty names. Add a "Cultures" bullet like `serpentreach.md`'s, naming the spec, plan, files and test. Add the
    spec's "To confirm in game" list to "Needs an in-game test".
  - `racial-traditions.md`: add the eight rows to the Traditions table and mention the eight hold cultures in the intro.
    The "Files" row's 40 traditions becomes 48; its 17 units stay, because that count covers only `UNITS`.
  - `racial-armies.md`: add the seven units to the "Dwarf clans" row and the art table, including that Warchanters and
    Railway Robbers take Anbennar icons no unit used, and that Fourfoot Chargers share the Ramriders' art.
  - `CLAUDE.md`: in the West Dwarovar row, mention the eight hold cultures and West Dwarovar Dwarven language. In the
    Racial traditions row, change 40 to 48 and add the eight hold cultures.

- [ ] **Step 2: Run all tool tests**

  Run: `python -I -m unittest discover -s tools/tests`. Expected: `OK`.

- [ ] **Step 3: Run tiger**

  Run: `python -I tools/validate.py`. Expected: no new report naming the new files or keys. Fix any that do. Do not
  baseline them.

- [ ] **Step 4: Commit**

```bash
git add docs/systems/west-dwarovar.md docs/systems/racial-traditions.md docs/systems/racial-armies.md CLAUDE.md
git commit -m "West Dwarovar cultures: docs and in-game checklist"
```

# Great projects: framework and Cannor (design)

Date: 2026-10-09. Status: built (see "Changes during the build").
Sub-project 1 of 3 of the great projects. Sub-project 2 is the Middle Dwarovar (Dwarven Monuments on the CK3 map);
sub-project 3 is the rest of the map (Bulwar, Salahad, Kheterata, Dragon Coast, Deepwoods). Both reuse this
framework.

## Goal

Turn the EU4 Anbennar great projects that lie in Cannor into CK3 special buildings: multi-level monuments with
effects translated from EU4, placed in the right barony, shown with their EU4 painting in the county view. Anbennar
CK3's placeholders for these projects become the full versions. The base mod stays untouched.

## Decisions taken

| Question | Decision |
|---|---|
| Decomposition | By region: (1) framework + Cannor, (2) Middle Dwarovar, (3) rest of the map |
| Effects | Faithful: every EU4 modifier goes through one translation table to its closest CK3 modifier, scaled |
| Start state (1022) | Monuments that exist in EU4 (starting tier 1+) and whose EU4 `date` is before 1022.1.1 start built at level 1; others are empty slots; Anbennar's placed buildings keep their history |
| Art | Building icons: fitting vanilla `type_icon`s. County-view holding art: the monument's EU4 painting |
| Approach | A: a one-time importer writes curated data, a generator builds every output |
| Existing Anbennar buildings for EU4 projects | Included as same-key overrides that keep Anbennar's structure and add the EU4 tiers |
| Anbennar placeholders without an EU4 project | Untouched (Rathroost, Old/Bal Damenath, Highcour, Redfort, Ruby Pass, Damesear Seaports, Lorentaine Red Walls) |
| Canals | Not built (CK3 has no canal mechanic); the Marrhold Tunnel may return as a Dwarovar gate in sub-project 2 |
| Kobold projects without a same-named title | Placed in county `c_soxun_kobildzex` |

## Sources

| Mod | Workshop id (EU4, app 236850) | Folder |
|---|---|---|
| Anbennar | 1385440355 | `common/great_projects/`, `localisation/`, `gfx/interface/great_projects/`, `map/` |
| Cannorian Monuments | 2811184350 | same layout |
| Dwarven Monuments | 2791499822 | same layout |

When a submod redefines a project key that base Anbennar also defines, the submod wins (Cannorian before
Dwarven before base, matching the submods' load order). Province names come from base Anbennar's
`localisation/*prov*` (`PROV<id>`); regions from `map/area.txt` → `region.txt` → `superregion.txt`.

## Scope: Cannor

Cannor = EU4 superregions `western_cannor_superregion`, `escann_superregion`, `gerudia_superregion`:
82 projects. Of these:

| Group | Count | Output |
|---|---|---|
| New monuments | 64 | New buildings `aov_monument_<eu4key>_01/_02/_03`, including Palace of Unity (`palace_of_unity`) in a second Anbenncóst barony |
| Anbennar placeholders that are EU4 projects | 3 chains | Temple of the Highest Moon (same-key override of `temple_highest_moon_01`), Lorenan's Rest (same-key override of `lorenans_rest_01`), and EU4's Imperial Palace (`imperial_palace_anbenncost`) as **Castle Dameris** (the Imperial Palace did not exist yet in 1022): Anbennar's commented-out keys `castle_dameris_01/_02` plus a new `castle_dameris_03`, all three levels named "Castle Dameris". Anbennar's reserved `imperial_palace_anbennar_*` keys stay unused, for its later Imperial Palace content |
| Anbennar's full implementations | 14 | Same-key overrides plus new upper levels (below): `castanorian_citadel_*` (Bal Dostan, Bal Mire, Bal Ouord, Bal Vroren, Bal Hyl, Bal Vertesk, North, South), `calasandur_castle_*` (Aelcandar, Escandar, Calascandar), `castle_bladeskeep_*`, `lake_palace_*`, `holy_site_the_necropolis_01` |
| Canals | 1 | Excluded (Marrhold Tunnel) |

The exact per-project list (EU4 key, CK3 key, barony, start level, art) is the importer's output in
`tools/data/monuments/cannor.py`, reviewed by hand.

## Player-facing behaviour

- Each monument has a special building slot in one barony. Level 1 is built there (gold and time); levels 2 and 3
  are upgrades (`next_building`), as EU4's tiers 1-3. EU4's tier 0 (inert) has no CK3 level.
- Monuments existing before 1022 start built at level 1 (see Decisions). Players and AI can upgrade them.
- Effects at each level come from that EU4 tier's modifiers through the translation table:
  `province_modifiers` → the barony/county, `area_modifier` → the county (`county_modifier`), `country_modifiers` → the
  holder's character.
- **Culture gate:** EU4's `can_use_modifiers_trigger` / `can_upgrade_trigger` (cultures, culture groups, religions)
  becomes `is_enabled` (effects active) and `can_construct` (build/upgrade) on the CK3 building, through a
  culture-mapping table. Outside the gate the building stays but does nothing, as in EU4. An EU4 group with no
  CK3 equivalent leaves the gate open, recorded in the data.
- **One-off upgrade effects** (EU4 `on_upgraded`: a free building, a court mage, estate loyalty) become `on_complete`
  effects where the translation table has an equivalent (e.g. a court mage → a learned courtier; estate loyalty →
  prestige or piety); otherwise they are dropped and listed in the data.
- **Costs and times** (translation table, tunable): EU4 tier 1/2/3 cost factor 1000/2500/5000 × 0.4 → 400/1000/2000
  gold; EU4 upgrade time 120/240/480 months × 0.5 → 5/10/20 years.
- **County view:** a barony with any level of a monument shows the monument's EU4 painting as its holding art;
  baronies without one, or monuments without a painting, show the normal holding art.
- **Names and descriptions:** EU4's project names; descriptions from EU4's loc where present, else a one-line
  description written in the data. Each level's tooltip lists effects as CK3 shows them.

### Placement rules

- The name-matched barony (EU4 province name = CK3 barony or county name, accents and case ignored); for a county
  match, its capital barony.
- When two monuments share a county (Oldhaven, Moonmount, Portnamm, Westport, Anbenncóst, the North Citadel,
  Bladeskeep, the Viswalls, Soxun Kobildzex), the second takes the next barony of that county without a special slot.
- A barony that already has an Anbennar `special_building_slot` is never reused for a new monument; the 14, the
  Temple of the Highest Moon and Lorenan's Rest use Anbennar's existing placement. Castle Dameris has none in
  Anbennar, so it gets a new slot in Anbenncóst's capital barony, and Palace of Unity the next Anbenncóst barony.
- Kobildzex Guild of Trapsmiths and the Dragonhoard (EU4 "Deeb Kobilderd", no CK3 title): county `c_soxun_kobildzex`.
- Every placement the importer cannot resolve is listed in its report and must be set by hand in the data before
  the generator accepts it.

### The 14 existing Anbennar buildings

- Anbennar's keys, structure and placement stay: ruins → rebuilt stages (e.g. `castanorian_citadel_bal_ouord_01`
  ruins → `_02` rebuilt), the Lake Palace's two levels, the Necropolis's holy-site faith logic, its triggers and
  history.
- Anbennar's built level (the rebuilt stage, or `_01` where there is no ruins stage) is EU4 tier 1: it gains tier 1's
  translated effects alongside its own. Ruins stages keep Anbennar's effects only.
- Its `next_building` is extended to new `aov_monument_<eu4key>_02` / `_03` for EU4 tiers 2-3. For the Lake Palace,
  whose `_02` already exists, `lake_palace_02` is tier 2 and gains tier 2's effects, and `_03` continues the chain.
- The overrides are **generated from Anbennar's current definitions** (copy + insert, marked `# Anbennar Overhaul`),
  so an Anbennar update needs only a regenerate. Same for the three placeholder chains.

## Architecture

### Data

| File | Content |
|---|---|
| `tools/data/monuments/translation.py` | `MODIFIERS`: EU4 modifier key → (CK3 key, multiplier, block `province`/`county`/`duchy`/`holder`) or `DROP` with a reason; `ONE_OFF`: EU4 `on_upgraded` effect patterns → CK3 effect or `DROP`; `CULTURES`: EU4 culture / culture group / religion → CK3 trigger; `COST` and `TIME` scales; `ICONS`: category → vanilla `type_icon` |
| `tools/data/monuments/cannor.py` | `MONUMENTS`: one dict per project: `eu4_key`, `source`, `ck3_key` (new `aov_monument_<eu4key>` or an Anbennar key), `kind` (`new`/`override`/`placeholder`), `barony`, `start_level` (0 or 1), `category` (icon), `gate` (CK3 trigger text), `tiers` (3 × translated modifier blocks and one-off effects), `name`, `desc`, `art` (EU4 file or none), `notes` (dropped keys, hand decisions) |

### Tools

| Tool | Does |
|---|---|
| `tools/import_eu4_monuments.py --region cannor` | Reads the three EU4 mods, applies the precedence and region filter, matches baronies, translates tiers through `translation.py`, and writes `tools/data/monuments/cannor.py` plus a report of unmatched placements, untranslated keys and gate fallbacks. Re-running it shows a diff against the curated file; hand fixes live in `tools/data/monuments/cannor_hand.py` (`HAND`), merged on every run (`tiers` key by key) |
| `tools/build_monuments.py` | Validates the data and writes every output (below). Fails on any unmapped modifier key, unresolved barony, duplicate slot or missing loc |

### Outputs (generated; header "generated ... do not edit by hand")

| File | Content |
|---|---|
| `common/buildings/aov_monuments_cannor.txt` | New monument buildings, all levels, plus `castle_dameris_01/_02/_03` (EU4's Imperial Palace) under Anbennar's reserved keys |
| `common/buildings/zz_aov_monument_overrides_cannor.txt` | The 14 and the two placeholder overrides (Highest Moon, Lorenan's Rest): Anbennar's definitions copied with the EU4 effects and `next_building` inserted;  |
| `history/provinces/aov_monuments_cannor.txt` | `special_building_slot` (and level 1 where it existed before 1022) per new monument |
| `localization/english/aov_monuments_cannor_l_english.yml` | Building names and descriptions (`building_<key>`, `building_<key>_desc`) |
| `common/customizable_localization/aov_monument_illustration.txt` | `AovMonumentIllustration` (province scope): one entry per monument with art, `has_building_or_higher` on its level 1 → loc key holding the picture path |
| `gfx/interface/illustrations/aov_monuments/<eu4key>.dds` | EU4 paintings, DXT1 decoded to uncompressed BGRA at their EU4 size |
| `gui/window_county_view.gui` | Generated from Anbennar's copy: the holding illustration shows `AovMonumentIllustration` when it is not empty (marked `# Anbennar Overhaul`) |

The county-view override and the building overrides are added to CLAUDE.md's generated-files table and the
Anbennar-update steps.

## Verification

- Tool tests:
  - importer: precedence (submod over base), region filter, name matching with accents, the Soxun Kobildzex rule,
    the shared-county rule, the start-level rule (EU4 tier ≥ 1 and date < 1022.1.1);
  - data: all 82 Cannor projects are built, overridden or excluded with a reason (only the canal); every EU4 modifier
    key in the data has a translation row; every gate maps or is recorded as open;
  - generator: every level chains to the next; no barony gets two special slots; no new slot lands on an Anbennar
    slot; overrides keep every non-modifier line of Anbennar's definition; every building has name and description
    loc; illustration custom loc covers every monument with art; art files have their declared sizes;
  - DXT1 decoder against a known block.
- `python -I tools/validate.py` clean.
- In game: monuments appear in their baronies, level 1 pre-built where expected; upgrade costs and times match the
  tooltip; effects switch off for an ungated culture; the county view shows the EU4 painting; the 14 keep their
  ruins → rebuilt flow and gain levels 2-3; the Necropolis keeps its holy-site effects.

## Risks

- **County-view override** is a fourth whole-file GUI override; rerun its generator after Anbennar updates and CK3
  patches.
- **Building overrides** of 17 Anbennar chains must win over Anbennar's definitions (`zz_` file loads later); check
  `database_conflicts.log`.
- **Translation quality:** EU4 economy keys (trade, manufactories, estates, development) have no direct CK3 match;
  the table's stand-ins set the balance, and are the place to tune it.
- **Texture paths from custom loc** (`texture = "[...Custom(...)]"`) need an in-game check; fallback: a GUI branch
  per monument generated into the override.
- **EU4 dates:** some projects have placeholder dates (`01.01.01`); they count as before 1022.

## Out of scope

- Middle Dwarovar and the rest of the map (sub-projects 2 and 3), canals, relocating monuments (EU4 `can_be_moved`),
  EU4 monuments outside the CK3 map, Anbennar placeholders without an EU4 project.

## Changes during the build

1. Hand fixes live in `tools/data/monuments/cannor_hand.py` (`HAND`, merged by the importer on every run; `tiers`
   merge key by key), not `# hand` comments.
2. EU4 `area_modifier` lands in CK3 `county_modifier` (the engine allows `duchy_capital_county_modifier` only on
   duchy-capital buildings).
3. Castle Dameris is generated into `aov_monuments_cannor.txt`, not the overrides file.
4. The 5 EU4 mission monuments (Palace of Unity, three Elikhander monuments, Bastion of the God Fragment) use their
   commented `# start = N` province.
5. One-off EU4 effects inside a conditional `if`/`else` are not translated (listed in each tier's `dropped`);
   courtier one-offs use `gender_female_chance = 50`.
6. Overrides of Anbennar levels do not add the EU4 culture gate (it would switch off Anbennar's own effects). The
   gate is wrapped in a `custom_tooltip` ("Built and used by: ...", naming the CK3 cultures, heritages and faiths
   it checks). Revised after the final review: a CK3 upgrade replaces the previous level's effects, so the new
   upper levels (`aov_monument_<k>_02/_03`) of the 16 chains that start with an Anbennar building are copies of
   the chain's top Anbennar level (its last Anbennar-keyed level) with the key renamed, the EU4 tier merged as in
   item 7, `cost_gold`/`construction_time` from the tier and `next_building` set (none at level 3). They keep
   Anbennar's `is_enabled`, flags, `effect_desc`, `show_disabled`, `type_icon` and `ai_value`; the EU4 gate goes
   into `can_construct` only (appended to Anbennar's, or a new block), never `is_enabled`. New monuments keep the
   gate in both. Consequence: the citadels sum Anbennar's fort level 6 (or 8) with EU4's (capped since, item 14).
7. A modifier key already in an Anbennar block becomes one summed line (named values resolved from
   `00_building_values.txt`).
8. Balance guard: no level above fort_level 4 or county tax_mult 0.3 (Morgurax and Humac's Tomb capped in the hand
   file); 10 gates stay open (EU4 gates on tags/flags/legacies), each noted.
9. Paintings also come from EU4 sprite definitions (`GFX_great_project_<key>`); 51 of 81 monuments have one; ruins
   stages never show it.
10. Quotes in names and descriptions become `'` in loc.
11. Effect guard: every level of every monument has an effect (a modifier or an `on_complete`); levels of chains
    that start with an Anbennar building carry Anbennar's effects. `build_monuments.py` validates the data before
    writing (barony/province, duplicate province, name/desc, icon category, modifier keys that are translation-table
    targets or hand keys, the effect guard) and raises `GeneratorError` naming the monument. Castle Dameris gets
    hand tiers translated from the EU4 event modifiers its `on_upgraded` adds (imperial authority -> prestige,
    favours -> vassal opinion, diplomatic reputation -> diplomacy); Palace of Unity, Ascajar (level 1) and the
    Moonmount Library (level 1) get modest hand tiers (see their notes).
12. Generated levels use vanilla's special-building `ai_value` (base 100, `culture_likely_to_fortify_modifier` for
    fortresses and castles, `ai_pious_building_preference_modifier` for temples, factor 0 while
    `free_building_slots > 0`); copies of Anbennar levels keep Anbennar's `ai_value` plus that guard; Anbennar's own
    levels are unchanged.
13. EU4 gate atoms inside `NOT`/`NOR` are not mapped (noted per monument); the gate is built from the positive
    atoms only. One-off effects reward `barony.holder` (as vanilla building `on_complete` does). Monuments that start
    unbuilt prefer a free barony of their county with a holding in Anbennar's history (Palace of Unity
    `b_elvendocks`, Lorentaine Mage Academy `b_rosionn`); the Dragonhoard keeps `b_zenturomai` (no free barony of
    Soxun Kobildzex has a holding) and is reported by the importer.
14. Balance follow-ups to the final review (three items parked in PR #3):
    - **Fort-level cap.** A summed `fort_level` stops at max(8, Anbennar's own resolved value for that level; 8 is
      vanilla's strongest special building, `alamut_castle_02`). The surplus is added 1:1 to
      `defender_holding_advantage` on the same level (Anbennar's fort-level and advantage tiers carry the same
      numbers). The citadels' upper levels and Calascandar, North and South Citadel level 1 now have fort_level 8
      and +1 to +4 holding advantage. `FORT_LEVEL_CAP` in `build_monuments.py`; a test checks every level of the
      written building files.
    - **Upgrade cost.** New upper levels cost max(EU4 tier cost, cost of the level they upgrade from) and take the
      longer construction time (Anbennar's raw value, such as `very_slow_construction_time`, is kept when it wins),
      so citadel and castle upgrades cost 2000 gold, not 1000. Levels with no cost line (Anbennar's pre-built
      Temple of the Highest Moon and Lorenan's Rest) set no floor.
    - **Necropolis.** Hand field `gate_mode: "or"`: on the new upper levels the EU4 gate (Cannorian Pantheon) is one
      more alternative inside Anbennar's `OR` (pantheon or holy site of the holder's faith) instead of an extra
      requirement, so a holy-site holder of another faith who can build level 1 can also upgrade it. Other gated
      chains keep the gate as a requirement.

## Sub-project 3: the rest of the map (built)

Regions `bulwar` (EU4 `bulwar_superregion`), `salahad` (`north_salahad_superregion` with Akasik and Kheterata,
`south_salahad_superregion`, `djinnakah_superregion`) and `deepwoods` (`deepwoods_superregion`,
`deepwoods_portal_superregion`), all `on_map_only`. No other EU4 superregion has a project whose province matches a
CK3 title. The Dragon Coast is EU4's `dragon_coast_region` inside `western_cannor_superregion`, so its 6 projects
were already built with Cannor.

| Region | Built | Excluded |
|---|---|---|
| Bulwar | 12 | Hero's Gate, Jorkad Dam, Queen's Throne (Skewered Drake): dungeons |
| Salahad | 10 | Esuvrem, Arskitse: no CK3 title; Great Merfolk Canal: canal; Befouled Aur-Kes-Akasik: event variant |
| Deepwoods | 6 | Eternal Pillars 3, 4, 7, 8, 9: no CK3 title; Deepwoods Fey Portal: canal |

Changes to the framework:

1. `VARIANTS` in the importer: an EU4 project that an event swaps in for another in the same province is excluded
   ("variant of <base>"). Explicit, because a key-prefix rule would also catch real second monuments (Morgurax).
2. EU4 text cleaning in the importer: the Sarhal descriptions' opening dash rule and literal `\n` are dropped, and
   typographic quotes and dashes become ASCII (Cannor needed hand descriptions for this). EU4 loc lines that are not
   UTF-8 are read as Windows-1252.
3. Translation rows for the new EU4 keys (trade value, friendly movement, imperial mandate, harpy queendom power,
   Jaddari fervor, mages estate, siege ability, ...) and gate rows for Bulwari, gnollish, harpy, Akasi, Fangaulan
   and elven groups and the Bulwari, Xhazobkult and Akasi religions; Haless, ogre and orc atoms are ignored.
4. EU4 admirals and planetouched generals become a martial courtier, like generals. This also adds one to the
   Imperial Dockyard of Neckcliffe (Cannor) at level 3.
5. Hand fixes: Koroshesh is a one-barony county, so the Grand Library (built in 1022) keeps it and the Grain Port is
   placed in Kaashesh (same duchy, coastal on the EU4 map); balance caps on the Ash Palace (domain limit 1/2/2, not
   4/7/10), Ebbusubtu (piety 0.5/0.75/1), the Oasis of Water Dreams and the Eternal Pillars (tax 0.3), Arzax Eklu
   (supply 0.5, not 10.25); a written description for the Pillars of Eternity (EU4 has none).

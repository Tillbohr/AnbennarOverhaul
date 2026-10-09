# Great projects: framework and Cannor (design)

Date: 2026-10-09. Status: approved in chat (decomposition, effects, start state, art, approach, content, the
14 existing buildings, translation and costs); awaiting written-spec review.
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
| Anbennar placeholders that are EU4 projects | 3 chains | Temple of the Highest Moon (same-key override of `temple_highest_moon_01`), Lorenan's Rest (same-key override of `lorenans_rest_01`), and EU4's Imperial Palace (`imperial_palace_anbenncost`) defined under Anbennar's commented-out keys `imperial_palace_anbennar_01/_02/_03` (its `castle_dameris_*` keys stay unused: no EU4 source) |
| Anbennar's full implementations | 14 | Same-key overrides plus new upper levels (below): `castanorian_citadel_*` (Bal Dostan, Bal Mire, Bal Ouord, Bal Vroren, Bal Hyl, Bal Vertesk, North, South), `calasandur_castle_*` (Aelcandar, Escandar, Calascandar), `castle_bladeskeep_*`, `lake_palace_*`, `holy_site_the_necropolis_01` |
| Canals | 1 | Excluded (Marrhold Tunnel) |

The exact per-project list (EU4 key, CK3 key, barony, start level, art) is the importer's output in
`tools/data/monuments/cannor.py`, reviewed by hand.

## Player-facing behaviour

- Each monument has a special building slot in one barony. Level 1 is built there (gold and time); levels 2 and 3
  are upgrades (`next_building`), as EU4's tiers 1-3. EU4's tier 0 (inert) has no CK3 level.
- Monuments existing before 1022 start built at level 1 (see Decisions). Players and AI can upgrade them.
- Effects at each level come from that EU4 tier's modifiers through the translation table:
  `province_modifiers` → the barony/county, `area_modifier` → the duchy capital county, `country_modifiers` → the
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
  Temple of the Highest Moon and Lorenan's Rest use Anbennar's existing placement. The Imperial Palace has none in
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
| `tools/import_eu4_monuments.py --region cannor` | Reads the three EU4 mods, applies the precedence and region filter, matches baronies, translates tiers through `translation.py`, and writes `tools/data/monuments/cannor.py` plus a report of unmatched placements, untranslated keys and gate fallbacks. Re-running it shows a diff against the curated file; it never overwrites hand fields marked `# hand` |
| `tools/build_monuments.py` | Validates the data and writes every output (below). Fails on any unmapped modifier key, unresolved barony, duplicate slot or missing loc |

### Outputs (generated; header "generated ... do not edit by hand")

| File | Content |
|---|---|
| `common/buildings/aov_monuments_cannor.txt` | New monument buildings, all levels |
| `common/buildings/zz_aov_monument_overrides_cannor.txt` | The 14 and the two placeholder overrides (Highest Moon, Lorenan's Rest): Anbennar's definitions copied with the EU4 effects and `next_building` inserted; plus `imperial_palace_anbennar_01/_02/_03`, new definitions under Anbennar's reserved keys |
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

# Dwarven hold digging (design)

Date: 2026-10-10. Status: design approved, not built.
Sub-project 1 of the dwarven mechanics. The others (roadmap at the end) get their own specs.

## Goal

Dwarven rulers dig their holds deeper over generations, as in EU4 Anbennar's hold digging: long digs paced by
random events the player answers. In CK3 a hold is its own holding type whose primary building is the hold level
(like a castle level); digging happens in repeated **Delving Campaign** activities whose phases are the dig's
stages. Holds can be ruined by conquest and restored with a decision. The base mod stays untouched.

## Decisions taken

| Question | Decision |
|---|---|
| What is a hold | New holding type `dwarven_hold_holding`; primary building `dwarven_hold_01`..`_10` is the hold level (LotR RiE's `dwarven_holding` pattern) |
| Which holds | Exactly the EU4 Anbennar holds (working, ruined or infested at 1444) whose province is on the CK3 map: 9 holds. No founding of new holds |
| Start state (1022) | All working except Khugdihr (ruined). EU4's 1444 ruin/infestation is later history; CK3's 1022 history has dwarves in Hehodovar and Gor Ozumbrog |
| How digging works | Activity campaigns (~2 years each) add progress to the hold; a level needs several campaigns. The ruler is free between campaigns |
| Activity phases | Survey, Excavation, Shoring, Breakthrough: the dig's stages |
| Events | EU4-style random events for the player during each phase change the campaign's progress |
| Hold states | Working or ruined only. Infested holds are left to the Dwarovar situation (roadmap) |
| Ruin | Only when a non-dwarf conquers a dwarf-held hold barony (the previous holder was dwarven) |
| Restoring | Decision *Clear the Ruins of [Hold]*: gold and prestige, 5-year restoration, then working |
| Situation | No situation in this spec. A region-wide Dwarovar crisis situation is roadmap item 1 |

## The 9 holds

EU4 name, CK3 title (matched by name as in the great-projects importer), the hold barony (county capital, or the
matched barony), the 1022 start level and state.

| Hold | EU4 1444 | CK3 title | Hold barony | 1022 culture | Start |
|---|---|---|---|---|---|
| Marrhold | dig 1 | `c_marrhold` | `b_marrhold` | marrodic (human) | level 1, working |
| Anvilwright | dig 1 | `b_anvilwright` | `b_anvilwright` | silver dwarvish | level 1, working |
| Verkal Gulan | dig 2 | `c_verkal_gulan` | `b_gulandhum` | gold dwarvish | level 2, working |
| Seghdihr | dig 2 | `c_seghdihr` | `b_kar_fimthrun` | citrine dwarvish | level 2, working |
| Ovdal Tûngr | dig 2 | `c_ovdal_tungr` | `b_irovar` | copper dwarvish | level 2, working |
| Rubyhold | dig 2 | `c_rubyhold` | `b_hul_az_amekh` | ruby dwarvish | level 2, working |
| Hehodovar | infested | `c_hehodovar` | `b_kar_hargun` | pyrite dwarvish | level 2, working |
| Gor Ozumbrog | infested | `c_gor_ozumbrog` | `b_topazhjardan` | topaz dwarvish | level 2, working |
| Khugdihr | ruined | `c_khugdihr` | `b_aghatehargun` | darkscale (kobold) | level 1, **ruined** |

Hehodovar and Gor Ozumbrog start at level 2: great holds in 1022 that had fallen by 1444. Marrhold's humans and
Khugdihr's kobolds hold real holds but gain no level effects (below).

## Holds as a holding type

- `dwarven_hold_holding` is added to `common/holdings/00_holdings.txt` through the existing generator's
  `ADDITIONS` (`tools/build_holdings_override.py`). `primary_building = dwarven_hold_01`; its `buildings` list is
  `castle_holding`'s list plus the three dwarven buildings below.
- Governments: every government whose `primary_holding` or `valid_holdings` includes `castle_holding` also lists
  `dwarven_hold_holding` in `valid_holdings`, so a feudal or clan dwarf holding their hold gets no wrong-holding
  penalty (LotR RiE does the same). Anbennar ships its own `common/governments/00_government_types.txt` and
  `01_japan_government_types.txt`, so a new generator `tools/build_governments_override.py` copies them and appends
  the key (marked `# Anbennar Overhaul`), the same way as the holdings override.
- New holdings of this type cannot be constructed on empty baronies; the only holds are the 9 converted at game
  start (see Risks: holding construction).
- Hold levels `dwarven_hold_01`..`_10` (one chain via `next_building`) are never offered in the build menu
  (`can_construct_potential = { always = no }`); only a finished dig raises the level.
- `is_enabled` of every level: the holder has dwarven heritage and the hold is not ruined. Otherwise the level has
  no effect at all (an `is_enabled` building is wholly off), as LotR's holdings under other races; the holding
  itself and its other buildings stay.

### Level effects (starting values; tuned in `tools/data/holds.py`)

| Level | fort_level | defender_holding_advantage | levy_size | tax_mult | garrison_size | building_slot_add |
|---|---|---|---|---|---|---|
| 1 | 2 | 2 | 0.05 | 0.05 | 0.10 | 0 |
| 2 | 2 | 3 | 0.10 | 0.08 | 0.20 | 0 |
| 3 | 3 | 4 | 0.15 | 0.11 | 0.30 | 1 |
| 4 | 3 | 5 | 0.20 | 0.14 | 0.40 | 1 |
| 5 | 4 | 6 | 0.25 | 0.17 | 0.50 | 1 |
| 6 | 4 | 7 | 0.30 | 0.20 | 0.60 | 2 |
| 7 | 5 | 8 | 0.35 | 0.23 | 0.70 | 2 |
| 8 | 5 | 9 | 0.40 | 0.26 | 0.80 | 2 |
| 9 | 6 | 10 | 0.45 | 0.29 | 0.90 | 3 |
| 10 | 6 | 12 | 0.50 | 0.32 | 1.00 | 3 |

`fort_level`, `defender_holding_advantage` and `garrison_size` are `province_modifier`; `levy_size` and `tax_mult`
`county_modifier`; `building_slot_add` `province_modifier` (cumulative values, since an upgrade replaces the
previous level). A level-10 hold is a little stronger than a vanilla castle level 4 plus a strong special
building, never above the great-projects balance guard (fort_level 8).

Each level also gives a castle's flat values, as the same named script values castles use: `levy`, `max_garrison`,
`garrison_reinforcement_factor` (building top level) and `monthly_income` (`province_modifier`). The castle of the
level's art band (`ASSET_BAND`: levels 1-2 `castle_01`, 3-4 `castle_02`, 5-7 `castle_03`, 8-10 `castle_04`) is the
floor; deeper levels step up within the band (`_FLAT_TIERS` in `tools/data/holds.py`). They are switched off with the
level by `is_enabled`.

Castle buildings (economy, military, fortification) can be built in a hold: Anbennar's holding-level requirement
triggers `building_requirement_castle_city_church` and `building_requirement_castle_city_church_temple_citadel_tribe`
are overridden (`common/scripted_triggers/zz_aov_building_requirement_triggers.txt`) with a `dwarven_hold_holding`
branch that treats hold levels 1/3/5/8 as castle levels 01/02/03/04.

### Dwarven buildings

Dwarven-only (`can_construct_potential`: dwarven heritage holder) and gated on the hold level
(`can_construct`: `has_building_or_higher = dwarven_hold_0N`); `is_enabled` as the levels (dwarven holder, hold not
ruined). The AI builds them like vanilla buildings (`ai_value` base 10/9/8 with the general, tier-1 and
economy/military/piety preference modifiers):

| Building | From level | Effect (level 1; 3 levels each, effects doubling and tripling) |
|---|---|---|
| Deep Mine `deep_mine_01..03` | 3 | `tax_mult` +0.05, `supply_limit_mult` +0.10 (county) |
| Runeforge `runeforge_01..03` | 5 | `heavy_infantry_damage_mult` +0.05, `heavy_infantry_toughness_mult` +0.05 (character) |
| Hall of the Ancestors `hall_of_the_ancestors_01..03` | 7 | `monthly_prestige` +0.2, `monthly_piety` +0.2 (character) |

## Digging: the Delving Campaign

### Progress on the hold

Each hold province has `var:aov_dig_progress` (starts 0). The target for the next level is
`aov_dig_target = 50 × next level` (100 for level 2 … 500 for level 10; 2700 in all). When a campaign's progress
brings the hold to its target, the hold rises one level and the progress resets to the surplus. Progress belongs
to the hold: it survives the ruler's death and changes of holder among dwarves.

### The activity

`activity_hold_dig` (*Delving Campaign at [Hold]*), in `common/activities/activity_types/aov_hold_dig.txt`:

- **Host**: has dwarven heritage, personally holds a working hold barony below level 10, not at war, can pay.
  The phase location is fixed to the hold (the host's eligible hold; when the host has more than one, the activity
  location picker offers each eligible hold province).
- **Guests**: none invited (host and entourage only).
- **Cost**: `aov_dig_campaign_cost` = 50 × current level gold, plus the investment option.
- **Options** (planning screen):
  - *Pace*: Careful (×0.75 progress, fewer setback events), Steady (×1), Reckless (×1.35, more setback events).
  - *Investment*: None, Generous (+100 gold, ×1.25), Lavish (+250 gold, ×1.5).
- **Phases** (all `is_predefined`, fixed order; each phase sets its length in `on_phase_active` with
  `progress_activity_phase_after`, as LotR's mining activity does): Survey 3 months, Excavation 12 months,
  Shoring 6 months, Breakthrough 1 month.
- **Validity**: the activity ends early (no progress kept from it) when the host loses the hold barony, the hold is
  ruined, or the hold is besieged or occupied. Whether war alone invalidates a running activity is checked during
  planning; if the engine forces it, a declared or received war also ends the campaign.
- **AI**: hosts campaigns when it can afford them (gold reserve check), not at war, weighted by stewardship and
  greed/diligence traits; `ai_check_interval` 12 months.

### Campaign progress

On start the activity stores `var:aov_campaign_progress = aov_dig_campaign_base`:

`aov_dig_campaign_base = (20 + stewardship / 2 + learning / 4 + traits) × pace × investment`, where traits is
+5 for `diligent`, +5 for `architect`, −5 for `lazy` (Anbennar has no dwarven skill traits; `race_dwarf` is the
heritage check, not a bonus). With average skills a campaign yields about 30; level 2 needs about 4 campaigns
(~8 years), level 10 about 17 (~35 years), level 1 to 10 about 90 campaigns.

### Events (EU4-style)

Namespace `aov_hold_dig`. Players only; AI campaigns use the base value. Each phase's `on_phase_active` schedules one
random pulse (`trigger_event = { on_action = aov_hold_dig_<phase>_pulse days = ... }`, the LotR pattern) that picks
one event for that phase, so a campaign has up to 3 events (Survey, Excavation, Shoring), and Breakthrough ends it.
Each event offers 2-3 options that change `aov_campaign_progress` (±5 to ±20), cost or gain gold/prestige, or risk
a skill check. Reckless pace raises the weight of setback events; Careful lowers it.

| Phase | Events |
|---|---|
| Survey | Old Tunnel Maps; Unstable Strata; A Prospector's Claim |
| Excavation | A Rich Vein (take the gold or push deeper); Flooded Gallery; The Miners' Strike; A Sealed Rune Door; Something in the Deep (prowess or martial check) |
| Shoring | Gallery Collapse; A Master Engineer Arrives; Shortage of Timber |

Breakthrough (`on_phase_active`): adds `aov_campaign_progress` to the hold; on a level-up fires *Breakthrough at
[Hold]* with one random discovery: gems (gold = 25 × new level), a rich vein (county modifier
`aov_hold_rich_vein`, `tax_mult` +0.1 for 10 years) or old dwarven lore (learning lifestyle XP +500); otherwise
fires *The Campaign Ends* with the progress made and the remaining target. Artifacts are left to Runesmithing
(roadmap).

## Ruined holds

- **Ruin**: `on_title_gain` (appended on_action) where the title is a hold barony, the gain is by conquest, the
  new holder lacks dwarven heritage and the previous holder had it: a non-dwarf conquering a dwarf-held hold (a
  non-dwarf taking a hold from another non-dwarf, as Marrhold's humans at start, does not ruin it). Effects: `var:aov_hold_ruined` set, `aov_dig_progress` reset to 0, county
  modifier `aov_ruined_hold` (`tax_mult` −0.5, `development_growth_factor` −0.5, `levy_size` −0.5), any campaign at
  the hold ends. The hold level is kept but disabled (`is_enabled` requires not ruined).
- **Game start**: Khugdihr is ruined (level 1).
- **Restoring**: decision *Clear the Ruins of [Hold]* (`common/decisions/aov_hold_decisions.txt`). Shown to a
  dwarven-heritage ruler who personally holds a ruined hold with no restoration running or pending
  (`var:aov_restore_pending`); the decision's event lists each such hold. Cost 300 gold and 200 prestige. The AI
  checks it yearly and takes it when it has twice the gold cost and the prestige. Adds province modifier `aov_restoring_hold` for 5 years (no effect
  but the timer; tooltip "Restoration under way"), and schedules *[Hold] Restored* after 5 years, which clears the
  ruin variable and modifier. If the restorer loses the hold meanwhile, the restoration continues for the new holder
  only if they are dwarven; otherwise it is cancelled.

## Architecture

### Data and generators

| File | Content |
|---|---|
| `tools/data/holds.py` | `HOLDS` (the 9 rows above: EU4 name, CK3 title, hold barony, start level, ruined); `LEVELS` (the level table); dig targets, campaign cost and base-value constants |
| `tools/build_holds.py` | Writes `common/buildings/aov_dwarven_holds.txt` (the 10 levels and the 3 dwarven buildings), `common/scripted_effects/aov_hold_setup_effects.txt` (game-start conversion: `set_holding_type`, level, Khugdihr's ruin), `localization/english/aov_holds_l_english.yml` |
| `tools/build_holdings_override.py` | `ADDITIONS` gains `dwarven_hold_holding` |
| `tools/build_governments_override.py` (new) | Copies Anbennar's government files and adds `dwarven_hold_holding` to `valid_holdings` |

### Hand-written script

`aov_hold_*` files: the activity and its on_actions, scripted triggers (`aov_is_hold`, `aov_hold_is_working`,
`aov_can_host_dig`), scripted effects (level up, ruin, restore), script values (targets, cost, campaign base),
modifiers (`aov_ruined_hold`, `aov_restoring_hold`, the discovery modifier), the decision, the events
(`events/aov_hold_dig_events.txt`, `events/aov_hold_ruin_events.txt`), the on_actions (game start, `on_title_gain`),
loc.

### Art

- Holding illustration: the vanilla castle illustrations (the hold levels copy `castle_01`..`_04`'s assets by level
  band), and vanilla `gfx/interface/illustrations/event_scenes/tgp_ruined_holding.dds` while ruined (shown through
  the county view's custom loc, as the monument paintings are). EU4's `hold_0N` files are 38 px modifier icons
  (`gfx/interface/ideas_EU4/`), not illustrations; they become the `aov_ruined_hold` / level modifier icons.
- Map: holds use the castle meshes. Monument paintings keep priority in the county view for the five Dwarovar
  monuments in these holds.
- Activity: vanilla activity art (a mine or mountain illustration) until custom art exists.

## Verification

- Tool tests: every `HOLDS` title and barony exists in Anbennar and the barony belongs to the county; exactly one
  hold is ruined at start; the level chain is unbroken and every level has effects; dig targets rise; campaign base
  is positive; generated files are fresh; the conversion effect covers exactly `HOLDS`; the government override
  adds the key to every castle-capable government and changes nothing else.
- `python -I tools/validate.py` clean.
- In game: the 9 holds are converted at start with their levels; Khugdihr is ruined; a dwarven player runs a
  campaign with events in each phase and progress shown at the end; a level-up raises the building; a non-dwarf
  conquest ruins a hold; *Clear the Ruins* restores it after 5 years; Marrhold (human) shows the holding without
  level effects; no wrong-holding-type penalty for a feudal dwarf.

## Risks

- **Setting the primary building from script**: how to raise a holding's primary building level by effect
  (`add_building` of the next level, or another effect) is confirmed during planning; the level-up depends on it.
- **Activity and war**: whether a running activity survives the host's war (see Validity).
- **Holding construction**: which game list offers holding types when building on an empty barony (government
  `valid_holdings` may make the new type constructible); confirmed during planning, and the type is kept out of it.
- **Ruined illustration in the county view**: reuses the monument-painting mechanism (an `AovMonumentIllustration`
  entry for ruined holds); a monument painting in the same barony takes priority.
- **Governments override**: a generated whole-file copy, rerun after Anbennar updates (added to CLAUDE.md's update
  steps).
- **AI**: campaigns must not drain AI treasuries; the gold reserve check and `ai_will_do` are tuned in play.

## Roadmap (later sub-projects, each its own spec)

1. **The Dwarovar situation** (EU4): region-wide crises as phases (Goblintide, Serpent's Rot, Hoardcurse) that
   slow digs and threaten holds; brings back infested holds.
2. **Delving tradition and mining tree** (LotR RiE, TODO list): a dwarven culture tradition and a mining lifestyle
   tree that speed campaigns.
3. **Expeditions** (EU4 expeditions and dungeons, LotR mining activity): activities from a hold into the deep for
   treasure, artifacts and lore.
4. **The Runelink** (EU4): rail between holds as a building chain; movement and supply between linked holds.
5. **Runesmithing** (EU4 runes, LotR crafting): dwarven artifacts made at the Runeforge.
6. **Hold models on the map** (LotR's Erebor gate): art, pending permission for LotR assets.

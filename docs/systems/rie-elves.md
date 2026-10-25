# Elven Haven (RiE elven holding and elf buildings)

## Generated files

| File | Generator | Why |
|---|---|---|
| `common/buildings/aov_elven_buildings.txt`, `common/buildings/aov_elven_haven.txt`, `common/scripted_triggers/aov_elven_triggers.txt`, `common/script_values/aov_elven_values.txt`, `common/scripted_effects/aov_elven_haven_effects.txt`, `localization/english/aov_elven_l_english.yml`, the building type icons the blocks name (`gfx/interface/icons/building_types/`), `gfx/interface/icons/holding_types_tab/elven_holding.dds`, `gfx/interface/illustrations/holding_types/refuge_*.dds` | `python -I tools/build_rie_elves.py` | RiE's elf buildings and elven settlement levels, copied block by block through the elf rewrite rules (data `tools/data/rie_elves.py`), with our names; the Haven levels take the castle models of `build_holding_models.py`; the conversion effect is built from the data and Anbennar's castle and tribe build lists. Run after `build_rie_dwarves.py`, before `build_holdings_override.py` (which lists the Haven's buildings) and `build_governments_override.py`; rerun `build_racial_levies.py` afterwards (it reads the elven buildings' levy bonuses). |

Hand-written: `common/on_action/aov_elven_haven_on_actions.txt` (game start), `common/decisions/aov_elven_haven_decisions.txt`,
`events/aov_elven_haven_events.txt` (picker), `common/scripted_effects/aov_elven_haven_decision_effects.txt`,
`common/scripted_triggers/aov_elven_haven_triggers.txt`, `common/script_values/aov_elven_haven_conversion_values.txt`,
`common/modifier_definition_formats/aov_elven_haven_formats.txt`, `localization/english/aov_elven_haven_decisions_l_english.yml`,
and the Haven branch of `common/scripted_triggers/zz_aov_building_requirement_triggers.txt`.

## System

- **Holding:** `elven_holding` ("Elven Haven"), `primary_building = elven_settlement_01`, levels `elven_settlement_01..07`
  (Haven Glade to Shining Haven City) with RiE's level stats. Its build list (`build_rie_elves.haven_buildings`) is
  the 24 elf lines, the artificer and battlemage academies and the 15 RiE mines; no vanilla building. Every government
  that accepts castles accepts it (tribal included). The two holding-level requirement triggers count Haven levels
  1/3/5/7 as castle levels 1-4, so duchy and special buildings work in a Haven.
- **Models:** level N shows the castle models of `HAVEN_ASSET_BAND[N]` (castle 1/1/2/2/3/3/4) from
  `build_holding_models.py`, so moon and sun elves see the high-elf castles and wood elves the sanctuaries; their
  pictures are RiE's refuge illustrations (`ILLUSTRATIONS`).
- **Elves only:** every copied block checks `is_elvish_culture` in `can_construct_potential` or `can_construct` (the build
  stops otherwise); Haven levels need an elven holder (`aov_rie_elf_holder_trigger`) to be raised. The Haven levels
  have no `is_enabled`: a non-elf who takes a Haven keeps its stats but cannot raise it, and the elven buildings in
  it stop working (their `is_enabled`).
- **Rewrites** (data `TOKEN_RENAMES`, `BLOCK_REPLACEMENTS`, `DROP_STATEMENTS`): `is_elf` to `is_elvish_culture`; RiE's
  Maiar, hope, Valinor, wastelands, elven-county and tribal gates removed (tribal elves may raise Havens); RiE's
  guild parameter gate reduced to its default level; RiE's high elves (`heritage_calaquendi`) are moon and sun elves;
  RiE's monster men-at-arms modifiers dropped; every `effect_desc` dropped (they describe activity discounts wired to
  RiE activities or vanilla building keys); RiE's three elven terrain triggers copied as `aov_rie_elven_*` without
  terrains Anbennar lacks. RiE's per-duchy and per-kingdom caps on Haven levels are commented out in RiE itself, so
  there are none.
- **Text:** every name and description is ours (`NAMES`, `HOLDING_LOC`); `FORBIDDEN_LORE` stops any Middle-earth word.
- **Conversion** (`aov_convert_to_elven_haven_effect`, barony province scope): Haven level from `LEVEL_MAP` (castle
  1/2/3/4 to 1/3/5/7, tribe 1/2 to 1/2); vanilla buildings in `BUILDING_MAP` become their elven line at the same level
  (capped at the line's top and the Haven level); every other building a castle or tribe lists is removed (mines and
  academies stay); then `set_holding_type = elven_holding` and the Haven buildings are added.
- **Game start:** every elf-held castle or tribe in a county of elven culture converts (`aov_elven_haven_game_start`,
  on `on_game_start`). An elf ruling a county of another culture (Eborthíl, Tefori) converts it by decision. Cities
  and temples do not convert.
- **Decision:** *Raise an Elven Haven* (`aov_raise_elven_haven_decision`, elf ruler of at least a county, 5-year
  cooldown) opens `aov_elven_haven.1`, which offers up to three eligible domain baronies (capital first, then by
  Haven level); the chosen one costs 100 gold per Haven level and 100 prestige. The AI takes it with twice the cost.
- **To confirm in game:** the start conversion (levels, swapped buildings, nothing vanilla left in a slot);
  `set_holding_type` and `add_building` order; the county view and holding tab for a Haven; Deepwoods tribes with a
  Haven capital (tribal mechanics); the picker names and costs.

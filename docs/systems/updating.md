# Updating to a new Anbennar version, CK3 patch or RiE update

1. Replace `../anbennar-ck3-dev-master` with the new Anbennar release.
2. Run `python -I tools/build_rie_dwarves.py` first (the next two import its output), then `python -I tools/build_holdings_override.py` and `python -I tools/build_holds.py` and `python -I tools/build_governments_override.py` and `python -I tools/build_hud_override.py` and `python -I tools/build_lifestyle_override.py` and `python -I tools/build_county_view_override.py`, and `python -I tools/build_map_graphics.py`, and `python -I tools/build_holding_models.py` (the culture files are whole-file overrides of Anbennar's) and `python -I tools/build_portraits.py` (the gene files are whole-file overrides of Anbennar's) and `python -I tools/build_rie_courts.py` (Anbennar's scripted illustrations and court scene cultures are whole-file overrides) and `python -I tools/build_monuments.py` (the monument overrides copy Anbennar's current definitions; it errors naming any monument key Anbennar no longer defines) and `python -I tools/build_deepwoods_groves.py` (it errors when a grove county was renamed or moved). The `map_data/` height files are whole-file overrides of Anbennar's, regenerated from its new heightmap by `build_map_graphics.py`.
3. Run tiger and the tool tests (below) and fix anything that references renamed Anbennar content. The tests fail if
   Anbennar renames `anb_enhance_ability_interaction` or adds another way to start its Enhance Ability scheme (removed
   from the game; see `EnhanceAbilityRemovedTests`).
4. Re-copy Anbennar's `title_revocation_standard_can_pick_title_trigger` (`common/scripted_triggers/00_interaction_triggers.txt`)
   into `common/scripted_triggers/zz_aov_interaction_triggers.txt`, keeping the `# Anbennar Overhaul` faction-title exclusion.
5. Re-copy Anbennar's `building_requirement_castle_city_church` and
   `building_requirement_castle_city_church_temple_citadel_tribe` (`common/scripted_triggers/00_building_requirement_triggers.txt`)
   into `common/scripted_triggers/zz_aov_building_requirement_triggers.txt`, keeping the `# Anbennar Overhaul` dwarven
   hold branch (castle levels 01/02/03/04 = hold levels 1/3/5/8). `BuildingRequirementOverrideTests` fails until they match.
6. Re-copy Anbennar's `start_compel_interaction` and `start_dominate_interaction` into
   `common/character_interactions/zz_aov_spell_overrides.txt`, keeping the `# Anbennar Overhaul` lines. Its
   `anb_enhance_ability_interaction` is a never-shown stub and needs no re-copy.
7. Test in game; check `database_conflicts.log` for overhaul keys now also defined by Anbennar (notably `magic_duelist_focus`, which `zz_aov_magic_focuses.txt` must keep overriding).

After a CK3 patch, rerun `python -I tools/build_hud_override.py`, `python -I tools/build_lifestyle_override.py` and `python -I tools/build_county_view_override.py` too: their sources are the game's `hud.gui`, `window_character_lifestyle.gui` and `window_county_view.gui` (when Anbennar ships no copy).
Rerun `python -I tools/build_map_graphics.py` too once Realms in Exile has updated for the patch (its shaders are the source).
Rerun `python -I tools/build_holding_models.py` too after a CK3 patch (`city_01..04` are copied from the game) and after a Realms in Exile update (its holding models and shaders are the source).
Rerun `python -I tools/build_portraits.py` too after a CK3 patch (it skips files and names the game already has) and after a Realms in Exile update (its portrait entries, templates, accessories and models are the source).
Rerun `python -I tools/build_rie_courts.py` too after a CK3 patch (the grandeur levels file is the game's) and after a Realms in Exile update.
Rerun `python -I tools/build_rie_dwarves.py`, then `build_holds.py` and `build_holdings_override.py`, after a Realms in Exile update (its dwarf buildings, ore modifiers, `dwarven_depths` levels and pictures are the source) and after a CK3 patch (it skips icons and names the game already has).

## Generator commands

| Task | Command |
|---|---|
| Validate (new reports only) | `python -I tools/validate.py` |
| Validate (everything) | `python -I tools/validate.py --all` |
| Accept current reports as baseline | `python -I tools/validate.py --baseline` (only after confirming they are inherited from Anbennar or from a file copied verbatim from Realms in Exile) |
| Rebuild holdings override | `python -I tools/build_holdings_override.py` |
| Rebuild RiE dwarves | `python -I tools/build_rie_dwarves.py` (needs Realms in Exile installed; run before `build_holds.py` and `build_holdings_override.py`, which import its output) |
| Rebuild dwarven holds | `python -I tools/build_holds.py` (copies Anbennar's castle assets into the hold levels; level effects from `build_rie_dwarves.py`) |
| Rebuild governments override | `python -I tools/build_governments_override.py` |
| Rebuild HUD override | `python -I tools/build_hud_override.py` |
| Rebuild lifestyle window override | `python -I tools/build_lifestyle_override.py` |
| Rebuild county view override | `python -I tools/build_county_view_override.py` |
| Import EU4 monuments | `python -I tools/import_eu4_monuments.py --region <name>` (`cannor`, `dwarovar`, `bulwar`, `salahad`, `deepwoods`; needs the EU4 Anbennar, Cannorian and Dwarven Monuments mods installed; rewrites `tools/data/monuments/<region>.py`) |
| Rebuild monuments | `python -I tools/build_monuments.py` (every region; `--region <name>` for one, the shared illustration file is always rebuilt from all) |
| Run tool tests | `python -I -m unittest discover -s tools/tests -v` |
| Rebuild inventions | `python -I tools/build_inventions.py` (needs EU4 Anbennar installed for icons) |
| Rebuild spells | `python -I tools/build_spells.py` (needs EU4 Anbennar installed for magic art) |
| Rebuild magic lifestyle art | `python -I tools/build_magic_lifestyle_art.py` (needs EU4 Anbennar and CK3 installed) |
| Rebuild map graphics | `python -I tools/build_map_graphics.py` (needs Realms in Exile installed) |
| Rebuild holding models | `python -I tools/build_holding_models.py` (needs Realms in Exile installed) |
| Rebuild RiE portraits | `python -I tools/build_portraits.py` (needs Realms in Exile installed; the clothing keys in the culture files come from `build_holding_models.py`) |
| Rebuild RiE backgrounds and courts | `python -I tools/build_rie_courts.py` (needs Realms in Exile installed; uses the clothing keys of `build_portraits.py`) |
| Rebuild Deepwoods grove arms and names | `python -I tools/build_deepwoods_groves.py` (needs EU4 Anbennar installed for the flags and province names) |

# Updating to a new Anbennar version, CK3 patch or RiE update

1. Replace `../anbennar-ck3-dev-master` with the new Anbennar release.
2. Run `python -I tools/build_rie_dwarves.py` first (the next two import its output), then `python -I tools/build_holdings_override.py` and `python -I tools/build_holds.py` and `python -I tools/build_governments_override.py` and `python -I tools/build_hud_override.py` and `python -I tools/build_lifestyle_override.py` and `python -I tools/build_county_view_override.py`, and `python -I tools/build_map_graphics.py`, and `python -I tools/build_holding_models.py` (the culture files are whole-file overrides of Anbennar's) and `python -I tools/build_portraits.py` (the gene files are whole-file overrides of Anbennar's) and `python -I tools/build_rie_courts.py` (Anbennar's scripted illustrations and court scene cultures are whole-file overrides) and `python -I tools/build_monuments.py` (the monument overrides copy Anbennar's current definitions; it errors naming any monument key Anbennar no longer defines); and `python -I tools/build_racial_levies.py` (new Anbennar levy sources; it errors on a `levy_size` in a folder it does not know); and `python -I tools/build_knight_icons.py` (its interface files are whole-file overrides of the game's and Anbennar's); then check that the Deepwoods grove counties and baronies still exist (their arms and names are hand-maintained, see `deepwoods-groves.md`). The `map_data/` height files are whole-file overrides of Anbennar's, regenerated from its new heightmap by `build_map_graphics.py`.
3. Run tiger and the tool tests (below) and fix anything that references renamed Anbennar content. The tests fail if
   Anbennar renames `anb_enhance_ability_interaction` or adds another way to start its Enhance Ability scheme (removed
   from the game; see `EnhanceAbilityRemovedTests`). If Anbennar changes the `lich` trait's `opposites`, copy them into
   `aov_adv_can_become_lich` (`common/scripted_triggers/aov_advancement_conditions.txt`; Lichdom level 3).
4. Re-copy Anbennar's `title_revocation_standard_can_pick_title_trigger` (`common/scripted_triggers/00_interaction_triggers.txt`)
   into `common/scripted_triggers/zz_aov_interaction_triggers.txt`, keeping the `# Anbennar Overhaul` faction-title exclusion.
5. Re-copy Anbennar's `building_requirement_castle_city_church` and
   `building_requirement_castle_city_church_temple_citadel_tribe` (`common/scripted_triggers/00_building_requirement_triggers.txt`)
   into `common/scripted_triggers/zz_aov_building_requirement_triggers.txt`, keeping the `# Anbennar Overhaul` dwarven
   hold branch (castle levels 01/02/03/04 = hold levels 1/3/5/8). `BuildingRequirementOverrideTests` fails until they match.
6. Re-copy Anbennar's `start_compel_interaction` and `start_dominate_interaction` into
   `common/character_interactions/zz_aov_spell_overrides.txt`, keeping the `# Anbennar Overhaul` lines. Its
   `anb_enhance_ability_interaction` is a never-shown stub and needs no re-copy.
7. If `tools/tests/test_racial_armies.py` fails, re-copy the changed Anbennar fields into the racial armies overrides
   (four heritages, two traditions, 15 men-at-arms types; see `racial-armies.md`).
8. Test in game; check `database_conflicts.log` for overhaul keys now also defined by Anbennar (notably `magic_duelist_focus`, which `zz_aov_magic_focuses.txt` must keep overriding).

After a CK3 patch, rerun `python -I tools/build_hud_override.py`, `python -I tools/build_lifestyle_override.py` and `python -I tools/build_county_view_override.py` too: their sources are the game's `hud.gui`, `window_character_lifestyle.gui` and `window_county_view.gui` (when Anbennar ships no copy).
Rerun `python -I tools/build_map_graphics.py` too once Realms in Exile has updated for the patch (its shaders are the source).
Rerun `python -I tools/build_holding_models.py` too after a CK3 patch (`city_01..04` are copied from the game) and after a Realms in Exile update (its holding models and shaders are the source).
Rerun `python -I tools/build_portraits.py` too after a CK3 patch (it skips files and names the game already has) and after a Realms in Exile update (its portrait entries, templates, accessories and models are the source).
Rerun `python -I tools/build_knight_icons.py` too after a CK3 patch (the military, knights, army and battle summary windows are the game's).
Rerun `python -I tools/build_racial_levies.py` too after a CK3 patch (the game's buildings, traditions and doctrines are levy sources).
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
| Rebuild race knight badges | `python -I tools/build_knight_icons.py` |
| Rebuild racial levy correction | `python -I tools/build_racial_levies.py` |
| Rebuild monuments | `python -I tools/build_monuments.py` (every region; `--region <name>` for one, the shared illustration file is always rebuilt from all) |
| Run tool tests | `python -I -m unittest discover -s tools/tests` |
| Rebuild inventions | `python -I tools/build_inventions.py` (icons are committed; nothing is read from EU4) |
| Rebuild spells | `python -I tools/build_spells.py` (art is committed; nothing is read from EU4) |
| Rebuild magic advancements | `python -I tools/build_advancements.py` (art is committed; nothing is read from EU4) |
| Rebuild map graphics | `python -I tools/build_map_graphics.py` (needs Realms in Exile installed) |
| Rebuild holding models | `python -I tools/build_holding_models.py` (needs Realms in Exile installed) |
| Rebuild RiE portraits | `python -I tools/build_portraits.py` (needs Realms in Exile installed; the clothing keys in the culture files come from `build_holding_models.py`) |
| Rebuild RiE backgrounds and courts | `python -I tools/build_rie_courts.py` (needs Realms in Exile installed; uses the clothing keys of `build_portraits.py`) |

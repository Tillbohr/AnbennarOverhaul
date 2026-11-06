# Updating to a new Anbennar version, CK3 patch or RiE update

1. Replace `../anbennar-ck3-dev-master` with the new Anbennar release.
2. Run `python -I tools/build_serpentreach.py` first (it draws Serpentreach, Segbandal and West Dwarovar; its `provinces.png`, `definition.csv`, `default.map`, `adjacencies.csv` and 8 locator files are whole-file overrides of Anbennar's; `build_holds.py` and `build_map_graphics.py` use its titles and layout, and `build_holding_models.py` and `build_holds.py` its province terrain (the dwarf model's province lists); it stops naming the problem if province 2426 or the EU4 fit changed, see `serpentreach.md`), then `python -I tools/build_segbandal.py` (Segbandal's titles and history; it follows Anbennar's Segbandal titles and stops naming any `EXISTING` county Anbennar dropped, see `segbandal.md`), then `python -I tools/build_west_dwarovar.py` (West Dwarovar's titles and history; it stops if Anbennar gives Khugdihr a holder or a new county, see `west-dwarovar.md`), then `python -I tools/build_rie_dwarves.py` (the next two import its output), then `python -I tools/build_rie_elves.py` (the holdings override imports its Haven build list), then `python -I tools/build_holdings_override.py` and `python -I tools/build_holds.py` and `python -I tools/build_governments_override.py` and `python -I tools/build_hud_override.py` and `python -I tools/build_lich_maa.py` (Anbennar's generic men-at-arms and the recruit screens) and `python -I tools/build_lifestyle_override.py` and `python -I tools/build_county_view_override.py`, and `python -I tools/build_map_graphics.py`, and `python -I tools/build_holding_models.py` (the culture files are whole-file overrides of Anbennar's) and `python -I tools/build_portraits.py` (the gene files are whole-file overrides of Anbennar's) and `python -I tools/build_rie_courts.py` (Anbennar's scripted illustrations and court scene cultures are whole-file overrides) and `python -I tools/build_monuments.py` (the monument overrides copy Anbennar's current definitions; it errors naming any monument key Anbennar no longer defines); and `python -I tools/build_racial_levies.py` (new Anbennar levy sources; it errors on a `levy_size` in a folder it does not know); and `python -I tools/build_knight_icons.py` (its interface files are whole-file overrides of the game's and Anbennar's); and `python -I tools/build_holy_sites.py` (14 Anbennar religion files are whole-file overrides, for the Halessi and High Philosophy holy sites, the faith icons replacing `the_dame` and the Jaherian Cults icon; and Anbennar's patron deity and infernalist doctrine files, which gain `icon` lines); and `python -I tools/build_race_relations.py` (Anbennar's `anb_marriage_trigger` and the two alliance interactions, copied with the race relations gate); and `python -I tools/build_racial_traditions.py` (it errors naming any culture or tradition Anbennar no longer defines); and `python -I tools/build_dynasty_names.py` (its name lists copy Anbennar's given names; it errors naming any name list Anbennar dropped or gave real dynasty names, which then comes out of `tools/data/dynasty_names.py`); and `python -I tools/build_gnoll_portraits.py` (Anbennar's head assets are whole-file overrides; it errors if Anbennar's kobold head lines it anchors on are gone); then check that the Deepwoods grove counties and baronies still exist (their arms and names are hand-maintained, see `deepwoods-groves.md`). If `tools/tests/test_base_art_fixes.py` fails, follow `base-art-fixes.md` (copied art and men-at-arms icon overrides). The `map_data/` height files are whole-file overrides of Anbennar's, regenerated from its new heightmap by `build_map_graphics.py`.
3. Run tiger and the tool tests (below) and fix anything that references renamed Anbennar content. The tests fail if
   Anbennar renames `anb_enhance_ability_interaction` or adds another way to start its Enhance Ability scheme (removed
   from the game; see `EnhanceAbilityRemovedTests`). If Anbennar changes the `lich` trait's `opposites`, copy them into
   `aov_adv_can_become_lich` (`common/scripted_triggers/aov_advancement_conditions.txt`; Lichdom level 3). The lich
   portrait (`gfx/portraits/portrait_modifiers/aov_lich.txt`) and the gnoll portrait (`aov_gnoll.txt`) set the
   `hairstyles` and `beards` genes to `no_hairstyles` and `no_beard` (`mode = add`: the engine rejects `replace` on
   these special genes), and the Lich's clothes replace `clothes`, `cloaks` and `headgear` with `no_clothes`, `no_cloak`
   and `no_headgear`; check those templates still exist after an Anbennar update.
4. Re-copy Anbennar's `title_revocation_standard_can_pick_title_trigger` (`common/scripted_triggers/00_interaction_triggers.txt`)
   into `common/scripted_triggers/zz_aov_interaction_triggers.txt`, keeping the `# Anbennar Overhaul` faction-title exclusion.
5. Re-copy Anbennar's `building_requirement_castle_city_church` and
   `building_requirement_castle_city_church_temple_citadel_tribe` (`common/scripted_triggers/00_building_requirement_triggers.txt`)
   into `common/scripted_triggers/zz_aov_building_requirement_triggers.txt`, keeping the `# Anbennar Overhaul` dwarven
   hold branch (castle levels 01/02/03/04 = hold levels 1/3/5/8) and Elven Haven branch (Haven levels 1/3/5/7). `BuildingRequirementOverrideTests` fails until they match.
6. `common/character_interactions/zz_aov_spell_overrides.txt` holds never-shown stubs for Anbennar's
   `start_compel_interaction`, `start_dominate_interaction` and `anb_enhance_ability_interaction`; none needs a re-copy.
   `CompelDominateHiddenTests` and `EnhanceAbilityRemovedTests` fail if Anbennar renames one or adds another way to
   start its scheme: hide the new entry point the same way.
7. If `tools/tests/test_racial_armies.py` fails, re-copy the changed Anbennar fields into the racial armies overrides
   (four heritages, three traditions, 15 men-at-arms types; see `racial-armies.md`).
   Likewise for `tools/tests/test_cultural_maa.py`: re-copy the two mage men-at-arms, the tradition and the
   innovation it names (see `magic.md`, Mage men-at-arms), and give any new "LOC TO-DO" cultural unit a line in
   `localization/replace/english/aov_maa_flavor_replace_l_english.yml`.
   And for `tools/tests/test_faith_maa.py`: re-copy the four faith men-at-arms and their four traditions (see
   `faith-maa.md`).
   If `tools/tests/test_tradition_texts.py` fails, give each new placeholder tradition ("Test MAA", "TODO") a name
   and description in `localization/replace/english/aov_tradition_text_replace_l_english.yml`, and drop lines for
   traditions Anbennar has since named or removed.
   If `tools/tests/test_trait_text.py` fails, Anbennar has written its own Sun Reborn text: drop our lines from
   `aov_trait_text_replace_l_english.yml` (see `base-art-fixes.md`).
   If `tools/tests/test_decision_texts.py` fails, write the missing decision text (or drop lines Anbennar has since
   written) in `localization/replace/english/aov_decision_text_replace_l_english.yml`; its tooltips describe each
   decision's script, so reread the script if Anbennar changed what a decision does. If its `DecisionOverrideTests`
   fail, re-copy the decision from Anbennar into `common/decisions/zz_aov_decision_overrides.txt`, keeping the line
   marked `# Anbennar Overhaul` (Restore the Reaver Kingdom of Divenhal points its `desc` at the `_desc` key), or
   drop the override if Anbennar fixed it.
   If `TraditionRemovalTests.test_sundancer_is_anbennars_without_the_levy_penalty` (`test_racial_armies.py`) fails,
   re-copy Anbennar's `tradition_sundancer_legions` into `zz_aov_racial_traditions.txt` without its `levy_size` and
   `levy_reinforcement_rate` lines (see `racial-traditions.md`).
   If `tools/tests/test_elven_cultures.py` fails: for `PuristOverrideTests`, re-copy Anbennar's
   `roll_racial_purity_trait_for_character` (`common/scripted_effects/anb_scripted_effects/anb_racial_effects.txt`)
   into `common/scripted_effects/zz_aov_elven_culture_overrides.txt`, keeping the two lines marked
   `# Anbennar Overhaul`; for `CultureDefinitionTests`, copy the parent culture's changed field into
   `aov_elven_cultures.txt`; for `GameStartTests`, fix the title list in `aov_elven_cultures_effects.txt` (see
   `elven-cultures.md`).
8. Test in game; check `database_conflicts.log` for overhaul keys now also defined by Anbennar (notably `magic_duelist_focus`, which `zz_aov_magic_focuses.txt` must keep overriding).

After a CK3 patch, rerun `python -I tools/build_hud_override.py`, `python -I tools/build_lifestyle_override.py` and `python -I tools/build_county_view_override.py` too: their sources are the game's `hud.gui`, `window_character_lifestyle.gui` and `window_county_view.gui` (when Anbennar ships no copy).
After a CK3 patch, if `PerkAlertTests` fails, re-copy the game's `action_can_spend_perk_point`
(`common/important_actions/00_lifestyle.txt`) into `common/important_actions/zz_aov_lifestyle_actions.txt`, keeping the
`aov_has_focus_magic = yes # Anbennar Overhaul` line in its `NOR`.
Rerun `python -I tools/build_map_graphics.py` too once Realms in Exile has updated for the patch (its shaders are the source).
Rerun `python -I tools/build_holding_models.py` too after a CK3 patch (`city_01..04` are copied from the game) and after a Realms in Exile update (its holding models and shaders are the source).
Rerun `python -I tools/build_portraits.py` too after a CK3 patch (it skips files and names the game already has) and after a Realms in Exile update (its portrait entries, templates, accessories and models are the source).
Rerun `python -I tools/build_knight_icons.py` too after a CK3 patch (the military, knights, army and battle summary windows are the game's).
Rerun `python -I tools/build_racial_levies.py` too after a CK3 patch (the game's buildings, traditions and doctrines are levy sources).
Rerun `python -I tools/build_rie_elves.py` and `python -I tools/build_racial_levies.py` (in generator order) whenever `ADDITIONS` in `build_holdings_override.py` change (the Haven conversion removal list and the levy count read those buildings).
Rerun `python -I tools/build_race_relations.py` too after a CK3 patch (the alliance interactions are the game's, shipped in Anbennar's `00_alliance.txt`).
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
| Rebuild RiE elves (Elven Haven) | `python -I tools/build_rie_elves.py` (needs Realms in Exile installed; after `build_rie_dwarves.py`, before `build_holdings_override.py` and `build_governments_override.py`) |
| Rebuild dwarven holds | `python -I tools/build_holds.py` (copies Anbennar's castle assets into the hold levels; level effects from `build_rie_dwarves.py`) |
| Rebuild governments override | `python -I tools/build_governments_override.py` |
| Rebuild HUD override | `python -I tools/build_hud_override.py` |
| Rebuild lifestyle window override | `python -I tools/build_lifestyle_override.py` |
| Rebuild county view override | `python -I tools/build_county_view_override.py` |
| Rebuild race knight badges | `python -I tools/build_knight_icons.py` |
| Rebuild gnoll head assets | `python -I tools/build_gnoll_portraits.py` (`--import` re-copies the art from Victoria 3 Anbennar) |
| Rebuild holy sites and faith icons | `python -I tools/build_holy_sites.py` |
| Rebuild racial levy correction | `python -I tools/build_racial_levies.py` |
| Rebuild race relations overrides | `python -I tools/build_race_relations.py` |
| Rebuild dynasty name lists | `python -I tools/build_dynasty_names.py` (EU4 names are committed in `tools/data/dynasty_names.py`; nothing is read from EU4) |
| Rebuild racial traditions | `python -I tools/build_racial_traditions.py` (needs the unit art copied; then rerun `build_racial_levies.py` if a tradition gained a levy modifier) |
| Rebuild monuments | `python -I tools/build_monuments.py` (every region; `--region <name>` for one, the shared illustration file is always rebuilt from all) |
| Run tool tests | `python -I tools/run_tests.py` (or, one after another, `python -I -m unittest discover -s tools/tests`) |
| Rebuild inventions | `python -I tools/build_inventions.py` (icons are committed; nothing is read from EU4) |
| Rebuild spells | `python -I tools/build_spells.py` (art is committed; nothing is read from EU4) |
| Rebuild magic advancements | `python -I tools/build_advancements.py` (art is committed; nothing is read from EU4) |
| Rebuild map graphics | `python -I tools/build_map_graphics.py` (needs Realms in Exile installed) |
| Rebuild Serpentreach | `python -I tools/build_serpentreach.py` (needs EU4 Anbennar installed; draws Serpentreach, Segbandal and West Dwarovar; run before `build_segbandal.py`, `build_west_dwarovar.py`, `build_holds.py`, `build_holding_models.py` and `build_map_graphics.py`) |
| Rebuild Segbandal | `python -I tools/build_segbandal.py` (needs EU4 Anbennar installed; run after `build_serpentreach.py`, before `build_holds.py`, `build_holding_models.py` and `build_map_graphics.py`) |
| Rebuild West Dwarovar | `python -I tools/build_west_dwarovar.py` (needs EU4 Anbennar installed; run after `build_serpentreach.py` and `build_segbandal.py`, before `build_rie_elves.py`, `build_holds.py`, `build_holding_models.py` and `build_map_graphics.py`) |
| Rebuild Dwarovar tribes | `python -I tools/build_dwarovar_tribes.py` (needs EU4 Anbennar installed; run after `build_governments_override.py`, whose tribal government it copies, and after `build_west_dwarovar.py`; before `build_holds.py`; rerun after a CK3 patch or an Anbennar update, for the government, the six blocked decisions and the Segbandal's titles) |
| Rebuild holding models | `python -I tools/build_holding_models.py` (needs Realms in Exile installed) |
| Rebuild RiE portraits | `python -I tools/build_portraits.py` (needs Realms in Exile installed; the clothing keys in the culture files come from `build_holding_models.py`) |
| Rebuild RiE backgrounds and courts | `python -I tools/build_rie_courts.py` (needs Realms in Exile installed; uses the clothing keys of `build_portraits.py`) |

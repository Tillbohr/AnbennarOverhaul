# Magic schools and magic lifestyle

The Magic HUD tab and the mana in the resource bar sit in the generated `gui/hud.gui` (see artificery.md).

## Generated files

| File | Generator | Why |
|---|---|---|
| `gui/window_character_lifestyle.gui` | `python -I tools/build_lifestyle_override.py` | The lifestyle window is whole-file only. The script copies Anbennar's `gui/window_character_lifestyle.gui` if it has one, else the game's, and adds a `magic_lifestyle` copy after each of the three `wanderer_lifestyle` blocks (XP bar background, progress bar, unspent-points icon) using the magic art (marked `# Anbennar Overhaul: magic lifestyle`). Never edit the output by hand. |
| `common/modifiers/aov_spell_modifiers.txt`, `common/scripted_triggers/aov_spell_triggers.txt`, `common/scripted_effects/aov_spell_effects.txt`, `common/scripted_guis/aov_spell_sgui.txt`, `common/character_interactions/aov_spell_interactions.txt`, `gui/aov_magic_generated.gui`, `localization/english/aov_spells_l_english.yml`, `gfx/interface/icons/aov_magic/`, `gfx/interface/skinned/hud_maintab/aov_maintab_magic.dds` | `python -I tools/build_spells.py` | One block per spell, generated from `tools/data/spells.py` (edit the data, then rerun). The magic art (`gfx/interface/icons/aov_magic/`, the Magic tab icon) was imported once from EU4 Anbennar and is committed (not rebuilt); the build stops when a file the GUI names is missing. |
| `common/scripted_triggers/aov_advancement_triggers.txt`, `common/script_values/aov_advancement_values.txt`, `common/scripted_effects/aov_advancement_effects.txt`, `common/scripted_guis/aov_advancement_sgui.txt`, `gui/aov_advancements_generated.gui`, `localization/english/aov_advancements_l_english.yml` | `python -I tools/build_advancements.py` | One block per advancement (start, can-start, costs, completion dispatch, AI pick, Advancements page), generated from `tools/data/advancements.py`. Costs and durations are the generator's `GOLD`/`MANA`/`YEARS`. EU4's project plate and progress bar (`gfx/interface/icons/aov_magic/project_*.dds`) were imported once and are committed. |
| `common/men_at_arms_types/zz_aov_lich_maa_overrides.txt`, `common/scripted_triggers/aov_lich_maa_forbidden_triggers.txt`, `gui/window_menatarms_type_view.gui`, `gui/window_menatarms.gui` | `python -I tools/build_lich_maa.py` | A Lich's men-at-arms (see Lich men-at-arms below): Anbennar's generic men-at-arms (its `00_maa_types.txt`, else the game's) except siege engines, copied with `NOT = { has_trait = lich }` first in `can_recruit`, and the same list as `aov_lich_maa_forbidden_regiment`; the two recruit screens (whole-file only, from Anbennar else the game) with mana prices and the pay hook (marked `# Anbennar Overhaul`). It errors if another of our files already overrides one of those types. Never edit the output by hand. |

## Imported files (no generator)

The magic lifestyle art (18 DDS files: `gfx/interface/icons/{lifestyles,focuses,traits,lifestyles_perks,lifestyle_tree_backgrounds}/`
magic files, `gfx/interface/illustrations/lifestyles_background/magic_lifestyle.dds`,
`gfx/interface/progressbars/aov_progress_magic*.dds`) was composed once from EU4 Anbennar magic art and vanilla files.
Its generator `tools/build_magic_lifestyle_art.py` was removed; replace the files directly to change them.

The HUD alert for unspent magic perks, `gfx/interface/icons/alerts/aov_action_lifestyle_magic.dds` (3 frames of 144,
like vanilla's `action_lifestyle_*.dds`), was composed once: the flame of `magic_lifestyle.dds` on the game's
`_frame_purple.dds`. Its alert `aov_action_lifestyle_magic` is in `common/important_actions/aov_magic_lifestyle_actions.txt`;
vanilla's generic `action_can_spend_perk_point` is overridden in `zz_aov_lifestyle_actions.txt` to skip magic focuses
(`aov_has_focus_magic`), so a mage sees the magic alert instead of the generic arrows.

The Lich portrait (Godherja's skeleton, art from Elder Kings) was imported once with a scratch script and is edited by
hand: meshes and textures in `gfx/models/portraits/aov_lich/` (`aov_lich.asset`), accessories
`gfx/portraits/accessories/aov_lich.txt`, rune and gem-eye variations `gfx/portraits/accessory_variations/aov_lich.txt`
(textures in `textures/aov_lich/`); every name is prefixed `aov_`. The genes `common/genes/aov_lich_genes.txt`
(`aov_lich_flesh` hides the living head and body with vanilla's `bs_no_portrait` blend shapes; `aov_lich_head`,
`aov_lich_body`, `aov_lich_eyes`; index 0 of each is nothing) are applied by
`gfx/portraits/portrait_modifiers/aov_lich.txt` to anyone with the `lich` trait, which also removes eyes, lashes,
teeth, hair and beard. **Eyes:** the `aov_lich_eyes` gene holds the gems (template `aov_lich_gem_eyes`) and
Godherja's glowing eyes (`aov_lich_glowing_eyes_<colour>`: blue, gold, green, grey, pink, purple, red, teal, white; a
glowing ring or a full glowing pupil by value), imported once to `gfx/models/portraits/aov_lich/eyes/`
(`aov_lich_eyes.asset`) on the game's eye meshes. Godherja's glow is its own shader's emission from the normal map's blue
channel; Anbennar's `portrait_eye` shader glows from the properties texture's red channel instead
(`EMISSIVE_PROPERTIES_RED`), so each strength has a properties texture whose red is Godherja's mask and the rest
Anbennar's eye properties. The group `aov_lich_eyes` (`usage = both`, so the barbershop shows it as "Lich Eyes") gives
each Lich a random colour (equal weights below 100); in the barbershop a Lich can pick any colour, the gemstones or
empty sockets (weight 0, so never at random). **To confirm in game:** the eyes glow and sit in the skull's sockets, and
the barbershop shows the group for a Lich only. Godherja's lich clothes were imported the same way (scratch script, edited by hand since):
meshes and textures in `gfx/models/portraits/aov_lich/clothes/` (`aov_lich_clothes.asset`; lich colours only), the
accessories and variations in the same `aov_lich` files, and four genes. **Six looks:** each Lich gets one of six
robe-and-hood looks at random (group `aov_lich_outfit`, equal weights below 100, which CK3 picks by weighted random; a
weight of 100 or more is taken outright). A look's robe and hood share one variation pair
(`aov_lich_robes_look_<k>`/`aov_lich_hood_look_<k>`: one row of Godherja's `color_palette_robes_generic.dds` cut into
`color_palette_lich_look_<k>.dds`, and one of its fabric patterns), so they always match; genes `aov_lich_clothes`
(`aov_lich_robes_<k>`) and `aov_lich_hood` (`aov_lich_hood_<k>`: up 3, down 1, none 5; fits under vanilla's `crown`,
`hat`, `cap` and `helmet` tags). The robes hide `clothes` (`no_clothes`) and `cloaks` (`no_cloak`) unless
`portrait_wear_armor_trigger`, when only the hood is added. Vanilla's clothes, cloaks and headgear are extra genes from
`mode = add` modifiers, so they are hidden with `mode = add`; `mode = replace` only rewrites the DNA's gene and left
them showing. `aov_lich_mask` (half-mask for one in three) and `aov_lich_crown` (Godherja's Lich King crown at kingdom
tier, Archlich crown at empire tier, hiding `headgear` with `no_headgear`; the skull-fitted mesh when bare, the wider
one over a hood) have their own groups, so mask and crown vary on their own. Godherja's own cloak and hood-down tags were dropped. The RiE portrait
generator's orphan check skips this folder. The `lich` trait's icon is Godherja's `necromancy_undead_lich.dds` at
`gfx/interface/icons/traits/lich.dds` (120x120; the trait names no icon, so the game uses `<key>.dds`).
**To confirm in game:** vanilla's `no_clothes` (a nudity outfit) stays hidden under the robes; the hood and crown
meshes sit right on the skull.

**Mana in the resource bar:** a mage's mana (`aov_mana`, with `aov_mana_refill_month` as the monthly change) is shown
left of gold in the HUD top bar, as Godherja shows its magic: `tools/build_hud_override.py` inserts the widget before
the gold widget and moves the bar's end cap onto it while it shows (gold gets a plain piece then). Shown when
`aov_magic_available` (the Magic tab's test); icon Godherja's blue magic currency flame `gfx/interface/icons/currencies/icon_mixed_magic_00.dds`, resized to 60x60 with mips (CK3's gold icon size), at `gfx/interface/icons/aov_magic/mana.dds`;
tooltip `AOV_HUD_MANA_TT`. Landed and unlanded Liches get their own character-window backgrounds (see `rie-courts.md`).

**Lich men-at-arms:** a Lich raises the dead instead of recruiting living soldiers. `aov_lich_skeletons` (skirmishers)
and `aov_lich_skeleton_archers` (archers), `common/men_at_arms_types/aov_lich_maa_types.txt`, are Godherja's `skeleton`
and `skeleton_archers` (stats; its `raised_undead` art as `aov_raised_undead`, the regiment icon cut from the small
picture): stack 250, no buy cost, no upkeep, no provisions. They cost mana instead, 0.2 per skeleton (50 a subregiment;
`common/script_values/aov_lich_maa_values.txt`). CK3 costs can only be gold, prestige or piety, and no on_action fires
on a recruit, so: the recruit screens show `AOV_LICH_MAA_COST` instead of the gold price for types whose icon key is
`aov_raised_undead` (the GUI has no type key), their Create and Increase Size buttons run scripted GUI
`aov_lich_maa_pay` right after, and `quarterly_playable_pulse` runs it too (AI recruits, or a Lich short of mana).
`aov_lich_maa_pay` charges for the raised dead's full size (`maa_max_troops_count`) beyond `var:aov_lich_maa_paid`;
what the mana cannot cover stays owed, and `can_recruit` (`aov_lich_maa_can_recruit`: the `lich` trait and mana for the
debt plus one subregiment) blocks more until it is paid. A Lich cannot recruit Anbennar's ten generic men-at-arms
(siege engines stay; cultural and racial troops are untouched, user choice), and on becoming one
(`aov_adv_lich_ascend`, and history Liches on `on_game_start_after_lobby`) loses regiments of those types
(`aov_lich_maa_on_becoming_lich`, `destroy_maa_regiment`). **To confirm in game:** `MenAtArmsType.GetIconKey` works in
the recruit list, the pay runs after Create (else the quarterly tick collects it), whether Increase Size honours
`can_recruit`, AI Liches raise skeletons, and the map models (vanilla soldiers by culture; Godherja's undead models
were not ported).

## System

- **Magic schools:** eight schools (Abjuration, Conjuration, Divination, Enchantment, Evocation, Illusion, Necromancy,
  Transmutation) for mages (`has_magical_affinity`, Anbennar). Mana (100 + 50 per affinity level, refilled quarterly at
  3x the monthly rate), per-school knowledge levels 0-3 (300/800/2000 progress) from studying one chosen school and
  from casting; reaching a level stops the study of that school until the mage presses Study again (AI mages re-pick) (choosing a new school with the Study button opens event `aov_magic.2`, the mage reading in a study;
  AI mages skip it); `magic_mastery` = sum of levels. 48 spells in `tools/data/spells.py` (spec
  `docs/superpowers/specs/2026-10-08-magic-schools-design.md`): self/realm/war spells cast from the Magic window
  (`gui/aov_window_magic.gui`, HUD tab below Artificery, generated pages `gui/aov_magic_generated.gui`), targeted
  spells as interactions in Anbennar's Spells category (Compel, Dominate overridden to need mana and knowledge;
  Anbennar's Enhance Ability is removed from the game by a hidden stub override). Necromancy risks Forbidden Magic Practitioner under witchcraft-illegal/shunned faiths. Spells that only touch a domain, capital, levies or vassals (`needs_land` in `tools/data/spells.py`) need `is_landed`.
  **AI and landless adventurers:** `quarterly_playable_pulse` and `yearly_playable_pulse` fire for landless adventurers too, so AI
  adventurer mages study, cast window spells and start advancements like AI rulers; `needs_land` spells and `aov_adv_has_domain`
  levels keep them off what does nothing without land. Hand-written
  logic in `aov_magic_*` files; Summon Elementals spawns an army (at the capital, or where a landless caster is) removed after the spell's duration (`aov_spell_summon_elementals_years`, extended by Bound Elementals).
- **Magic lifestyle:** fills the "Known gaps" magic-lifestyle skeleton listed in the base mod's CLAUDE.md (which cannot be edited). Anbennar's stub `magic_lifestyle` made full: three trees of 9 perks (Arcane Scholar, Battle Mage,
  Mindweaver; `common/lifestyle_perks/aov_magic_*_perks.txt`), each ending in a trait
  (`common/traits/aov_magic_lifestyle_traits.txt`), and three focuses (`common/focuses/zz_aov_magic_focuses.txt`;
  Anbennar's `magic_duelist_focus` is overridden as Battle Mage, name via `localization/replace/`). Mages only: every
  magic focus has `is_shown`/`is_valid` and every magic perk `can_be_picked` = `has_trait = magical_affinity`, because
  the engine picks game-start focuses and perks by `auto_selection_weight` without checking the lifestyle's `is_valid`
  (`MagesOnlyTests`). Perks feed magic only
  through `common/script_values/aov_magic_lifestyle_values.txt` (the bonus layer: study rate, spell cost and duration,
  mana, dark-magic risk), so tune balance there. Spell cost and duration are per-caster values
  `aov_spell_<k>_cost` / `_years` generated into `common/script_values/aov_spell_values.txt`; casting also grants
  magic lifestyle XP. `magic_mastery` = school levels + magic perks. The art is imported (above); the lifestyle window override comes from
  `tools/build_lifestyle_override.py`. Spec
  `docs/superpowers/specs/2026-10-08-magic-lifestyle-design.md`.
- **Magic advancements:** one three-level advancement per school, adapted from EU4 Anbennar's magical projects
  (spec `docs/superpowers/specs/2026-10-22-magic-advancements-design.md`): Magical Fortress (wards: county modifiers
  re-laid yearly), Summon Extraplanars (a host's men-at-arms and base-type boosts), Orb of Omniscience (court artifact;
  boosts Scry, Foresight, Manipulated Fortune), Enchanted Artifact (one weapon/armor/crown/regalia/trinket per mage,
  strengthened each level; the trinket feeds mana and spell cost), Battlemage Academy (building tiers
  `battlemage_academy_01-03`, Recruit Battlemage Commander decision (the recruit is a gender your faith and culture let lead armies, vanilla's `root_soldier_female_chance`), Battlemages men-at-arms), Mirror Image (+1 all
  skills per level, body double on imprisonment), Lichdom (EU4's Pursue Lichdom: The Phylactery, The Transformation
  Potion, The Dark Ritual, three choice-event steps each in `events/aov_lichdom_events.txt`; the mage drinks the potion,
  dies and rises with Anbennar's `lich` trait and Forbidden Magic Practitioner whatever the faith, no prisoner needed;
  losing the phylactery before then starts Lichdom over), Homunculus (`aov_homunculus` courtier, domain labour). Any mage, landed or not (`aov_adv_eligible`: Magical Affinity; effects that need a capital skip it or use the mage's location); Magical Fortress, Battlemage Academy and Homunculus Labour (level 3) need land (`aov_adv_has_domain`). Level N needs school level N; a level
  costs gold and mana up front and completes on the quarterly tick. A mage either studies or works on one advancement
  (starting clears `aov_studying`; the Study buttons are invalid while `aov_adv_committed` is set); Abandon refunds
  nothing. A level that fires its own event instead of the success one saves scope:aov_adv_own_event: a lost Orb or
  enchanted artifact ends the work (event 44); the Dark Ritual ends in Consumption (`aov_lichdom.10`). Lichdom's steps:
  the generated start effect calls the data's `on_start` hook (`aov_adv_lichdom_on_start`, the first step); the
  quarterly pulse fires the next one at a third and two thirds of the level's months (`aov_adv_lichdom_steps`,
  `var:aov_lichdom_step`); faster choices add progress capped by `aov_lichdom_progress_cap` so every step still fires. A character who loses Magical Affinity abandons the commitment (quarterly tick; `on_title_lost`); a mage who drops to courtier keeps it, frozen, since progress runs on `quarterly_playable_pulse`. State: `aov_adv_committed`, `aov_adv_working_level`, `aov_adv_progress`, `aov_adv_<key>_lvl`, plus
  `aov_adv_orb`, `aov_adv_enchanted_*`, `aov_adv_phylactery`, `aov_lichdom_vessel`, `aov_lichdom_step`, `aov_adv_host`, `aov_adv_homunculus`; all die with the
  mage, while artifacts, homunculi, buildings and regiments remain. Hand-written: level effects
  `common/scripted_effects/aov_advancement_level_effects.txt`, start conditions
  `common/scripted_triggers/aov_advancement_conditions.txt`, events `events/aov_advancement_events.txt`, modifiers,
  men-at-arms, building, decision, trait, templates, on_actions (`aov_advancement_*`). Every balance number is in
  `common/script_values/aov_advancement_tuning.txt`. The Magic window (`gui/aov_window_magic.gui`) has Advancements and
  Spells tabs under the school buttons (GUI variable `aov_magic_tab`, unset = Advancements); study progress shows on
  the Spells tab's school header.
- **Mage men-at-arms:** Anbennar's Battlemages (`battlemages`, shown as War Mages so they differ from the academy's
  own Battlemages) are recruited from a Battlemage Academy of tier 2 or more instead of the Magic Schools innovation;
  the academy also recruits `aov_battlemages` (tier 2) and `aov_battlemages_3` (tier 3). Storm Sorcerers are disabled
  (`can_recruit = { always = no }`; gnomes field artificers instead), their tradition
  `tradition_test_maa_anb_storm_sorcerers` hidden, unpickable and removed from every culture at game start
  (`common/on_action/aov_mage_maa_on_actions.txt`). Both units are Anbennar's blocks with only `can_recruit` changed
  (`common/men_at_arms_types/zz_aov_mage_maa_overrides.txt`, tradition in
  `common/culture/traditions/zz_aov_mage_traditions.txt`); `common/culture/innovations/zz_aov_mage_innovations.txt`
  drops the unit line from Magic Schools, which keeps its +10% magic lifestyle experience. Druids and Skalds are
  recruited by faith (`faith-maa.md`); Wren Hedge Witches and Bladedancers are unchanged. `tools/tests/test_cultural_maa.py` fails when Anbennar changes a copied block
  or adds a cultural mage unit.

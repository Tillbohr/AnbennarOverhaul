# RiE portraits

## Generated files

| File | Generator | Why |
|---|---|---|
| `gfx/portraits/portrait_modifiers/aov_rie_*.txt`, `common/scripted_triggers/aov_rie_portrait_triggers.txt`, `common/genes/03_genes_special_accessories_hairstyles.txt`, `04_genes_special_accessories_beards.txt`, `05_genes_special_accessories_clothes.txt`, `06_genes_special_accessories_headgear.txt`, `07_genes_special_accessories_misc.txt` (whole-file overrides of Anbennar's), `gfx/portraits/accessories/aov_rie_portraits.txt`, `gfx/portraits/accessory_variations/aov_rie_portraits.txt` (with its pattern textures and palettes at RiE's paths), `gfx/models/portraits/**` (`aov_rie_<name>.asset` files and their meshes and textures, at RiE's paths) | `python -I tools/build_portraits.py` | RiE's portrait look for halflings, elves and dwarves from `tools/data/portraits.py` (edit the data, then rerun; see Systems, RiE portraits). Genes are whole-file: each gene file is Anbennar's bytes plus the new RiE templates inside the gene block, between `# Anbennar Overhaul: Realms in Exile templates` and `# Anbennar Overhaul: end of Realms in Exile templates`. 1264 files (~1.1 GiB; `.dds`/`.mesh` via Git LFS). Never edit the output by hand; rerun after an Anbennar or RiE update. `tools/tests/test_build_portraits.py` (`FreshnessTests`) fails when the files are stale or orphaned. |

## System

- **RiE portraits:** halflings wear RiE's hobbit look (gnomes keep Anbennar's, user choice), moon elves RiE's Noldor look, sun elves its Vanyar
  (white and gold) look, wood elves its Lasgalendrim (Silvan) look, and all 11 dwarf cultures RiE's dwarf look (its
  Longbeard, Firebeard and Broadbeam entries: dwarf hats, crowns, boots, royal cloak, armour, hair and beards) over
  Anbennar's vanilla northern European everyday clothes (user choice: its `northern_commoners`/`_low_nobles`/
  `_high_nobles` entries, copied with `"source": "anbennar"`, the high one widened to kings and emperors; RiE's own
  dwarf everyday clothes are vanilla HRE-style ones; RiE's southern and eastern dwarf styles are not used): clothes,
  headgear, legwear, war armour and helmets, hairstyles and beards. Halflings are beardless; female dwarves have no beards (user choice:
  RiE's female dwarf beard entries are not copied and its beard game rules read `always = no`). RiE's generic elves
  wear vanilla clothes, so the sun and moon elves use its Vanyar and Noldor entries (user choice) and its generic
  `elven_clothes_*`/`elven_legwear` are not copied. Spec `docs/superpowers/specs/2026-10-15-rie-portraits-design.md`;
  generator `tools/build_portraits.py`, data `tools/data/portraits.py`. Cultures get the `clothing_gfx` keys
  `aov_hobbit_clothing_gfx`, `aov_vanyar_clothing_gfx` (sun), `aov_noldor_clothing_gfx` (moon),
  `aov_lasgalendrim_clothing_gfx`, `aov_dwarf_clothing_gfx` and `aov_southern_dwarf_clothing_gfx` (copper, gold,
  marble: that key first, then the dwarf key; no entry uses it, it only keeps their differently continuing list apart,
  as CK3 needs every list starting with one key to continue the same way), prepended by `build_holding_models.py`. Each RiE portrait group with
  copied entries becomes a new group `aov_rie_<group>` (`usage = game`, RiE's priority) in `aov_rie_<RiE file>`. It
  sorts after Anbennar's files, so at equal priority it overwrites Anbennar's choice for these races only, while
  religious, situational, special and barbershop groups (higher priority) still win. Inside a group the first modifier
  weighing 100 or more wins, so `ENTRIES` lists a culture's specific entry before the generic one it should beat
  (Valinor before generic elven armour). The entries in `ENTRIES` are RiE's, with renames: `CULTURE_INPUT` and the
  `portrait_<key>_clothing(_spouse)_trigger` names (`INPUTS`: RiE's Vanyar have its generic `elven` key, so `elven` ->
  `aov_vanyar`, `noldor` -> `aov_noldor`; any other RiE culture key becomes `aov_rie_none`, always false; the court
  fashion modifiers' `INPUT_PARAMETER` too), RiE's dwarf heritages (`HERITAGES`: its western clans ->
  `aov_rie_western_dwarf_culture_trigger` = every dwarf of ours, its eastern and southern clans ->
  `aov_rie_other_dwarf_culture_trigger`, always false), RiE's beard game rules
  (`GAME_RULES`) and literal `REPLACE`s (`culture:lasgalendrim`/`vanyar`, RiE's `is_elf` -> `has_elvish_heritage`,
  `cannot_be_killed`, the Oropher dynasty, RiE characters). Option `up_to_emperor` widens an entry's high-noble
  clothing trigger to kings and emperors (Vanyar, Noldor and hobbit noble clothes: RiE has no royal entry for them, so
  their kings would fall back to Anbennar's vanilla robes). `EXTRA_ENTRIES` adds the hobbit no-beard entry and, in the
  cloaks group, no vanilla cloak for elves (RiE's elves get none: they are not in its cloak proxy lists) and for
  hobbit-dressed halfling men (vanilla cloaks clip through RiE's hobbit outfit, seen on a gnome); war cloaks come from the
  armour group, which applies later. The triggers (`aov_rie_portrait_triggers.txt`) take vanilla's shape
  (`portrait_shared_clothing_contents_trigger` with `CULTURE_FLAG = <input>`). The build stops if a copied entry names a
  culture, heritage, title, dynasty, character, scripted trigger or activity type Anbennar lacks. Left out (RiE-only):
  Sindar, Galadhrim, Falathrim, Cuind, Kinn-lai, Penni, Bree variants, eastern and southern dwarves (and RiE's
  western dwarf everyday clothes), title crowns, the Noldor
  second-age, Gil-galad, Glorfindel, Feanorian, golden and high king armour, the Greybeards, sickness, barbershop, the
  hobbit travel cloak (RiE duel flag), the dwarf mining entries (RiE's `activity_mining`) and Oropher's helmet. Hobbit
  women and hobbit hats stay vanilla-styled: RiE has no hobbit women's clothes or hobbit hats. **Genes:** templates the
  entries name and Anbennar lacks (40 today) are copied into the gene block of Anbennar's gene file at the gene's lowest
  free indices; DNA holds an index in one byte, so the build stops above 255 (headgear: 251 of 256 used). A template
  Anbennar also defines with different content (`dwarven_hairstyles`: Anbennar's is vanilla-only) is copied as
  `aov_rie_<name>` and the entries are pointed at it (`template_renames`, a build note lists them). Anbennar also
  reuses six AGOT hair model names (`female_hair_custom_01/02/03/05/07/08`) for its Kheteratan hairstyles, which made
  RiE's dwarf and elf women's hair a white Kheteratan wig: a pdxmesh/entity name Anbennar (not the game) defines with
  other content than RiE (`model_clash`) is copied from RiE as `aov_rie_<name>` with every reference to it, the
  accessories naming such entities are copied as `aov_rie_<accessory>` (`accessory_renames`) and our template
  insertions point at them; a texture whose file name Anbennar or the game has with other content is copied renamed
  too (4 of the 6 are in today's lists). **Assets:** 303 accessories, 476 pdxmesh/entity blocks (copied block by block
  into `aov_rie_<name>.asset` beside RiE's original, so relative mesh paths hold), 58 variation blocks and ~1060
  meshes and textures, all at RiE's
  paths, because RiE names pattern masks and variation textures by full path. Names and files Anbennar or the game
  already has stay theirs (guarded by `test_copied_files_never_shadow_anbennar_or_game`). RiE edits some vanilla files
  in place (23 hair and hood textures; its own meshes depend on the edits: with vanilla's strand texture RiE's opaque
  hair shader drew elf hair flat white), so those are copied as `aov_rie_<name>` into
  `gfx/models/portraits/aov_rie_edited/` (one copy each: CK3 finds textures by name) and the copied blocks are pointed
  at them (`place_file`). Every copied mesh's shader must be an `Effect` of the game's or this mod's shaders.
  **To confirm in game:** that equal-priority groups apply in file order, how RiE's hobbit clothes sit on Anbennar's
  halfling bodies, and the 255 index cap.

# RiE portraits for halflings, gnomes, elves and dwarves (design)

Date: 2026-10-15. Status: approved choices, implementation in `tools/build_portraits.py`.

## Goal

Characters of four Anbennar races wear Realms in Exile's look: clothes, headgear, legwear, cloaks, war armour and
helmets, hairstyles and beards.

| Anbennar cultures | RiE look | clothing_gfx key |
|---|---|---|
| every `heritage_halfling` culture | Hobbit | `aov_hobbit_clothing_gfx` |
| `sun_elvish` | Vanyar (white and gold) | `aov_vanyar_clothing_gfx` |
| `moon_elvish` | Noldor | `aov_noldor_clothing_gfx` |
| `wood_elvish` | Lasgalendrim (Silvan) | `aov_lasgalendrim_clothing_gfx` |
| every `heritage_dwarven` culture | Dwarf (RiE's Longbeard/Firebeard/Broadbeam hats, crowns, boots, armour, hair, beards) over Anbennar's vanilla northern European clothes | `aov_dwarf_clothing_gfx` |
| `copper_dwarvish`, `gold_dwarvish`, `marble_dwarvish` (Anbennar's MENA-dressed dwarves) | the same | `aov_southern_dwarf_clothing_gfx` first (unused; keeps their list apart), then `aov_dwarf_clothing_gfx` |

User choices: all clothing layers plus hair and beards; southern dwarf variant for the three MENA-dressed dwarf cultures.
Halflings and gnomes lose their beards (RiE hobbits are beardless). Round 2 (in-game feedback, 2026-10-16): no female
dwarf beards; sun elves Vanyar and moon elves Noldor, because RiE's generic elves wear vanilla clothes; western
dwarves keep RiE's western set (vanilla HRE-style clothes, as in RiE). Hobbit women and hobbit hats stay
vanilla-styled: RiE has none of its own. Round 3: gnomes keep Anbennar's look (user choice; the hobbit outfit
clipped on them), and Anbennar's reuse of AGOT hair model names is handled (below). Round 4: every dwarf wears
Anbennar's own northern European everyday clothes (its `northern_*` clothes entries, copied with
`"source": "anbennar"` and input `aov_dwarf`) under RiE's dwarf hats, crowns, boots, armour, hair and beards; RiE's
southern and eastern dwarf styles are dropped.

## How CK3 picks the look

Portrait modifier groups (`gfx/portraits/portrait_modifiers`) each pick one modifier for a character; groups apply in
priority order, a later group overwrites the same gene, and equal priorities apply in file order. A group with no
modifier of weight > 0 changes nothing. So the overhaul adds **new groups** (`aov_rie_<RiE group>`) in
`aov_rie_*.txt` files with the RiE group's priority: they sort after Anbennar's `0*`/`anb_*` files and overwrite its
choice for the target races only, while higher-priority groups (religious, situational, special, barbershop) still win.
The groups have `usage = game`, so they never show in the barbershop.

The modifiers are RiE's own entries, copied from a hand-picked list (`tools/data/portraits.py`, `ENTRIES`) with
token renames so they refer to our cultures:

- `CULTURE_INPUT` and the `portrait_<key>_clothing(_spouse)_trigger` names: `hobbit`/`elven`/`noldor`/`lasgalendrim`/
  `dwarf` become `aov_hobbit`/`aov_vanyar`/`aov_noldor`/`aov_lasgalendrim`/`aov_dwarf` (RiE's Vanyar culture has the
  generic elven key; its Vanyar entries add `culture:vanyar`); every other RiE culture key becomes `aov_rie_none`
  (always false). The court fashion modifiers' `INPUT_PARAMETER` is renamed the same way.
- RiE dwarf heritages: `heritage_longbeard`/`firebeard`/`broadbeam` become `aov_rie_western_dwarf_culture_trigger`
  (every dwarf of ours), `heritage_blacklock`/`stonefoot`/`ironfist`/`stiffbeard` become
  `aov_rie_other_dwarf_culture_trigger` (always false).
- RiE's dwarf beard game rules become `always = no` (no female dwarf beards; their entries are not copied either).
- Per-entry literal replacements in the data for anything else (e.g. `culture:lasgalendrim`).
- Inside a group the first modifier weighing 100 or more wins, so a culture's specific entry is listed before the
  generic one it should beat. Option `up_to_emperor` widens an entry's high-noble clothing trigger to kings and
  emperors where RiE has no royal entry (Vanyar, Noldor, hobbit), so those kings do not fall back to vanilla robes.
- Extra entries: hobbits beardless; no vanilla cloaks for elves (RiE gives its elves none) and for hobbit-dressed
  halfling and gnome men (vanilla cloaks clip through RiE's hobbit outfit).

Entries for RiE-only cultures (Sindar, Galadhrim, Falathrim, Cuind, Kinn-lai, Penni, Bree), eastern dwarves, title-specific
crowns (Khazad-dum, Erebor), the Greybeard religion, sickness, the barbershop and body weight are left out, and so are
entries that hinge on RiE-only content: the hobbit travel cloak (a flag RiE's duel events set), the dwarf mining cloak
and headgear (RiE's `activity_mining`) and Oropher's helmet (RiE's `dynasty_oropher`). RiE's `is_elf` and
`cannot_be_killed` triggers become `culture ?= { has_elvish_heritage = yes }` and `always = no`. The build stops if a
copied entry still names a culture, heritage, title, dynasty, scripted trigger or activity type Anbennar lacks.

The triggers (`common/scripted_triggers/aov_rie_portrait_triggers.txt`) follow vanilla's shape:
`portrait_<k>_clothing_trigger` (CULTURE_SCOPE = scope:culture) and `_spouse_trigger` (culture), both through vanilla's
`portrait_shared_clothing_contents_trigger` (`has_clothing_gfx = <k>_clothing_gfx`, or the adopted cultural style flag).

## Genes, accessories, models

- Gene templates the copied entries name and Anbennar lacks are copied from RiE into generated whole-file overrides of
  Anbennar's gene files (`common/genes/03..07_*.txt`; Anbennar overrides all five, and genes are whole-file), inside
  the gene block, marked, re-indexed to the gene's lowest free indices. DNA stores a template index in one byte, so
  the build stops above 255 (Anbennar's headgear gene uses 242 of 256 slots; the new races need 11).
- Accessories the templates name and neither Anbennar nor the game defines are copied from RiE
  (`gfx/portraits/accessories/aov_rie_portraits.txt`); accessories RiE does not define are the game's (DLC included).
- Entities and pdxmeshes the accessories use are copied block by block into `.asset` files at their RiE paths, with
  every mesh, texture, pattern mask and accessory variation they name, also at their RiE paths, because RiE refers to
  pattern masks and variation textures by full path. A file whose path Anbennar or the game also has is never
  overwritten. RiE edits some vanilla files in place (23 hair and hood textures) and its own meshes depend on the
  edits (with vanilla's strand texture RiE's opaque hair shader drew elf hair flat white), so RiE's version is copied
  as `aov_rie_<name>` into `gfx/models/portraits/aov_rie_edited/` and the copied blocks point at it. Entities and
  textures that only the game has stay the game's.
- A template the entries name that Anbennar defines with different content (`dwarven_hairstyles`) is copied from RiE
  as `aov_rie_<name>`, and the entries point at the copy.
- Anbennar reuses AGOT hair model names (`female_hair_custom_01/02/03/05/07/08`) for its Kheteratan hairstyles, so RiE's
  hair lists showed dwarf and elf women in white Kheteratan wigs. A pdxmesh/entity name Anbennar (not the game) defines
  with other content than RiE is copied from RiE as `aov_rie_<name>`, the accessories naming it are copied as
  `aov_rie_<accessory>`, our template insertions point at those, and a texture whose name Anbennar or the game has
  with other content is copied renamed as well.
- Accessory variations (`variation`, `pattern_textures`, `color_palette` blocks) the meshes name are copied into
  `gfx/portraits/accessory_variations/aov_rie_portraits.txt` when Anbennar and the game lack them.
- Every shader the copied meshes name must exist in the game's or this mod's portrait shaders.

## Culture files

`tools/build_holding_models.py` already regenerates `anb_elven.txt` and `anb_dwarf.txt`; it now also prepends the
clothing keys and writes `anb_halfling.txt` and `anb_gnome.txt`. As with building and unit keys, every clothing_gfx
list that starts with a new key must continue identically (checked).

## Risks to confirm in game

1. Equal-priority groups apply in file order (documented in `_portrait_modifiers.info`; our files sort last).
2. RiE's hobbit clothes on Anbennar's halfling bodies (the meshes carry body blend shapes).
3. The 255 index cap for gene templates.
4. Texture lookups by name for meshes copied at their RiE paths.

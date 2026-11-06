# Orc portraits

Serpentspine orcs have Elder Kings 2's (EK2, Workshop 2887120253; credit to its team) standard orc look: its face, tusks,
male horns, build and hair lists. Their skin is brown, gray or black instead of EK2's green. Clothes and armour are not
EK2's: `black_orc` keeps `western_clothing_gfx` until they are chosen. Spec
`docs/superpowers/specs/2026-11-05-orc-portraits-design.md`.

## Generated files

| File | Generator | Why |
|---|---|---|
| `common/genes/02_genes_accessories_misc.txt` (whole-file override of the game's) | `python -I tools/build_orc_portraits.py` | `teeth_accessory` is in the game's file, which Anbennar does not override, and gene files are whole-file. It is the game's bytes plus the `aov_orc_teeth` template between `# Anbennar Overhaul` markers, at the gene's lowest free index. Rerun after a CK3 patch. `FreshnessTests` fails when it is stale. |
| `gfx/models/portraits/male_head/male_head.asset`, `female_head/female_head.asset` | `python -I tools/build_head_assets.py` | Shared with the gnoll head. Orc lines: nose and lip blend shapes (both sexes), horns (male), attributes `aov_orc_nose_bs`, `aov_orc_lips_bs`, `aov_orc_horns_bs`, and `aov_orc_tusks_bs` mapped to `<sex>_bs_neutral`, which is how EK2 lets a head gene set a shape on the teeth. |
| `orc_hairstyles`, `orc_beards` in `common/genes/03_genes_special_accessories_hairstyles.txt`, `04_genes_special_accessories_beards.txt` | `python -I tools/build_portraits.py`, data `EXTRA_TEMPLATES` in `tools/data/portraits.py` | EK2's two lists, between `other templates` markers. All accessories are Anbennar's or the game's, and the build stops if one disappears. |
| `gfx/models/portraits/aov_orc/*.mesh`, `*.dds`, `gfx/models/portraits/<sex>_head/blendshapes/aov_orc_*.mesh` | `python -I tools/build_orc_portraits.py --import [ek2 folder]` | Imported once from EK2, unchanged, under new names, and committed (`IMPORTS`): about 8 MB. Nothing shadows an Anbennar or game file. `ArtTests` checks the copies still match EK2 when it is installed. |

Hand-written: `common/ethnicities/aov_orc_ethnicities.txt`, `common/genes/aov_orc_genes.txt`,
`gfx/models/portraits/aov_orc/aov_orc_teeth.asset`, `gfx/portraits/accessories/aov_orc.txt`,
`gfx/portraits/portrait_modifiers/aov_orc.txt`, `localization/english/aov_orc_portraits_l_english.yml`, and the
`ethnicities` block of `black_orc` in `common/culture/cultures/aov_tribes_cultures.txt`. `WiringTests`, `GeneTests`,
`EthnicityTests` and `ModifierTests` check that they name each other.

## System

- **Delivery:** ethnicities and inherited genes, as EK2 does it, so orcs vary, children inherit and half-orcs blend. It
  reaches new games only: a character's DNA is generated when the game starts or they are born. `cave_goblin` is unchanged.
- **Ethnicities:** `orc_base` is EK2's `race_orc` with its genes renamed; no culture names it. `black_orc` splits evenly
  between `orc_brown`, `orc_gray` and `orc_black`, which set only skin. A later orc culture can use a different mix.

  | Ethnicity | `skin_color` box | `skin_color_saturation` | Palette colours |
  |---|---|---|---|
  | `orc_brown` | 0.4 0.65 0.8 0.85 | 0.5 (no change) | `#63432a` to `#30190f` |
  | `orc_gray` | 0.0 0.5 0.2 0.75 | 0.0 to 0.05 (almost no colour) | `#828282` to `#3f3f3f` |
  | `orc_black` | 0.0 0.85 0.2 1.0 | 0.0 to 0.05 (almost no colour) | `#2d2d2d` to `#181818` |

  These use the game's `skin_palette.dds` (EK2's own palette would change everyone) and Anbennar's
  `skin_color_saturation` gene. All three use that one template, so a brown and a gray parent can pass on a value between
  the two. The colours are raw palette values, which the head texture and lighting change in game.
- **Genes:** `aov_orc_nose`, `aov_orc_forehead`, `aov_orc_tusks`, `aov_orc_wrinkles`, `aov_orc_horns`, EK2's values, each with
  an empty index 0 template that everyone else keeps. Horns are male only, on about 3 in 11 men, because EK2's female entry
  is empty.
- **Left out of EK2's ethnicity:** the green skin gene; metallic skin, eye sclera and pupil (all set to 0); eyebrows (the
  default look); `hairline_type`, which reads shapes only EK2's edited hair assets have, so mohawks go with it; and
  `gene_eye_size`, whose `eye_size` attribute Anbennar's head lacks, replaced by the game's `gene_bs_eye_size`.
- **Teeth:** `aov_orc_teeth.asset` is EK2's teeth with only the tusk and mouth-movement shapes kept. EK2's teeth texture has
  zero alpha, so the skin shader does not tint it and tusks stay tooth-coloured on any skin. A portrait modifier sets the
  teeth, not the ethnicity, because `teeth_accessory` is `inheritable = no`: a half-orc raised in a human culture would
  otherwise have no visible tusks. It applies to `race_orc` and `race_half_orc`, not Liches.
- **Hair and beards:** `aov_orc_hair` and `aov_orc_beards` set no priority, like Anbennar's base groups, so this file overrides
  them by file order while religious, situational and special groups win. Those base groups hold the baby hair and boys'
  lack of beards, so the hair group starts at `@baby_hair_age` (5, Anbennar's value) and the beard group at 18. Adult orcs
  are never bald, because the random bald chance is in the base group; EK2's `orc_hair` has none either. EK2 gives
  `orc_beards` weight 0 in its own beard file, so its orcs appear to take a generic beard; we use the list because
  `black_orc`'s generic beards are western.
- **Not used:** Anbennar ships an unused `male_orc_teeth.mesh`, its `orc_teeth_*` shapes and a `bs_orc_teeth_lips` attribute,
  whose lip shape differs from EK2's. They are left alone.

## Validation

`tools/validate.py` shows 6 `unknown-field` errors in `common/genes/aov_orc_genes.txt`: `inheritable` five times and
`sync_inheritance_with` once. They are not baselined, because they are not inherited from Anbennar or RiE. They appear to be
false alarms from tiger: Anbennar's working race genes (`mer_genes.txt`, `anb_monstrous_genes.txt`) use `inheritable` in
the same kind of block with no `error.log` complaint, and EK2 ships both fields. If check 1 below is clean, they can be
accepted.

## In-game checks

Not yet run. A clean tiger pass does not prove any of this.

1. A new game loads with no `error.log` lines for `aov_orc`, the head assets or `teeth_accessory`, or for
   `sync_inheritance_with`, which the game only uses in colour genes and EK2 uses on its morph gene `beast_teeth`.
2. `black_orc` rulers, wives and children show the orc face and all three colours; skin is brown, gray or black with no
   green.
3. **Main risk:** gray and black render correctly at saturation 0. Anbennar's kobolds only use 0.75 to 1.0 of this gene,
   so this end has never been used. If it fails, add a small `aov_orc_skin` gene with its own `skin_hsv_shift_curve`.
4. Black skin keeps enough facial detail to read. Raise the box if it doesn't.
5. Tusks sit in the mouth and do not tear when the mouth moves, including with the `portrait_skin` shader under
   Anbennar's copy of `portrait.shader`, on men, women and children.
6. Horns appear on about 3 in 11 men and look right on all three skins.
7. EK2's hair and beard lists appear, babies keep baby hair, boys and women have no beards, and religious and special
   headwear still win.
8. Other races' portraits and characters with hand-written DNA in `common/dna_data` are unchanged. The new genes are absent
   from that DNA and should fall back to index 0.
9. A child of a brown and a gray orc comes out between the two. A half-orc, if one can be made in the console, blends and
   has the tusked teeth.
10. An orc Lich shows the Lich skeleton with no tusks or hair showing through.

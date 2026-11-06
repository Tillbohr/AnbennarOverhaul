# Orc portraits

Serpentspine orcs have Elder Kings 2's (EK2, Workshop 2887120253; credit to its team) standard orc face, tusks, male horns
and build, with brown, gray or black skin instead of EK2's green. Their hair, beards and clothes come mostly from Realms in
Exile (RiE), so that they look gruff rather than human. Spec
`docs/superpowers/specs/2026-11-05-orc-portraits-design.md`; the clothes come from the comparison at
https://claude.ai/artifact/L2SzuuQn3EzvJcSBE9XSvz.

## Generated files

| File | Generator | Why |
|---|---|---|
| `common/genes/02_genes_accessories_misc.txt` (whole-file override of the game's) | `python -I tools/build_orc_portraits.py` | `teeth_accessory` is in the game's file, which Anbennar does not override, and gene files are whole-file. It is the game's bytes plus the `aov_orc_teeth` template between `# Anbennar Overhaul` markers, at the gene's lowest free index. Rerun after a CK3 patch. `FreshnessTests` fails when it is stale. |
| `gfx/models/portraits/male_head/male_head.asset`, `female_head/female_head.asset` | `python -I tools/build_head_assets.py` | Shared with the gnoll head. Orc lines: nose and lip blend shapes (both sexes), horns (male), attributes `aov_orc_nose_bs`, `aov_orc_lips_bs`, `aov_orc_horns_bs`, and `aov_orc_tusks_bs` mapped to `<sex>_bs_neutral`, which is how EK2 lets a head gene set a shape on the teeth. |
| The `aov_orc_*` hair, beard, clothes, legwear and headgear templates in `common/genes/03_`, `04_`, `05_`, `06_` and `07_genes_special_accessories_*.txt`, and the RiE accessories they name, with their models and textures | `python -I tools/build_portraits.py`, data `EXTRA_TEMPLATES` in `tools/data/portraits.py` | Inserted between `other templates` markers. Every accessory must be Anbennar's, the game's, in `aov_orc.txt` or RiE's, which are copied in; the build stops otherwise. The RiE art adds about 117 MB. |
| `gfx/models/portraits/aov_orc/**/*.mesh`, `*.dds`, `gfx/models/portraits/<sex>_head/blendshapes/aov_orc_*.mesh`, `gfx/portraits/accessory_variations/textures/patterns/aov_orc/*.dds`, `gfx/portraits/accessory_variations/textures/aov_orc_rags_palette.dds` | `python -I tools/build_orc_portraits.py --import [ek2 folder]` | Imported once from EK2 and committed (`IMPORTS`), about 20 MB, unchanged under new names, except the rags' palette, which is lightened (`lighter_palette`), and the fur mask, which gets a full mip chain (`full_mip_dds`). The game loads pattern textures into arrays whose members must match the first in size, format and mip count, or it crashes on launch; EK2's masks all have 2 mips and the game's 10, and `PatternArrayTests` guards this. Nothing shadows an Anbennar or game file. `ArtTests` checks the copies still match EK2 when it is installed. |

Hand-written: `common/ethnicities/aov_orc_ethnicities.txt`, `common/genes/aov_orc_genes.txt`,
`gfx/models/portraits/aov_orc/aov_orc_teeth.asset`, `gfx/models/portraits/aov_orc/rags/aov_orc_rags.asset`,
`gfx/portraits/accessories/aov_orc.txt`, `gfx/portraits/accessory_variations/aov_orc.txt`,
`gfx/portraits/portrait_modifiers/aov_orc.txt`, `localization/english/aov_orc_portraits_l_english.yml`, and the
`ethnicities` and `clothing_gfx` of `black_orc` in `common/culture/cultures/aov_tribes_cultures.txt`. `WiringTests`,
`GeneTests`, `EthnicityTests`, `ModifierTests`, `GruffHairTests` and `WardrobeTests` check that they name each other.

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
- **Hair and beards (user choice after the first in-game test: gruff, not human):** by race trait. EK2's lists were mostly
  styled human hair and full beards, which hid the tusks and made orcs read as bearded men, so they are gone.
  `aov_orc_hairstyles` is RiE's Moria orc list without its two groomed human styles, with RiE's purpose-made mountain orc
  hair weighted highest and shaved heads common. `aov_orc_beards` is RiE's orc list: 4 in 5 men are clean-shaven, and the
  rest have orc beards or muttonchops. The hair list names DLC hair (FP2 to FP4) without RiE's DLC gates; a player without
  that DLC would see those few as bald, which suits an orc.
- **How those groups combine:** `aov_orc_hair` and `aov_orc_beards` set no priority, like Anbennar's base groups, so this file
  overrides them by file order. Groups with a priority still win, but others without one do not, so their forced cases are
  excluded by hand: baby hair (the hair group starts at `@baby_hair_age`, 5, Anbennar's value), boys' lack of beards (18),
  forced baldness (`nick_the_actually_bald`, `hajj_halq_modifier`, `shaven_bald_modifier`, `bald_head`), forced shaving
  (`beardless_eunuch`, `no_beard`).
- **Clothes (user choice: the comparison's recommended mix):** by culture, through `aov_orc_clothing_gfx`, first on `black_orc`'s
  `clothing_gfx`, with `western_clothing_gfx` behind it. A later orc culture opts in with the same key.

  | Rank | Men | Women |
  |---|---|---|
  | Everyday, and all children | EK2's goblin rags, two cuts | EK2's goblin rags |
  | Barons and counts | RiE's fur-collar tribal tunic | Same |
  | Dukes and up | RiE's Moria armour and bone crown | RiE's goblin armour and bone crown |
  | War, any rank | RiE's rusted Mordor plate and Uruk helmet | Same |

  RiE's orc entries have no rank tiers, so the groups in `aov_orc.txt` are ours, at the priorities of Anbennar's groups (1 for
  base clothes and headgear, 4 for armour), using its rank triggers. Children wear the rags because the tunic and the women's
  armour have no child shape. Everyone else takes `no_headgear`, and no orc wears a cloak, so nothing western shows through.
  Vanilla has no imperial armour trigger, so emperors use `portrait_imperial_trigger`. The rags' palette is EK2's made 1.8 times
  lighter, because as shipped about 60% of it sits close to black skin. Fits the gene slots: headgear is at 251 of 256.
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
7. Hair and beards read as gruff and not human: mostly shaved or matted, most men clean-shaven with tusks showing. Babies keep
   baby hair, boys and women have no beards, a eunuch has no beard, and "the Bald" is bald. Hair and eye colours look right
   (Anbennar's palettes differ from EK2's, and about a fifth of orcs get mid-gray hair at any age). The barbershop works.
8. Other races' portraits and characters with hand-written DNA in `common/dna_data` are unchanged. The new genes are absent
   from that DNA and should fall back to index 0.
9. A child of a brown and a gray orc comes out between the two. A half-orc, if one can be made in the console, blends and
   has the tusked teeth.
10. An orc Lich shows the Lich skeleton with no tusks or hair showing through.
11. Each rank wears its clothes (rags, tunic, armour and crown, plate and helmet in war) on men, women and children, and on an
    emperor. Nothing western shows: no hat, no cloak. How the helmets and crown sit on the orc head is unknown until seen; RiE's
    Mordor helmet sits high on a vanilla head, and may be shaped for its uruk head.
12. Rags read on black skin, and Moria armour does not make a black-skinned ruler one dark shape.
13. Religious clothes still win (priority 3) on an orc priest. A non-orc in the ruler designer is not offered orc features.

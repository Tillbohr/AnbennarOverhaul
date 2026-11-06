# Orc portraits design

Serpentspine orcs take Elder Kings 2's (EK2, Workshop `2887120253`) standard orc look: its face, tusks, male horns, build
and hair lists. Their skin is brown, gray or black instead of EK2's green. Clothes and armour are not part of this work.

The placeholder `black_orc` culture currently uses the human `arab` ethnicity (`docs/systems/dwarovar-tribes.md`,
Placeholders). This replaces that for orcs only.

## Intent

- **User asked:** port EK2's orc appearance, keeping the standard orc look. Serpentspine orcs range from brown through
  gray to black. The user approved the three colour ranges below from swatches.
- **User asked:** do not port EK2's orc clothes. Clothes and armour will be chosen after comparing the Warcraft mod, EK2
  and Realms in Exile (RiE), in the separate session "Compare orc clothes: Warcraft, EK2 and RiE".
- **Assumed, not objected to:** EK2's art goes in this public repo as RiE's does, and EK2 is credited in the system doc.

**Success:** a new game shows `black_orc` characters with EK2's orc face and tusks, in all three colours, varying
individually and passing their look to children, with no change to any other character's portrait.

## Approach

Ethnicities and inherited genes, as EK2 does it. The alternative, a portrait modifier on `race_orc` as gnolls have,
would reach existing saves but gives no half-orc blend and no looks passed from parents. The cost of this approach is
that the look reaches new games only, since a character's DNA is generated when the game starts or they are born.

The one exception is the tusked teeth, which come from a portrait modifier. See Teeth.

## Ethnicities

`common/ethnicities/aov_orc_ethnicities.txt`, hand-written. `black_orc` in `common/culture/cultures/aov_tribes_cultures.txt`
changes to an even split:

```
ethnicities = {
	1 = orc_brown
	1 = orc_gray
	1 = orc_black
}
```

`orc_base` copies EK2's `race_orc` (`template = "vanity_character_base"`, in
`001_ek_ethnicities_mer_C_orsimer.txt`) with the changes under Genes. It keeps EK2's height, build, face, ear, eye colour
and hair colour values. No culture names it directly. The three colours use `template = "orc_base"` and differ only in
skin:

| Ethnicity | `skin_color` box (x1 y1 x2 y2) | `skin_color_saturation` value | Palette colours |
|---|---|---|---|
| `orc_brown` | 0.4 0.65 0.8 0.85 | 0.5 (no change) | `#63432a` to `#30190f` |
| `orc_gray` | 0.0 0.5 0.2 0.75 | 0.0 to 0.05 (almost no colour) | `#828282` to `#3f3f3f` |
| `orc_black` | 0.0 0.85 0.2 1.0 | 0.0 to 0.05 (almost no colour) | `#2d2d2d` to `#181818` |

- **Palette:** the game's `skin_palette.dds`, which Anbennar uses. EK2 ships its own palette, which is close to the game's
  at these coordinates except at the very bottom. It is not imported, because it would change every character.
- **Saturation gene:** Anbennar's `skin_color_saturation` (`anb_color_modification_genes.txt`), template
  `skin_color_saturation`: value 0 removes all colour, 0.5 changes nothing. All three ethnicities use this one template, so
  a brown and a gray parent can pass on a value between the two rather than one or the other.
- The colours above are raw palette values. The head texture and lighting change them in game. They are expected to need
  tuning after the first test.

## Genes

`common/genes/aov_orc_genes.txt`, hand-written from EK2's blocks. Five new inherited morph genes, each with an empty
index 0 template that everyone else keeps:

| EK2 gene | New gene | Template | Does |
|---|---|---|---|
| `race_gene_mer_nose` (`ek_genes_mer.txt`) | `aov_orc_nose` | `orc_nose` | Sets `aov_orc_nose_bs`, EK2's nose shape |
| `race_gene_mer_forehead` (`ek_genes_mer.txt`) | `aov_orc_forehead` | `orc_forehead` | EK2's forehead normal decal, male and female |
| `beast_teeth` (`ek_genes_teeth.txt`) | `aov_orc_tusks` | `orc_tusk_size` | Sets `aov_orc_tusks_bs` and `aov_orc_lips_bs`. Keeps `sync_inheritance_with = skin_color`. Female values cap at 0.9, as EK2's |
| `race_extra_wrinkly_gene` (`ek_genes_beast_features.txt`) | `aov_orc_wrinkles` | `orc_wrinkles` | Age and body decals, using the game's own textures |
| `race_giantish_horns` (`ek_genes_beast_features.txt`) | `aov_orc_horns` | `orc_horns` | Sets `aov_orc_horns_bs` and EK2's horn decal. Male only: EK2's female entry is empty |

Ranges in `orc_base` are EK2's. Horns stay at EK2's weights: 3 in 11 male orcs have any, and the decal only appears at
gene strength above 0.5.

Left out of the EK2 ethnicity:

| EK2 entry | Why |
|---|---|
| `race_gene_skin_color` (`orsimer_skin`) | This is the green. Replaced by the colours above |
| `race_gene_skin_metallic`, `eye_sclera`, `eye_pupil` (`cross_pupils`) | All set to 0, so they do nothing |
| `race_gene_mer_eyebrows_01` (`human_eyebrows`) | This is the default look. Anbennar has no such template |
| `hairline_type` | Reads `bs_hair_receding` and `bs_hair_wp`, which only EK2's edited hair assets have (75 and 67 assets, none in Anbennar or the game). Mohawks go with it |
| `teeth_accessory` | Set by the portrait modifier instead. See Teeth |
| `gene_eye_size` | EK2's `epe_genes_morph.txt`, reading an `eye_size` attribute Anbennar's head lacks. Replaced by the game's `gene_bs_eye_size`, template `eye_size_neg`, range 0.0 to 0.4 for the same small eyes |

## Art

Imported once by `python -I tools/build_orc_portraits.py --import`, committed, about 6 MB, unchanged from EK2. All
names are new, so no Anbennar or game file is replaced. `.mesh` and `.dds` go through Git LFS by the existing rules.

| Art | From EK2 | Copied as |
|---|---|---|
| Nose, both sexes | `blendshapes/<sex>_orc_nose.mesh` | `gfx/models/portraits/<sex>_head/blendshapes/aov_orc_<sex>_nose.mesh` |
| Lips, both sexes | `blendshapes/<sex>_orc_teeth_lips.mesh` | `.../blendshapes/aov_orc_<sex>_lips.mesh` |
| Horns, male | `blendshapes/male_giantish_head_spikes.mesh` | `.../male_head/blendshapes/aov_orc_male_horns.mesh` |
| Teeth, both sexes | `<sex>_teeth_ek2.mesh` and its `_bs_lower_down`, `_bs_cheek_fat_neg`, `_bs_orc_tusks` shapes | `gfx/models/portraits/aov_orc/aov_orc_<sex>_teeth*.mesh` |
| Teeth textures | EK2's `male_teeth_diffuse.dds`, `male_teeth_ssao_color.dds`, which differ from the game's | `gfx/models/portraits/aov_orc/aov_orc_teeth_diffuse.dds`, `aov_orc_teeth_ssao_color.dds` |
| Forehead | `decals/male_head/mer_head_forehead_01.dds`, `decals/female_head/mer_head_forehead_02.dds` | `gfx/models/portraits/aov_orc/aov_orc_<sex>_forehead_normal.dds` |
| Horn decal | `decals/male_head/giant_horns/giantish_horns_01_{diffuse,normal,properties}.dds` | `gfx/models/portraits/aov_orc/aov_orc_horns_{diffuse,normal,properties}.dds` |

**Measured, with a read-only script:** every head shape has the game's head counts (2,770 vertices, 2,770 UVs, 5,360
triangles, male and female), and the tusk shapes match EK2's teeth mesh (447 vertices, 694 triangles). EK2's teeth
texture has zero alpha, so the skin shader does not tint it and tusks stay tooth-coloured on any skin. The horn decal
covers under 1% of the head, and its opaque pixels average a tan colour (110, 92, 62).

Anbennar ships an unused `male_orc_teeth.mesh` (377 vertices), its `orc_teeth_*` shapes and a `bs_orc_teeth_lips`
attribute, whose lip shape differs from EK2's. They are left alone, and EK2's come in under new names.

## Teeth

`gfx/models/portraits/aov_orc/aov_orc_teeth.asset` is EK2's `<sex>_teeth_ek2.asset`, renamed, with its kamal, beast and
vampire shapes removed. It uses EK2's `portrait_skin` shader, the two copied textures and the game's
`male_teeth_normal.dds` and `male_teeth_properties.dds`, as EK2's female teeth also do.
`gfx/portraits/accessories/aov_orc.txt` holds `male_aov_orc_teeth` and `female_aov_orc_teeth`, each with
`shared_pose_entity = head` as EK2's.

`teeth_accessory` is defined in the game's `02_genes_accessories_misc.txt`, which Anbennar does not override, and is
`inheritable = no`. So:

- `build_orc_portraits.py` writes `common/genes/02_genes_accessories_misc.txt`: the game's file plus the template
  `aov_orc_teeth`, at the gene's lowest free index, between `# Anbennar Overhaul` markers.
- The portrait modifier below sets it, instead of the ethnicity as in EK2. Because the gene does not inherit, a half-orc
  raised in a human culture would otherwise get normal teeth and no visible tusks.

## Portrait modifier

`gfx/portraits/portrait_modifiers/aov_orc.txt`, hand-written:

| Group | Sets | For |
|---|---|---|
| `aov_orc_teeth`, `usage = game` | `teeth_accessory` to `aov_orc_teeth`, `mode = replace`, as `aov_gnoll` sets eyes | `race_orc` or `race_half_orc`, not `lich` (the Lich portrait hides the head) |
| `aov_orc_hair`, `usage = game` | `hairstyles` to `orc_hairstyles`, `mode = add`, as EK2's `orc_hair` | `race_orc` |
| `aov_orc_beards`, `usage = game` | `beards` to `orc_beards`, `mode = add` | `race_orc` |

The hair and beard groups set no priority, like Anbennar's base `hairstyles` group, so this file overrides them by file
order while religious, situational and special groups still win. This is the same reliance on file order as RiE's
portraits (`docs/systems/rie-portraits.md`, still to confirm in game). They keep EK2's exclusions:
`is_from_ruler_designer`, `has_character_flag = has_scripted_appearance`.

Each also needs an age condition, because Anbennar's base group holds the baby hair. `aov_orc_hair` applies only at
`scope:age >= @baby_hair_age`, with the variable redefined at the top of the file with Anbennar's value, so babies keep
their baby hair. Anbennar's random bald chance (`no_hair`) is in the base group too, so adult orcs are never bald unless
`orc_hairstyles` or a later group makes them so. EK2's orcs have no separate bald chance in its `orc_hair` entry either.

Two changes from EK2: it selects by `heritage_orcish` and we select by the race trait, as gnolls do. And EK2's own beard
modifier gives `orc_beards` weight 0, with no other orc entry found in its beard files, so EK2's orcs appear to take a
generic beard. We use `orc_beards` because it is the list EK2 wrote for orcs and `black_orc`'s generic beards are western.

## Changes to generators

Two sets of files need orc additions and already have an owner:

- **Head assets.** `male_head.asset` and `female_head.asset` are whole-file overrides written by
  `build_gnoll_portraits.py`. Their writing moves to a new `tools/build_head_assets.py`, which adds both gnoll and orc lines
  after the same kobold anchors and stops if an anchor is missing or repeated. `build_gnoll_portraits.py` keeps only the
  `--import` of gnoll art. Orc lines:
  - blend shapes for nose and lips (both sexes) and horns (male);
  - attributes `aov_orc_nose_bs`, `aov_orc_lips_bs`, `aov_orc_horns_bs`;
  - `aov_orc_tusks_bs` mapped to `<sex>_bs_neutral`, which is how EK2 lets a teeth shape be set by a head gene.
- **Hair and beard templates.** `03_genes_special_accessories_hairstyles.txt` and `04_genes_special_accessories_beards.txt`
  are written by `build_portraits.py`. A new `EXTRA_TEMPLATES` entry in `tools/data/portraits.py` holds EK2's two lists,
  which are inserted at free indices under their own marker comment. All 34 hairstyles and 18 beards exist in Anbennar or
  the game, and the build stops if one disappears.

`docs/systems/updating.md` gets the new commands and the order: `build_portraits.py` and `build_head_assets.py` are
independent of each other, and `build_orc_portraits.py` reads only the game's file. Rerun it after a CK3 patch.

## Tests

`tools/tests/test_build_orc_portraits.py`, plus updated gnoll tests for the moved code:

- `FreshnessTests`: the generated teeth gene file and head assets match a fresh build; Anbennar's and the game's content
  survives unchanged apart from marked lines.
- `ArtTests`, when EK2 is installed: each imported file matches its EK2 source. Head shapes match the game's head mesh
  counts and teeth shapes match their base mesh.
- `WiringTests`:
  - every gene and template in `aov_orc_ethnicities.txt` is defined;
  - no ethnicity names a left-out gene;
  - every attribute a gene sets is on an entity;
  - every texture path exists in this mod or the game;
  - accessories, entities and meshes name each other;
  - `black_orc` lists the three colours and `cave_goblin` still lists `arab`.

Tiger is run as usual, and new reports are read rather than baselined.

## In-game checks

A clean tiger pass does not prove any of this.

1. A new game loads with no `error.log` lines for `aov_orc`, the head assets or `teeth_accessory`.
2. `black_orc` rulers, wives and children show the orc face and all three colours; skin is brown, gray or black with no
   green.
3. **Main risk:** gray and black render correctly at saturation 0. Anbennar's kobolds only use 0.75 to 1.0 of this gene,
   so this end has never been used. If it fails, add a small `aov_orc_skin` gene with its own `skin_hsv_shift_curve`.
4. Black skin keeps enough facial detail to read. Raise the box if it doesn't.
5. Tusks sit in the mouth and do not tear when the mouth moves, including with the `portrait_skin` shader under
   Anbennar's copy of `portrait.shader`, on men, women and children.
6. Horns appear on about 3 in 11 men and look right on all three skins.
7. EK2's hair and beard lists appear, babies keep baby hair, and religious and special headwear still win.
8. Other races' portraits and characters with hand-written DNA in `common/dna_data` are unchanged. The new genes are absent
   from that DNA and should fall back to index 0.
9. A child of a brown and a gray orc comes out between the two. A half-orc, if one can be made in the console, blends and
   has the tusked teeth.
10. An orc Lich shows the Lich skeleton with no tusks or hair showing through.

## Out of scope

- **Clothes and armour.** `black_orc` keeps `western_clothing_gfx` until the comparison session reports and the user
  chooses.
- **Goblins.** `cave_goblin` keeps `arab`. EK2's goblin look would be its own job.
- **EK2's other orc types** (iron, wood, Malahk). Later orc cultures can use a different mix of the three colours.
- **Other orc cultures, and army models.**
- **Existing saves.** DNA already generated stays as it is.

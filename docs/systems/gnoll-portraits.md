# Gnoll portraits

Gnolls (Anbennar's `race_gnoll` trait) have Victoria 3 Anbennar's hyena head: its muzzle and ears, spotted fur and
gnoll eyes, with no hair or beard. Anbennar ships gnolls with the `arab` human ethnicity, so before this they looked
human.

## Generated files

| File | Generator | Why |
|---|---|---|
| `gfx/models/portraits/male_head/male_head.asset`, `gfx/models/portraits/female_head/female_head.asset` (whole-file overrides of Anbennar's) | `python -I tools/build_gnoll_portraits.py` | The gnoll head is a blend shape, which has to be listed in the head mesh and the head entity, and asset files can only be overridden whole. Each file is Anbennar's plus two lines marked `# Anbennar Overhaul`: the blend shape after Anbennar's kobold head normals and the `gnoll_head_bs` attribute after its kobold head proportions. The generator stops if either kobold line is missing or repeated. Rerun after an Anbennar update. `tools/tests/test_build_gnoll_portraits.py` (`FreshnessTests`) fails when the files are stale. |
| `gfx/models/portraits/male_head/blendshapes/aov_gnoll_male_head_bs.mesh`, `gfx/models/portraits/female_head/blendshapes/aov_gnoll_female_head_bs.mesh`, `gfx/models/portraits/aov_gnoll/aov_gnoll_eyes_diffuse.dds`, `gfx/models/portraits/aov_gnoll/aov_gnoll_head_diffuse.dds` | `python -I tools/build_gnoll_portraits.py --import [vic3 folder]` (needs Victoria 3 Anbennar, default `~/anbennar-vicky3-dev-main`) | Imported once and committed. The head shapes and eye texture are copied unchanged from Vic3 Anbennar (`gnoll_head_bs.mesh`, `gnoll_female_head_bs.mesh`, `pupil_gnoll_L.dds`). The fur (`decals/male_head/gnoll/gnoll_head_base_diffuse.dds`) is converted from sRGB to linear colour and rewritten as a 1024 px DXT5 with 11 mips (the game's decal format) by `tools/dxt5.py`, because the skin shader reads a decal's colour as linear (see System). Vic3's gnoll normal map is flat (every pixel neutral) and its properties have no scattering or specular, so they are not imported: the head keeps CK3's own. `ArtTests` checks the copies still match Vic3 Anbennar and the fur matches a fresh conversion, when Vic3 Anbennar is present. |

Hand-written: `common/genes/aov_gnoll_genes.txt`, `gfx/portraits/portrait_modifiers/aov_gnoll.txt`,
`gfx/portraits/accessories/aov_gnoll.txt`, `gfx/models/portraits/aov_gnoll/aov_gnoll_eyes.asset`,
`localization/english/aov_gnoll_portraits_l_english.yml`. `WiringTests` checks that they name each other.

## System

- **Why the Vic3 head fits:** Vic3's gnoll head shapes have the same 2,770 vertices in the same order, the same UVs and
  the same 5,360 triangles as the game's male and female heads (the triangles are listed in a different order, as in
  Anbennar's working kobold head), so they work as CK3 blend shapes unchanged, and the fur texture lines up on the CK3
  head. Unlike the kobold head (position only, plus a separate normals shape), the gnoll blend shape is listed without
  `data`, as in Vic3, so it blends the muzzle's normals and tangents too.
- **Head:** the special gene `aov_gnoll_head` (template `aov_gnoll_head_full`) sets `gnoll_head_bs` and paints the
  fur's colours over the whole head with one decal, the way Elder Kings 2 (Workshop 2887120253,
  `ek_genes_beast_features.txt`) does Khajiit fur: diffuse `replace`, applied after the skin colour (so every gnoll has
  the same fur), at priority 20, above the game's eyebrow and lip decals (10). The fur is stored in linear colour:
  Anbennar's skin shader (`gfx/FX/jomini/portrait.shader`, `portrait_decals.fxh`) reads a decal's colour as linear,
  while the head texture it replaces is sRGB, so Vic3's sRGB fur came out far too light in game (dark brown spots as
  light tan, the dark muzzle near white; a render that treats the fur that way matches the in-game screenshot). The head
  keeps the game's normal map and properties, so the face keeps its creases, subsurface scattering and specular. Like
  the game's `gene_wounded`, it is a special gene (`special_genes`, not part of anyone's DNA) added by the portrait
  modifier with `mode = add`. The same template and fur serve both sexes and children.
- **What did not work** (in-game tests): Vic3's own way, a `texture_override` on a regular gene set by `mode = replace`,
  showed the blend shape but kept the human `complexion` texture, at weight 2147483647 (Anbennar's kobold value) and at
  1,000,000,000. Then the fur as decals: on that regular gene (with Vic3's flat normal map and properties) the faces
  were pale and smooth, and two gnolls had two different tones; as a special gene (normal map and properties dropped)
  faint light spots showed. Both fit the gamma problem above, which the linear fur fixes; whether the regular gene's
  decals drew at all was not settled. The special gene stays, as the pattern the game itself uses for decals added by
  portrait modifiers (the game and the reference mods change head textures from portrait modifiers only through
  `complexion` templates or decal genes added with `mode = add`).
- **Eyes:** the accessory gene `aov_gnoll_eyes` draws Vic3's gnoll iris on the game's eye meshes
  (`aov_<sex>_gnoll_eyes_entity`, only the diffuse changed, as Anbennar's kobold eyes do), and the modifier replaces
  `eye_accessory` with `no_eyes`, the Lich portrait's pattern. The iris keeps the character's eye colour.
- **Who:** the portrait modifier group `aov_gnoll` (`usage = game`, priority 100) applies to anyone with `race_gnoll`
  that is not a Lich (the Lich portrait hides the head). A blind gnoll (`aov_gnoll_blind`) gets the head but keeps the
  game's eyes, so it still looks blind. Both remove hair (`no_hairstyles`) and beard (`no_beard`) with `mode = add`, as
  Anbennar's own hair modifiers do: `hairstyles` and `beards` are special genes, and the engine rejects `replace` on them
  (`error.log`: "replace only work for regular genes"; the Lich portrait had the same error until this was fixed there
  too). Being a modifier, it needs no culture or ethnicity change and applies to existing saves.
- **Left as is:** the body, hands and skin colour stay human (in Vic3 too); the fur fades to tan low on the neck.
  Helmets and crowns are not fitted to the ears.

## In-game checks

1. A gnoll ruler (Sandfang or Fieldstalker culture) shows the hyena head and fur in the character window, with gnoll
   eyes and no hair or beard; female gnolls and gnoll children too.
2. Expressions and mouth animation move the muzzle without tearing.
3. Every gnoll has the same fur colours whatever its skin colour; the face keeps its creases and a little shine;
   the eyes sit in the sockets.
4. A blind gnoll shows the game's blind eyes; a gnoll Lich shows the Lich skeleton with no gnoll eyes.
5. `error.log` has no errors for `aov_gnoll`, `gnoll_head_bs` or the head assets.

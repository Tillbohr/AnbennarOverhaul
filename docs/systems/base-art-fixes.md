# Base art fixes

Anbennar ships art for some traits and men-at-arms that the game never shows: either the file name is not the one the
game looks up, or the unit's `icon` points at a generic vanilla icon instead. The overhaul copies the art to the
expected name, or sets the unit's `icon` to Anbennar's own art. Traits Anbennar left on a missing or vanilla stand-in
icon get one imported from EU4 Anbennar or another mod. Tests: `tools/tests/test_base_art_fixes.py`.

## Copied files (no generator)

| Overhaul file | Copied from | Why |
|---|---|---|
| `gfx/interface/icons/traits/education_adeanic_knight_0.dds` … `_5.dds` | Anbennar `gfx/interface/icons/traits/adeanic_knight_1.dds` … `_6.dds` (level N gets file N+1) | The six Adeanic knight education traits use the default icon name, `<trait key>.dds`. |
| `gfx/interface/icons/regimenttypes/griffon_riders.dds` | Anbennar `gfx/interface/icons/regimenttypes/griffon_knights.dds` | The `griffon_riders` men-at-arms has `icon = griffon_riders`, and the game looks up its icon and both pictures by that name. |
| `gfx/interface/illustrations/men_at_arms_{big,small}/griffon_riders.dds` | Warcraft: Guardians of Azeroth Reforged 2 (Workshop 2949767945), `gfx/interface/illustrations/men_at_arms_{big,small}/gryphon.dds` | Anbennar's `griffon_knights.dds` pictures are vanilla's `camel_riders.dds`, so the overhaul uses the Warcraft mod's gryphon riders instead (credited in `credits.txt`). |
| `gfx/interface/illustrations/men_at_arms_{big,small}/{battlemages,druids,skalds}.dds` | Anbennar `men_at_arms_{big,small}/mages.dds` | The pictures these units showed before their icon swap (below). |
| `gfx/interface/illustrations/men_at_arms_{big,small}/rangers.dds` | the game's `men_at_arms_{big,small}/bowmen.dds` | The pictures Oakfoot Rangers showed before. Also replaces Anbennar's `men_at_arms_small/rangers.dds`, a copy of the game's big bowmen picture at the wrong size. |

## Men-at-arms icons

A unit's `icon` names its icon (`icons/regimenttypes/<icon>.dds`) and both pictures
(`illustrations/men_at_arms_{big,small}/<icon>.dds`). Anbennar ships its own icon for these nine units but leaves them on
a generic vanilla one. The pictures come from Anbennar where it has them under the new name (all vanilla copies), or
from the copies above.

| Unit | Anbennar icon | Overhaul icon | Set in |
|---|---|---|---|
| `adventurers_maa` | `heavy_infantry` | `adventurers` | `common/men_at_arms_types/zz_aov_maa_icon_overrides.txt` |
| `damerian_longbowmen` | `bowmen` | `damerian_longbowmen` | same |
| `oakfoot_rangers` | `bowmen` | `rangers` | same |
| `thorn_squares` | `pikemen` | `thorn_square` | same |
| `wexonard_greatswords` | `heavy_infantry` | `wexonard_greatswords` | same |
| `battlemages` | `mages` | `battlemages` | `zz_aov_mage_maa_overrides.txt` (magic) |
| `druids`, `skalds` | `mages` | `druids`, `skalds` | `zz_aov_faith_maa_overrides.txt` (faith men-at-arms) |
| `smallknights` | `heavy_cavalry` | `smallknights` | `zz_aov_halfling_maa_overrides.txt` |

The blocks in `zz_aov_maa_icon_overrides.txt` are Anbennar's with only the `icon` line changed. `ICON_SWAPS` in
`tools/tests/test_cultural_maa.py` lists every swap; the override tests compare each block with Anbennar's after
putting the old icon back.

Not wired: the remaining unused Anbennar icons. Bards, beastslayers, ekinerak, paladins, rogues and sellswords have
no unit. Arannese bardiches, gladeguard, mounted gladeguard, hedge knights, horde, mireknights, spellbreakers, war
mammoths and Wexonard axeguards are vanilla copies.

## Trait icons

| Traits | Overhaul files | Source |
|---|---|---|
| The 15 avatars (`anb_avatar_<god>`) | `gfx/interface/icons/traits/anb_avatar_<god>.dds` | EU4 Anbennar's personal-deity icons, `gfx/interface/hindu_deities_strip.dds` (42 px frames, 1-based): Castellos 1, the Dame 2, Adean 4, Munas 5, Ara 6, Balgar 7, Esmaryal 8, Ryala 9, Minara 10, Falah 11, Nerat 12, Nathalyne 13, Begga 14, Wip 224. Each frame cropped, Lanczos 2x up (`eu4_import.convert`, `upscale2x`), resized to 120 px with mips. EU4 has no personal deity for Uelos: `anb_avatar_uelos.dds` is Anbennar's `faith/cult_of_uelos.dds` resized to 120 px (`eu4_import.py convert --resize 120x120 --mips`). |
| The six racial purists (`<race>_purist`) | `gfx/interface/icons/traits/<race>_purist.dds` | The game's `traits/pure_blooded.dds`, one shared icon, unchanged. |
| The 18 planetouched (`planetouched_<element>_<level>`) | `gfx/interface/icons/traits/planetouched_<element>_<level>.dds`, `common/traits/zz_aov_trait_icon_overrides.txt` | The Warcraft TC (Workshop 2949767945) `traits/user_of_elemental_{fire,water,earth,air}_magic_<level>.dds`, `user_of_life_magic_<level>.dds`, `user_of_shadow_magic_<level>.dds`, levels 1 to 3 (one to three stars), unchanged. Anbennar sets these traits' icon to vanilla's `varangian.dds`, so the override file holds Anbennar's 18 blocks with only that name replaced by `<trait key>.dds`. |
| `vampire`, `lycanthrope` | `gfx/interface/icons/traits/vampire.dds`, `lycanthrope.dds` | Elder Kings 2 (Workshop 2887120253) `traits/vampire_character.dds` and `lycan_character.dds`, unchanged (60 px). |
| `bladeshunned` | `gfx/interface/icons/traits/bladeshunned.dds` | The game's `traits/disinherited.dds`, unchanged. |
| `sun_reborn` | `gfx/interface/icons/traits/sun_reborn.dds` | EU4 Anbennar's Phoenix Empire reform icon, `gfx/interface/government_reform_icons/phoenix_empire.dds` (56 px): `eu4_import.py convert --upscale2x --resize 120x120 --mips`. |
| `sun_reborn_descendant` | `gfx/interface/icons/traits/sun_reborn_descendant.dds` | A copy of the overhaul's `sun_reborn.dds`: the Sun Reborn's line shows the same phoenix. |

The avatars, purists, vampire, lycanthrope, bladeshunned, sun_reborn and sun_reborn_descendant use the default icon name (`<trait key>.dds`), so they need no script change.

## Trait text

`localization/replace/english/aov_trait_text_replace_l_english.yml` writes the Sun Reborn text Anbennar left as
"GILLY TODO": the Sun Reborn trait's description and its language flag line, and the description of the descendants'
trait. It also renames the descendants' trait from "Sun Reborn" (the same name as the Sun Reborn's own trait) to
"Scion of the Sun Reborn". The text names no one, so it fits Jaher at game start and anyone who is proclaimed Sun
Reborn later. `tools/tests/test_trait_text.py` checks that only placeholders (and that name) are
replaced.

## After an Anbennar update

If `test_base_art_fixes.py` fails, Anbennar changed a unit or planetouched block (recopy it into
`zz_aov_maa_icon_overrides.txt` or `zz_aov_trait_icon_overrides.txt` with the overhaul icon), changed a copied file
(recopy it), added an avatar trait (give it an icon), or set the icon itself (drop the swap).

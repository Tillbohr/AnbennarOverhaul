# Base art fixes

Anbennar ships art for some traits and men-at-arms that the game never shows: either the file name is not the one the
game looks up, or the unit's `icon` points at a generic vanilla icon instead. The overhaul copies the art to the
expected name, or sets the unit's `icon` to Anbennar's own art. Tests: `tools/tests/test_base_art_fixes.py`.

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

## After an Anbennar update

If `test_base_art_fixes.py` fails, Anbennar changed a unit block (recopy it into `zz_aov_maa_icon_overrides.txt` with
the overhaul icon), changed a copied file (recopy it), or set the icon itself (drop the swap).

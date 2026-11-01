# Regional elven cultures

Anbennar ships three elven cultures: `moon_elvish` (Cannor), `sun_elvish` (Bulwar) and `wood_elvish` (Deepwoods,
split from the moon elves in 1017). This system splits them into regional cultures so each can later get its own
traditions. Every new culture is a divergence (`parents`) of `wood_elvish` or `moon_elvish`, with `heritage_elven`
(the only elven heritage) and `language_moon_elven` (EU4 has one elven language).

## Files (hand-written; no generator)

| File | What |
|---|---|
| `common/culture/cultures/aov_elven_cultures.txt` | the 13 cultures |
| `localization/english/aov_elven_cultures_l_english.yml` | names, prefixes, collective nouns, history lines |
| `common/on_action/aov_elven_cultures_on_actions.txt` | `on_game_start` hook |
| `common/scripted_effects/aov_elven_cultures_effects.txt` | county and character assignment |
| `common/scripted_effects/zz_aov_elven_culture_overrides.txt` | Anbennar's `roll_racial_purity_trait_for_character`, copied with lineage checks |
| `tools/tests/test_elven_cultures.py` | definitions match their parent, loc, assignment titles still hold parent-culture counties, override still matches Anbennar |

## Cultures

| Culture | Parent | Ethos | Counties at game start | Lore (EU4 Anbennar) |
|---|---|---|---|---|
| `lake_elvish` Lake Elvish | wood | courtly | `d_lake_grove_1` | Salla Elyn (I26): Elynáile, elven politics and philosophy |
| `mountain_elvish` Mountain Elvish | wood | stoic | `d_mountain_grove_1` | Salla Myna (I27): Ciranmyna, the Speardancer, "Never to Fall" |
| `thorn_elvish` Thorn Elvish | wood | spiritual | `d_thorn_grove_1` | Salla Drennen (I28): closest to the fey, the first druids |
| `bone_elvish` Bone Elvish | wood | stoic | `d_bone_grove_1` | Salla Cenág (I29): the Bone Struggle, scouts |
| `hunter_elvish` Hunter Elvish | wood | bellicose | `d_hunter_grove_1` | Salla Fealgarn (I30): great-beast hunters |
| `flower_elvish` Flower Elvish | wood | bureaucratic | `d_flower_grove_1` | Salla Scotha (I31): alchemists, botanists, merchants |
| `river_elvish` River Elvish | wood | communal | `d_river_grove_1` | Salla Ahain (I32): satyrs, peace and abundance |
| `arrow_elvish` Arrow Elvish | wood | bellicose | `d_arrow_grove_1` | Salla Ayeth (I33): archers, acrobats, carpenters |
| `shadow_elvish` Shadow Elvish | wood | courtly | `d_shadow_grove_1` | Salla Ghúl (I34): Ashentree fey, the Witch of the East |
| `redglader` Redglader | moon | courtly | `d_redglades`, `c_gladegate` | Redglades (A03): Ioriel Redrose, accords with Lorent in 1001 |
| `ibevari` Ibevari | moon | bellicose | `k_ibevar` | Ibevar (A32): the Forlorn Vale, Blaiddscal academy |
| `celmaldorian` Celmaldorian | moon | communal | `c_celmaldor` | Celmaldor (Z22): Maldorian, the Elves of the Reach |
| `venaili` Venáili | moon | stoic | `d_venail` | Venáil (A21): seafarers of the Remnant Fleet |

`created` is cosmetic (the culture window's history line): 1020 for the groves (after the 1017 retreat); Redglades
1001, Celmaldor 995, Ibevar and Venáil 1021.10.31 (their title history).

Each copies its parent's traditions, martial custom, head determination, name list, ethnicities and gfx (coat of
arms, buildings, clothing and units, as the overhaul's generated `anb_elven.txt` gives the parent), so nothing
changes in play until regional traditions are added. `CultureDefinitionTests` fail if a parent's field changes
(say, after `build_holding_models.py` gives it a new gfx key): copy the new value. The name list stays the parent's
because Anbennar's title flavorization (`common/flavorization/00_anb_title_holders.txt`: Ceann, Prince) and
dynasty naming are keyed on it; a regional name list can be added later as a second `name_list` line (the first
one is the primary).

Not split:
- `sun_elvish`: at 1022 the sun elves are Jaher's host, one people; EU4's desert elves (Jaddari) come centuries later.
- `wood_elvish` keeps no land (`test_no_grove_county_left_wood_elvish`) and stays the parent of the groves.
- `moon_elvish` keeps Silverwoods/Moonhaven, Varivar, Arbaran, Elvenaire, Elfsmithy, Casnamóine, Elvelenn and the
  moon elves living among humans (Anbennar's moon elf minority system, `moon_elvish_city`).
- EU4's other elves (star, sea, eclipse, dawn, horizon, sunrise, sunset, desert), the Ruinborn and the degenerated
  elves have no land or people on the CK3 map in 1022 (Aelantir, the Haless colonies, or later events).
- Half-elves are already human x moon elf cultures in Anbennar (divergences in `anb_damesheader.txt`,
  `anb_escanni.txt`, `anb_lencori.txt`; hybrids in `common/culture/creation_names/anb_names_hybrid.txt`).

## Game start

`aov_elven_cultures_game_start_effect` (on `on_game_start`):
1. Counties: every de jure county of each title above that still has the parent culture takes the regional
   culture (`aov_set_regional_elven_culture_effect`; county titles use `aov_set_regional_elven_county_culture_effect`).
   Counties of other cultures inside `k_ibevar` (Escin, Whistlehill, Hushdell, Crintheda) are left alone.
2. Characters: every living wood or moon elf whose location (their court's capital) is in a county of an elven culture
   descended directly from their own takes that culture. This covers the rulers the game generates for the
   unheld Deepwoods counties, the historical rulers (Ioriel, Ibenion, Ultarion, Arda, Variondar, Maldorian,
   Camnaril, Liandel) and their courts. A moon elf at a human court keeps `moon_elvish`; the elven heritage check
   keeps human cultures descended from moon elves out.

Anbennar rolls racial purist traits on `on_game_start_after_lobby`, after this; the override keeps moon elf
cultures at moon elves' 25% (wood elves keep the 5% default, sun elves 90%).

## Compatibility

Checks of exact culture keys were switched to culture lineage so the new cultures count as their parent:
- Racial men-at-arms already use `aov_*_elven_lineage_trigger` (`racial-armies.md`).
- Elven walls (`build_holding_models.py`, `uses_elf_gfx`): an elven culture that is or descends from a culture with
  the elf building gfx.
- Elven Haven AI weights for RiE's high elves (`tools/data/rie_elves.py`): every elven culture outside the wood
  elf lineage.
- Monument gates (`tools/data/monuments/*.py`): `culture = { aov_<moon|sun|wood>_elven_lineage_trigger = yes }`.

Known gaps (Anbennar checks the exact key; left alone to keep its files unmodified):
- Pool characters (`00_pool_repopulation_character_templates.txt`) spawn as `wood_elvish` in the Deepwoods and
  `moon_elvish` in Cannor.
- `k_ibevar`'s AI primary-title preference checks `moon_elvish`.
- The four moon elf hybrids (Calindalic, Urionmari, Nuralenic, Thilosian) form only from `moon_elvish`.
- Anbennar's culture-window descriptions (`anb_culture_desc_*`) exist only for moon and sun elves.

**To confirm in game:** the 13 cultures appear on the map at 1022 in the grove duchies and moon elf realms; the
Deepwoods rulers, Ioriel, Ibenion, Maldorian and Camnaril have the regional culture; the moon elf courtiers of human
rulers stay Moon Elvish; the culture window shows the parent and history line; elven walls, elven men-at-arms and
the Deepwoods monuments (Ciranmyna) still work for the new cultures; regional rulers keep the Ceann/Prince titles.

# Racial traditions

Every racial culture that had no tradition of its own gets one, written from EU4 Anbennar's ideas for its realm or
culture group, and most of them unlock a men-at-arms unit. Three human cultures with two traditions or fewer get an
existing tradition. The Sundancer Legions are back for sun elves, without their levy penalty. The five Serpentreach
hold cultures (`serpentreach.md`) get a clan tradition and unit each, and marble dwarves get a second tradition for
their homeland.

## Files

| File | Generator | Why |
|---|---|---|
| `common/culture/traditions/aov_racial_traditions.txt`, `common/men_at_arms_types/aov_regional_maa_types.txt`, `common/script_values/aov_regional_maa_values.txt`, `common/scripted_effects/aov_racial_traditions_effects.txt`, `localization/english/aov_racial_traditions_l_english.yml` | `python -I tools/build_racial_traditions.py` (data `tools/data/racial_traditions.py`) | 40 traditions, 17 units with their costs, the game-start grants and their text, from one data file. It errors on an unknown culture or tradition, a unit no tradition unlocks, a missing icon, or a Realms in Exile word in our text. Rerun `build_racial_levies.py` afterwards if a tradition gains a levy modifier. |

Hand-written:
- `common/on_action/aov_racial_traditions_on_actions.txt`: the `on_game_start` hook.
- `tradition_sundancer_legions` in `common/culture/traditions/zz_aov_racial_traditions.txt`: Anbennar's tradition
  without `levy_size = -0.35` and `levy_reinforcement_rate = -0.35`. `sundancer_legions` and `jaherkadezim` in
  `zz_aov_racial_maa_overrides.txt` use Anbennar's gate again (`valid_for_maa_trigger` with the tradition's parameter).
  `aov_racial_armies_game_start` no longer removes the tradition.
- The clan units in `common/men_at_arms_types/aov_dwarven_maa_types.txt` are gated by
  `valid_for_maa_trigger = { PARAMETER = aov_unlock_maa_<unit> }`, set by the clan tradition.
- Druids (`zz_aov_faith_maa_overrides.txt`): the Druidic tenet or the Thorn grove's `aov_unlock_maa_thorn_druids`.
- Text for the Sundancer Legions (Anbennar ships "GILLY TODO"): `aov_tradition_text_replace_l_english.yml`.
- Art: Realms in Exile's icon, big and small pictures, copied once as `aov_rie_<art>` into
  `gfx/interface/icons/regimenttypes/` and `gfx/interface/illustrations/men_at_arms_{big,small}/`.

## How it works

- **Gate.** Each tradition is shown to its heritage and can be picked by its culture and every culture descended from
  it (`any_parent_culture_or_above`). The moon and wood elf traditions use the racial armies lineage triggers
  (`aov_moon_elven_lineage_trigger`, `aov_wood_elven_lineage_trigger`).
- **Grant.** `aov_racial_traditions_game_start_effect` adds each culture's traditions at game start when it lacks
  them. The regional elf cultures (`elven-cultures.md`) get their parent's tradition and their own.
- **Units.** A unit needs its tradition's parameter (`aov_unlock_maa_<unit without aov_>`), through
  `valid_for_maa_trigger` (vanilla's, which also covers landless adventurers). Costs follow the racial armies pricing:
  the role's vanilla buy cost and upkeep × √(regiment damage ratio × regiment toughness ratio); high upkeep is 3× low.
  Elf units are elite (25 or 50 men); gnoll and halfling units have 100 men.
- **Cost.** Every tradition costs the base prestige, like `tradition_gnomish_ingenuity`, with no ethos penalty.

## Traditions

| Tradition | Cultures | Effects | Unlocks |
|---|---|---|---|
| Elven High Culture | moon_elvish, redglader, ibevari, celmaldorian, venaili | prestige +15%, Diplomacy +1, mercenary hire cost −15% | |
| The Ranger Art | wood_elvish and the nine grove cultures | movement speed +10%, supply duration +25%, forest and taiga advantage +4 | |
| Ioriel's Accords | redglader | different-culture opinion +10, cultural acceptance +25% (culture) | Érhetana Sentinels |
| Defense of the Forlorn Vale | ibevari | defender advantage +4, knight effectiveness +15%, archer damage +10% | Blaiddscal Blademasters |
| Elves of the Reach | celmaldorian | Diplomacy +1, embarkation cost −30%, naval speed +15% | Escorts of the Trade Princes |
| Lessons of the Remnant Fleet | venaili | embarkation cost −40%, naval speed +20%, diplomatic range +20% | Remnant Fleet Marines |
| The Verdant Pact | lake_elvish | vassal limit +5, vassal levy and tax contribution +10% | Oak Oath Guard |
| Never to Fall | mountain_elvish | garrison +30%, hills and mountains advantage +4 | Speardancers |
| Closest to the Fey | thorn_elvish | piety +15%, Learning +1, defender advantage +2 | Druids |
| The Bone Struggle | bone_elvish | hostile scheme success +10, siege phase time −10%, hostile county attrition +10% | Bonecoated Infiltrators |
| Great Beast Hunters | hunter_elvish | light cavalry damage and toughness +15%, upkeep −20% (Hyodeth); prestige +10% | |
| Every Elf a Botanist | flower_elvish | domain tax +10%, health +0.25, hostile scheme success +5 | Scotha Poison Archers |
| A Grove of Peace and Abundance | river_elvish | stress gain −15%; counties: development +15%, opinion +5 | |
| Clan of the Greatest Archers | arrow_elvish | archer damage +15% and toughness +10% (Ayethi), building cost −10% | |
| The Shadow Grove | shadow_elvish | enemy hostile scheme success −10, Intrigue +1, dread gain +15% | Witchwood Stalkers |
| Our Rubies | ruby_dwarvish | prestige +10%, domain tax +10%, siege phase time −10% | Grudgebearers |
| Silver Army Engineers | silver_dwarvish | siege phase time −15%, Stewardship +1, siege weapon upkeep −20% | Silverforge Engineer Corps |
| Solid as Stone | stone_dwarvish | hard casualties −10%, defender advantage +3, pikemen toughness +10% | Tortoise Formation |
| Giantbane | agate_dwarvish | archer damage +10%, knight effectiveness +10%, prowess +2 | Giantbane Crossbows |
| Uthojdihr Seafarers | copper_dwarvish | embarkation cost −40%, naval speed +15%, wetlands advantage +4 | Uthojdihr Marines |
| The Citrine Code | citrine_dwarvish | different-culture opinion +10, Diplomacy +1, skirmisher damage +15% | Seg Band Gnollhunters |
| The Three Golden Gates | gold_dwarvish | domain tax +10%, garrison +25%, mercenary hire cost −15% | Golden Gate Guard |
| The Thirteen Stages of Enlightenment | pyrite_dwarvish | fascination +15%, build time −15%, Learning +1 | Massed Clockwork Bows |
| The Titanium Orders | titanium_dwarvish | heavy infantry toughness +15%, prowess +2 | Dauvek Veker |
| The Copper Road Pact | topaz_dwarvish | movement speed +15%, garrison +20%, defender advantage +2 | Copper Road Wardens |
| Masons of the Deep | marble_dwarvish | building cost −15%; counties: development +10% | Brightbeard Hammers |
| The Whitestone Council | marble_dwarvish (second grant) | powerful vassal opinion +10, councillor opinion +10, piety +10% | |
| The Glasslords | cobalt_dwarvish | domain tax +10%, Learning +1; counties: development +10% | Lens Crossbows |
| The Aegis of the Serpentreach | diamond_dwarvish | prestige +10%, Diplomacy +1, vassal opinion +5 | Lightflare Guard |
| The Warding Gate | flint_dwarvish | defender advantage +4, enemy hostile scheme success −10, hostile county attrition +10% | Flint Forest Rangers |
| The Hold Where Love Lives | garnet_dwarvish | fertility +15%, spouse opinion +15; counties: opinion +5 | Orcrend Guard |
| Hearts of Fire | basalt_dwarvish | prowess +2, heavy infantry damage +15%, hostile county attrition +10% | Basalt Berserkers |
| Scavengers and Raiders | sandfang_gnoll | raid speed +25%, loot +25%, supply duration +20% | Hyena Riders |
| A Tight Leash | fieldstalker_gnoll | dread gain +20%, county control growth +15%, hostile county attrition +10% | Fieldstalker Packs |
| Apple Lords | ciderfoot_halfling | health +0.2, stress gain −10%, domain tax +10% | Orchard Bowmen |
| Begga's Two Hands | beefoot_halfling | Diplomacy +1, domain tax +10%, different-faith opinion +10 | Seedoud Marines |
| Mound Forts | bluefoot_halfling | garrison +25%, defender advantage +3, hard casualties −10% | Mound Wardens |
| Small Country Envoys | visfoot_halfling | Diplomacy +1, different-culture opinion +10 | Moot Keepers |
| Charter Rights | imperial_halfling | Stewardship +1; counties: opinion +5 | Charter Rangers |
| Hearth and Harvest | moonfoot_halfling | levy reinforcement +15%; counties: development +10% | Hearth Muster |

Existing traditions granted to thin human cultures: Reverian `tradition_seafaring`, Shasoura `tradition_caravaneers`,
Taric `tradition_winter_warriors`.

Left alone (they already have one): harpies, kobolds, Suncrown gnolls, gnomes (`tradition_gnomish_ingenuity`), and the
Oakfoot, Redfoot, Roysfoot and Hillfoot halflings. Old Gerudian and Dostanorian hold no land at game start.

## Units

| Unit | Type | Men | Damage/toughness per man | Buy | Low upkeep | RiE art |
|---|---|---|---|---|---|---|
| Érhetana Sentinels `aov_erhetana_sentinels` | skirmishers | 50 | 50/70 | 105 | 0.35 | `thorn_guard` |
| Blaiddscal Blademasters `aov_blaiddscal_blademasters` | heavy infantry | 25 | 320/190 | 210 | 0.93 | `noldor_glaivesmen` |
| Escorts of the Trade Princes `aov_trade_prince_escorts` | pikemen | 50 | 85/120 | 165 | 0.66 | `seaward_spearmen` |
| Remnant Fleet Marines `aov_remnant_fleet_marines` | skirmishers | 50 | 55/65 | 105 | 0.35 | `falathrim_haven_guard` |
| Oak Oath Guard `aov_oak_oath_guard` | heavy infantry | 25 | 270/230 | 210 | 0.94 | `galadhrim_sentinels` |
| Speardancers `aov_speardancers` | heavy infantry | 25 | 300/200 | 210 | 0.92 | `galadhrim_warriors` |
| Bonecoated Infiltrators `aov_bonecoated_infiltrators` | skirmishers | 50 | 55/65 | 105 | 0.35 | `silent_stingers` |
| Scotha Poison Archers `aov_scotha_poison_archers` | archers | 50 | 120/35 | 115 | 0.41 | `druedain_poison_archers` |
| Witchwood Stalkers `aov_witchwood_stalkers` | archers | 50 | 115/40 | 120 | 0.43 | `marksmen_of_the_matron` |
| Hyena Riders `aov_hyena_riders` | light cavalry | 100 | 30/18 | 110 | 0.45 | `hunter_orcs_on_fell_wargs` |
| Fieldstalker Packs `aov_fieldstalker_packs` | skirmishers | 100 | 16/22 | 65 | 0.22 | `caragor_pack` |
| Orchard Bowmen `aov_orchard_bowmen` | archers | 100 | 24/10 | 55 | 0.2 | `vineyard_bowmen` |
| Seedoud Marines `aov_seedoud_marines` | skirmishers | 100 | 12/18 | 50 | 0.17 | `quayside_crossbowmen` |
| Mound Wardens `aov_mound_wardens` | pikemen | 100 | 18/30 | 75 | 0.3 | `hobbit_bounders` |
| Moot Keepers `aov_moot_keepers` | heavy infantry | 100 | 28/22 | 85 | 0.37 | `moot_keepers` |
| Charter Rangers `aov_charter_rangers` | archers | 100 | 22/12 | 55 | 0.21 | `hobbit_hunters` |
| Hearth Muster `aov_hearth_muster` | skirmishers | 100 | 10/18 | 50 | 0.16 | `hobbit_muster` |

Wood elf units stay open to every wood elf culture (`racial-armies.md`); the Hunter and Arrow traditions strengthen
Hyodeth and Ayethi through light cavalry and archer modifiers, which also reach other units of those types.

## Tests

`tools/tests/test_build_racial_traditions.py`: gates, unit unlocks, every other parameter reaching its unit, pricing,
art, game-start grants, loc, generator errors and freshness. `test_racial_armies.py` checks the Sundancer override
against Anbennar (only the two levy lines dropped) and the tradition gates of the Sundancer and clan units.

## To confirm in game

1. At 1022 each listed culture shows its new tradition; the regional elf cultures show two (Elven High Culture or The
   Ranger Art, and their own); sun elves show the Sundancer Legions without a levy penalty.
2. Each new unit appears in its culture's recruit list with the RiE icon and picture, and the tradition tooltip names it.
3. Sun elves can recruit Sundancer Legionaries and Jaherkadezim; a divergent sun elf culture without the tradition cannot.
4. Each dwarf clan can still recruit its clan unit; a Thorn elf ruler of another faith can recruit Druids.
5. Each modifier shows in the tradition tooltip (no blank lines for an unknown modifier).
6. The Reverian, Shasoura and Taric cultures show their added tradition.

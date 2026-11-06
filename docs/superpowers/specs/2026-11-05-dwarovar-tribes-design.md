# Dwarovar tribes design

Orcs and goblins take the Serpentspine as the lore has it in 1022. 27 tribes rule 215 of the 256 carved counties under
two new tribal-style governments that ignore de jure. The dwarven kingdoms stay whole on the de jure map, as titles to
reclaim. Only six holds on the map are still dwarven.

This replaces the assumption in `2026-11-02-serpentreach-design.md` and `2026-11-03-west-dwarovar-design.md` that the
holds are still dwarven at the 1022 start.

## Intent

- **User asked:** put orcs and goblins in the Serpentspine and Serpentreach with one placeholder culture each, under a
  government that does not rely on de jure territory, so the dwarven hold kingdoms stay intact while tribes form their
  own realms on land that does not belong to them. Placement must follow Anbennar's lore.
- **User chose:**
  - *West Dwarovar:* the lore start, with no dwarves there at all in 1022.
  - *Serpent's Vale:* held by the Amldihr orcs for now; ogres are a later job.
  - *Governments:* an orcish warband and a goblin chiefdom, which function like tribal governments and ignore de jure
    penalties.
  - *Realm identity:* a tribal realm's name and arms come from its ruler's dynasty and change with it.
  - *Duels:* an orc vassal of an orcish realm can challenge the ruler. The winner kills the loser; a winning vassal
    becomes the new top ruler. Goblins cannot challenge. The ruler can refuse, at the price of their prestige and
    standing.
  - *Titles:* special decisions to form duchy, kingdom and empire titles, and a special option to grant titles to
    vassals. Dukes can create count vassals.
  - *Culture revival:* a decision only, and only for a dwarf holding no other hold.
  - *Ruined holds:* the existing mechanic is removed. The user plans to rework this later.
- **Success:**
  - The game starts cleanly with the placement below.
  - The de jure map is unchanged and stays unchanged in play.
  - Tribal realms show their ruler's dynasty name and arms, and both change after a duel.
  - Tribes fight each other and the dwarves, and the AI does not spill onto the surface before the lore's Greentide.
  - A dwarf who reclaims a lost hold can revive its culture.
  - The generators rebuild everything after an Anbennar update.

## Lore basis

Sources: the Anbennar Wiki (`Category:Serpentspine`, `Orcish_Warpath`, `The_Western_Collapse`,
`Siege_of_the_Serpentreach`, `Segbandal`, `Black_Orc`, `Hold_of_<name>`) and EU4 Anbennar's mission and event text. Where
they disagree it is by a few years, and the later date is used.

| Hold | In 1022 | Why |
|---|---|---|
| Seghdihr, Verkal Gulan | Dwarven | Four Segbandal kings meet Jaher in 1015. Seghdihr falls to Jexis in 1139 |
| Hehodovar | Dwarven, gates barred | Retreated in 816; destroyed in 1156 |
| Gor Ozumbrog | Dwarven | Sacked after 1139; lost in 1154 |
| Arg-Ôrdstun | Dwarven, sealed | Sealed itself by decree in 4538 BA; never falls |
| Ovdal Lodhum | Dwarven | Reopened its gates in 2631 BA; never falls |
| Gor Vazumbrog | Orc (Skewered Drake) | Dragon in 472; Gorrath's warband settled in 894; clan named in 937 |
| Verkal Skomdihr | Goblin | Deepwoods goblins took it in 1 AA when the Warding Gate exploded |
| Shazstundihr | Goblin | Uninhabitable from a cursed relic by 271 BA; goblins squat there |
| Orlghelovar | Orc | 2686 BA |
| Gor Bûrad | Orc | 3641 BA |
| Haraz Orldhûm | Orc | 5750 BA, when goblin slaves opened the gates |
| Orlazam-az-dihr | Orc | 5850 BA |
| Mithradhûm | Orc | 5860 BA |
| Amldihr | Orc | 5888 BA |
| Er-Natvir | Orc | 5934 BA |
| Verkal Kozenad | Orc | 5970 BA |
| Hul-Jorkad | Orc | First to fall (6000 BA). The Segbandal held it from about 4467 BA until about 2681 BA |
| Dûr-Vazhatun | Goblin | Astral madness in 6284 BA, before the orcs. The goblins are an assumption from EU4's 1444 map |
| Khugdihr | Kobold | Dwarves driven out in 476; kobolds until Nimrith dies in 1103. Already so in Anbennar |

Three more facts shape the design:

- **Orcs dominate in 1022, not goblins.** After 894 the wiki describes the Dwarovar as a land of orcs, with goblin tribes
  fought or enslaved en masse. EU4's goblin-heavy 1444 map comes after the Greentide (1424) took most orcs out.
- **Some clans do not exist yet.** Mountainshark forms in 1428 and Siegebreaker around 1415, so neither is used. Darkscale
  kobolds spread only after 1103, so kobolds stay around Khugdihr. Clans with no founding date stay as placeholders.
- **Orc kingdoms have precedent.** Khogond-u Madrul ran from Mithradhûm to Er-Natvir from 126 BA to 66 AA. Most clan
  infoboxes give the government as "Dwarovar Warband".

## Placement

Totals: 148 orc, 67 goblin, 31 dwarf and 10 kobold counties.

| Region | Counties | Dwarves | Orcs | Goblins | Kobolds |
|---|---|---|---|---|---|
| Serpentreach | 67 | 5 | 38 | 24 | |
| West Dwarovar | 132 | 0 | 97 | 25 | 10 |
| Segbandal | 57 | 26 | 13 | 18 | |

Each tribe is one connected piece on the province map, checked with county adjacency from `map_data/provinces.png` and
the two `CROSSINGS`. The seat is the first county. Areas are EU4 area keys without `_area`.

### Dwarves

| Realm | Counties | Areas |
|---|---|---|
| Arg-Ôrdstun | 1 | the hold county only (`c_arg_ordstun`) |
| Ovdal Lodhum | 4 | `ovdal_lodhum` |
| Hehodovar | 6 | `hehos_legacy`, `dwarovrod_30_32` |
| Seghdihr | 9 | `seghdihr`, `dwarovrod_33_35`, `steamsource` |
| Verkal Gulan | 3 | `verkal_gulan` |
| Gor Ozumbrog | 8 | `ozumbrog`, `dwarovrod_38_41` |

The four Segbandal holds stay connected through their own land.

### Orcs

| Tribe | Seat | Counties | Areas | Fallen hold |
|---|---|---|---|---|
| Masked Butcher | Bloodied Altar | 14 | `north_altar`, `south_altar`, `orlghelovar`, `argrod_origin` | Orlghelovar |
| Moltenbrand | Gor Bûrad | 14 | `gor_burad`, `argrod_14_16`, `argrod_junction`, `argrod_9_11`, Lavawater, Bûrad Depths | Gor Bûrad |
| Diamond Mines orcs | Greater Mines | 6 | `arg_ordstun` (not the hold), `kings_caverns` | |
| Still Caverns orcs | Caravan's Rest | 4 | `still_caverns` | |
| Amldihr orcs | Amldihr | 18 | `amldihr`, `royal_terrace`, `common_terrace`, `assembly_terrace`, `castle_hill` | Amldihr |
| Orldhûm orcs | Haraz Orldhûm | 17 | `orldhum`, `dwarovrod_4_6`, `dwarfbreak`, `dark_depths`, `chainlink_mines` | Haraz Orldhûm |
| Mithradhûm orcs | Mithradhûm | 14 | `mithradhum`, `dwarovrod_7_9`, `dwarovrod_10_12`, `riftway` | Mithradhûm |
| Kozenad orcs | Verkal Kozenad | 13 | `stunad_kozenad`, `dwarovrod_15_17`, `travelers_refuge`, `zokkorna_caverns` | Verkal Kozenad |
| Orlazam orcs | Orlazam-az-dihr | 13 | `orlazam`, `dagrinrod_4_6`, `dagrinrod_7_9`, `old_dagrinrod` | Orlazam-az-dihr |
| Wretched Skull | Hul-Jorkad | 11 | `jorkad_junction`, `azmak`, `dwarovrod_21_24` | Hul-Jorkad |
| Railyard orcs | Er-Natvir | 11 | `railyard`, `railyard_exchange`, `dagrite_depths` | Er-Natvir |
| Skewered Drake | Gor Vazumbrog | 9 | `vazumbrog`, `dwarovrod_27_29`, `misty_cave_trail` | Gor Vazumbrog |
| Deep One's orcs | Waterlogged Cave | 4 | `deep_ones_lair` | |

### Goblins

| Tribe | Seat | Counties | Areas | Fallen hold |
|---|---|---|---|---|
| Skomdihr goblins | Verkal Skomdihr | 7 | `stunad_skomdihr`, `argrod_6_8` | Verkal Skomdihr |
| Burnt Skin | Molten Core | 6 | `zarn`, Molten Core, Bûradforge | |
| Shazstundihr squatters | Shazstundihr | 4 | `shazstundihr` | Shazstundihr |
| Thieving Arrow | Arrowden | 4 | `thievesbane` | |
| Shroomfissure | Shroomcave | 3 | `shroomfissure` | |
| Vazhatun goblins | Dûr-Vazhatun | 6 | `vazhatun`, `dagrinrod_13_15` | Dûr-Vazhatun |
| Spiderwretch | Weballey | 6 | `westnest`, `eastnest` | |
| Goblin's Bypass | Goblinsroad | 4 | `goblins_bypass` | |
| Railskulker | Underpassage | 3 | `skulkers_lair` | |
| Truedagger | Broken Dagger Pass | 3 | `broken_dagger_pass` | |
| Snotfinger | Snotslair | 3 | `snotslair` | |
| Trolltamer | North Greatcavern | 7 | `greatcavern`, `stunad_kradoz` | |
| Greedy Grin | Old Coinvault | 6 | `goblin_grotto`, `diggers_road` | |
| Xazor goblins | Pit of Xazor | 5 | `xazor`, `ulagom` | |

### Kobolds

`khugdihr`, `dwarovrod_1_3` and `fallen_asra` stay as they are today (10 counties).

### What placement leaves out

- Ogres in the Vale (EU4's Mossmouth) wait for their own culture and portraits.
- Cave trolls (EU4's Grizehûd, south of Verkal Gulan) sit inside Trolltamer's land for now.
- No tribe county is one of Anbennar's own (`EXISTING` in `tools/data/segbandal.py`, `tools/data/west_dwarovar.py`), so
  Anbennar's province history is not touched. A test keeps it so.

## Governments

Two governments, `orcish_warband_government` ("Orcish Warband") and `goblin_chiefdom_government` ("Goblin Chiefdom"), in
a generated `common/governments/aov_dwarovar_governments.txt`.

- **Copied from `tribal_government`** by the generator, from the overhaul's generated `00_government_types.txt`, so a CK3
  patch carries through. That includes its rules, `primary_holding = tribal_holding`, `tribal_vassal` contracts, and the
  flags `government_is_tribal`, `use_prestige_to_buy_maa` and `government_can_raid_rule`. About 200 game files read
  `government_is_tribal`, so this flag is what gives them tribal laws and wars.
- **Added:**
  - `government_ignores_rightful_liege_penalties = yes`. Vanilla's `steppe_admin_government` and RiE's
    `orcish_government` use it; it is not in `_governments.info`, so it is tested in game.
  - `sticky_government = yes`, `use_as_base_on_landed = yes`, `use_as_base_on_rank_up = yes`.
  - `dynasty_named_realms = yes`.
  - `can_get_government`: `has_trait = race_orc` or `race_goblin` respectively.
  - Flag `government_is_dwarovar_tribe`, plus `government_is_orcish_warband` or `government_is_goblin_chiefdom`.
- **Vanilla decisions blocked:** a generated `common/decisions/zz_aov_dwarovar_tribes_overrides.txt` copies these from
  Anbennar's files, adding `NOT = { government_has_flag = government_is_dwarovar_tribe }` to `is_shown`. The generator
  stops if a key is gone, as `build_race_relations.py` does.
  - `convert_to_feudalism_liege_converted_decision`, `convert_whole_realm_to_feudalism_decision` and
    `convert_whole_realm_to_feudalism_west_african_pagan_decision`: tribes do not feudalise.
  - `tribal_challenge_ruler_decision`: replaced by the duel below, and goblins must not be able to challenge.
  - `found_duchy_decision`, `found_kingdom_decision` and `found_empire_decision`: these make dynamic titles, which land
    could drift into. Tribes use the pool decisions instead.
- **Keeping government by race:** `on_title_gain` changes a new holder to the matching government when they are an orc or
  goblin in a realm of these governments. RiE does the same.
- **Holdings:** a tribe county's first barony becomes `tribal_holding`, in place of `castle_holding`. Hold baronies stay
  `dwarven_hold_holding`. Other baronies in tribe counties start empty.

## Tribal titles

### The pool

A generated `common/landed_titles/aov_dwarovar_tribes.txt` defines blank top-level titles with no de jure land, modelled
on vanilla's `k_danelaw`. No title belongs to a tribe.

| Pool | Orcish (name in the title) | Goblin (name in the title) |
|---|---|---|
| Duchy | 40, `d_aov_warband_NN` ("Warband") | 40, `d_aov_chiefdom_NN` ("Chiefdom") |
| Kingdom | 20, `k_aov_warband_NN` ("Warhost") | 15, `k_aov_chiefdom_NN` ("High Chiefdom") |
| Empire | 6, `e_aov_warband_NN` ("Horde") | 4, `e_aov_chiefdom_NN` ("Swarm") |

Wording is placeholder. Sizes are in the data file, so a run-out is fixed by raising a number. A decision or interaction
with no free title is shown unavailable, with a tooltip.

Every pool title has:

- `de_jure_drift_disabled = yes`, so no land drifts into it;
- `no_automatic_claims = yes`;
- `ignore_titularity_for_title_weighting = yes`, so it is chosen as the primary title;
- `definite_form = yes`, so it does not read "Kingdom of";
- `can_create = { always = no }`, as only script creates them;
- its own map colour, spread by hue, as the game cannot take a colour from a dynasty.

`create_dynamic_title` is not used: drift is switched off in a title's definition, and no effect sets it during play.

A title with no holder is free for reuse. Taking one sets its capital to the ruler's capital (`set_capital_county`) and
applies the dynasty arms. A pool title reaching a holder who is neither orc nor goblin is destroyed, which frees it.

### Name and arms follow the dynasty

The ruler's dynasty is the realm's identity, so tribe names in the placement tables are dynasty names. Ten take their
EU4 country's flag as dynasty arms, converted once with `tools/eu4_import.py convert`:

| Dynasty | EU4 tag | Dynasty | EU4 tag |
|---|---|---|---|
| Masked Butcher | H81 | Railskulker | H75 |
| Thieving Arrow | H87 | Truedagger | H85 |
| Burnt Skin | M05 | Snotfinger | H89 |
| Wretched Skull | H86 | Skewered Drake | H73 |
| Spiderwretch | H90 | Greedy Grin | H82 |

The other 17 take generated arms and names; their table names are place labels for this spec.

- **Arms:** `aov_tribe_title_sync_effect` runs `set_coa = root.dynasty` on a pool title when its holder changes
  (`on_title_gain`) and at game start. Vanilla sets arms with `set_coa = holder.house` and `set_coa = dynasty:<key>`. The
  scoped dynasty form is unproven and is part of the first test.
- **Name in the title window:** the pool title's localization reads its holder's dynasty when displayed, such as
  `d_aov_warband_01: "[GetTitleByKey('d_aov_warband_01').GetHolder.GetDynasty.GetName] Warband"`. `GetTitleByKey` is
  common in vanilla localization, but no vanilla title name uses a data function, so this may not work.
- **Name on the map:** `dynasty_named_realms = yes` with `house_based_map_names = yes` on the two cultures' name lists.
  Vanilla's rules apply: a culture head is named after the culture ("The Orcs"), a ruler who is not their dynasty's head
  shows the title's name, and players can turn the feature off in settings.
- **Fallback for the title name:** a generated name for each known dynasty, set with `set_title_name` from a table. New
  dynasties formed in play would keep the plain pool name.

All pool titles follow this, including vassal duchies, so a vassal's duchy shows that vassal's dynasty.

### Starting tiers

Every tribe's chief starts as a duke on a pool duchy, as orc kingdoms were occasional rather than normal. Each other EU4
area in the tribe has a sub-chief as the chief's vassal. Counties, not duchies, are what they hold: a tribe never holds a
dwarven title.

### Forming and granting

| Action | Who | Needs | Gets |
|---|---|---|---|
| Decision: form a duchy-level title | A tribal count | 3 or more counties in the realm; 250 prestige | A free pool duchy |
| Decision: form a kingdom-level title | A tribal duke | 15 or more counties in the realm; 500 prestige | A free pool kingdom |
| Decision: form an empire-level title | A tribal king | 40 or more counties in the realm; 1000 prestige | A free pool empire |
| Interaction: raise a vassal | A tribal ruler | Vassal two or more tiers below the ruler, of a tribal government; 200 prestige from the ruler | A free pool title one tier below the ruler, for that vassal |

- Thresholds and costs are in the data file, as starting values to tune.
- The normal create-title route needs a de jure county, which is why these exist.
- Kings raise dukes and emperors raise kings. A duke creates count vassals with vanilla's grant interaction, by granting
  a county from their domain to a courtier. It works on any held county, de jure or not, so no new interaction is needed;
  this is on the in-game list.
- A pool title the ruler already holds can still be granted through vanilla's grant interaction.
- The Amldihr and Orldhûm orcs meet the kingdom requirement at the start. AI weights must keep this from all happening
  in the first year.

## Keeping dwarven titles dwarven

- **Generated titles:** the Serpentreach, Segbandal and West Dwarovar generators add `can_create` to every duchy, kingdom
  and empire they write, refusing `government_is_dwarovar_tribe`, and `de_jure_drift_disabled = yes` to their kingdoms
  and empires.
- **Anbennar's titles:** `k_seghdihr`, `k_hehodovar`, `k_verkal_gulan`, `k_gor_ozumbrog`, their duchies and
  `e_middle_dwarovar` live in Anbennar's files. A generated `zz_aov_` override redefines only these titles, nested as in
  Anbennar, repeating each one's own fields copied from Anbennar and adding the same `can_create` and drift settings. Their
  counties are not repeated and stay as they are. The first test shows why it takes this form (see First test results).
- **Dwarven rulers removed:**
  - The elders of whole duchies now held by tribes.
  - The emperors of `e_serpentreach` and `e_west_dwarovar`, which end unheld.
  - All eight West Dwarovar kingdom holders.
  - Serpentreach's kings, except Arg-Ôrdstun and Ovdal Lodhum, who become independent kings of their own kingdoms.
- **Dwarven rulers added:** kings for Hehodovar (Pyrite) and Gor Ozumbrog (Topaz, dynasty az-Fiobmhor from the wiki),
  which Anbennar ships with no holder, under `e_middle_dwarovar` as `k_verkal_gulan` is. Every county in a dwarven realm's
  table above has a holder.
- **Fallen holds:** the 13 tribe-held holds stay `dwarven_hold_holding` at their start levels. Hold level effects already
  need a dwarven holder, so they give a tribe nothing.

## Duels (orcs only)

A decision, `aov_challenge_warlord_decision`, modelled on vanilla's `tribal_challenge_ruler_decision` and
`tribal.1001` (`events/government_events/tribal_events.txt`), run through vanilla's `configure_start_single_combat_effect`.
RiE's `decision_challenge_the_orc_leader` is switched off in RiE itself (`always = no`), so it is reference only. Vanilla's
own challenge reads `government_is_tribal` and would let goblins challenge, so it is blocked for these governments (see
Governments).

- **Who:** a landed direct vassal with `has_trait = race_orc`, of an independent ruler with
  `government_is_orcish_warband`. Goblin vassals cannot challenge.
- **Limits:** adult, not imprisoned, neither side at war, a 5-year cooldown per challenger.
- **The ruler chooses:** the challenge reaches them as an event, to accept or refuse.
- **If the ruler refuses:**
  - their prestige drops to the lowest level (`add_prestige_level = -5`, which vanilla's effect clamps at the bottom;
    the check is on the in-game list);
  - they get a permanent character modifier, `aov_refused_challenge` ("Refused the Challenge"), with
    `general_opinion = -50`, a starting value to tune;
  - no duel is fought and no titles change. The challenger's cooldown still runs.
- **The fight:** `FATALITY = no`, so nobody dies inside the combat; the outcome event does the killing, in the order
  below.
- **If the challenger wins:** they take every title the ruler holds, the ruler's vassals pass with them, and the ruler
  dies (`death_reason = death_duel`). Transfers happen before the death, so the realm does not partition. The sync
  effect then sets the winner's arms and name.
- **If the ruler wins:** the challenger dies, and their titles pass to their heir normally.
- **AI:** challenges when its prowess beats the ruler's by a margin, weighted by traits; never when far weaker. An AI
  ruler rarely refuses, and only when far weaker, as refusal costs so much.

`general_opinion` is the only field reaching every ruler, including vassals in other realms. Courtiers and other
non-rulers take the malus too. The modifier stays on that character for life and does not pass to their heir.

Goblin chiefdoms have no duels. Their rulers inherit normally, and the dynasty rules still apply.

## Wars

- **The existing wars stay:** `aov_monster_conquest_cb` and `aov_purge_monsters_cb` already work without de jure. The
  purge war is how dwarves reclaim land.
- **New `aov_tribal_war_cb`:** a tribal ruler takes a neighbouring county of another tribal ruler. The existing monster
  war targets only non-monstrous rulers, so without this the tribes could not fight each other, which the lore has them
  doing constantly.
- **No early surface conquest by the AI:** tribes hold surface gates (Orlghelovar, Shazstundihr, Glogund Cave, Verkal
  Skomdihr, Hul-Jorkad, Dwarfhope). The lore's Greentide is not until 1424. AI tribal rulers do not start a conquest war
  on a county outside `world_serpentreach`, `world_west_dwarovar` and `world_segbandal`. Raiding stays allowed, and
  players are not limited.

## Placeholder cultures and faiths

- **Cultures:** `black_orc` and `cave_goblin`, EU4's most common of each, with `heritage_orcish` and `heritage_goblinoid`
  and their own languages. Anbennar has none of these, only the race traits. Name lists come from EU4, with
  `house_based_map_names = yes` and collective nouns "Orcs" and "Goblins".
- **Faiths:** placeholder Old Dookan and Goblinic Shamanism, each with the holy sites a faith needs.
- **Look:** humans for now, as gnolls were. Vic3 Anbennar has `orc_head_bs` and `goblin_head_bs` for a later portraits
  job (see `gnoll-portraits.md`).
- **Monstrous status:** the race traits already make them monstrous under `aov_is_monstrous_trigger`.

## Reviving a hold's culture

A decision only, "Revive the Heritage of [Hold]", with no prompt on creating a kingdom.

- **Available to** a landed dwarf where all of these hold:
  - they personally hold exactly one hold, of any kind, and it is this hold;
  - the hold's de jure kingdom has no holder;
  - their culture is not the hold's.
- **Effect:** the ruler, spouse and children take the hold's culture, and so does the hold's county. The rest of the
  realm's land is untouched. Costs 500 prestige, a starting value to tune.
- **Examples:** Arg-Ôrdstun conquering Orlghelovar never gets it. A hold-less dwarf who settles Orlghelovar does. So does
  a vassal granted it, which is the one way a large dwarven realm can bring a culture back.
- **AI:** takes it only when the hold is their capital.
- **Data:** a `culture` field on each hold in `tools/data/holds.py`, read by `build_holds.py` to generate the decision's
  per-hold data.

| Hold | Culture | Hold | Culture |
|---|---|---|---|
| Hul-Jorkad | `lead_dwarvish` | Verkal Skomdihr | `flint_dwarvish` |
| Verkal Kozenad | `opal_dwarvish` | Gor Bûrad | `basalt_dwarvish` |
| Er-Natvir | `dagrite_dwarvish` | Gor Vazumbrog | `titanium_dwarvish` |
| Mithradhûm | `mithril_dwarvish` | Khugdihr | `agate_dwarvish` |
| Amldihr | `kronium_dwarvish` | Seghdihr | `citrine_dwarvish` |
| Orlazam-az-dihr | `ramsteel_dwarvish` | Hehodovar | `pyrite_dwarvish` |
| Haraz Orldhûm | `platinum_dwarvish` | Verkal Gulan | `gold_dwarvish` |
| Dûr-Vazhatun | `sapphire_dwarvish` | Gor Ozumbrog | `topaz_dwarvish` |
| Orlghelovar | `cobalt_dwarvish` | Arg-Ôrdstun | `diamond_dwarvish` |
| Shazstundihr | `marble_dwarvish` | Ovdal Lodhum | `garnet_dwarvish` |

The clan units and traditions of these cultures return with the culture. 11 of the 13 Serpentreach and West Dwarovar
cultures (all but diamond and garnet), plus marble and titanium, have no land at the start.

## Removing ruined holds

The existing mechanic comes out completely. No replacement is part of this work.

**Behaviour afterwards:**

- A non-dwarf conquering a dwarf-held hold changes nothing about the hold, other than its level effects switching off
  because the holder is no longer a dwarf.
- Khugdihr no longer starts ruined.
- A hold's level effects, digs and the Delve Deeper decision need only a dwarven holder.

**What goes:**

| Area | Items |
|---|---|
| Decision | `aov_clear_ruins_decision` in `common/decisions/aov_hold_decisions.txt` |
| Events and loc | `events/aov_hold_ruin_events.txt`, `localization/english/aov_hold_ruin_l_english.yml`, the ruin lines in `aov_holds_l_english.yml` |
| on_actions | `aov_hold_on_title_gain` and `aov_hold_restoration_handover` in `aov_hold_on_actions.txt`; the ruin check in `aov_hold_dig_on_actions.txt` |
| Triggers and effects | `aov_hold_is_ruined`, `aov_hold_ruin_effect` and the restoration effects; `aov_hold_is_working` keeps only `aov_is_hold` until the plan decides whether to inline it |
| Delve picker | The ruin branches in `events/aov_hold_delve_events.txt` |
| Data | `ruined`, `RUINED_MODIFIER` and `RUINED_ART` in `tools/data/holds.py`; the `ruined_hold` entry in `tools/data/holding_art.py` |
| Generators | The ruin parts of `tools/build_holds.py` (level effect gate, setup, `aov_ruined_hold` and `aov_restoring_hold` modifiers, loc); rerun with `build_monuments.py` and `build_county_view_override.py` for the county view picture and `window_county_view.gui` |
| Tests | Delete `test_hold_ruin.py`; update `test_build_holds.py`, `test_build_monuments.py`, `test_hold_data.py`, `test_hold_dig.py` |
| Docs | `docs/systems/dwarven-holds.md`, `segbandal.md`, `great-projects.md`, this project's `CLAUDE.md` where they describe ruin |

Other uses of the word "ruin" in the monument, invention and elf text are unrelated and stay. The plan greps each file
above again before removing anything.

## Generators

| File | Generator | Change |
|---|---|---|
| `tools/data/dwarovar_tribes.py` | new data | Tribes, seats, areas, dynasties, arms, pool sizes, thresholds |
| `tools/build_dwarovar_tribes.py` | new generator | Governments, pool titles and their loc and arms, tribe characters, dynasties, tribe title history |
| `tools/build_serpentreach.py`, `build_segbandal.py`, `build_west_dwarovar.py` | changed | Read the data file: tribe counties take the tribe's culture, faith and holding; drop the rulers listed above; add `can_create` and drift settings |
| `tools/data/holds.py`, `build_holds.py` | changed | Ruin removed, `culture` per hold, revival data |
| Hand-written `aov_dwarovar_*` files | new | Decisions, interaction, duel events, wars, on_actions, sync and revival effects, cultures, faiths, loc |

Order: after `build_governments_override.py` (its tribal government is the source) and after `build_west_dwarovar.py`;
before `build_holds.py`. `docs/systems/updating.md` records it. A new `docs/systems/dwarovar-tribes.md` holds the system
notes, and `CLAUDE.md`'s systems table gets a row. `serpentreach.md`, `segbandal.md` and `west-dwarovar.md` get their
ruler notes corrected.

## Build order

1. **In-game test first.** One orc ruler on one pool title, on a throwaway branch. It answers:
   - Does the title name read the holder's dynasty, in the title window and on the map?
   - Does `set_coa = root.dynasty` apply the arms?
   - Do penalties disappear for vassals outside the ruler's de jure land?
   - Does land stay put under `de_jure_drift_disabled`?
   - Can a later file add `can_create` to an Anbennar title?

   The answers fix which naming route and title override get built, and are recorded in this spec.
2. Remove ruined holds. This stands on its own and lands first, so the later steps never build on it.
3. Placeholder cultures and faiths.
4. Governments, pool titles, sync effect, decisions and the raise-a-vassal interaction.
5. Tribes on the map: data file, generator changes, dwarven rulers removed and added.
6. Wars and the AI surface rule.
7. Duels.
8. Culture revival.
9. Docs, tiger baseline review and the full in-game list.

## First test results

Run in game over four rounds on a throwaway branch, since deleted.

| Question | Answer | What gets built |
|---|---|---|
| Does the title name read the holder's dynasty? | Yes. The duchy's window reads "Skewered Drake Warband"; the map reads "SKEWERED DRAKE" and never "The Orcs". A primary kingdom reads "The Skewered Drake Kingdom (Skewered Drake Warhost)" | The `GetTitleByKey` name; the `set_title_name` table is not needed |
| Does the dynasty's arms apply? | Yes, with both `set_coa = holder.dynasty` and `set_coa = holder.house` | `set_coa = holder.dynasty` |
| Do de jure penalties go? | Yes. No rightful-liege line in a vassal's opinion, and vassals pay full tax and levies | `government_ignores_rightful_liege_penalties` as designed |
| Does land stay put? | No drift seen. A drift-off title and a control with no drift setting both showed no progress after a year, with rulers holding the duchies and no drift line in the title window. Why the control does not drift is unknown | `de_jure_drift_disabled` stays on every title; the observer run (in-game item 3) checks again |
| Can a later file add `can_create` to an Anbennar title? | Only by redefining the title, in its real parent, with its own fields repeated | The generated override under "Keeping dwarven titles dwarven" |

How redefining a title behaves:

- At the top level, `k_hehodovar` left `e_middle_dwarovar`, though its provinces kept their titles.
- Nested in `e_middle_dwarovar`, it stayed, but the empire lost its colour and cultural name. Redefining a title clears its
  own fields; children left out of the redefinition keep theirs.
- Nested with the fields repeated, `k_hehodovar` has its colour and duchies and refuses creation. The user did not report
  the empire's name and colour in that round, so that check joins the in-game list.

Other findings:

- `error.log` shows 12 lines per new government: "Could not find the preregistered modifier type '<government>_opinion'",
  and the same for `_vassal_opinion`, `_tributary_opinion`, `_opinion_same_faith` and the tax, levy, herd and prestige
  contribution modifiers. Entries in `common/modifier_definition_formats` did not silence them, so the build does not ship
  that file. RiE has no such entries for its own government either. The government worked anyway, but no test has shown
  these modifiers are harmless beyond that.
- A name list's names and `name_list_<key>` need loc, or the engine logs an error for each.
- `race_orc` reads "Orc (Sin): -10" under `ancestor_worship`. The placeholder faiths must not have this.
- A city barony generates a mayor vassal, so tribe counties leave their other baronies empty, as designed.

## Testing

**Tool tests:**

- Every county is assigned exactly once; each tribe is one connected piece; totals match the tables.
- No tribe county is one of Anbennar's `EXISTING`.
- Every hold has a `culture`.
- Nothing in `common`, `events`, `gui` or `tools` still names `aov_hold_ruined`, `aov_hold_is_ruined` or
  `aov_clear_ruins_decision`.
- Goblins fail the duel's `is_shown` check, read from the interaction's script.
- Every pool title has its required fields and no de jure children.
- Every generated dwarven title has `can_create` and drift settings.
- `FreshnessTests` for each generated file.

**Validation:** `python -I tools/validate.py` shows no new reports, or each is explained.

**In-game list, beyond the first test:**

1. The game starts cleanly with all pool titles and tribes.
2. Tribes, characters, cultures and faiths show as in the tables; six holds are dwarven.
3. The de jure kingdom map mode is unchanged at the start and after a long observer run. `e_middle_dwarovar` still reads
   "Segbandal" to a dwarven ruler, with colour `36 96 143`.
4. What the game does with counties left unheld, such as Khugdihr's. This was not checked during design.
5. Cultures with no followers survive and are not stuck far behind on innovations when revived. If they are, the revival
   decision catches them up.
6. Duels: all three outcomes. On a win, the realm does not partition and name and arms change. On a refusal, prestige
   falls to the lowest level from any starting level, and the modifier shows -50 in other rulers' opinion breakdowns and
   stays after years pass. A goblin vassal is never offered the challenge.
7. Forming duchy, kingdom and empire titles; the raise-a-vassal interaction; a duke granting a county to a courtier
   creates a count vassal; pool titles are reused once free; a pool running out shows the tooltip.
   Holds behave as before apart from ruin: conquest does not change them, and digging still works under a dwarf.
8. Tribal law and military windows work with the new governments, and tribes cannot feudalise.
9. Revival appears and hides as specified, with Arg-Ôrdstun conquering Orlghelovar as the negative case.
10. AI behaviour over several decades: tribes fight each other, do not start surface conquests, and do not overrun the
    Segbandal's 26 counties in the first decade.

## Out of scope

- Orc and goblin portraits, armies, traditions, men-at-arms and clothing.
- Culture splits into EU4's clans (moltenbrand, trolltamer, forest goblins and others).
- Ogres in the Vale, cave trolls and hobgoblins.
- Goblin slavery as a mechanic.
- The Greentide itself as an event.
- Warband ruler titles ("Warlord", "Chief") in place of Duke and King.

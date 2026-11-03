# Serpentreach dwarf cultures: draft for review

Status: **draft, reviewed 2026-11-03** (all questions answered), nothing implemented.

## What EU4 Anbennar has

EU4 gives each of the six Serpentreach holds its own culture in the `dwarven` group, with the hold as its primary tag.
At 1444 only Arg-Ôrdstun and Ovdal Lodhum are still dwarven. The other holds and the Argrod are held by cave,
straggler and skinburner goblins, black, blooded and moltenbrand orcs and darkscale kobolds. EU4 only has the group's
shared male and female names. A few cultures have their own dynasty names.

| Hold (tag) | EU4 culture | CK3 today | Lore from the nation and idea texts |
|---|---|---|---|
| Orlghelovar (I12) | cobalt_dwarf | none | The Glasslords: blue Orlghelovar glass, taught glassmaking to humans; Guntîrhug university, natural sciences; the Glasshammer Fair in Amldihr; mirrors fill the hold with daylight; glassblowers' lungs make trumpeters, so armies march behind bands; fell through greed and decadence |
| Shazstundihr (I11) | marble_dwarf (Whitebeard, Brightbeard) | **`marble_dwarvish` exists** (Bahar diaspora; overhaul tradition *Masons of the Deep*, unit Brightbeard Hammers) | The Marble Gate; sculptors and builders of Bahar's God-King cities; open to Bulwari humans; the Mausoleum of Argor Whitebeard; contracts "written in marble"; the Whitestone Council of 50; Mhoki Brightbeard killed the precursor emperor |
| Arg-Ôrdstun (H76) | diamond_dwarf (Stormheart) | none | Nominal capital of the Serpentreach; kimberlite clast shafts; the Gromdhal lapidary guild; lightflare armour, diamond-studded to blind cave ambushers; the Aegis of the Serpentreach diamond; hegemony over the holds; the War of the Bloody Gem against the High King; Queen Halkraz the Defiant |
| Verkal Skomdihr (I13) | flint_dwarf | none | The Warding Gate against the fey of the Deepwoods; forest rangers; the only dwarven carpenters; Kekig's labyrinth; superstitious (stone circles on doorsteps); first handheld flintlocks; herbal remedies from Deepwoods and cave plants |
| Ovdal Lodhum (H77) | garnet_dwarf (Slatecutter) | none | The Hold Where Love Lives: the Tunnel of Love, honeymoon hold of the old empire; wine; glowing garnet love-stones; midwives sought by royal families; just and honourable rulers; Gerin Orcrend, a human orc-slayer elected king |
| Gor Bûrad (I16) | basalt_dwarf | none | Firetop Mountain, black basalt halls round a lava lake; the Fireglass Forge (obsidian); berserker rage, "hearts of fire"; Borbordûz, the fire duel over the lava lake; every dwarf keeps their own weapons; held out against the orcs longer than any northern hold |

## Proposal

1. **Five new cultures**, in a hand-written `common/culture/cultures/aov_serpentreach_cultures.txt`: `cobalt_dwarvish`,
   `diamond_dwarvish`, `flint_dwarvish`, `garnet_dwarvish`, `basalt_dwarvish`. They use Anbennar's key style.
   Shazstundihr keeps the existing `marble_dwarvish`. Its Anbennar definition stays unchanged, and it gets a homeland
   tradition at game start (below).
2. **Language (decided 2026-11-03):** a new `language_serpentreach_dwarven` pillar, spoken by the five new cultures.
   It goes in a hand-written `common/culture/pillars/aov_serpentreach_language.txt`, defined like Anbennar's
   dwarven languages (`language_is_shown_trigger`, `ai_will_do`), with a bronze colour of its own and name loc.
   `marble_dwarvish` keeps `language_segbandalic_dwarven`, because it is Anbennar's culture and its people live in
   the Bahar diaspora.
3. **Shared fields**, the same as the overhaul's dwarf cultures: `heritage_dwarven`, `martial_custom_male_only`,
   `head_determination_domain`, `name_list_dwarven`, `ethnicities = { 100 = dwarf }`, and the overhaul's RiE gfx keys
   (`aov_dwarven_building_gfx`, `aov_dwarf_clothing_gfx`, `aov_dwarven_unit_gfx` before Anbennar's). No `parents`,
   because these are founding cultures older than the CK3 start, not divergences.
4. **Placement (decided 2026-11-03):** every county and character of a hold's kingdom takes that hold's culture. `build_serpentreach.py`
   replaces its single `CULTURE = "stone_dwarvish"` with a kingdom → culture map in `tools/data/serpentreach.py`.
   Province and character history are generated, so no game-start effect is needed. This differs from the elven
   cultures, which had to override Anbennar history.
5. **Traditions:** each culture gets `tradition_mountain_homes` (every Anbennar dwarf clan except stone has it) and two
   or three vanilla or Anbennar traditions taken from its EU4 ideas. The racial traditions system adds one new
   tradition of its own at game start, most with a clan unit (`tools/data/racial_traditions.py`, the same as the 11
   existing clans). Each culture gets a different ethos, so the six differ in play.
6. **Colours:** the cultures take the hold's EU4 country colour, the same colour its kingdom uses on the map.
   Arg-Ôrdstun's grey would clash with `stone_dwarvish` and `silver_dwarvish` (170-177 grey), so diamond gets a pale
   ice blue instead.
7. **Dynasty names (decided 2026-11-03):** six of the generated per-duchy dynasties (today `az-<duchy>`) take EU4
   names, with no `az` prefix. The holds' ruling lines come from EU4's 1444 rulers, and the other names come from the
   culture dynasty lists:

   | Duchy | Dynasty | EU4 source |
   |---|---|---|
   | `d_arg_ordstun` (the emperor's line) | Whiteforged | H76's ruler Ardeginn XXII Whiteforged, the Second Diamond Queen |
   | `d_kings_caverns` | Stormheart | diamond_dwarf dynasty names |
   | `d_ovdal_lodhum` | Garnetpick | H77's Dwalra Garnetpick (the native line; Gerin Orcrend is a human who marries in later) |
   | `d_still_caverns` | Slatecutter | garnet_dwarf dynasty names |
   | `d_shazstundihr` | Whitebeard | marble_dwarf names; Argor Whitebeard, the hold's founder |
   | `d_south_altar` | Brightbeard | marble_dwarf names; Mhoki Brightbeard |

   A duchy → (name, prefix) map in `tools/data/serpentreach.py` drives this. The dynasty keys
   (`aov_dynasty_<duchy>`) stay the same; only the `dynn_` loc and the prefix change. EU4 gives cobalt, flint and
   basalt no dynasty names of their own, so their duchies keep `az-<duchy>`.

### The cultures

| Culture | Colour | Ethos | Base traditions | DLC tradition |
|---|---|---|---|---|
| Cobalt Dwarvish | 0 71 171 (EU4) | bureaucratic | mountain_homes, philosopher_culture (Guntîrhug), music_theory (Glass and Trumpets) | artisans (Lords of Glass; `royal_court`, like stone) |
| Diamond Dwarvish | 185 225 240 (ice) | courtly | mountain_homes, ancient_miners (clast shafts), hereditary_hierarchy (Diamond Kings, Halkraz) | artisans (Gromdhal guild) |
| Flint Dwarvish | 55 144 90 (EU4, moss) | spiritual | mountain_homes, forest_fighters (forest rangers), medicinal_plants (herbal remedies) | none |
| Garnet Dwarvish | 247 179 215 (EU4) | communal | mountain_homes, wedding_ceremonies (Tunnel of Love), distinguished_winemakers (Love and Wine) | none |
| Basalt Dwarvish | 240 72 72 (EU4) | bellicose | mountain_homes, stand_and_fight (Bûrad Pride), metal_craftsmanship (Armory of Gor Bûrad) | none |

Two picks were dropped after the review, while checking the plan (2026-11-03):
- Flint loses `tradition_test_maa_anb_dwarven_handgunners`. The racial armies system removes it from every culture
  at game start and disables `dwarven_handgunners` (`racial-armies.md`), so it would unlock nothing. The first
  flintlocks go into the Flint Forest Rangers' flavour text instead.
- Basalt loses `tradition_fp1_trials_by_combat`. It is shown only to North Germanic heritage with Northern Lords, and
  no vanilla culture starts with it. The fire duel goes into the *Hearts of Fire* text instead.
| Marble Dwarvish | unchanged | egalitarian | unchanged: mountain_homes, xenophilic, hard_working, diasporic | none |

Ethos spread: Anbennar's dwarves are mostly stoic, communal and bureaucratic. Courtly (Arg-Ôrdstun's pride and
splendour), spiritual (flint's superstition and wards) and bellicose (Gor Bûrad's anger) are new among dwarves.

### Their own traditions and clan units

The numbers are placeholders, set at the level of the existing clan traditions. Units follow the racial armies
pricing (`racial-traditions.md`). The art is RiE's dwarf sets that no clan uses yet.

| Culture | Tradition | Effects (draft) | Unit | Type | RiE art |
|---|---|---|---|---|---|
| Cobalt | **The Glasslords** (Lords of Glass, Reflecting Daylight, Guntîrhug) | domain tax +10%, development growth +10%, Learning +1 | Orlghelovar Lens Crossbows (crossbows aimed through cobalt-glass sights) | archers | `ironfist_crossbowmen` |
| Diamond | **The Aegis of the Serpentreach** (Aegis, Diamond Hegemony, Rebellious Legacy) | monthly prestige +10%, Diplomacy +1, vassal opinion +5 | Lightflare Guard (diamond-studded armour) | heavy infantry, high toughness | `broadbeam_heavy_infantry` |
| Flint | **The Warding Gate** (Warding Gate, Flint Superstitions, Kekig's Labyrinth) | defender advantage +4, enemy hostile schemes −10% success, hostile county attrition +10% | Flint Forest Rangers | skirmishers, forest advantage | `stiffbeard_skirmishers` |
| Garnet | **The Hold Where Love Lives** (Full of Love, Dwarven Midwives, Honourable Leadership) | fertility +15%, spouse opinion +15, county opinion +5 | Orcrend Guard (Gerin Orcrend's anti-orc doctrine) | pikemen | `broadbeam_pikemen` |
| Basalt | **Hearts of Fire** (Hearts of Fire, the Great Anger, Scorched Halls) | prowess +2, heavy infantry damage +15%, hostile county attrition +10% | Basalt Berserkers | heavy infantry, high damage and low toughness | `firebeard_heavy_infantry` |
| Marble | **The Whitestone Council** (Whitestone Council, Mausoleum of Argor Whitebeard), a second overhaul tradition beside *Masons of the Deep* | powerful vassal opinion +10, councillor opinion +10, piety +10% | none (keeps Brightbeard Hammers) | none | none |

**Marble homeland flavour (decided 2026-11-03):** Shazstundihr's council of 50 and its ancestral mausoleum become a
second overhaul tradition for `marble_dwarvish`. It is added at game start by the racial traditions grant, the same
way as *Masons of the Deep*, so Anbennar's culture definition is never overridden. Every marble dwarf gets it,
including the Bahar diaspora, because EU4 has one marble culture and the council is that culture's institution. All
three modifier keys are used in vanilla (`powerful_vassal_opinion`, `councillor_opinion`, `monthly_piety_gain_mult`).
The rejected alternative was a separate homeland culture that diverges from marble. It would split one EU4 culture
in two and leave the diaspora as a second marble culture.

**All five new cultures get a unit (decided 2026-11-03).** Lens Crossbows and Orcrend Guard are new names that EU4
does not have, built on the Guntîrhug/glass and Gerin Orcrend ideas. Their names and art can still change in review.

## Touch points (for the implementation plan)

- New: `common/culture/pillars/aov_serpentreach_language.txt` (the language),
  `common/culture/cultures/aov_serpentreach_cultures.txt` and `localization/english/aov_serpentreach_cultures_l_english.yml`
  (name, prefix, collective noun, a history line from the EU4 nation text, the language name), plus a test like `test_elven_cultures.py`.
- `tools/data/serpentreach.py` + `tools/build_serpentreach.py`: per-kingdom culture (counties and characters) and the
  six dynasty renames.
- `tools/data/racial_traditions.py`: six traditions (five new cultures plus marble's Whitestone Council) and
  game-start grants (marble's entry becomes two traditions). Then rerun `build_racial_traditions.py` and
  `build_racial_levies.py`.
- The five clan units are hand-written, like the 11 existing ones: `aov_dwarven_maa_types.txt`,
  `aov_racial_maa_values.txt`, `aov_racial_armies_l_english.yml`, and RiE art copied once as `aov_rie_<art>`.
- gfx: `build_holding_models.py` and `build_portraits.py` only rewrite Anbennar's culture files, so the new culture
  file copies `stone_dwarvish`'s three gfx lines from the overhaul's `anb_dwarf.txt`, and a test keeps them equal.
- Docs: a "Serpentreach cultures" section in `serpentreach.md` and rows in `racial-traditions.md`.
- The modifier keys used in the effects (scheme success, spouse opinion, vassal opinion) must be checked against
  vanilla usage first. There is no `script_docs` dump.

## Open questions

1. ~~Language~~: decided. The five new cultures get a new Serpentreach Dwarven language (proposal item 2).
2. ~~Placement scope~~: decided. Each hold's culture fills its whole kingdom (proposal item 4).
3. ~~Marble~~: decided. Marble gets the Whitestone Council as a second overhaul tradition, and its definition stays as
   Anbennar ships it.
4. ~~Units~~: decided. All five new cultures get a clan unit.
5. ~~Dynasty renames~~: decided (proposal item 7).

All review questions are answered. Next step: turn this draft into a spec and an implementation plan.

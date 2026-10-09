# Artificer factions — design

Date: 2026-10-08. Status: approved in chat (titles, elections, influence, Factions tab), awaiting written-spec review.
Builds on: `docs/superpowers/specs/2026-10-08-artificery-inventions-design.md` (research, sponsors, slots) and the
EU4-style Inventions tab / event-style research popup (`gui/aov_window_artificery*.gui`).

## Goal

Make the three artificer factions real: each is a landless duchy title held for life by an elected gnome, shown in
the Artificery window's Factions tab with its coat of arms, its leader's portrait and an influence bar for the
player's realm. Influence rises and falls with the player's patronage, gives bonuses when high and penalties when
low, and changes what research costs.

## Decisions taken

| Question | Decision |
|---|---|
| How many titles | Three global titles: `d_brillites`, `d_mechanists`, `d_technomancers` (duchy tier, `landless = yes`) |
| Tenure | Held until death; a new holder is elected when the holder dies |
| Holder status | Stays a vassal of their old liege; the title cannot be revoked |
| Electors | Every ruler passing `can_use_artificery_trigger`; vote weight grows with that faction's influence in the voter's realm |
| Candidates | Exactly three, chosen when the leader dies: the best unlanded adult gnomes at artificer courts, topped up from gnomes anywhere; every artificer nation votes for one; with no voters the best candidate wins |
| Influence | Per ruler, per faction, 0–100, five levels with themed modifiers |
| Influence sources | Sponsoring research, Make Amends and the faction leader's opinion of the ruler (quarterly); **active inventions do not change influence** |
| Research cost | Base 50 gold, scaled by the sponsored faction's level (Hostile ×2 … Exalted ×½) |
| Hostile factions | Can still be sponsored (at double cost); they no longer refuse |
| Make Amends | Factions tab button: 100 gold for +10 influence, only below 40, capped at 40 |

## Player-facing behaviour

### The titles

- Names: **The Brillite Circle** (`d_brillites`), **The Mechanist Guild** (`d_mechanists`), **The Technomancer
  Conclave** (`d_technomancers`); holder titles *Spark-Primarch*, *Guildmaster Mechanist*, *Arch-Technomancer*
  (title-holder flavorization).
- `definite_form = yes`, `ruler_uses_title_name = no`, `no_automatic_claims = yes`, `can_use_nomadic_naming = no`,
  `capital = c_nimscodd` (Nimscodd, heart of the Gnomish Hierarchy).
- Not revocable: an `aov_` override of Anbennar's `title_revocation_standard_can_pick_title_trigger` adds
  `aov_is_artificer_faction_title = no` (same pattern as the head-of-faith exclusion already in that trigger).
  With no automatic claims, the titles cannot be usurped or targeted by claim wars.
- Coats of arms (Anbennar emblems, `common/coat_of_arms/coat_of_arms/aov_artificer_factions.txt`):
  - Brillites: purple field, gold `ce_anb_cog` with a white `ce_anb_crystal_magic` spark at its hub.
  - Mechanists: steel-grey and black `pattern_checkers_01`, two interlocking bronze `ce_anb_cog`s.
  - Technomancers: deep blue field, `ce_anb_cog_02` in blue/magenta/teal (a cog with a glowing core).

### Elections

An election is held when a holder dies, and once at game start for each vacant title.

- **Vacancy:** when the holder dies the title is taken away from the inheritance (see Architecture, *Title
  succession*) and stays vacant for the 30-day election.
- **Three candidates** are chosen the moment the leader dies, and they are the only names on the ballot.
  - Pool: `has_trait = race_gnome`, adult, not imprisoned, `is_ruler = no`, not holding another faction title,
    courtier of a ruler passing `can_use_artificery_trigger`. The three highest scores are chosen.
  - If that pool has fewer than three, the rest are filled with the highest-scoring adult gnomes anywhere in the
    world (unlanded first, then any). Fewer than three only if fewer gnomes exist.
  - Score = Learning × 2 + the faction's skill (Brillites: Diplomacy; Mechanists: Stewardship;
    Technomancers: Martial).
- **Every artificer nation votes.** An artificer nation is a ruler passing `can_use_artificery_trigger`; each casts
  one vote for one of the three candidates. Vote weight by their influence level with that faction: Hostile 1,
  Displeased 2, Neutral 3, Favored 4, Exalted 5.
  - AI nations vote for their own courtier if one is a candidate, else for the highest score.
  - **Every vote is cast through an event panel** (`aov_artificer_factions.1`, a `character_event`), sent to every
    voting nation when the election opens. AI nations receive it too and pick by the AI rule via `ai_chance`.
    - Portraits: the three candidates as `lower_left_portrait`, `lower_center_portrait`, `lower_right_portrait`;
      the late leader as `right_portrait` (shown greyed, as the dead are); the voter as `left_portrait`.
    - Description: the faction, the late leader, and one line per candidate (name, liege, score).
    - One option per candidate, "Vote for [candidate]", each with `highlight_portrait` on its candidate so hovering
      the option lights up that portrait; the option tooltip shows the weight of this nation's vote.
    - Theme: a new event theme `aov_artificery` (`type_inspiration` icon, `bp2_university` background), shared
      with the research popup's look.
    - A player who has not answered by the count has their vote cast by the AI rule.
- **Result:** after 30 days the weighted votes are counted (ties: highest score). The winner gets the title and
  stays with their liege as a landless vassal. Every voter gets a short result notification.
- **No artificer nations:** the three candidates are still chosen; the highest score wins at once, no event.
- **No gnomes at all:** the title stays vacant; a yearly check retries.

### Influence

Stored on each ruler as three variables; only meaningful while they pass `can_use_artificery_trigger` (dormant
otherwise, like inventions: modifiers removed, values kept).

- Starts at **40** for each faction the first time a ruler is eligible.
- **Sponsoring** a faction's research: +20 to that faction, −10 to each of the other two.
- **While that faction's research runs:** +1 per quarter to it.
- **Favour fades:** above 40, −1 per quarter.
- **Grudges stay:** below 40 there is no natural recovery (other than the leader's opinion, below).
- **The leader's opinion of the ruler**, each quarter (vacant title: no change):

  | Leader's opinion | Influence per quarter |
  |---|---|
  | +50 or more | +2 |
  | +20 to +49 | +1 |
  | −19 to +19 | 0 |
  | −20 to −49 | −1 |
  | −50 or less | −2 |

  Applies at any influence level, so a friendly leader can heal a grudge and a hostile one erodes favour. It
  adds to the other quarterly changes (e.g. above 40 with a +20 leader, fade and opinion cancel out).
- **Make Amends** (Factions tab, per faction): 100 gold, +10, only while below 40, never above 40.
- Clamped to 0–100.
- **Heirs** inherit the predecessor's influence when they have none of their own.

| Level | Influence | Research cost | Research time | Modifier |
|---|---|---|---|---|
| Hostile | 0–14 | 100 | +25% | strong penalty |
| Displeased | 15–29 | 75 | +25% | mild penalty |
| Neutral | 30–59 | 50 | normal | none |
| Favored | 60–84 | 38 | normal | bonus |
| Exalted | 85–100 | 25 | −25% | strong bonus |

The cost and time are those of the faction being sponsored, read when research starts. A refund (nothing left to
discover) returns what was actually paid.

Themed character modifiers (values proposed; keys verified with tiger at implementation):

| | Hostile | Displeased | Favored | Exalted |
|---|---|---|---|---|
| Brillites (inspiration) | learning −1, prestige gain −15%, stress gain +10% | prestige gain −5% | learning +1, lifestyle XP +5%, prestige gain +5% | learning +2, lifestyle XP +10%, prestige gain +10% |
| Mechanists (industry) | domain tax −10%, build time +15% | domain tax −5% | domain tax +5%, build time −5% | domain tax +10%, build time −15%, capital development growth +0.1 |
| Technomancers (arcane war) | advantage −5, martial −1 | advantage −2 | martial +1, knight effectiveness +10% | martial +2, advantage +3, knight effectiveness +15% |

### Factions tab

Replaces the placeholder. Three stacked cards, one per faction, in the order Brillites, Mechanists, Technomancers:

- Left: the title's coat of arms; beside it the holder's portrait (head) with name and holder title; "Vacant —
  election under way" / "Vacant" when there is no holder.
- Right of that: the faction name and a one-line description of its school.
- Below: the **influence bar**, styled like the trait level-track bar (`gui/shared/progressbars.gui` textures and
  `widget_level_marker`), filled to the ruler's influence, with markers at 15, 30, 60 and 85. The current level's
  marker glows; each marker's tooltip lists that level's modifier, research cost and time. The bar's tooltip shows
  the exact value and what changes it, including the leader's opinion of the ruler and the resulting change per
  quarter.
- Under the bar: current level name, current research cost with this faction, and the **Make Amends** button
  (disabled with a tooltip when at or above 40, or short of gold).

### Research popup

- The three placeholder leaders become the title holders (`datacontext` = the holder); a vacant title shows an empty
  plate reading "Vacant".
- Each sponsor option shows that faction's current cost, and its tooltip shows the influence change (+20 / −10).

### AI

- Sponsors as today; prefers factions at Displeased or worse when it can afford them (to avoid penalties).
- Uses Make Amends when a faction is Hostile and it has more than 300 gold.
- Votes as described above.

## Architecture

### New files

| File | Content |
|---|---|
| `common/landed_titles/aov_artificer_faction_titles.txt` | the three titles |
| `common/coat_of_arms/coat_of_arms/aov_artificer_factions.txt` | their coats of arms |
| `common/flavorization/aov_artificer_faction_flavorization.txt` | holder titles |
| `common/modifiers/aov_artificer_faction_modifiers.txt` | 12 level modifiers (`aov_<faction>_<level>`) |
| `common/script_values/aov_artificer_faction_values.txt` | influence, level index, cost, duration, election score per faction |
| `common/scripted_triggers/aov_artificer_faction_triggers.txt` | `aov_is_artificer_faction_title`, candidate/elector triggers, level triggers |
| `common/scripted_triggers/zz_aov_interaction_triggers.txt` | single-object override of `title_revocation_standard_can_pick_title_trigger` (copied from Anbennar, one added line, marked `# Anbennar Overhaul`) |
| `common/scripted_effects/aov_artificer_faction_effects.txt` | influence change/clamp, level modifier refresh, election start/vote/resolve, inheritance |
| `common/scripted_guis/aov_artificer_faction_sgui.txt` | Make Amends per faction, holder/vacancy visibility |
| `common/on_action/aov_artificer_faction_on_actions.txt` | game start, quarterly (decay, refresh), on_death (holder and election anchor), yearly vacancy retry |
| `events/aov_artificer_faction_events.txt` | vote event panel (every nation), result notification |
| `common/event_themes/aov_artificery_event_themes.txt` | `aov_artificery` theme |
| `localization/english/aov_artificer_factions_l_english.yml` | everything above |

### Changed files

- `common/scripted_effects/aov_artificery_research_effects.txt`: `aov_artificery_start_research_common` pays the
  faction's scaled cost (stored in `aov_research_paid`), sets the scaled duration and applies the +20/−10 influence
  change; the refund pays back `aov_research_paid`.
- `common/scripted_triggers/aov_artificery_research_triggers.txt`: the gold check uses the sponsored faction's cost
  (one trigger per faction, used by that faction's sGUIs).
- `common/on_action/aov_inventions_on_actions.txt` / `aov_artificery_inherit`: inherit influence.
- `gui/aov_window_artificery.gui`: Factions tab body.
- `gui/aov_window_artificery_research.gui`: leaders bound to the title holders; per-faction cost text.
- `localization/english/aov_artificery_l_english.yml`: cost texts become per faction.

### State

- Ruler variables: `aov_influence_brillites`, `aov_influence_mechanists`, `aov_influence_technomancers` (0–100),
  `aov_research_paid`.
- Global variables per faction during an election: `aov_election_<faction>` (flag: open), a candidate list
  `aov_candidates_<faction>`, and per-candidate vote totals stored as variables on the candidates
  (`aov_votes_<faction>`), cleared after the count.
- The level modifier present on the ruler is derived (`aov_<faction>_<level>`), refreshed whenever influence changes
  and each quarter.

### Title succession

The holder's heir must not inherit. Primary approach: in `on_death`, when the dying character holds a faction
title, open the election and remove the title from them (`destroy_title` on the landless title); the winner later
receives it with `create_title_and_vassal_change` + `get_title`. Fallback if a destroyed static title cannot be
re-granted: let the title pass to the heir as an interim holder (marked `aov_interim_holder`, shown as "Interim" in the
Factions tab) while the same 30-day vote runs, then transfer it to the winner. Both keep every nation's vote. Which one works is the first implementation task.

### Election timing

`trigger_event` with `days = 30` on the highest-weight elector; the quarterly pulse also resolves any election open
for more than 30 days, in case that elector died.

## Out of scope

- Faction leaders acting on their own (schemes, demands, events with the leader).
- Influence from inventions (explicitly excluded).
- Changing the Inventions tab or the research flow beyond cost, time and leader portraits.

## Verification

- Tool tests (`python -I -m unittest discover -s tools/tests -v`) for the static parts: three titles with the
  required flags, coats of arms present, revoke override contains Anbennar's trigger plus the exclusion, 12 modifiers,
  cost/duration values per level, loc keys for every referenced key.
- `python -I tools/validate.py` clean (modifier keys, loc, scripted GUI scopes).
- In game (manual): titles filled at game start; killing a holder (console `kill`) opens an election, the player's
  vote event appears when they own an academy, the winner gets the title and remains their liege's vassal; Revoke
  Title does not list the faction title; the Factions tab shows CoA, portrait, bar and markers; sponsoring changes
  influence and cost; Make Amends works and stops at 40; changing the leader's opinion (console `add_opinion`) moves influence by the
  table's amount each quarter; level modifiers appear and swap at thresholds.

## Risks

- **Re-granting a destroyed static title** (see Title succession): verified first; fallback defined.
- **The revoke override** copies an Anbennar trigger; after an Anbennar update it must be re-copied. Listed in the
  CLAUDE.md update steps.
- **Other ways to lose a title** (e.g. Anbennar or vanilla events that strip titles, diarch or admin interactions):
  checked with a grep for `revoke_title`-style effects during implementation; the faction titles are excluded where a
  scripted trigger allows it.
- **Landless duchy vassals** count toward the liege's vassal list; accepted (user decision).

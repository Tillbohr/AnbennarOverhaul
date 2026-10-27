# Gnomish artificery

The HUD override also carries the Magic tab (see magic.md).

## Generated files

| File | Generator | Why |
|---|---|---|
| `gui/hud.gui` | `python -I tools/build_hud_override.py` | The main tab bar is whole-file only. The script copies Anbennar's `gui/hud.gui` if it has one, else the game's, and inserts the Artificery and Magic tabs after `tab_situation` and a mage's mana before the resource bar's `gold` widget (all marked `# Anbennar Overhaul`; see magic.md). Never edit the output by hand. |
| `common/modifiers/aov_invention_modifiers.txt`, `common/scripted_triggers/aov_invention_triggers.txt`, `common/script_values/aov_invention_values.txt`, `common/scripted_effects/aov_invention_effects.txt`, `common/scripted_guis/aov_invention_sgui.txt`, `common/customizable_localization/aov_invention_custom_loc.txt`, `gui/aov_inventions_generated.gui`, `localization/english/aov_inventions_l_english.yml`, `gfx/interface/icons/aov_inventions/` | `python -I tools/build_inventions.py` | One block per invention, generated from `tools/data/inventions.py` (edit the data, then rerun). The icons in `gfx/interface/icons/aov_inventions/` were imported once from EU4 Anbennar and are committed (not rebuilt); a new invention needs its icon there first, or the build stops. |

## System

- **Gnomish artificery:** `tradition_gnomish_ingenuity` (gnomish heritage only; added to all gnomish cultures on
  game start; stripped from non-gnomes on culture creation/tradition add) → `artificer_academy_01` (regular
  castle/city building, university icon and modifiers, one per ruler's domain, all of a ruler's academies disabled
  if they hold 2+) → `artificer_handgunners` MaA (shown as Artificers; Anbennar's generic `artificers` and `armored_artificers` are disabled in `zz_aov_gnome_maa_overrides.txt`; handgunner stats, needs the tradition and an enabled academy in
  the recruiter's domain).
- **Artificery tab:** HUD main tab below Situations (`gui/hud.gui`, generated) shown when the player passes
  `can_use_artificery_trigger` (gnome race, Gnomish Ingenuity culture, exactly one academy) via scripted GUI
  `aov_artificery_available`. Opens `gui/aov_window_artificery.gui` (scripted widget, variable
  `aov_artificery_window`) with Factions/Inventions tabs (variable `aov_artificery_tab`, unset = Factions).
- **Artificery inventions:** 60 inventions in `tools/data/inventions.py` (EU4 Anbennar mapping in
  `docs/research/2026-10-08-eu4-artificer-inventions.md`). Research sponsored by Brillites (5 y, random),
  Mechanists (10 y, chosen field) or Technomancers (15 y, chosen invention); cost and time set by that faction's
  influence (below); tiers gated by culture
  era; 3/4/5 slots with a 1-year cooldown; state in ruler variables, inherited by the heir; dormant while
  ineligible. Logic in `aov_artificery_research_*` files and `common/on_action/aov_inventions_on_actions.txt`.
- **Inventions tab UI:** EU4-style. Tier I/II/III tabs (variable `aov_inventions_tier`, unset = I), each with
  Society/Economic/Military sections of invention boxes (generated types `aov_inventions_tier_<n>`), drawn with EU4
  Anbennar's inventions-menu buttons (`aov_invention_button_<category>.dds`, frames: locked/undiscovered, discovered,
  active; converted from DX10 by the generator). Clicking a box
  runs `aov_inv_<key>_toggle_sgui` (activate, or deactivate with the slot cooldown); hovering shows
  `aov_invention_<key>_tooltip` (name, field/tier, description, effects, status).
- **Research popup:** `gui/aov_window_artificery_research.gui`, drawn like a character event (`bp2_university`
  background, `type_inspiration` icon). The three faction title holders stand on the right ("Vacant" plate when
  empty); each option shows that faction's price. Steps use GUI variable `aov_research_stage` (unset →
  `mechanists` / `technomancers` → `tech_<field>` proposals).
- **Artificer factions:** global landless duchies `d_brillites`, `d_mechanists`, `d_technomancers`
  (`common/landed_titles/aov_artificer_faction_titles.txt`), held for life, not revocable (revoke-trigger override).
  When a holder dies (`common/on_action/aov_artificer_faction_on_actions.txt`) the title is destroyed and
  `aov_election_open` (`common/scripted_effects/aov_artificer_election_effects.txt`) picks three gnome candidates;
  every artificer nation votes, weighted by influence level (players via event `aov_artificer_factions.1`), and
  the count after 30 days grants the title to the winner, who stays their liege's vassal. A gnome holds at most
  one faction title; a faction title gained any other way (Grant Titles, inheritance) is destroyed and re-elected
  (`on_title_gain`, title variable `aov_elected_holder`). Vacant titles are filled at game start and yearly. **Influence** per ruler and faction (`aov_influence_<f>`, 0-100, start 40): sponsoring
  +20 / rivals -10, +1/quarter while their research runs, -1/quarter above 40, ±1-2/quarter from the leader's
  opinion, Make Amends (100 gold, +10, up to 40). Levels Hostile/Displeased/Neutral/Favored/Exalted give modifiers
  `aov_<f>_<level>` and set research cost (100/75/50/38/25) and time (+25%/+25%/-/-/-25%). Values in
  `common/script_values/aov_artificer_faction_values.txt`; Factions tab cards in `gui/aov_artificer_factions.gui`.

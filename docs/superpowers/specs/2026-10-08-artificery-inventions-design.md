# Artificery inventions — design

Date: 2026-10-08. Status: approved in chat (Sections 1 and 2), awaiting written-spec review.
Builds on: `docs/superpowers/specs/2026-10-08-artificery-tab-shell-design.md` (the Artificery tab and window).
Content source: `docs/research/2026-10-08-eu4-artificer-inventions.md` (60 inventions, EU4 → CK3 mapping).

## Goal

Fill the Inventions tab of the Artificery window with EU4 Anbennar's artificer inventions: research sponsored by
one of three artificer factions, a list of inventions filterable by category, and a limited number of active
slots. Eligible AI rulers use the same system. The Factions tab stays a placeholder (separate spec).

## Decisions taken

| Question | Decision |
|---|---|
| How inventions are gained | Research sponsored by Brillites (5 y, random), Mechanists (10 y, choose category), Technomancers (15 y, choose category then 1 of 3) |
| Research cost | 50 gold to start, for every sponsor; durations fixed |
| How discoveries take effect | Fixed slots: discovered inventions are activated into slots |
| Slot count | 3 in Early Medieval, 4 in High Medieval, 5 in Late Medieval (ruler's culture era) |
| Swapping | Free, but an emptied slot cannot be refilled for 1 year |
| Ownership | Stored on the ruler; inherited by the heir with everything else |
| Era gate | Tier 1 needs `culture_era_early_medieval`, tier 2 `culture_era_high_medieval`, tier 3 `culture_era_late_medieval` |
| Filters | Three toggles in the Inventions tab: Economic, Military, Society |
| Content | All 60 inventions in the research doc, including 3 new men-at-arms types |
| Icons | EU4 Anbennar's `Artf_<faction><category><tier>` privilege icons |

## Player-facing behaviour

### Eligibility

Everything below applies only to a character passing `can_use_artificery_trigger` (gnome, Gnomish Ingenuity
culture, exactly one academy; defined in the shell). An ineligible character holding artificery state keeps it
**dormant**: invention modifiers removed, research timer paused, no AI actions. When they become eligible again,
active inventions' modifiers are restored and the timer resumes.

### Availability of an invention

An invention is *available* to a ruler when all hold:
- the ruler's culture has reached the invention's tier era (`culture = { has_cultural_era_or_later = <era> }`);
- its faith lock, if any, is met (`faith.religion` matches the CK3 religion listed in the data table);
- its gnome lock, if any, is met (the 4 EU4 gnome-only inventions; covered by eligibility already, kept as data).

Unavailable inventions are hidden if faith/gnome-locked, and shown as **Locked** (tooltip names the era) if
only the era is missing.

### Inventions tab

Top to bottom:
1. **Slots bar:** `Slots <active> / <max>`, plus `<n> cooling down` when any slot is on cooldown.
2. **Research panel:**
   - Running project: sponsor name and icon, time left in years and months, and the target invention for
     Technomancer projects.
   - Otherwise a **Research** button. Disabled (with tooltip) when a project is running, the ruler has under
     50 gold, or no available invention is undiscovered.
3. **Filter row:** toggle buttons **Economic**, **Military**, **Society**, all on by default. A category whose
   toggle is off is hidden from the list. Filter state is UI-only (GUI variable system), not saved.
4. **Invention list,** grouped under Tier 1 / Tier 2 / Tier 3 headers. Each row: icon, name, status, and a
   tooltip with description and effects. Statuses:
   - **Active:** button *Deactivate*.
   - **Discovered:** button *Activate*, disabled when no slot is free.
   - **Undiscovered:** greyed out; shows which sponsors could still discover it.
   - **Locked:** greyed out, tooltip "Requires the <era> era".

### Research popup

Opened by the Research button; a separate window over the Artificery window, closed by a close button or
after confirming.

| Sponsor | Duration | Player choice | Discovered invention |
|---|---|---|---|
| Brillites | 5 years | none | uniformly random undiscovered available invention, any category, any unlocked tier |
| Mechanists | 10 years | category | uniformly random undiscovered available invention of that category |
| Technomancers | 15 years | category, then one of up to 3 offers | the chosen invention |

- A category button is disabled when that category has no undiscovered available invention.
- **Technomancer offers:** the first time a category is viewed in a research cycle, up to 3 random undiscovered
  available inventions of that category are rolled and stored. Reopening the popup or re-selecting the category
  shows the same offers. Offers are cleared when a project completes. If fewer than 3 remain, all are offered.
- **Confirm** removes 50 gold, stores the project and starts the timer. For Brillites and Mechanists the
  invention is drawn **at completion**, from what is available then.
- On completion: the invention becomes Discovered and event `aov_artificery.1` shows the sponsor and the
  invention, with an option to activate it immediately if a slot is free.
- If a drawn pool is empty at completion (e.g. faith changed), the 50 gold is refunded and the event says so.

### Slots

- Maximum: 3 / 4 / 5 by the ruler's culture era (early / high / late medieval). Tribal: 3.
- Free slots = maximum − active − slots on cooldown.
- Activating needs a free slot. Deactivating starts a 1-year cooldown on one slot.
- If active inventions exceed the maximum (era or culture change, heir with another culture), the most recently
  activated ones are deactivated until they fit; these do not start cooldowns.

### Succession

On a ruler's death all artificery state (discoveries, active inventions, cooldowns, research project, Technomancer
offers) is copied to `player_heir`, or `primary_heir` when there is no player heir. Active inventions are applied
to the heir if they are eligible, otherwise held dormant. The dead ruler's modifiers die with them.

### AI

For an eligible AI ruler, every quarter:
- **Research:** if idle, at least 50 gold, and something is discoverable, start a project. Sponsor weights
  Brillites 50, Mechanists 30, Technomancers 20 (re-rolled if that sponsor has no valid category). Category and
  Technomancer offer chosen at random.
- **Slots:** while a slot is free, activate the highest-tier discovered invention, preferring Military while at
  war and Economic otherwise; ties random.
- AI never deactivates inventions except through the over-maximum rule.

### Content

All 60 inventions and their CK3 effects as listed in `docs/research/2026-10-08-eu4-artificer-inventions.md`
(Economic 16, Military 26, Society 18; tiers per EU4). Category for the filter is EU4's category, kept even where
the effect looks like another category. Values in the doc are starting values, tuned during implementation; the
two keys marked *(verify)* there are resolved during implementation or replaced with verified keys.

New men-at-arms, each recruitable only while its invention is **active** (`can_recruit` checks it):

| Invention | MaA key | Base type | Stats |
|---|---|---|---|
| Prototype Tanks | `aov_prototype_tanks` | `heavy_cavalry` | vanilla `heavy_cavalry`-type baseline +25 % damage and toughness |
| War Golems | `aov_war_golems` | `heavy_infantry` | vanilla `heavy_infantry`-type baseline +25 % damage and toughness |
| Damestear Reactor Megacannon | `aov_damestear_megacannon` | `siege_weapon` | vanilla trebuchet-type siege value ×1.5 |

Deactivating the invention stops new recruitment; existing regiments stay (vanilla behaviour for lost
`can_recruit`).

### Icons

Each invention uses its EU4 privilege icon `Artf_<Br|Ma|Te><Ec|Mi|So><1-3>`. The four inventions without one in
EU4 (plane_of_water_teleporter, subterrenes, mirage_detector_3000, think_thought_transmitters) use the icon for
their category and tier with the faction of their EU4 influence modifier. The 27 icon files are copied from
EU4 Anbennar `gfx/interface/privileges/` into `gfx/interface/icons/aov_inventions/` by the generator.

## Architecture

### Data and generator

- `tools/data/inventions.py`: one table, the single source of truth. Per invention: `key`, `category`, `tier`,
  `faith` (CK3 religion key or None), `gnome_only`, `icon` (Artf code), `modifier` (CK3 modifier block as text),
  `maa` (MaA key or None), `name`, `desc`.
- `tools/build_inventions.py` writes these generated files (each with a "generated, do not edit" header):

| Output | Contents |
|---|---|
| `common/modifiers/aov_invention_modifiers.txt` | `aov_invention_<key>` character modifier per invention |
| `common/scripted_triggers/aov_invention_triggers.txt` | per invention: `_available`, `_discovered`, `_active`; per category/tier: "has undiscovered available" |
| `common/scripted_effects/aov_invention_effects.txt` | per invention: discover, activate, deactivate; random draw per category and overall; inherit-all; suspend-all / resume-all |
| `common/scripted_guis/aov_invention_sgui.txt` | per invention: activate and deactivate (with `is_shown` / `is_valid`) |
| `gui/aov_inventions_list.gui` | one row widget per invention, grouped by tier, visibility from scripted GUIs and filter variables |
| `localization/english/aov_inventions_l_english.yml` | names, descriptions, modifier name/desc keys |
| `gfx/interface/icons/aov_inventions/*.dds` | 27 icons copied from EU4 Anbennar |

- Unit tests (`tools/tests/test_build_inventions.py`): 60 entries, unique keys, valid category/tier, every
  invention has modifier + triggers + effects + sGUI + row + loc, era per tier correct, faith keys are in an
  allow-list of CK3 Anbennar religions, deterministic output.

### Hand-written files

| File | Contents |
|---|---|
| `common/on_action/aov_artificery_on_actions.txt` | `quarterly_playable_pulse`: research countdown, completion, slot-maximum enforcement, AI research and slot filling, dormant/awake switch. `on_death`: inherit-all to heir. `on_culture_era_changed`: slot-maximum enforcement for the culture's rulers. |
| `common/scripted_effects/aov_artificery_research_effects.txt` | start research (charge gold, store project), complete research, Technomancer offer rolling, slot cooldown, over-maximum enforcement |
| `common/scripted_triggers/aov_artificery_research_triggers.txt` | can start research, slot maximum / free slot values via script values |
| `common/script_values/aov_artificery_values.txt` | `aov_invention_slots_max`, `aov_invention_slots_free`, research quarters per sponsor |
| `common/scripted_guis/aov_artificery_research_sgui.txt` | sponsor, category, offer selection and confirm; open/close popup |
| `events/aov_artificery_events.txt` | `aov_artificery.1` discovery (and refund variant) |
| `gui/aov_window_artificery_research.gui` + scripted-widget registration | research popup |
| `gui/aov_window_artificery.gui` | Inventions tab body replaces the placeholder: slots bar, research panel, filters, instance of the generated list |
| `common/men_at_arms_types/aov_invention_maa_types.txt` | the three new MaA |
| `localization/english/aov_artificery_l_english.yml` | UI and event text for the hand-written parts |

### State (character variables on the ruler)

| Variable | Meaning |
|---|---|
| `aov_inv_<key>` | 1 = discovered, 2 = active |
| `aov_inv_<key>_order` | activation counter value, for "most recently activated first" |
| `aov_inv_activation_counter` | increments on each activation |
| `aov_research_sponsor` | `flag:brillites` / `flag:mechanists` / `flag:technomancers`; unset = idle |
| `aov_research_category` | `flag:economic` / `flag:military` / `flag:society` (Mechanists, Technomancers) |
| `aov_research_target` | `flag:<key>` (Technomancers) |
| `aov_research_quarters_left` | 20 / 40 / 60 at start, −1 per quarter while eligible |
| `aov_tech_offer_<category>_<1-3>` | rolled Technomancer offers, `flag:<key>` |
| `aov_slot_cd_<1-5>` | slot cooldowns, set with `years = 1` |
| `aov_artificery_dormant` | set while modifiers are suspended |

Popup selection state (chosen sponsor/category/offer before Confirm) lives in GUI variables, not script.

## Out of scope

The Factions tab and any faction influence or approval from sponsoring; research speed modifiers; per-invention
art beyond the EU4 icons; balancing passes beyond starting values; invention events beyond discovery.

## Verification

- Generator unit tests and deterministic-output check; `python -I tools/validate.py` clean.
- In game (console to shorten timers via setting `aov_research_quarters_left`):
  - Each sponsor: cost charged, timer length, discovery event, correct pool (Brillites any category, Mechanists
    chosen category, Technomancers chosen offer); offers stable across reopening; refund when pool is empty.
  - Era gating: tier 2/3 shown Locked before their era and discoverable after.
  - Filters hide and show categories; statuses and buttons correct.
  - Slots: maximum per era, activation blocked when full, 1-year cooldown after deactivation, over-maximum
    deactivation order.
  - Succession: heir inherits everything; dormant heir has no modifiers and no progress, wakes when eligible.
  - AI: an observed eligible AI starts research and fills slots.
  - Each new MaA recruitable only while its invention is active.

## Risks

- **~60 generated GUI rows** in one list: generated to avoid hand errors; performance is fine at this size.
- **Scripted GUI count** (~120 per-invention sGUIs): generated, named consistently, covered by tests.
- **Heir with a different culture era** loses slots; handled by the over-maximum rule.
- **EU4 content mismatch** (faction/icon inconsistencies in EU4 data): icon choice is fixed in the data table;
  faction influence is deferred to the Factions spec.
- **Character modifiers on a dormant ruler:** must be removed and restored in one place (suspend/resume-all)
  so effects never double-apply; tests check every invention is covered by both.

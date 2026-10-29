# Race relations

As in EU4 Anbennar, the monstrous peoples are hostile to everyone else, and everyone else to them. Liches, and
Vampires and Werewolves once their secret is exposed, count as monstrous too.

## Who is monstrous

`aov_is_monstrous_trigger` (`common/scripted_triggers/aov_race_relations_triggers.txt`) is true for:

- Anbennar's monstrous races (`is_monstrous_race`): centaur, gnoll, goblin, half-goblin, half-hobgoblin, harpy,
  hobgoblin, kobold, ogre, ogrillon, orc, troll, trollkin;
- Liches (`lich` trait), at once: the Lichdom advancement's `aov_adv_lich_ascend` updates the marker;
- Vampires (`vampire`) and Werewolves (`lycanthrope`) only once exposed (`aov_exposed_monster` character flag).

EU4 also counts lizardfolk, giantkind and degenerated elves and spares a few cultures (city goblins, Dovesworn gnolls,
Goldscale kobolds, ...); CK3 Anbennar has none of those races or cultures, so the race list is Anbennar's own.

## What hostility does

| EU4 Anbennar | Overhaul |
|---|---|
| `root_monstrous` opinion -100 between a monstrous and a non-monstrous nation | Marker traits `aov_monstrous` and `aov_civilized` (`common/traits/aov_race_relations_traits.txt`), opposites of each other with `opposite_opinion = -200` (doubled from EU4 so other opinion sources cannot outweigh it) |
| `both_monstrous` opinion +20 between monstrous nations | `aov_monstrous` has `same_opinion = 20` |
| `cb_monster_vs_civ` (neighbours) | `aov_monster_conquest_cb`: a monstrous ruler takes a neighbouring county of a non-monstrous ruler (prestige 50 + 5 per realm size, at most 100) |
| `cb_civ_vs_monster` (neighbours, half aggressive expansion) | `aov_purge_monsters_cb`: the other way round, half the cost, and piety on victory |
| (none) | No marriage, betrothal, concubinage or alliance across the line; alliances across it break |

Both casus belli (`common/casus_belli_types/aov_race_relations_wars.txt`) are built on the game's `county_conquest_cb`
and target a county next to the attacker's realm. A war is between rulers, so the ruler's own side counts, not the
county's people.

CK3 can only give race-wide opinion through traits the other character holds, so every character carries one of the
two markers. `aov_race_relations_update_effect` keeps the marker in step with `aov_is_monstrous_trigger`, gives a hidden
Vampire or Werewolf their secret, and breaks a ruler's alliances across the line. It runs:

- for every character at game start (`on_game_start_after_lobby`) and once a year (`yearly_global_pulse`), as
  `aov_race_relations_sweep_effect`, which touches only characters whose marker or secret is stale. Anbennar sets race
  traits in character templates after creation and a few events change races, so the sweep catches what the hooks below
  miss; a newly created character can carry the wrong marker for up to a year;
- for a newborn (`on_birth_child`) and a new title holder (`on_title_gain`);
- when a Mage becomes a Lich, and when a Vampire or Werewolf secret is exposed.

Marriage and alliance checks use `aov_is_monstrous_trigger` directly, never the marker, so they are right at once.

## Vampires and Werewolves

`common/secret_types/aov_race_relations_secrets.txt` defines `secret_aov_vampire` and `secret_aov_werewolf`. Every
unexposed Vampire or Werewolf gets one. It is shunned by everyone and not criminal, so it can be found, used for
blackmail and exposed like any other secret. On exposure the owner gets `aov_exposed_monster` for good and turns
monstrous. Nothing in Anbennar gives these traits yet; they come from the console or future content.

The `vampire` and `lycanthrope` traits themselves stay visible on the character sheet (Anbennar's traits); only the
hostility waits for exposure.

## Marriage and alliance gate

Anbennar routes every marriage, betrothal and concubine check through `anb_marriage_trigger` (its racial
compatibility rules). The overhaul copies it with one line added that calls `aov_race_marriage_allowed_trigger`; the
only two interactions that create alliances, `negotiate_alliance_interaction` and `perk_alliance_interaction`, are
copied with `aov_race_alliance_allowed_trigger` first in `is_valid_showing_failures_only`. Marriages already made
(history, or before a Lich rose or a Vampire was exposed) stand.

**Future race rules** (for example: only the same race may marry, so humans never end up in elvish cultures) go in
`aov_race_marriage_allowed_trigger` in `aov_race_relations_triggers.txt`. It receives `ACTOR` and `RECIPIENT`, wraps
its check in a `custom_description` so the marriage window says why, and needs no generator change.

## Generated files

| File | Generator | Why |
|---|---|---|
| `common/scripted_triggers/zz_aov_race_relations_overrides.txt` | `build_race_relations.py` | Anbennar's `anb_marriage_trigger` plus the marriage gate (scripted triggers override by key) |
| `common/character_interactions/zz_aov_race_relations_overrides.txt` | `build_race_relations.py` | the game's two alliance interactions (as shipped by Anbennar) plus the alliance gate (interactions override by key) |

Rerun `python -I tools/build_race_relations.py` after every Anbennar update and CK3 patch. It stops when a copied key is
gone, defined twice, or already overridden by another overhaul file, or when an interaction no longer has exactly one
`is_valid_showing_failures_only`. `tools/tests/test_build_race_relations.py` fails when the copies are stale.

The copies carry 37 inherited tiger reports (Anbennar's racial-compatibility tooltip warnings reached through the
copied trigger, and the game's `ai_potential` deprecation and one `OR` tooltip warning in the copied interactions),
plus 2 strict-scopes false positives on `secret_exposed_notification_effect`; see `validation-baseline.md`.

## In-game checks

Static checks pass (tiger, tests); none of this has run in game yet.

1. Hover an orc ruler from a human ruler's view: opinion shows -200 from the opposite marker, and +20 between two
   monstrous rulers (an orc and a goblin). Check that the -200 is applied once, not once per marker.
2. A human and an orc cannot marry or betroth; the marriage window shows "Monstrous and civilized peoples cannot
   marry". A human and an elf still can.
3. Negotiate Alliance between a human and an orc ruler is greyed out with the alliance reason.
4. A monstrous ruler sees Monstrous Conquest against a neighbouring human ruler; the human sees Purge the Monsters.
   AI rulers declare these wars over a few years.
5. `add_trait = vampire` on a courtier (console): within a year (or at once on a title gain) they hold the Vampire
   secret and stay Civilized. Expose it: they turn Monstrous, alliances across the line break, opinions flip.
6. A Mage who drinks the Lichdom potion turns Monstrous at once.
7. Check `database_conflicts.log`: the two generated files should override `anb_marriage_trigger`,
   `negotiate_alliance_interaction` and `perk_alliance_interaction` and nothing else.

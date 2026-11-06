# Dwarovar tribes

## Wars a tribal AI can still reach the surface with

`aov_ai_tribe_may_not_target_trigger` stops AI tribes starting `aov_monster_conquest_cb` and `aov_tribal_war_cb` on a
county outside the Serpentspine. These other wars are not touched; the in-game observer run decides whether any needs an
override:

| War | File | Who can use it | Reach |
|---|---|---|---|
| `county_conquest_cb` | Anbennar's `00_conquest.txt` | Anyone not landless | A neighbouring county, for a ruler whose faith or culture allows it |
| `tribal_subjugation_cb` | Anbennar's `00_subjugation.txt` | `government_is_tribal`, at prestige level | A neighbouring tribal ruler, which the surface also has |
| `vassalization_cb` | Anbennar's `00_vassalization.txt` | Anyone not landless | Any neighbour |
| `invasion_war` | Anbennar's `00_invasion_war.txt` | `government_is_tribal` once a lifetime | A kingdom, against the rules on `used_lifetime_invasion` |
| `ep3_pillaging_foray` and the other `07_ep3_wars.txt` wars | Anbennar's `07_ep3_wars.txt` | Mostly landless and administrative rulers | Unlikely for tribes |

Raiding stays allowed by design.

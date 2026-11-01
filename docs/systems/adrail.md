# Isle of Adráil

Anbennar ships province 524 as a test realm: county `c_test_1` with barony `b_testoria_castle`, de jure under
`d_test_1` → `k_test` → `e_test`, all held by the test character Emperor Testor (6000000,
`history/characters/000_test_characters.txt`; titles in `history/titles/000_k_test.txt`). None of these titles
has localization, so the map showed the raw key `e_test`. Province 524 is EU4 Anbennar's **Isle of Adráil** (same
province id and map colour), the Magisterium's island in the East Damesear area.

The overhaul turns it back into Adráil without editing Anbennar's landed titles:

| File | Change |
|---|---|
| `history/titles/aov_adrail.txt` | `c_test_1` de jure under `d_damesear` from 1000.1.1, held by Marion Silmuna (holder of Damesear) from 1021.10.4; `e_test` and `d_test_1` vacated the same day |
| `common/on_action/aov_adrail_on_actions.txt` | Emperor Testor dies (`death_vanished`) at game start, so he is not left as a landless pool character |
| `localization/english/aov_adrail_l_english.yml` | county "Adráil", barony "Isle of Adráil" (EU4's province name) |

With the county gone, `d_test_1`, `k_test` and `e_test` have no de jure land and no holder, so they do not show on
the map and cannot be created. The keys stay: removing them needs a full override of `anb_landed_titles.txt`, and
Anbennar uses `d_test_1` as a placeholder duchy in 48 geographical regions
(`map_data/geographical_regions/geographical_region.txt`) and as a temporary de jure parking duchy in
`anb_decision_major_events.0045` (moving Damesear's capital). Both keep working.

**To confirm in game:** the island shows as Adráil in Marion's domain at the 1022 bookmark, the accented name renders
in the map font, and no `e_test` realm or Emperor Testor remains.

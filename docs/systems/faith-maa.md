# Faith men-at-arms

Four of Anbennar's cultural men-at-arms belong to a religion more than a culture, so the overhaul gates them by the
recruiter's faith. Anbennar marked Druids and Skalds `# Change to religion` itself.

| Unit | Recruited by a faith with | Faiths at game start | Was |
|---|---|---|---|
| Dercinges | `tenet_druids_of_the_deruwren` | Ollodousges | Carnetori tradition |
| Druids | `tenet_druids_of_the_deruwren` | Ollodousges | Carnetori tradition |
| Skalds | `tenet_skaldic_tales` | Skaldhyrric Faith, Reverian Cult, West Damish | Gerudian tradition |
| Knights of the Spear | `doctrine_patron_deity_adean`, `_the_dame_adean` or `_adean_minara` | Court of Adean, Cult of Adean, Vernid Adean, Whiterose Court, Luna Damish | Adenner tradition |

- Both tenets can only be picked by their own religion (Lencori, Skaldhyrric). The patron god can be changed on
  reformation, so any Cannorian faith that takes Adean gains Knights of the Spear.
- Each unit is Anbennar's block with only `can_recruit` changed
  (`common/men_at_arms_types/zz_aov_faith_maa_overrides.txt`).
- Their four traditions (`tradition_test_maa_anb_dercinges`, `_druids`, `_skalds`, `_knights_of_the_spear`) are
  hidden, unpickable (`common/culture/traditions/zz_aov_faith_traditions.txt`) and removed from every culture at game
  start (`aov_faith_maa_game_start`, `common/on_action/aov_faith_maa_on_actions.txt`). Carnetori and Gerudian cultures
  gain a free tradition slot. The Druids and Skalds traditions also carried `allows_mageknight_accolade`, so those
  cultures now get the Mageknight accolade like any other: from the Magic Schools or Diranbe innovation.
- Anbennar's debug `tradition_test_maa` (never shown) still lists the unlock parameters; nothing reads them now.
- `tools/tests/test_faith_maa.py` fails when Anbennar changes a copied block, renames a gate doctrine, or adds another
  tradition that unlocks one of the four units.

## In-game checks

1. A Carnetori Ollodousges ruler can recruit Druids and Dercinges; the same ruler after converting to another faith
   cannot (check whether existing regiments stay).
2. A Gerudian Skaldhyrric ruler and a Reverian Cult ruler can recruit Skalds.
3. An Adenner Court of Adean ruler can recruit Knights of the Spear; the recruit tooltip names the doctrines.
4. Carnetori and Gerudian cultures no longer show the "Test MAA" traditions.

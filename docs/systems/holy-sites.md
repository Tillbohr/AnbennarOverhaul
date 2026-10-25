# Holy sites

Anbennar ships two faiths without holy sites: Devouring Path (Halessi religion) and Silk Turban (High Philosophy).
Both belong to emigrants from Haless and Rahen, which lie off the CK3 map, and each starts with one county in
Salahad. The overhaul gives each four holy sites: its starting county and three counties next to it.

| Faith | Holy site | County, barony | Modifier |
|---|---|---|---|
| Devouring Path | Benoné | `c_benone`, `b_benone` (the Beikling enclave) | health +0.15 |
| Devouring Path | Ianviréri | `c_ianvireri`, `b_ianvireri` | mountains advantage +3 |
| Devouring Path | Mohíra | `c_mermigan`, `b_mohira` | dread gain +10% |
| Devouring Path | Phiomústi | `c_kotidurnor`, `b_phiomusti` | intrigue +1 per piety level |
| Silk Turban | Davharral | `c_davharral`, `b_davharral` (the Raghamidesh colony) | domain tax +10% |
| Silk Turban | Rahenšah | `c_sahkuz`, `b_rahensah` | building gold cost -10% |
| Silk Turban | Nabašah | `c_sahnuses`, `b_nabasah` | development growth +10% |
| Silk Turban | Edenlil | `c_edenlil`, `b_edenlil` | diplomacy +1 per piety level |

## Generated files

| File | Generator | Why |
|---|---|---|
| `common/religion/holy_site_types/aov_holy_sites.txt` | `build_holy_sites.py` | the eight holy sites |
| `localization/english/aov_holy_sites_l_english.yml` | `build_holy_sites.py` | site and modifier names |
| `common/religion/religion_types/anb_halessi.txt`, `anb_high_philosophy.txt` | `build_holy_sites.py` | a faith's holy sites can only be listed in its religion, and religions are whole-file overrides; these are Anbennar's files with marked `holy_site` lines added |

The data is in `tools/data/holy_sites.py`. Rerun `python -I tools/build_holy_sites.py` after every Anbennar update,
or Anbennar's later changes to these two religions are hidden by the stale copies. `tools/tests/test_build_holy_sites.py`
fails when the copies are stale, and the generator stops when a county or barony is gone, a faith is renamed, or a
faith gains holy sites of its own in Anbennar (then drop it from the data).

The two copies carry 14 inherited tiger warnings (missing `WitchGod*` localization entries in Anbennar's religion
blocks); see `validation-baseline.md`.

## In-game checks

1. The Devouring Path and Silk Turban faith views list four holy sites each, with names and modifiers.
2. A Beikling ruler at Benoné can start a pilgrimage (Devouring Path encourages pilgrimages).
3. Each of the eight baronies shows a Grand Temple slot (`holy_site_other_grand_temple_01`). Anbennar's
   `game_start` gives one to every holy site whose province has no special slot; none of these eight has one.
   Only a ruler of the site's faith can build it, it needs Crop Rotation, and tribal, nomadic or wanua holders can't build it.
4. The other religions in both files are unchanged (Halessi and High Philosophy still load, `database_conflicts.log`
   shows only the expected file overrides).

# Holy sites and faith icons

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

## Faith icons

Anbennar gives 31 faiths EU4's personal-deity icon of the Dame (`the_dame`) as a stand-in. The same generator swaps
each one's `icon` line, and its `reformed_icon` line where that is also the stand-in (8 unreformed faiths), for an
icon picked to match the faith's description. The pictures are 100x100 DDS copied unchanged from other CK3 total
conversions (Za'am's resized from RiE's 758x768 original) into `gfx/interface/icons/faith/aov_<faith>.dds`; they are
imported once and committed, not regenerated. Businori uses Anbennar's own unused `cult_of_nerat` icon, since
Selkar-Nera is their Nerat. `tools/data/faith_icons.py` lists every faith, its icon and the source mod and file.

An entry with `replaces` swaps that Anbennar icon instead of `the_dame`. Jaherian Cults shares the generic Sun Cult
icon (`bulwari_sun_cult`) and gets EU4 Anbennar's icon for the New Sun Cult instead, the EU4 religion (also keyed
`bulwari_sun_cult`) that holds Jaher to be Surael Reborn: frame 46 of `gfx/interface/icon_religion.dds` (64 px
frames), cropped, Lanczos 2x and resized to 100 px with `eu4_import.py`'s helpers.

| Religion | Faiths and icon source |
|---|---|
| Akasi | Father Amahash, Mother Akhat, Father Aiji: the Warcraft TC's water, fire and air runes (Mother Akasik is earth) |
| Alenic | Ansuwir: AGOT storm god; Moors Cult: EK2 Hagraven cult |
| Bulwari Sun Cults | Jaherian Cults: EU4 Anbennar New Sun Cult (replaces `bulwari_sun_cult`) |
| Businori | Selkaran Primacy: Anbennar's `cult_of_nerat` |
| Cannorian Pantheon | Ryala: EK2 Dibella; Southern Castellos: PoD Via Regalis crown; Emulant Cults: EK2 cult of heroes; Luna Damish: RiE moon; Cult of Adean (Adenica): Godherja war knight; Border Cults: Godherja Gravewatch; Tefori Damish: AGOT Lady of the Waves; Lightfather: RiE sun; Stonescepter Court: After the End throne |
| Dragon cults | Korbarid: PoD thrashing dragon; Elkaesal: Warcraft blue dragonflight; Za'am: RiE dragon cult |
| Fey | Fey Cult: EK2 Green Pact |
| Gerudian | Old Gerudian: RiE `viking_05` |
| Infernal Court | Daedric princes from EK2, matched by domain: Hedine Sanguine, Forsara Nocturnal, Ildran Hermaeus Mora, Kazraiel Mehrunes Dagon, Canturian Molag Bal, Ibberal Namira, Mesner Clavicus Vile |
| Lencori | Eidoueni: Godherja horse; Ollodousges: EK2 druidic |
| Milcori | Cult of the Enduring Ones: RiE Witch-king |
| Tyvorkan | Táric Faith: EK2 woodland man |

To change an icon, copy a new 100x100 DDS over `aov_<faith>.dds` (or point the data at another file) and rerun the
generator.

## Generated files

| File | Generator | Why |
|---|---|---|
| `common/religion/holy_site_types/aov_holy_sites.txt` | `build_holy_sites.py` | the eight holy sites |
| `localization/english/aov_holy_sites_l_english.yml` | `build_holy_sites.py` | site and modifier names |
| `common/religion/religion_types/anb_*.txt` (14 files: `akasi`, `alenic`, `bulwari_sun_cults`, `businori`, `cannorian_pantheon`, `dragon_cult`, `fey`, `gerudian`, `halessi`, `high_philosophy`, `infernal_court`, `lencori`, `milcori`, `tyvorkan`) | `build_holy_sites.py` | a faith's holy sites and icon can only be set in its religion, and religions are whole-file overrides; these are Anbennar's files with marked `holy_site` lines added and marked `icon`/`reformed_icon` lines (`# Anbennar Overhaul, was <old icon>`) changed |

The data is in `tools/data/holy_sites.py` and `tools/data/faith_icons.py`; the icon pictures in
`gfx/interface/icons/faith/aov_*.dds` are committed by hand. Rerun `python -I tools/build_holy_sites.py` after every
Anbennar update, or Anbennar's later changes to these religions are hidden by the stale copies.
`tools/tests/test_build_holy_sites.py` fails when the copies are stale, and the generator stops when a county or
barony is gone, a faith is renamed, a faith gains holy sites of its own in Anbennar, or a faith no longer has the
icon it replaces (then drop it from the data), or an icon file is missing.

The copies carry Anbennar's own tiger reports (604 in all, none on a changed line); see `validation-baseline.md`.

## In-game checks

1. The Devouring Path and Silk Turban faith views list four holy sites each, with names and modifiers.
2. A Beikling ruler at Benoné can start a pilgrimage (Devouring Path encourages pilgrimages).
3. Each of the eight baronies shows a Grand Temple slot (`holy_site_other_grand_temple_01`). Anbennar's
   `game_start` gives one to every holy site whose province has no special slot; none of these eight has one.
   Only a ruler of the site's faith can build it, it needs Crop Rotation, and tribal, nomadic or wanua holders can't build it.
4. The other religions in these files are unchanged (they still load, `database_conflicts.log` shows only the
   expected file overrides).
5. The religion view and faith map mode show the new icon for each of the 31 faiths, e.g. Cult of Ryala (lotus),
   Luna Damish (moon), the seven infernal cults (Daedric emblems); no faith still shows the teal moon disc.
6. Faith creation and reformation of a pagan faith (e.g. Ansuwir) shows the new icon for the reformed faith.

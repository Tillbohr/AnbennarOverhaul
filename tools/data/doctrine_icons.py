"""Icons for Anbennar doctrines and tenets that ship without a picture (the faith window showed the pink placeholder).

CK3 draws a doctrine's icon from gfx/interface/icons/faith_doctrines/<icon>.dds, where <icon> is the doctrine's `icon`
field or else its key. Anbennar has no such folder, so these files carry the exact names Anbennar's doctrines look up
(no aov_ prefix is possible without overriding the doctrines). The pictures were made once and are committed; this
module records where each came from, and tools/tests/test_doctrine_icons.py checks that every doctrine the faith
window draws an icon for has one, and that Anbennar has not started shipping its own file of the same name.

Sources:
- ("deity", [frames]): EU4 Anbennar gfx/interface/hindu_deities_strip.dds, the personal-deity icons (42 px frames,
  1-based, the `sprite` of common/personal_deities/anb_cannorian_deities.txt). One frame: Lanczos 2x, then 120 px.
  Two or three frames (a doctrine naming several gods): each god at 76 px (two, top left to bottom right) or 64 px
  (three, top, bottom left, bottom right) on a 120 px transparent canvas, the first god drawn first.
- ("religion", frame): EU4 Anbennar gfx/interface/icon_religion.dds (64 px frames, the religion's `icon`): Lanczos 2x,
  then 120 px.
- ("file", path): an existing picture, resized to 120 px (mod-relative), or copied unchanged when it is a tenet.
All doctrine icons are 120x120 BGRA with mips, like vanilla's main-group doctrine icons; the tenet is RiE's 260x400.
"""

RIE = "C:/Program Files (x86)/Steam/steamapps/workshop/content/1158310/2291024373"

DOCTRINE_ICONS = {
    # Cannorian patron deities (doctrine_patron_deity group, main_group)
    "doctrine_patron_deity_castellos": ("deity", [1]),
    "doctrine_patron_deity_the_dame": ("deity", [2]),
    "doctrine_patron_deity_adean": ("deity", [4]),
    "doctrine_patron_deity_munas": ("deity", [5]),
    "doctrine_patron_deity_ara": ("deity", [6]),
    "doctrine_patron_deity_balgar": ("deity", [7]),
    "doctrine_patron_deity_esmaryal": ("deity", [8]),
    "doctrine_patron_deity_ryala": ("deity", [9]),
    "doctrine_patron_deity_minara": ("deity", [10]),
    "doctrine_patron_deity_falah": ("deity", [11]),
    "doctrine_patron_deity_nerat": ("deity", [12]),
    "doctrine_patron_deity_nathalyne": ("deity", [13]),
    "doctrine_patron_deity_begga": ("deity", [14]),
    "doctrine_patron_deity_wip": ("deity", [224]),
    "doctrine_patron_deity_the_dame_munas": ("deity", [2, 5]),
    "doctrine_patron_deity_the_dame_adean": ("deity", [2, 4]),
    "doctrine_patron_deity_ara_the_dame": ("deity", [6, 2]),
    "doctrine_patron_deity_adean_minara": ("deity", [4, 10]),
    "doctrine_patron_deity_esmaryal_the_dame_ara": ("deity", [8, 2, 6]),
    "doctrine_patron_deity_castellos_esmaryal_falah": ("deity", [1, 8, 11]),
    "doctrine_patron_deity_castellos_falah_nerat": ("deity", [1, 11, 12]),
    "doctrine_patron_deity_castellos_the_dame_nerat": ("deity", [1, 2, 12]),
    "doctrine_patron_deity_uelos": ("religion", 141),  # EU4 uelos_cult, the trident
    # Castellosi Monolatrism: the crown already used for the Southern Cult of Castellos (PoD Via Regalis)
    "doctrine_patron_deity_south_castellos": ("file", "gfx/interface/icons/faith/aov_southern_cult_of_castellos.dds"),
    # Infernalist doctrines (doctrine_infernalist group, main_group)
    "doctrine_hidden_infernalist": ("religion", 124),  # EU4 shadow_pact
    "doctrine_open_infernalist": ("religion", 93),  # EU4 infernal_court
    # Khetist (doctrine_khet group, main_group; Anbennar's `icon = khetarchy`)
    "khetarchy": ("religion", 38),  # EU4 elikhetist, the golden Khet
    # Dwarven Syncretism tenet (Anbennar's `icon = anb_tenet_dwarven_reverence`): RiE's dwarf statue tenet
    "anb_tenet_dwarven_reverence": ("file", RIE + "/gfx/interface/icons/faith_doctrines/tenet_dwarf_statue.dds"),
}

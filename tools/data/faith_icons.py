"""Data for tools/build_holy_sites.py: icons for Anbennar faiths that ship with the placeholder icon.

Anbennar gives 31 faiths EU4's personal-deity icon of the Dame (`the_dame`) as a stand-in. Each entry maps one of
them to an icon in gfx/interface/icons/faith/ and records where the art came from. The pictures were copied once
from other CK3 total conversions (100x100 DDS, unchanged, except Za'am, resized from RiE's 758x768 original) and are
committed; the generator only swaps the faith's `icon` (and `reformed_icon`, where it is also the placeholder) line
in a whole-file copy of the Anbennar religion file.

Sources: EK2 = Elder Kings 2 (2887120253), RiE = LotR: Realms in Exile (2291024373), Godherja = Godherja (2326030123),
PoD = Princes of Darkness (2216659254), AGOT = A Game of Thrones (2962333032), AtE = After the End (3192256710),
WC = the Warcraft total conversion (2949767945). Workshop ids are under steamapps/workshop/content/1158310.
"""

PLACEHOLDER = "the_dame"

FAITH_ICONS = {
    # Akasi: the elemental Fathers and Mother beside Mother Akasik (earth); one elemental rune each.
    "father_amahash": {"icon": "aov_father_amahash", "source": "WC wcmw_water_rune_3"},
    "mother_akhat": {"icon": "aov_mother_akhat", "source": "WC wcmw_fire_rune_3"},
    "father_aiji": {"icon": "aov_father_aiji", "source": "WC wcmw_air_rune_3"},
    # Alenic
    "ansuwir": {"icon": "aov_ansuwir", "source": "AGOT stormgod"},  # Ariadas of the storms
    "moors_cult": {"icon": "aov_moors_cult", "source": "EK2 hagraven_cult"},  # the Crimson One, open witchcraft
    # Businori: Selkar-Nera, Judge of the Dead, is their Nerat; Anbennar ships an unused Nerat icon.
    "businori_cult": {"icon": "cult_of_nerat", "source": "Anbennar cult_of_nerat"},
    # Cannorian Pantheon
    "cult_of_ryala": {"icon": "aov_cult_of_ryala", "source": "EK2 dibella"},  # love and beauty
    "southern_cult_of_castellos": {"icon": "aov_southern_cult_of_castellos", "source": "PoD viaregalis"},
    "vernid_adean": {"icon": "aov_vernid_adean", "source": "EK2 cult_of_heroes"},  # the Emulants
    "luna_damish": {"icon": "aov_luna_damish", "source": "RiE moon"},
    "adenican_adean": {"icon": "aov_adenican_adean", "source": "Godherja mfi_war_knight"},  # birthplace of knighthood
    "border_cults": {"icon": "aov_border_cults", "source": "Godherja gravewatch_icon"},  # watch over the necropoleis
    "tefori_damish": {"icon": "aov_tefori_damish", "source": "AGOT ladyofthewaves"},  # the Cult of the Tides
    "cult_of_the_lightfather": {"icon": "aov_cult_of_the_lightfather", "source": "RiE sun"},
    "stonescepter_court": {"icon": "aov_stonescepter_court", "source": "AtE global_throne"},  # led by Busilar's monarch
    # Dragon cults
    "korbarid_dragon_cult": {"icon": "aov_korbarid_dragon_cult", "source": "PoD thrashingdragon"},  # serpentine Balakururi
    "elkaesal_dragon_cult": {"icon": "aov_elkaesal_dragon_cult", "source": "WC wcrtd_blue_dragon_religion"},  # the White Dragon
    "zaam": {"icon": "aov_zaam", "source": "RiE dragon_cult_icon (resized)"},  # Zaamalot the Black Dragon
    # Fey
    "fey_cult": {"icon": "aov_fey_cult", "source": "EK2 greenpact"},  # bargains with the Emerald Lady
    # Gerudian
    "old_gerudian_faith": {"icon": "aov_old_gerudian_faith", "source": "RiE viking_05"},
    # Infernal Court: one Daedric prince per demon lord, matched by domain.
    "cult_of_hedine": {"icon": "aov_cult_of_hedine", "source": "EK2 sanguine"},  # carnal exaltation
    "cult_of_forsara": {"icon": "aov_cult_of_forsara", "source": "EK2 nocturnal"},  # shadows, risk and reward
    "cult_of_ildran": {"icon": "aov_cult_of_ildran", "source": "EK2 hermaeus"},  # gnosticism, law
    "cult_of_kazraiel": {"icon": "aov_cult_of_kazraiel", "source": "EK2 mehrunes"},  # war and sacrifice
    "cult_of_canturian": {"icon": "aov_cult_of_canturian", "source": "EK2 molag"},  # domination, human supremacy
    "cult_of_ibberal": {"icon": "aov_cult_of_ibberal", "source": "EK2 namira"},  # ritual cannibalism
    "cult_of_mesner": {"icon": "aov_cult_of_mesner", "source": "EK2 clavicus"},  # adorcism, the mask
    # Lencori
    "eidoueni": {"icon": "aov_eidoueni", "source": "Godherja mfi_horse"},  # Artanos, god of war and horses
    "ollodousges": {"icon": "aov_ollodousges", "source": "EK2 druidic"},
    # Milcori
    "milcori_cult": {"icon": "aov_milcori_cult", "source": "RiE custom_witch_king"},  # the Lich-Kings
    # Tyvorkan
    "taric_faith": {"icon": "aov_taric_faith", "source": "EK2 woodland_man"},  # Vahio and the spirits of the land
}

"""The nine Deepwoods grove duchies and their EU4 Anbennar counterparts, for tools/build_deepwoods_groves.py.

Each duchy gets the flag of its EU4 "Salla" realm as its coat of arms, and each county the name of its EU4 province.

Matching (2026-10-17): the CK3 Deepwoods is a reshaped copy of EU4's. EU4's west and east Deepwoods regions, minus the
"Vyr" forest paths, fall into nine separate clearings of 7-9 provinces, and each grove duchy is one of them (same
relative place, same shape: Lake Grove has the lake hole of Salla Elyn's clearing). Anbennar had already named every
county after an EU4 province of its clearing, in the same part of the clearing (checked on side-by-side renders of both
province maps), but without the accents, with two misspellings (Hofoon, Drennenthille) and with no name at all for
c_bone_grove_1_5 (its name sits on the unused key c_bone_grove_1_2). So the counties keep Anbennar's choice of province
and get the EU4 spelling. Rerun the matching if Anbennar redraws the Deepwoods.

Baronies (2026-10-17): a county's capital barony (its first in the landed titles) takes the county's name; the other
EU4 provinces of each clearing go to the other baronies. Each clearing was laid over its duchy by an affine fit of the
EU4 province map onto the CK3 one (maximising the overlap of the two outlines plus the share of each county's EU4
province that lands in that county), and each remaining EU4 province went to the non-capital barony it covers most
(at least 10% of the province; one province per barony, largest total overlap). Contann (7015, under two capitals of
Salla Ayeth) and Trónnghúl (3046, under a capital and two baronies already named in Salla Ghúl) fit no free barony and
are unused. CK3 has ~13 baronies per duchy and EU4 7-9 provinces per clearing, so the other baronies (listed by the
build) keep Anbennar's name, placeholder or none.

duchy key -> {"tag": EU4 country tag (flag gfx/flags/<tag>.tga), "counties": {county key: EU4 province id},
              "baronies": {non-capital barony key: EU4 province id}}
"""

GROVES = {
    "d_lake_grove_1": {  # Salla Elyn
        "tag": "I26",
        "counties": {
            "c_lake_grove_1_1": 7000,  # Fadhthanél
            "c_lake_grove_1_2": 3004,  # Elynáile
            "c_lake_grove_1_3": 3007,  # Corsmyraeth
            "c_lake_grove_1_4": 7002,  # Podkanek
        },
        "baronies": {
            "b_lake_grove_6": 3005,  # Prehnmás
            "b_lake_grove_9": 3006,  # Chylys
            "b_lake_grove_11": 3008,  # Sáwelahain
            "b_lake_grove_13": 7001,  # Volnudu
        },
    },
    "d_bone_grove_1": {  # Salla Cenág
        "tag": "I29",
        "counties": {
            "c_bone_grove_1_1": 3009,  # Kynprehn
            "c_bone_grove_1_5": 7004,  # Reekava
            "c_bone_grove_1_3": 3067,  # Prehntir
            "c_bone_grove_1_4": 3012,  # Hofónn
        },
        "baronies": {
            "b_bone_grove_5": 3010,  # Cenarká
            "b_bone_grove_17": 7003,  # Leb'kadu
            "b_bone_grove_9": 7005,  # Swáile
            "b_bone_grove_10": 3011,  # Banshécors
        },
    },
    "d_thorn_grove_1": {  # Salla Drennen
        "tag": "I28",
        "counties": {
            "c_thorn_grove_1_1": 3013,  # Freyhmyfel
            "c_thorn_grove_1_2": 3015,  # Taródéns
            "c_thorn_grove_1_3": 3017,  # Drennethílle
            "c_thorn_grove_1_4": 7007,  # Faedayr
        },
        "baronies": {
            "b_thorn_grove_5": 3014,  # Trónnynde
            "b_thorn_grove_11": 3016,  # Ahainglan
            "b_thorn_grove_12": 7006,  # Tarósáwel
        },
    },
    "d_mountain_grove_1": {  # Salla Myna
        "tag": "I27",
        "counties": {
            "c_mountain_grove_1_1": 7008,  # Mynath
            "c_mountain_grove_1_2": 3020,  # Ciranmyna
            "c_mountain_grove_1_3": 3019,  # Prehnryn
            "c_mountain_grove_1_4": 3022,  # Cirantyrnn
        },
        "baronies": {
            "b_mountain_grove_5": 3021,  # Ddwfynáile
            "b_mountain_grove_6": 3018,  # Clirypríah
            "b_mountain_grove_8": 7009,  # Cytheliandiel
            "b_mountain_grove_9": 7010,  # Ceidwayr
        },
    },
    "d_hunter_grove_1": {  # Salla Fealgarn
        "tag": "I30",
        "counties": {
            "c_hunter_grove_1_1": 7013,  # Vtákizdo
            "c_hunter_grove_1_2": 3023,  # Syryuniad
            "c_hunter_grove_1_3": 3024,  # Taráile
        },
        "baronies": {
            "b_hunter_grove_4": 7012,  # Symhayr
            "b_hunter_grove_7": 7011,  # Fealgathílle
            "b_hunter_grove_11": 3026,  # Sáwelfeal
            "b_hunter_grove_12": 3025,  # Córyllann
        },
    },
    "d_arrow_grove_1": {  # Salla Ayeth
        "tag": "I33",
        "counties": {
            "c_arrow_grove_1_1": 7014,  # Gozyest
            "c_arrow_grove_1_2": 3034,  # Yntynú Ynde
            "c_arrow_grove_1_3": 3036,  # Brynbál
        },
        "baronies": {
            "b_arrow_grove_4": 3032,  # Llannlar
            "b_arrow_grove_7": 3033,  # Ayethstir
            "b_arrow_grove_11": 3037,  # Ciranfarch
            "b_arrow_grove_12": 3035,  # Dráyodéns
            "b_arrow_grove_14": 3038,  # Hanwrghúlthílle
        },
    },
    "d_flower_grove_1": {  # Salla Scotha
        "tag": "I31",
        "counties": {
            "c_flower_grove_1_1": 7016,  # Scothaéyrst
            "c_flower_grove_1_2": 3027,  # Scothalón
        },
        "baronies": {
            "b_flower_grove_2": 3028,  # Athían
            "b_flower_grove_3": 3029,  # Ciranéar
            "b_flower_grove_4": 3030,  # Emmylscotha
            "b_flower_grove_8": 3031,  # Petégís
            "b_flower_grove_9": 7017,  # Ciraelis
        },
    },
    "d_river_grove_1": {  # Salla Ahain
        "tag": "I32",
        "counties": {
            "c_river_grove_1_1": 7018,  # Satynr
            "c_river_grove_1_2": 7019,  # Gytaemina
            "c_river_grove_1_3": 3042,  # Yfelorr
        },
        "baronies": {
            "b_river_grove_2": 7020,  # Jekpraz
            "b_river_grove_3": 7021,  # Krazho
            "b_river_grove_8": 3040,  # Criódharká
            "b_river_grove_11": 3039,  # Trían
            "b_river_grove_14": 3041,  # Imyhain
        },
    },
    "d_shadow_grove_1": {  # Salla Ghúl
        "tag": "I34",
        "counties": {
            "c_shadow_grove_1_1": 3043,  # Pydrusyryun
            "c_shadow_grove_1_2": 7024,  # Ghúlapríah
        },
        "baronies": {
            "b_shadow_grove_3": 7023,  # Príahain
            "b_shadow_grove_4": 7022,  # Dywyáel
            "b_shadow_grove_7": 3045,  # Alftudídd
            "b_shadow_grove_8": 3044,  # Ddwfyn Pydr
            "b_shadow_grove_9": 3047,  # Ciranghúl
        },
    },
}

# EU4 regions the provinces must lie in (map/region.txt), and the prefix of EU4's forest-path provinces, which are
# not clearings and so never a county's match.
EU4_REGIONS = ("west_deepwoods_region", "east_deepwoods_region")
PATH_PREFIX = "Vyr "

# EU4 province names used with a correction: EU4 province id -> name.
NAME_FIXES = {
    3032: "Llannlar",  # EU4 writes "llannlar" (adjective "llannlari"), lower-case by mistake
}

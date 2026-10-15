"""Data for tools/build_holding_models.py: which cultures get which RiE holding-model graphics."""

# Culture groups: building_gfx key (the group's most common existing list; other lists get derived keys, see
# build_holding_models.assign_gfx), optional labels for the derived keys, and either explicit culture keys or a heritage (every culture of it).
GROUPS = {
    "high_elf": {"label": "High Elven", "gfx": "aov_high_elf_building_gfx", "cultures": ("moon_elvish", "sun_elvish")},
    "wood_elf": {"label": "Wood Elven", "gfx": "aov_wood_elf_building_gfx", "cultures": ("wood_elvish",)},
    "dwarven": {"label": "Dwarven", "gfx": "aov_dwarven_building_gfx", "heritage": "heritage_dwarven",
                "variant_labels": {"mena_building_gfx": "Dwarven (Southern)"}},
    "castanorian": {"label": "Castanorian", "gfx": "aov_castanorian_building_gfx", "heritage": "heritage_escanni"},
}

# Dwarven terrain: a castle or city here shows the dwarf model whoever holds it (the asset lists the provinces).
DWARF_TERRAIN_TERRAINS = ("dwarven_hold", "dwarven_hold_surface", "cavern", "dwarven_road")
# Provinces of those terrains that keep the ordinary models (263 is Old Passage, the dwarven road between Esmaria and
# Silverforge; user choice).
DWARF_PROVINCE_EXCLUDE = (263,)

# RiE subfolder (under gfx/models/buildings/) that holds each group's assets.
MODEL_SETS = {
    "high_elf": "elven/highelves",
    "wood_elf": "elven",
    "dwarven": "dwarven",
    "castanorian": "dunedain",
}


def _levels(kind: str, high_elf, wood_elf, castanorian, dwarven=None) -> dict:
    """building key -> group -> mesh names, for levels 01..04 of one holding kind (names get '_mesh')."""
    out = {}
    for level in range(4):
        groups = {
            "high_elf": [f"{name}_mesh" for name in high_elf[level]],
            "wood_elf": [f"{wood_elf[level]}_mesh"],
            "castanorian": [f"{name}_mesh" for name in castanorian[level]],
        }
        if dwarven:
            groups["dwarven"] = [f"{dwarven[level]}_mesh"]
        out[f"{kind}_0{level + 1}"] = groups
    return out


_HIGH_ELF = [(f"highelves_0{n}_01", f"highelves_0{n}_02") for n in range(1, 5)]
_WOOD_ELF = ["sindarin_sanctuary_01", "sindarin_sanctuary_02", "sindarin_sanctuary_03", "sindarin_sanctuary_03"]
_DWARVEN = [f"dwarven_holding_0{n}" for n in range(1, 5)]

# Building key -> group -> pdxmesh names (the spec's section 2 table). Dwarves only change castles and cities.
# Dwarf entries are the model of the terrain/mountain assets (see build_holding_models.build_buildings).
MODELS = {}
MODELS.update(_levels("castle", _HIGH_ELF, _WOOD_ELF,
                      [(f"building_dunedain_castle_0{n}",) for n in range(1, 5)], _DWARVEN))
MODELS.update(_levels("city", _HIGH_ELF, _WOOD_ELF,
                      [(name,) for name in ("gondor_city_01", "gondor_city_01", "gondor_city_02", "gondor_city_02")],
                      _DWARVEN))
# RiE has no dwarf temple: temples in dwarven terrain reuse the holding model of the same level.
MODELS.update(_levels("temple", _HIGH_ELF, _WOOD_ELF,
                      [[f"building_dunedain_temple_0{n}_{side}" for side in "ab"] for n in (1, 1, 2, 2)], _DWARVEN))

# Tribal holdings (wood elves only; every wood elf holding in the Deepwoods starts tribal).
MODELS["tribe_01"] = {"wood_elf": ["sindarin_sanctuary_01_mesh"]}
MODELS["tribe_02"] = {"wood_elf": ["sindarin_sanctuary_02_mesh"]}

# Background wall buildings (aov_elven_walls): group -> pdxmesh.
WALL_MODELS = {"high_elf": "highelves_fort_wall_mesh", "wood_elf": "sindarin_hedge_wall_01_mesh"}

# Walls follow the holding level for every culture (the vanilla chain needs fortification buildings that almost no
# holding has): level -> (province trigger, the primary holding buildings of that level). Anbennar and the game have
# no level 05+. Levels 1-2 and tribal holdings show no walls (walls_00); walls_01_tribal, walls_01 and walls_02 never show.
WALL_LEVELS = {
    3: ("has_building", ("castle_03", "city_03", "temple_03")),
    4: ("has_building_or_higher", ("castle_04", "city_04", "temple_04")),
}

# Walls of the castanorian group: re-emitted wall building -> pdxmesh (RiE's Gondorian walls with gatehouses).
CASTANORIAN_WALLS = {"walls_03": "dunedain_walls_03_mesh", "walls_04": "dunedain_walls_04_mesh"}

# Dwarven hold level (1..10) -> RiE dwarven pdxmesh, used by tools/build_holds.py (dwarf holders only; the
# assets are copied by tools/build_holding_models.py).
HOLD_DWARF_MESHES = {n: f"dwarven_holding_0{(n + 1) // 2}_mesh" for n in range(1, 11)}

"""Realms in Exile's army models for Anbennar's elves and dwarves, built by tools/build_holding_models.py.

The target cultures get a new unit_gfx key (prepended in the culture files that build_holding_models.py already
overrides), army entity links pick one RiE army entity per army quality, and the RiE army entities, with the weapon
and shield entities they attach, are copied block by block into one asset file beside their meshes and textures.
"""

import re
from functools import lru_cache
from pathlib import Path

import build_holding_models as bhm
from build_hud_override import GeneratorError
from data import unit_models as data

UNIT_LINE = re.compile(r"^(\s*unit_gfx\s*=\s*\{)(.*)$")
UNIT_LIST = re.compile(r"\bunit_gfx\s*=\s*\{([^}]*)\}")
LINKS_FILE = "gfx/models/units/entity_links/aov_army_entity_links.txt"
# Directly under infantry/, so the assets' "../animations/<x>.anim" paths reach the game's infantry animations.
ASSET_DIR = "gfx/models/units/infantry/aov_rie_units"
ASSET_FILE = f"{ASSET_DIR}/aov_rie_army_units.asset"
ANIMATIONS_DIR = "game/gfx/models/units/infantry/animations"
SHADER_FILE = "gfx/FX/pdxmesh.shader"

BLOCK_NAME = re.compile(r'\bname\s*=\s*"?([A-Za-z0-9_.\-]+)')
ENTITY_REF = re.compile(r'\b(pdxmesh|entity|clone)\s*=\s*"([^"]+)"')
ANIM_REF = re.compile(r'"([^"]*\.anim)"')
SHADER_REF = re.compile(r'\bshader\s*=\s*"([^"]+)"')
EFFECT = re.compile(r"^Effect\s+([A-Za-z0-9_]+)", re.MULTILINE)


def _header() -> list:
    first, *rest = bhm.HEADER()
    return [bhm.BOM + first.replace("build_holding_models.py", "build_holding_models.py (tools/rie_units.py)")] + rest


def unit_gfx_sequence(body: str) -> tuple:
    code = "\n".join(bhm.strip_comment(line) for line in body.splitlines())
    match = UNIT_LIST.search(code)
    return tuple(match.group(1).split()) if match else ()


def unit_targets(files: dict) -> dict:
    """Culture -> the unit_gfx key it gets. CK3 needs every gfx list that starts with one key to continue the same
    way, so all cultures of a group must share one unit_gfx list; a culture may be in one group only."""
    resolved = bhm.resolve_cultures(files, data.UNIT_GROUPS)
    sequences = {}
    for text in files.values():
        for key, _start, _end, body in bhm.culture_blocks(text):
            sequences[key] = unit_gfx_sequence(body)
    targets = {}
    for name, cultures in resolved.items():
        lists = {sequences[culture] for culture in cultures}
        if len(lists) != 1 or not next(iter(lists)):
            raise GeneratorError(f"unit group {name}: cultures need one shared, non-empty unit_gfx list, found "
                                 + "; ".join(" ".join(seq) or "(none)" for seq in sorted(lists)))
        for culture in cultures:
            if culture in targets:
                raise GeneratorError(f"culture {culture} is in two unit groups")
            targets[culture] = data.UNIT_GROUPS[name]["unit_gfx"]
    return targets


def override_unit_gfx(text: str, targets: dict) -> str:
    """The culture file with each target culture's unit_gfx key prepended to its unit_gfx line, marked."""
    return bhm.override_culture_file(text, targets, UNIT_LINE, "unit_gfx")


def localization_lines() -> list:
    """One loc line per unit_gfx key (written into tools/build_holding_models.py's localization file)."""
    return [f' {group["unit_gfx"]}:0 "{group["label"]}"' for group in data.UNIT_GROUPS.values()]


def entity_links_text() -> str:
    lines = _header() + ["# Army models of the elf and dwarf cultures; data in tools/data/unit_models.py. quality = army pips."]
    for group, models in data.ARMY_MODELS.items():
        gfx = data.UNIT_GROUPS[group]["unit_gfx"]
        previous = 0
        lines += ["", f"# {data.UNIT_GROUPS[group]['label']}"]
        for number, (pips, entity) in enumerate(models, start=1):
            if pips <= previous or not 1 <= pips <= 5:
                raise GeneratorError(f"{group}: army model pips must rise within 1..5, got {pips} after {previous}")
            previous = pips
            lines += ["", f"aov_{group}_army_{number:02d} = {{", "\ttype = army"]
            if pips > 1:
                lines.append(f"\tquality = {pips}")
            lines += [f"\tgraphical_cultures = {{ {gfx} }}", f"\tentity = {entity}", "}"]
        if models[0][0] != 1:
            raise GeneratorError(f"{group}: the first army model must start at 1 pip")
    return "\n".join(lines) + "\n"


@lru_cache(maxsize=None)
def _block_index(models: str) -> dict:
    """(pdxmesh|entity, name) -> [(block text, .asset path)] for every top-level block under a gfx/models folder."""
    index = {}
    for path in sorted(Path(models).rglob("*.asset")):
        text = path.read_text("utf-8-sig", errors="replace")
        for kind, _start, _end, body in bhm.culture_blocks(text):
            if kind not in ("pdxmesh", "entity"):
                continue
            match = BLOCK_NAME.search(_code(body))
            if match:
                index.setdefault((kind, match.group(1)), []).append((body, path))
    return index


def _code(block: str) -> str:
    return "\n".join(bhm.strip_comment(line) for line in block.splitlines())


def find_block(models: Path, kind: str, name: str) -> tuple:
    hits = _block_index(str(models)).get((kind, name), [])
    if not hits:
        raise GeneratorError(f"{kind} {name} not found in {models}")
    if len({body for body, _path in hits}) > 1:
        raise GeneratorError(f"{kind} {name} is defined differently in: {', '.join(str(p) for _b, p in hits)}")
    return hits[0]


def collect_blocks(models: Path, entities) -> list:
    """[(kind, name, block, source path)] for the entities and everything they use (pdxmeshes, attached and cloned
    entities), each once, dependencies first."""
    done, order = set(), []

    def visit(kind, name, chain):
        if (kind, name) in done:
            return
        if (kind, name) in chain:
            raise GeneratorError(f"{kind} {name} refers to itself through {' -> '.join(n for _k, n in chain)}")
        body, path = find_block(models, kind, name)
        if kind == "entity":
            for ref_kind, ref in ENTITY_REF.findall(_code(body)):
                visit("pdxmesh" if ref_kind == "pdxmesh" else "entity", ref, chain + [(kind, name)])
        done.add((kind, name))
        order.append((kind, name, body, path))

    for entity in entities:
        visit("entity", entity, [])
    return order


def referenced_files(block: str) -> list:
    """Mesh and texture file names a pdxmesh block names, in order."""
    found = []
    for ref in bhm.TEXTURE_REF.findall(_code(block)):
        if "/" in ref or "\\" in ref:
            raise GeneratorError(f"{ref} is a path, not a file name")
        if ref not in found:
            found.append(ref)
    return found


def check_animations(blocks: list, game: Path) -> None:
    """Every animation is one of the game's infantry animations, named as ../animations/<file>."""
    folder = Path(game) / ANIMATIONS_DIR
    for _kind, name, body, _path in blocks:
        for ref in ANIM_REF.findall(_code(body)):
            if not ref.startswith("../animations/") or "/" in ref[len("../animations/"):]:
                raise GeneratorError(f"{name}: animation {ref} is not ../animations/<file>")
            if not (folder / ref[len("../animations/"):]).is_file():
                raise GeneratorError(f"{name}: animation {ref} not found in {folder}")


def check_unit_shaders(blocks: list, shader_text: str) -> None:
    """Every shader a copied pdxmesh names needs its Effect in this mod's pdxmesh.shader (RiE's, copied by
    tools/build_map_graphics.py), or the mesh does not draw."""
    defined = set(EFFECT.findall(shader_text))
    for _kind, name, body, _path in blocks:
        for shader in SHADER_REF.findall(_code(body)):
            if shader not in defined:
                raise GeneratorError(f"{name} uses shader {shader}, which {SHADER_FILE} does not define")


def asset_text(blocks: list, models: Path) -> str:
    lines = _header() + ["# RiE army entities with the weapons and shields they attach, copied block by block."]
    for kind, name, body, path in blocks:
        source = path.relative_to(models).as_posix()
        lines += ["", f"# {kind} {name} from RiE gfx/models/{source}"]
        lines += [line.rstrip("\r") for line in body.rstrip("\r\n").split("\n")]
    return "\n".join(lines) + "\n"


def build_units(roots) -> dict:
    """The entity links, the asset file and the copied mesh and texture files, rel path -> bytes."""
    roots.check()
    models = roots.rie / "gfx/models"
    entities = [entity for models_ in data.ARMY_MODELS.values() for _pips, entity in models_]
    blocks = collect_blocks(models, entities)
    check_animations(blocks, roots.game)
    check_unit_shaders(blocks, bhm.read_text(bhm.SUBMOD / SHADER_FILE))
    files = {LINKS_FILE: entity_links_text().encode("utf-8"),
             ASSET_FILE: asset_text(blocks, models).encode("utf-8")}
    names = bhm._file_names(str(models))
    for kind, name, body, _path in blocks:
        if kind != "pdxmesh":
            continue
        for ref in referenced_files(body):
            found = names.get(ref, [])
            if not found:
                raise GeneratorError(f"{name}: {ref} not found in RiE's gfx/models")
            if len({p.read_bytes() for p in found}) > 1:
                raise GeneratorError(f"{name}: {ref} exists with different content in several RiE folders")
            files[f"{ASSET_DIR}/{ref}"] = found[0].read_bytes()
    bhm.check_collisions(roots, {ASSET_FILE: files[ASSET_FILE]})
    return files

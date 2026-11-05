"""One trace of the carved regions for a whole test run, kept on disk until an input changes. Tests only.

Tracing Serpentreach, Segbandal and West Dwarovar (build_serpentreach.layouts) and decoding Anbennar's provinces.png
take about two minutes in pure Python, and many tests need the result. `layouts()` gives each process one result and
reads it from .trace_cache (git-ignored) when a past trace had byte-identical inputs. Generators do not use this: they
always trace, and tests still render every file from the result, so the freshness tests compare real renders.

The cache key is a hash of every input: the data files the trace reads (`data_files`), the code of every tools module
build_serpentreach imports (`code_files`) and the Python version. A real trace runs watched: opening any other file
stops the run with TraceInputError, so a tracer that starts reading something new cannot be cached without it.
"""

import ast
import hashlib
import os
import pickle
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))  # python -I does not add the tools folder
CACHE = Path(__file__).resolve().parent / ".trace_cache"
KEEP = 3  # cached traces kept, for switching between branches
ANBENNAR_MAP = ("provinces.png", "definition.csv", "default.map")
EU4_MAP = ("area.txt", "climate.txt", "default.map", "definition.csv", "provinces.bmp", "region.txt", "terrain.txt")

_RESULT = []  # this process's (layouts, ck3)
_watch = {"active": False, "opened": set()}
_hooked = []


class TraceInputError(Exception):
    """A real trace opened a file its cache key does not hash."""


def data_files(anbennar: Path, eu4: Path) -> list:
    """Every data file the trace reads. Listed even when absent, so a file appearing or vanishing changes the key."""
    return ([anbennar / "map_data" / name for name in ANBENNAR_MAP]
            + sorted((anbennar / "common/landed_titles").glob("*.txt"))
            + [eu4 / "map" / name for name in EU4_MAP]
            + sorted((eu4 / "localisation").rglob("*_l_english.yml")))


def _imported_modules(path: Path) -> set:
    """Dotted names of everything `path` imports, function-level imports included."""
    names = set()
    for node in ast.walk(ast.parse(path.read_bytes())):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return names


def code_files(tools: Path = TOOLS) -> list:
    """build_serpentreach.py and every module under `tools` it reaches through imports."""
    seen, stack = set(), [tools / "build_serpentreach.py"]
    while stack:
        path = stack.pop()
        if path not in seen and path.is_file():
            seen.add(path)
            stack.extend(tools / f"{name.replace('.', '/')}.py" for name in _imported_modules(path))
    return sorted(seen)


def cache_key(anbennar: Path, eu4: Path, tools: Path = TOOLS) -> str:
    """Hash of every input's name and bytes, and of the Python running the trace."""
    digest = hashlib.sha256(sys.version.encode())
    for path in code_files(tools) + data_files(anbennar, eu4):
        root = next(r for r in (tools, anbennar, eu4) if path.is_relative_to(r))
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest() if path.is_file() else b"missing")
    return digest.hexdigest()


def _norm(path) -> str:
    return os.path.normcase(os.path.abspath(path))


def _audit(event, args):
    if _watch["active"] and event == "open" and isinstance(args[0], (str, os.PathLike)):
        _watch["opened"].add(_norm(args[0]))


def _unlisted_reads(opened: set, listed: list) -> list:
    """Opened files that are neither key inputs nor part of Python itself."""
    allowed = {_norm(path) for path in listed}
    python = tuple(_norm(root) + os.sep for root in {sys.prefix, sys.base_prefix})
    return sorted(path for path in opened - allowed
                  if not path.startswith(python) and not path.endswith(".pyc"))


def _watched_trace(trace, anbennar: Path, eu4: Path, tools: Path):
    """trace(anbennar, eu4), refusing a read of any file outside the key."""
    if not _hooked:  # an audit hook cannot be removed, so one stays and only records while a trace runs
        sys.addaudithook(_audit)
        _hooked.append(True)
    _watch.update(active=True, opened=set())
    try:
        result = trace(anbennar, eu4)
    finally:
        _watch["active"] = False
    unlisted = _unlisted_reads(_watch["opened"], data_files(anbennar, eu4) + code_files(tools))
    if unlisted:
        raise TraceInputError("the trace read files its cache key does not hash; add them to "
                              f"tools/tests/shared_trace.py data_files: {', '.join(unlisted)}")
    return result


def _real_trace(anbennar: Path, eu4: Path) -> tuple:
    import build_serpentreach as bs
    import serpentreach_layout as sl
    ck3 = sl.load_ck3(anbennar)
    return bs.layouts(anbennar, eu4, ck3), ck3


def _store(folder: Path, path: Path, result) -> None:
    """Write `path` whole or not at all, and drop all but the newest KEEP traces. Failing here only costs a retrace."""
    folder.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f".{os.getpid()}.tmp")
    try:
        temporary.write_bytes(pickle.dumps(result, protocol=pickle.HIGHEST_PROTOCOL))
        os.replace(temporary, path)
        traces = sorted(folder.glob("*.pickle"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in traces[KEEP:]:
            old.unlink()
    except OSError:
        temporary.unlink(missing_ok=True)


def load_or_trace(anbennar: Path, eu4: Path, folder: Path = CACHE, trace=_real_trace, tools: Path = TOOLS):
    """The cached trace of these exact inputs, or a real one, stored unless an input changed while it ran."""
    key = cache_key(anbennar, eu4, tools)
    path = folder / f"{key}.pickle"
    try:
        return pickle.loads(path.read_bytes())
    except (OSError, EOFError, pickle.PickleError, AttributeError, ImportError, IndexError):
        pass  # absent or unreadable: trace
    result = _watched_trace(trace, anbennar, eu4, tools)
    if cache_key(anbennar, eu4, tools) == key:
        _store(folder, path, result)
    return result


def layouts() -> tuple:
    """((Serpentreach's, Segbandal's, West Dwarovar's) layouts, sl.load_ck3(Anbennar)), one per process. Read-only:
    every test in the process shares them."""
    if not _RESULT:
        import build_serpentreach as bs
        _RESULT.append(load_or_trace(bs.ANBENNAR, bs.EU4))
    return _RESULT[0]


def seed_map_graphics(bmg, roots) -> None:
    """Fill build_map_graphics's per-build layouts from the shared trace, so it does not trace again.
    test_shared_trace checks that it would have asked the tracer for the same layouts."""
    (serp, seg, wd), ck3 = layouts()
    key = bmg._layout_key(roots)
    bmg._SERPENTREACH[key] = (serp, ck3[0])
    bmg._SEGBANDAL[key] = seg
    bmg._WEST_DWAROVAR[key] = wd


if __name__ == "__main__":  # tools/run_tests.py fills the cache here, before test processes need it
    layouts()

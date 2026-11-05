"""Run the tool tests in parallel: one process per test module, failures in full, little output otherwise.

    python -I tools/run_tests.py                         every module
    python -I tools/run_tests.py serpentreach holds      modules whose name contains either word
    python -I tools/run_tests.py -j 4                    at most 4 at a time

Exits 0 when every test passes. `python -I -m unittest discover -s tools/tests` runs the same tests one after another.
"""

import argparse
import concurrent.futures as futures
import locale
import os
import re
import subprocess
import sys
import time
from collections import namedtuple
from pathlib import Path

SUBMOD = Path(__file__).resolve().parent.parent
TESTS = SUBMOD / "tools/tests"
HELPER = TESTS / "shared_trace.py"
DEFAULT_JOBS = min(os.cpu_count() or 1, 12)  # the heaviest modules hold 1 to 3 GB each
NO_TESTS_RAN = 5  # unittest's exit code for a module with no tests

Outcome = namedtuple("Outcome", "module seconds tests failures errors skipped passed output")


def select(names: list) -> list:
    """Test module paths, all of them or those whose name contains one of `names`."""
    modules = sorted(TESTS.glob("test*.py"))
    return [m for m in modules if not names or any(name in m.stem for name in names)]


def parse(module: str, seconds: float, code: int, output: str) -> Outcome:
    """A module's result from unittest's closing lines; anything unreadable counts as a failed module."""
    ran = re.findall(r"^Ran (\d+) tests? in ", output, re.M)
    closing = "".join(re.findall(r"^(?:OK|FAILED|NO TESTS RAN)\b.*$", output, re.M)[-1:])

    def count(word):
        return sum(int(n) for n in re.findall(rf"\b{word}=(\d+)", closing))
    passed = (code == 0 and bool(ran)) or code == NO_TESTS_RAN
    return Outcome(module, seconds, int(ran[-1]) if ran else 0, count("failures"), count("errors"), count("skipped"),
                   passed, output)


def run_module(path: Path) -> Outcome:
    start = time.perf_counter()
    done = subprocess.run([sys.executable, "-I", "-m", "unittest", "discover", "-s", str(TESTS), "-p", path.name],
                          cwd=SUBMOD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = done.stdout.decode(locale.getencoding(), errors="replace").strip()
    return parse(path.stem, time.perf_counter() - start, done.returncode, output)


def fill_trace_cache(modules: list) -> None:
    """Trace once, before the modules that share the trace would each do it. If this fails, those tests report why."""
    if any(HELPER.stem in m.read_text(encoding="utf-8") for m in modules):
        subprocess.run([sys.executable, "-I", str(HELPER)], cwd=SUBMOD, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)


def summary(outcomes: list, seconds: float) -> str:
    bad = [o for o in outcomes if not o.passed]
    totals = (f"failures={sum(o.failures for o in outcomes)}, errors={sum(o.errors for o in outcomes)}, "
              f"skipped={sum(o.skipped for o in outcomes)}")
    slowest = ", ".join(f"{o.module} {o.seconds:.0f} s" for o in sorted(outcomes, key=lambda o: -o.seconds)[:5])
    return (f"Ran {sum(o.tests for o in outcomes)} tests from {len(outcomes)} modules in {seconds:.0f} s "
            f"({sum(o.seconds for o in outcomes):.0f} s of module time): "
            f"{'FAILED in ' + ', '.join(o.module for o in bad) if bad else 'OK'} ({totals})\nSlowest: {slowest}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("names", nargs="*", help="run only modules whose name contains one of these")
    parser.add_argument("-j", "--jobs", type=int, default=DEFAULT_JOBS, help=f"modules at a time (default {DEFAULT_JOBS})")
    args = parser.parse_args(argv)
    modules = select(args.names)
    if not modules:
        print(f"no test module matches {' '.join(args.names)}", file=sys.stderr)
        return 2
    start = time.perf_counter()
    fill_trace_cache(modules)
    outcomes = []
    with futures.ThreadPoolExecutor(max(args.jobs, 1)) as pool:
        for outcome in futures.as_completed(pool.submit(run_module, m) for m in modules):
            outcome = outcome.result()
            outcomes.append(outcome)
            if not outcome.passed:
                print(f"{'=' * 70}\n{outcome.module} FAILED\n{outcome.output}\n", flush=True)
    print(summary(outcomes, time.perf_counter() - start))
    return 0 if all(o.passed for o in outcomes) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="backslashreplace")  # a test's output may hold what the console cannot show
    sys.exit(main())

"""Run ck3-tiger on Anbennar Overhaul (with base Anbennar loaded via ck3-tiger.conf).

    python -I tools/validate.py              # show only reports not in the baseline
    python -I tools/validate.py --all        # show every report
    python -I tools/validate.py --baseline   # accept the current reports as the new baseline

The baseline (tools/tiger_baseline.json) holds known reports inherited from Anbennar, such as
the temple_citadel_holding warnings in the generated holdings copy. Re-baseline only after
checking that every new report really is inherited and not caused by the overhaul.
"""

import subprocess
import sys
from pathlib import Path

TIGER = Path("C:/Users/tyler/tools/ck3-tiger/ck3-tiger.exe")
SUBMOD = Path(__file__).resolve().parent.parent
BASELINE = SUBMOD / "tools" / "tiger_baseline.json"


def main() -> None:
    args = sys.argv[1:]
    if not TIGER.is_file():
        sys.exit(f"error: ck3-tiger not found at {TIGER}")

    if "--baseline" in args:
        with BASELINE.open("wb") as out:
            subprocess.run([str(TIGER), "--json", "."], cwd=SUBMOD, stdout=out, check=True)
        print(f"wrote {BASELINE}")
        return

    cmd = [str(TIGER), "--no-color"]
    if "--all" not in args and BASELINE.is_file():
        cmd += ["--suppress", str(BASELINE)]
    cmd.append(".")
    result = subprocess.run(cmd, cwd=SUBMOD, capture_output=True, text=True, encoding="utf-8")
    report = result.stdout.strip()
    print(report if report else "ck3-tiger: no new reports")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

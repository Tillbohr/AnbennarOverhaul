# Artificery Tab Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an Artificery main tab below Situations in the HUD tab bar, visible only to eligible gnome rulers, that opens an Artificery window with Factions and Inventions tabs holding placeholder text.

**Architecture:** Eligibility lives in one scripted trigger exposed through a scripted GUI. The button is inserted into a full-file `gui/hud.gui` override that a Python script regenerates from the vanilla file. The window is a scripted widget (own `.gui` file) toggled through `GetVariableSystem`, with the same frame as vanilla main-tab windows.

**Tech Stack:** CK3 1.19.0.6 script and PdxGui, Python 3 (stdlib only, `unittest`), ck3-tiger via `tools/validate.py`.

**Spec:** `docs/superpowers/specs/2026-10-08-artificery-tab-shell-design.md`

## Global Constraints

- Never write to `../anbennar-ck3-dev-master` or the game install; read them only.
- Script, GUI and localization files: UTF-8 **with BOM**, **LF** line endings, tabs for indentation. Python files: UTF-8 without BOM, LF, 4 spaces.
- New files use the `aov_` prefix; keys are not prefixed except GUI/loc keys of this feature (`aov_artificery_*`, `AOV_ARTIFICERY_*`).
- Run Python with `python -I`.
- Paths: game `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game`, base mod `../anbennar-ck3-dev-master`.
- Insertion point: directly after the `widget_hud_main_tab` whose `name = "tab_situation"`.
- Eligibility: `has_trait = race_gnome`, culture `has_cultural_tradition = tradition_gnomish_ingenuity`, `has_enabled_artificer_academy_trigger = yes`.
- Variables: `aov_artificery_window` (window open), `aov_artificery_tab` (unset = Factions, `'inventions'` = Inventions).
- No keyboard shortcut, no custom art (placeholder texture `gfx/interface/skinned/hud_maintab/maintab_estate.dds`).
- Ask the user before the first `git commit` of the execution; they have an unrelated uncommitted `CLAUDE.md` edit, so stage only the files each task names.

## Review Focus

1. **Generator rerun / already-generated input:** running the script on a source that already contains `tab_aov_artificery` must refuse, not insert a second tab. Test in Task 2 (`test_refuses_when_already_present`).
2. **Braces inside strings or comments in `hud.gui`** (e.g. `text = "{"` or `# }`) must not throw off brace matching and misplace the tab. Test in Task 2 (`test_ignores_braces_in_strings_and_comments`).
3. **BOM and CRLF in the source** must be preserved byte-for-byte outside the insertion so the override is a faithful copy. Test in Task 2 (`test_build_preserves_bom_and_crlf`).
4. **Ruler loses eligibility while the window is open** (academy captured, second academy inherited, heir is not a gnome): the button and window must both hide. Checked in Task 4 (in-game steps 3-4); both `visible` bindings read the same scripted GUI (Task 3).
5. **Vanilla main tab opened while Artificery is open:** Artificery must not draw over or under it. Checked in Task 4 (step 7); window `visible` includes `Not( IsRightWindowOpen )` (Task 3).

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `common/scripted_triggers/aov_artificer_triggers.txt` | modify | add `can_use_artificery_trigger` |
| `common/scripted_guis/aov_artificery_sgui.txt` | create | `aov_artificery_available` scripted GUI |
| `tools/build_hud_override.py` | create | regenerate `gui/hud.gui` with the Artificery tab |
| `tools/tests/test_build_hud_override.py` | create | unit tests for the generator |
| `gui/hud.gui` | generated | vanilla HUD + Artificery tab |
| `gui/aov_window_artificery.gui` | create | Artificery window |
| `gui/scripted_widgets/aov_scripted_widgets.txt` | create | registers the window |
| `localization/english/aov_artificery_l_english.yml` | modify | new loc keys |
| `CLAUDE.md` | modify | generated-files table, update steps, systems line |

---

### Task 1: Eligibility trigger and scripted GUI

**Files:**
- Modify: `common/scripted_triggers/aov_artificer_triggers.txt` (append at end)
- Create: `common/scripted_guis/aov_artificery_sgui.txt`
- Modify: `localization/english/aov_artificery_l_english.yml` (append a section)

**Interfaces:**
- Consumes: `has_enabled_artificer_academy_trigger` (character scope, already in `aov_artificer_triggers.txt`).
- Produces: scripted trigger `can_use_artificery_trigger` (character scope); scripted GUI `aov_artificery_available` (root = character), called from GUI as
  `[GetScriptedGui('aov_artificery_available').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]`.

- [ ] **Step 1: Confirm the validator is clean before changes**

Run: `python -I tools/validate.py`
Expected: `ck3-tiger: no new reports` (or a summary ending `fatal: 0, error: 0, ...` with nothing listed). If anything is listed, stop and report it; it predates this work.

- [ ] **Step 2: Append the trigger**

Append to `common/scripted_triggers/aov_artificer_triggers.txt` (keep BOM/LF; add a blank line before):

```
# Character scope
# The character may use the Artificery tab: a gnome whose culture has Gnomish Ingenuity
# and who holds exactly one (so enabled) Artificer Academy
can_use_artificery_trigger = {
	has_trait = race_gnome
	culture = {
		has_cultural_tradition = tradition_gnomish_ingenuity
	}
	has_enabled_artificer_academy_trigger = yes
}
```

- [ ] **Step 3: Create the scripted GUI**

Create `common/scripted_guis/aov_artificery_sgui.txt` (UTF-8 BOM, LF):

```
# Artificery tab: shown for characters that pass can_use_artificery_trigger.
# Read by the HUD button (gui/hud.gui, generated) and the window (gui/aov_window_artificery.gui).
aov_artificery_available = {
	scope = character
	is_shown = {
		can_use_artificery_trigger = yes
	}
}
```

- [ ] **Step 4: Add the loc keys for the whole feature**

Append to `localization/english/aov_artificery_l_english.yml` (one leading space, LF):

```

 # Artificery tab
 AOV_ARTIFICERY_BUTTON: "Artificery"
 AOV_ARTIFICERY_WINDOW_TITLE: "Artificery"
 AOV_ARTIFICERY_TAB_FACTIONS: "Factions"
 AOV_ARTIFICERY_TAB_INVENTIONS: "Inventions"
 AOV_ARTIFICERY_FACTIONS_PLACEHOLDER: "The artificer factions will be shown here."
 AOV_ARTIFICERY_INVENTIONS_PLACEHOLDER: "Inventions will be researched here."
```

- [ ] **Step 5: Validate**

Run: `python -I tools/validate.py`
Expected: no new reports. Tiger may report the new loc keys as unused until Tasks 2-3 reference them; if it does, rerun after Task 3 rather than baselining. Any report naming `can_use_artificery_trigger`, `aov_artificery_available` or `aov_artificer_triggers.txt` must be fixed now.

- [ ] **Step 6: Commit (after the user has OK'd commits)**

```bash
git add common/scripted_triggers/aov_artificer_triggers.txt common/scripted_guis/aov_artificery_sgui.txt localization/english/aov_artificery_l_english.yml
git commit -m "Add Artificery tab eligibility trigger and scripted GUI"
```

---

### Task 2: HUD override generator

**Files:**
- Create: `tools/build_hud_override.py`
- Create: `tools/tests/test_build_hud_override.py`
- Generate: `gui/hud.gui`
- Modify: `CLAUDE.md` (Generated files table, task table, update steps)

**Interfaces:**
- Consumes: scripted GUI `aov_artificery_available` and loc key `AOV_ARTIFICERY_BUTTON` (Task 1).
- Produces (module `build_hud_override`):
  - `class GeneratorError(Exception)`
  - `brace_delta(line: str) -> int`: `{` minus `}` outside double-quoted strings and `#` comments.
  - `insert_tab(text: str) -> str`: LF text without BOM in, same text with the Artificery block inserted out; raises `GeneratorError`.
  - `build(raw: bytes) -> bytes`: whole-file transform; keeps BOM and CRLF/LF, adds the header.
  - `find_source(anbennar: Path, game: Path) -> Path`: Anbennar's `gui/hud.gui` if it exists, else the game's; raises `GeneratorError` if neither exists.
  - Window variable used by the button: `aov_artificery_window`.

- [ ] **Step 1: Write the failing tests**

Create `tools/tests/test_build_hud_override.py`:

```python
"""Tests for tools/build_hud_override.py.

    python -I -m unittest discover -s tools/tests -v
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_hud_override as bho  # noqa: E402

HUD = (
    "widget = {\n"
    "\tvbox = {\n"
    "\t\twidget_hud_main_tab = {\n"
    "\t\t\tname = \"tab_activities\"\n"
    "\t\t}\n"
    "\n"
    "\t\twidget_hud_main_tab = {\n"
    "\t\t\tname = \"tab_situation\"\n"
    "\t\t\tblockoverride \"maintab_button\"\n"
    "\t\t\t{\n"
    "\t\t\t\tonclick = \"[ToggleGameView( 'situations' )]\"\n"
    "\t\t\t}\n"
    "\t\t}\n"
    "\n"
    "\t\twidget_hud_main_tab = {\n"
    "\t\t\tname = \"royal_court_button_tutorial_uses_this\"\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
)


class BraceDeltaTests(unittest.TestCase):
    def test_counts_braces(self):
        self.assertEqual(bho.brace_delta("a = { b = {"), 2)
        self.assertEqual(bho.brace_delta("}"), -1)

    def test_ignores_braces_in_strings_and_comments(self):
        self.assertEqual(bho.brace_delta('text = "{ not a brace }" # { nor }'), 0)
        self.assertEqual(bho.brace_delta('x = { # }'), 1)


class InsertTabTests(unittest.TestCase):
    def test_inserts_after_situation_tab(self):
        out = bho.insert_tab(HUD)
        sit_end = out.index('name = "tab_situation"')
        ours = out.index('name = "tab_aov_artificery"')
        court = out.index('name = "royal_court_button_tutorial_uses_this"')
        self.assertLess(sit_end, ours)
        self.assertLess(ours, court)

    def test_only_adds_the_marked_block(self):
        out = bho.insert_tab(HUD)
        lines = out.split("\n")
        begin = lines.index("\t\t" + bho.BEGIN)
        end = lines.index("\t\t" + bho.END)
        stripped = lines[:begin] + lines[end + 1:]
        # the block is inserted as: blank line, BEGIN ... END, directly after the closing brace
        self.assertEqual(lines[begin - 1], "")
        self.assertEqual("\n".join(stripped[:begin - 1] + stripped[begin:]), HUD)

    def test_block_uses_tab_indentation_of_siblings(self):
        out = bho.insert_tab(HUD)
        self.assertIn('\t\twidget_hud_main_tab = {\n\t\t\tname = "tab_aov_artificery"', out)

    def test_button_wiring(self):
        out = bho.insert_tab(HUD)
        self.assertIn("GetScriptedGui('aov_artificery_available').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )", out)
        self.assertIn("GetVariableSystem.Toggle( 'aov_artificery_window' )", out)
        self.assertIn("GetVariableSystem.Exists( 'aov_artificery_window' )", out)
        self.assertIn('tooltip = "AOV_ARTIFICERY_BUTTON"', out)
        self.assertIn(bho.TEXTURE, out)

    def test_block_braces_balance(self):
        self.assertEqual(sum(bho.brace_delta(l) for l in bho.insert_tab(HUD).split("\n")), 0)

    def test_missing_anchor(self):
        with self.assertRaises(bho.GeneratorError):
            bho.insert_tab(HUD.replace("tab_situation", "tab_renamed"))

    def test_refuses_when_already_present(self):
        with self.assertRaises(bho.GeneratorError):
            bho.insert_tab(bho.insert_tab(HUD))

    def test_unbalanced_braces(self):
        # file ends before the Situations widget closes
        broken = HUD[:HUD.index("\t\t\t}\n\t\t}\n\n\t\twidget_hud_main_tab = {\n\t\t\tname = \"royal")]
        with self.assertRaises(bho.GeneratorError):
            bho.insert_tab(broken)


class BuildTests(unittest.TestCase):
    def test_build_preserves_bom_and_crlf(self):
        raw = b"\xef\xbb\xbf" + HUD.replace("\n", "\r\n").encode("utf-8")
        out = bho.build(raw)
        self.assertTrue(out.startswith(b"\xef\xbb\xbf# Anbennar Overhaul: generated"))
        body = out[3:].decode("utf-8")
        self.assertNotIn("\n", body.replace("\r\n", ""))

    def test_build_lf_without_bom(self):
        out = bho.build(HUD.encode("utf-8"))
        self.assertFalse(out.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r\n", out)
        self.assertTrue(out.decode("utf-8").endswith(HUD[-20:]))


class FindSourceTests(unittest.TestCase):
    def test_prefers_anbennar(self):
        with tempfile.TemporaryDirectory() as tmp:
            anb, game = Path(tmp, "anb"), Path(tmp, "game")
            for root in (anb, game):
                (root / "gui").mkdir(parents=True)
                (root / "gui" / "hud.gui").write_text("x")
            self.assertEqual(bho.find_source(anb, game), anb / "gui" / "hud.gui")

    def test_falls_back_to_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            anb, game = Path(tmp, "anb"), Path(tmp, "game")
            (game / "gui").mkdir(parents=True)
            (game / "gui" / "hud.gui").write_text("x")
            self.assertEqual(bho.find_source(anb, game), game / "gui" / "hud.gui")

    def test_neither_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(bho.GeneratorError):
                bho.find_source(Path(tmp, "a"), Path(tmp, "b"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -I -m unittest discover -s tools/tests -v`
Expected: ERROR `ModuleNotFoundError: No module named 'build_hud_override'`.

- [ ] **Step 3: Write the generator**

Create `tools/build_hud_override.py`:

```python
"""Regenerate gui/hud.gui for Anbennar Overhaul.

The HUD tab bar can only be changed by overriding the whole hud.gui, so the submod ships a copy
with the Artificery main tab inserted directly below the Situations tab. The copy is taken from
Anbennar's gui/hud.gui if Anbennar ships one, otherwise from the game. Rerun this after every
CK3 patch and Anbennar update:

    python -I tools/build_hud_override.py [--anbennar PATH] [--game PATH]
"""

import argparse
import sys
from pathlib import Path

MARKER = "# Anbennar Overhaul"
BEGIN = f"{MARKER}: begin Artificery tab"
END = f"{MARKER}: end Artificery tab"
ANCHOR = 'name = "tab_situation"'
TAB_NAME = "tab_aov_artificery"
TEXTURE = "gfx/interface/skinned/hud_maintab/maintab_estate.dds"  # placeholder until custom art exists
REL_PATH = Path("gui/hud.gui")

SUBMOD = Path(__file__).resolve().parent.parent
DEFAULT_ANBENNAR = SUBMOD.parent / "anbennar-ck3-dev-master"
DEFAULT_GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game")

# Inserted after the Situations tab; {i} is the indentation of the sibling widgets
BLOCK = [
    BEGIN,
    "widget_hud_main_tab = {",
    f'\tname = "{TAB_NAME}"',
    "\tvisible = \"[GetScriptedGui('aov_artificery_available').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]\"",
    "",
    '\tblockoverride "maintab_button"',
    "\t{",
    f'\t\ttexture = "{TEXTURE}"',
    "\t\tonclick = \"[GetVariableSystem.Toggle( 'aov_artificery_window' )]\"",
    '\t\ttooltip = "AOV_ARTIFICERY_BUTTON"',
    "\t\tdown = \"[GetVariableSystem.Exists( 'aov_artificery_window' )]\"",
    "\t}",
    "}",
    END,
]


class GeneratorError(Exception):
    pass


def brace_delta(line: str) -> int:
    """Count '{' minus '}' outside double-quoted strings and '#' comments."""
    delta = 0
    in_string = False
    for ch in line:
        if ch == '"':
            in_string = not in_string
        elif in_string:
            continue
        elif ch == "#":
            break
        elif ch == "{":
            delta += 1
        elif ch == "}":
            delta -= 1
    return delta


def insert_tab(text: str) -> str:
    if TAB_NAME in text:
        raise GeneratorError(f"source already contains '{TAB_NAME}'; is it a generated file?")
    lines = text.split("\n")
    try:
        anchor = next(i for i, l in enumerate(lines) if l.strip() == ANCHOR)
    except StopIteration:
        raise GeneratorError(f"anchor '{ANCHOR}' not found; did a CK3 patch rename the Situations tab?")
    try:
        start = next(i for i in range(anchor, -1, -1) if lines[i].strip() == "widget_hud_main_tab = {")
    except StopIteration:
        raise GeneratorError("no 'widget_hud_main_tab = {' opens the Situations tab")

    depth = 0
    for end in range(start, len(lines)):
        depth += brace_delta(lines[end])
        if depth == 0:
            break
    else:
        raise GeneratorError("unbalanced braces in the Situations tab widget")

    indent = lines[start][: len(lines[start]) - len(lines[start].lstrip("\t"))]
    block = [""] + [indent + l if l else "" for l in BLOCK]
    lines[end + 1:end + 1] = block
    return "\n".join(lines)


def build(raw: bytes) -> bytes:
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    crlf = "\r\n" in text
    text = insert_tab(text.replace("\r\n", "\n"))
    header = (
        f"{MARKER}: generated by tools/build_hud_override.py from {REL_PATH.as_posix()}.\n"
        f"{MARKER}: do not edit by hand; edit the script and rerun it.\n"
    )
    text = header + text
    if crlf:
        text = text.replace("\n", "\r\n")
    return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")


def find_source(anbennar: Path, game: Path) -> Path:
    for root in (anbennar, game):
        path = root / REL_PATH
        if path.is_file():
            return path
    raise GeneratorError(f"no {REL_PATH.as_posix()} in {anbennar} or {game}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--anbennar", type=Path, default=DEFAULT_ANBENNAR)
    parser.add_argument("--game", type=Path, default=DEFAULT_GAME)
    args = parser.parse_args()
    try:
        src = find_source(args.anbennar, args.game)
        data = build(src.read_bytes())
    except GeneratorError as e:
        sys.exit(f"error: {e}")
    out = SUBMOD / REL_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    print(f"wrote {out} (from {src})")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -I -m unittest discover -s tools/tests -v`
Expected: all 15 tests `ok`.

- [ ] **Step 5: Generate the override and check the diff**

Run: `python -I tools/build_hud_override.py`
Expected: `wrote ...\gui\hud.gui (from C:\Program Files (x86)\...\game\gui\hud.gui)`.

Then check the only differences are the header and our block:

Run: `git diff --no-index --stat "C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game/gui/hud.gui" gui/hud.gui`
Expected: `1 file changed, 18 insertions(+), 1 deletion(-)`: 2 header lines + 1 blank + 14 block lines, plus the
first line counted as changed because the BOM moves from the original first line onto the header line.

Run: `git diff --no-index "C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game/gui/hud.gui" gui/hud.gui`
Expected: the insertion sits between the closing `}` of the `tab_situation` widget and the `widget_hud_main_tab = {` that holds `royal_court_button_tutorial_uses_this`, at the same indentation (four tabs).

Run the generator a second time and confirm `git status --short gui/hud.gui` shows the same file (deterministic output; `certutil -hashfile gui\hud.gui SHA256` before and after match).

- [ ] **Step 6: Update CLAUDE.md**

In `CLAUDE.md`:

Task table: add the row
```
| Rebuild HUD override | `python -I tools/build_hud_override.py` |
| Run tool tests | `python -I -m unittest discover -s tools/tests -v` |
```

Generated files table: add the row
```
| `gui/hud.gui` | `python -I tools/build_hud_override.py` | The main tab bar is whole-file only. The script copies Anbennar's `gui/hud.gui` if it has one, else the game's, and inserts the Artificery tab after `tab_situation` (marked `# Anbennar Overhaul`). Never edit the output by hand. |
```

"Updating to a new Anbennar version": change step 2 to
```
2. Run `python -I tools/build_holdings_override.py` and `python -I tools/build_hud_override.py`.
```
and add after the numbered list:
```
After a CK3 patch, rerun `python -I tools/build_hud_override.py` too: its source is the game's `hud.gui`.
```

- [ ] **Step 7: Validate**

Run: `python -I tools/validate.py`
Expected: no new reports from `gui/hud.gui`. Tiger checks GUI files only loosely; any report inside the inserted block (e.g. unknown loc key) must be fixed in the generator's `BLOCK` and the file regenerated. Reports elsewhere in `gui/hud.gui` are vanilla's: confirm by running tiger's `--all` and checking the same line numbers exist in the vanilla file, then `python -I tools/validate.py --baseline` only with the user's OK.

- [ ] **Step 8: Commit (after the user has OK'd commits)**

```bash
git add tools/build_hud_override.py tools/tests/test_build_hud_override.py gui/hud.gui CLAUDE.md
git commit -m "Add generated hud.gui with Artificery main tab"
```
Note: `CLAUDE.md` already has an unrelated user edit; ask the user whether to include it in this commit or use `git add -p CLAUDE.md` to stage only this task's hunks.

---

### Task 3: Artificery window

**Files:**
- Create: `gui/aov_window_artificery.gui`
- Create: `gui/scripted_widgets/aov_scripted_widgets.txt`
- Modify: `CLAUDE.md` (Systems section)

**Interfaces:**
- Consumes: scripted GUI `aov_artificery_available` (Task 1); variable `aov_artificery_window` set by the HUD button (Task 2); loc keys `AOV_ARTIFICERY_WINDOW_TITLE`, `AOV_ARTIFICERY_TAB_FACTIONS`, `AOV_ARTIFICERY_TAB_INVENTIONS`, `AOV_ARTIFICERY_FACTIONS_PLACEHOLDER`, `AOV_ARTIFICERY_INVENTIONS_PLACEHOLDER` (Task 1).
- Produces: window widget `aov_artificery_window`; body containers `aov_artificery_factions_body` and `aov_artificery_inventions_body` that later specs fill; variable `aov_artificery_tab`.

- [ ] **Step 1: Create the window**

Create `gui/aov_window_artificery.gui` (UTF-8 BOM, LF, tabs). Frame copied from vanilla `window_decisions.gui` and PoD's `POD_window_journeys.gui` (a scripted-widget main-tab window with the same visibility pattern):

```
######################################################
################# ARTIFICERY WINDOW ##################
######################################################
# Opened by the Artificery main tab (gui/hud.gui, generated by tools/build_hud_override.py).
# Shown while the variable is set, the player passes can_use_artificery_trigger,
# and no vanilla main-tab window is open.

window = {
	name = "aov_artificery_window"
	parentanchor = top|right
	layer = windows_layer
	movable = no

	using = Window_Size_MainTab

	visible = "[And( GetVariableSystem.Exists( 'aov_artificery_window' ), And( GetScriptedGui('aov_artificery_available').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End ), Not( IsRightWindowOpen ) ) )]"

	state = {
		name = _show
		using = Animation_FadeIn_Quick
		using = Sound_WindowShow_Standard
		using = Window_Position_MainTab
	}

	state = {
		name = _hide
		using = Animation_FadeOut_Quick
		using = Sound_WindowHide_Standard
		using = Window_Position_MainTab_Hide
	}

	margin_widget = {
		size = { 100% 100% }
		margin_top = 30
		margin_bottom = 25
		margin_right = 13

		widget = {
			size = { 100% 100% }

			vbox = {
				using = Window_Margins

				header_pattern = {
					layoutpolicy_horizontal = expanding

					blockoverride "header_text"
					{
						text = "AOV_ARTIFICERY_WINDOW_TITLE"
					}

					blockoverride "button_close"
					{
						onclick = "[GetVariableSystem.Clear( 'aov_artificery_window' )]"
					}
				}

				hbox = {
					name = "aov_artificery_tabs"
					layoutpolicy_horizontal = expanding

					button_tab = {
						name = "aov_artificery_tab_factions"
						onclick = "[GetVariableSystem.Clear( 'aov_artificery_tab' )]"
						down = "[Not( GetVariableSystem.Exists( 'aov_artificery_tab' ) )]"
						alwaystransparent = "[Not( GetVariableSystem.Exists( 'aov_artificery_tab' ) )]"

						blockoverride "tab_label"
						{
							text = "AOV_ARTIFICERY_TAB_FACTIONS"
							max_width = 220
						}
					}

					button_tab = {
						name = "aov_artificery_tab_inventions"
						onclick = "[GetVariableSystem.Set( 'aov_artificery_tab', 'inventions' )]"
						down = "[GetVariableSystem.HasValue( 'aov_artificery_tab', 'inventions' )]"
						alwaystransparent = "[GetVariableSystem.HasValue( 'aov_artificery_tab', 'inventions' )]"

						blockoverride "tab_label"
						{
							text = "AOV_ARTIFICERY_TAB_INVENTIONS"
							max_width = 220
						}
					}
				}

				# Factions tab: filled by the artificer factions spec
				vbox = {
					name = "aov_artificery_factions_body"
					visible = "[Not( GetVariableSystem.Exists( 'aov_artificery_tab' ) )]"
					layoutpolicy_horizontal = expanding
					layoutpolicy_vertical = expanding
					margin = { 20 20 }

					text_multi = {
						layoutpolicy_horizontal = expanding
						autoresize = yes
						max_width = 580
						text = "AOV_ARTIFICERY_FACTIONS_PLACEHOLDER"
						default_format = "#low"
					}

					expand = {}
				}

				# Inventions tab: filled by the inventions spec
				vbox = {
					name = "aov_artificery_inventions_body"
					visible = "[GetVariableSystem.HasValue( 'aov_artificery_tab', 'inventions' )]"
					layoutpolicy_horizontal = expanding
					layoutpolicy_vertical = expanding
					margin = { 20 20 }

					text_multi = {
						layoutpolicy_horizontal = expanding
						autoresize = yes
						max_width = 580
						text = "AOV_ARTIFICERY_INVENTIONS_PLACEHOLDER"
						default_format = "#low"
					}

					expand = {}
				}
			}
		}
	}
}
```

- [ ] **Step 2: Register the scripted widget**

Create `gui/scripted_widgets/aov_scripted_widgets.txt` (UTF-8 BOM, LF):

```
gui/aov_window_artificery.gui = aov_artificery_window
```

- [ ] **Step 3: Check the templates exist in vanilla**

Run: `grep -rn "template Window_Size_MainTab\b\|template Window_Position_MainTab\b\|template Window_Position_MainTab_Hide\b\|template Window_Margins\b\|type header_pattern = \|type button_tab = \|type text_multi = " "C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game/gui"`
Expected: at least one hit for each of the seven names. Fix any name with no hit before continuing.

- [ ] **Step 4: Validate**

Run: `python -I tools/validate.py`
Expected: no new reports. The loc keys from Task 1 are now all referenced; any "unused localization" report about them must be gone.

- [ ] **Step 5: Update CLAUDE.md Systems section**

Append under `## Systems` in `CLAUDE.md`:

```
- **Artificery tab:** HUD main tab below Situations (`gui/hud.gui`, generated) shown when the player passes
  `can_use_artificery_trigger` (gnome race, Gnomish Ingenuity culture, exactly one academy) via scripted GUI
  `aov_artificery_available`. Opens `gui/aov_window_artificery.gui` (scripted widget, variable
  `aov_artificery_window`) with Factions/Inventions tabs (variable `aov_artificery_tab`, unset = Factions);
  both tab bodies are placeholders until the factions and inventions systems are built.
```

- [ ] **Step 6: Commit (after the user has OK'd commits)**

```bash
git add gui/aov_window_artificery.gui gui/scripted_widgets/aov_scripted_widgets.txt CLAUDE.md
git commit -m "Add Artificery window with Factions and Inventions tabs"
```
(Same `CLAUDE.md` staging note as Task 2.)

---

### Task 4: In-game verification

Tiger does not validate GUI layout or bindings, so this is the real test. Done by the user, or with the `paradox-ai-modding:ck3-playtest` skill if the user grants permission to operate the game. Record each result as pass/fail with a note.

**Files:** none (fixes found here go back to the task that owns the file).

- [ ] **Step 1: Launch** the playset with Anbennar, then Anbennar Overhaul. After loading a save, check `logs/error.log` for lines mentioning `aov_`, `hud.gui` or `aov_window_artificery`. Expected: none.
- [ ] **Step 2: Eligible ruler.** Play a gnome ruler of a gnomish culture; in the console run `add_building artificer_academy_01` in a domain barony if none exists (or build one). Expected: the Artificery tab appears directly below Situations, with the placeholder icon and "Artificery" tooltip.
- [ ] **Step 3: Ineligible rulers.** Expected the tab is hidden for: a non-gnome ruler of a gnomish culture (`remove_trait race_gnome` and add another race trait, or play such a character); a gnome with no academy; a gnome holding two academies.
- [ ] **Step 4: Losing eligibility while open.** Open the window, then remove the academy (or add a second one). Expected: the window and the tab both disappear.
- [ ] **Step 5: Open/close.** Click the tab: window opens on the right like Military, button shows pressed. Click again: closes. Open and use the header close button: closes, button no longer pressed.
- [ ] **Step 6: Tabs.** First open shows Factions with its placeholder. Click Inventions: body switches. Click Factions: back. Close and reopen: the last selected tab is kept for the session.
- [ ] **Step 7: Vanilla tab interplay.** With Artificery open, click Military. Expected: Military shows, Artificery is hidden, no overlap. Close Military: Artificery reappears (its variable is still set); this matches the spec. If instead the two overlap, `IsRightWindowOpen` does not cover that view: apply the spec's Risks fallback (add `onclick = "[CloseGameView( '<view>' )]"` lines for each vanilla main-tab view to `BLOCK` in the generator, regenerate) and retest.
- [ ] **Step 8: UI scale.** Repeat Step 5 at a different UI scale in settings. Expected: the tab stays in the column and the window frame matches Military's.

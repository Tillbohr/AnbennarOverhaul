# Artificery tab — shell design

Date: 2026-10-08. Status: approved in chat, awaiting written-spec review.

## Goal

Add an **Artificery** main tab to the HUD tab bar (the column with Realm, Military, Situations, ...) that
opens an Artificery window with two toggleable tabs, **Factions** and **Inventions**. This spec covers only
the shell: the button, who sees it, the window and its tab switching. The inventions system (research and
selection) and the artificer factions system get their own specs later and fill in the two tab bodies.

## Decisions taken

| Question | Decision |
|---|---|
| Scope of this spec | Shell only; inventions and factions are separate later specs |
| How the button is added | Generated full-file `gui/hud.gui` override, rebuilt by a script (CLAUDE.md rule 4) |
| Where in the tab bar | Directly below the Situations tab (`tab_situation`), above the Royal Court button |
| "Is a gnome" | The ruler has the `race_gnome` trait (not culture heritage) |
| Academy requirement | Existing `has_enabled_artificer_academy_trigger`: exactly one academy in the domain |
| "Player or AI" | The UI is player-only; the shared eligibility trigger is what later AI logic reuses |

## Eligibility

New scripted trigger in `common/scripted_triggers/aov_artificer_triggers.txt`, character scope:

```
can_use_artificery_trigger = {
	has_trait = race_gnome
	culture = { has_cultural_tradition = tradition_gnomish_ingenuity }
	has_enabled_artificer_academy_trigger = yes
}
```

A ruler holding two or more academies has them all disabled, so they also lose the tab until they are back
to one. A ruler who loses their academy, culture tradition or gnome race loses the tab immediately; the
window hides with it.

New scripted GUI in `common/scripted_guis/aov_artificery_sgui.txt`:

```
aov_artificery_available = {
	scope = character
	is_shown = { can_use_artificery_trigger = yes }
}
```

The GUI reads eligibility only through this scripted GUI, evaluated with the player as root:
`[GetScriptedGui('aov_artificery_available').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]`.

## HUD button: generated `gui/hud.gui`

### Generator: `tools/build_hud_override.py`

Modelled on `tools/build_holdings_override.py`.

- Source file: Anbennar's `gui/hud.gui` if it exists (it does not today), otherwise the game's
  `game/gui/hud.gui`. The game path defaults to the Steam install path in CLAUDE.md and can be passed as an
  argument.
- Finds the line `name = "tab_situation"`, walks back to the `widget_hud_main_tab = {` that opens that
  widget, brace-matches to its closing brace, and inserts the Artificery widget after it.
- The inserted block is wrapped in `# Anbennar Overhaul` begin/end comment lines; a two-line header at the
  top of the file says it is generated and must not be edited by hand.
- Preserves the source's BOM and line endings.
- Exits with an error (writes nothing) if the anchor is missing, braces do not balance, or the block is
  already present in the source.
- Output: `gui/hud.gui` in this submod.

### Inserted widget

```
widget_hud_main_tab = {
	name = "tab_aov_artificery"
	visible = "[GetScriptedGui('aov_artificery_available').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"

	blockoverride "maintab_button"
	{
		texture = "<placeholder maintab texture>"
		onclick = "[GetVariableSystem.Toggle( 'aov_artificery_window' )]"
		tooltip = "AOV_ARTIFICERY_BUTTON"
		down = "[GetVariableSystem.Exists( 'aov_artificery_window' )]"
	}
}
```

- Icon: no artificery art exists yet. The button points at an existing vanilla
  `gfx/interface/skinned/hud_maintab/*.dds` texture as a placeholder, chosen during implementation to be
  visually distinct from its neighbours. Swapping in custom art later means adding a 45x45
  `gfx/interface/skinned/hud_maintab/aov_maintab_artificery.dds` and changing one path in the generator.
- No keyboard shortcut.

## Window

### Files

- `gui/aov_window_artificery.gui`: defines the window widget `aov_artificery_window`.
- `gui/scripted_widgets/aov_scripted_widgets.txt`: `gui/aov_window_artificery.gui = aov_artificery_window`.

The window is a scripted widget, not instanced in `hud.gui`, so the generated override contains only the
button.

### Frame and visibility

- Same frame as the vanilla main-tab windows (see `game/gui/window_military.gui`): `parentanchor = top|right`,
  `layer = windows_layer`, `using = Window_Size_MainTab`, show/hide states with `Window_Position_MainTab` /
  `Window_Position_MainTab_Hide`, `Window_Background` and `Window_Margins`.
- Visible when all three hold:
  1. `GetVariableSystem.Exists( 'aov_artificery_window' )`
  2. the player is eligible (the same scripted-GUI check as the button)
  3. `Not( IsRightWindowOpen )`, so opening a vanilla main tab such as Military covers it instead of
     overlapping. Implementation must confirm in game that `IsRightWindowOpen` is true for vanilla main-tab
     windows and false while only the Artificery window is open; if it is not, use the alternative listed
     under Risks.

### Contents

- Header: title "Artificery" and a close button that runs `GetVariableSystem.Clear( 'aov_artificery_window' )`.
- Tab row: two buttons, **Factions** and **Inventions**, in the vanilla tab-button style.
  - Factions: `onclick = "[GetVariableSystem.Clear( 'aov_artificery_tab' )]"`,
    `down = "[Not( GetVariableSystem.Exists( 'aov_artificery_tab' ) )]"`.
  - Inventions: `onclick = "[GetVariableSystem.Set( 'aov_artificery_tab', 'inventions' )]"`,
    `down = "[GetVariableSystem.HasValue( 'aov_artificery_tab', 'inventions' )]"`.
  - Factions is the default because an unset variable means Factions.
- Body: one container per tab, shown by the same conditions. Each holds a single localized placeholder line
  that the later specs replace.

### Localization (`localization/english/aov_artificery_l_english.yml`)

| Key | Text |
|---|---|
| `AOV_ARTIFICERY_BUTTON` | Artificery |
| `AOV_ARTIFICERY_WINDOW_TITLE` | Artificery |
| `AOV_ARTIFICERY_TAB_FACTIONS` | Factions |
| `AOV_ARTIFICERY_TAB_INVENTIONS` | Inventions |
| `AOV_ARTIFICERY_FACTIONS_PLACEHOLDER` | The artificer factions will be shown here. |
| `AOV_ARTIFICERY_INVENTIONS_PLACEHOLDER` | Inventions will be researched here. |

## Documentation updates

- CLAUDE.md "Generated files" table: add `gui/hud.gui` and its generator.
- CLAUDE.md "Updating to a new Anbennar version": rerun `build_hud_override.py`. Also rerun it after every
  CK3 patch, since its source is the vanilla file.
- CLAUDE.md "Systems": a line for the Artificery tab and its eligibility trigger.

## Out of scope

Inventions logic, factions logic, AI behaviour, keyboard shortcut, custom icon art.

## Verification

- Generator: diff the output against the source file; the only differences are the header and the inserted
  block. Running it twice gives the same output.
- `python -I tools/validate.py` reports nothing new (tiger checks the trigger, scripted GUI and loc keys; it
  does not validate GUI layout).
- In game:
  - The tab appears directly below Situations for an eligible gnome ruler.
  - It is hidden for a non-gnome ruler of a gnomish culture, for a gnome with no academy, and for a gnome
    holding two academies.
  - Clicking it opens and closes the window; the button shows as pressed while open.
  - The Factions/Inventions buttons switch the body; Factions shows on first open.
  - Opening Military while Artificery is open shows Military without overlap.
  - The close button closes the window.

## Risks

- **Other mods overriding `hud.gui`:** they conflict with this file; the later-loaded one wins. Accepted.
- **CK3 patches** change `hud.gui`; rerun the generator after each patch. A renamed `tab_situation` makes the
  generator fail loudly rather than misplace the tab.
- **`IsRightWindowOpen` does not behave as expected:** fall back to having the Artificery button's onclick
  close the vanilla main-tab views by name with `CloseGameView` before toggling, and accept that opening a
  vanilla tab while Artificery is open draws on top of it.

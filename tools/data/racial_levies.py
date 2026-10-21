"""Data for tools/build_racial_levies.py: the racial levy shares and which levy_size sources it corrects.

A racial holding's levy size is 1 + base + S - f x S = share x (1 + S), where S is the holding's summed levy_size
from the covered sources and f is the race's fraction below (spec: docs/superpowers/specs/2026-10-21-racial-armies-design.md).
"""

# race -> f: the part of every levy bonus a holding of that race must not receive (kobolds get half extra).
# The race is the owner culture's heritage parameter aov_racial_levy_<race> (zz_aov_racial_heritages.txt).
RACES = {"elven": 0.75, "dwarven": 0.40, "gnomish": 0.50, "kobold": -0.50}

STEP = 0.05  # one correction tier per 0.05 of S
S_MIN = -1.00  # S is clamped to this range; a holding outside it gets the end tier
S_MAX = 3.00

# Folders under common/ whose levy_size is corrected. The value says which object key the condition names:
# "top" = the top-level block, "nested" = the block one level down (a law inside its law group).
CLASSIFIED = {
    "buildings": "top",
    "culture/traditions": "top",
    "culture/innovations": "top",
    "culture/pillars": "top",
    "religion/doctrine_types": "top",
    "religion/holy_site_types": "top",
    "governments": "top",
    "laws": "nested",
    "traits": "top",
}

# Folders whose levy_size is left alone; each is temporary or too narrow to cause lasting drift.
IGNORED = {
    "modifiers": "event, activity and festival modifiers: temporary",
    "epidemics": "temporary",
    "domiciles": "estate buildings of landless and administrative rulers, not holdings",
    "council_positions": "depends on who sits on the council",
    "court_positions": "depends on who holds the position",
    "house_aspirations": "house-level, narrow",
    "confederation_types": "confederation members only",
    "subject_contracts": "special contracts, narrow",
    "scripted_effects": "not a modifier definition",
    "script_values": "not a modifier definition",
    "on_action": "not a modifier definition",
    "character_interactions": "not a modifier definition",
    "dynasty_perks": "dynasty-wide, narrow",
    "lifestyle_perks": "one character, narrow",
    "important_actions": "not a modifier definition",
}

# vassal_levy_contribution_mult: the heritages cut what vassals send a racial ruler by the same f, and these are the
# lasting sources of that modifier the ruler-level correction takes back (character scope).
CONTRIBUTION_CLASSIFIED = {
    "laws": "nested",
    "culture/traditions": "top",
    "culture/innovations": "top",
    "culture/pillars": "top",
    "religion/doctrine_types": "top",
    "religion/holy_site_types": "top",
    "governments": "top",
    "lifestyle_perks": "top",
    "dynasty_perks": "top",
    "traits": "top",
    "buildings": "top",
}
CONTRIBUTION_IGNORED = {k: v for k, v in IGNORED.items() if k not in CONTRIBUTION_CLASSIFIED}

# Keys whose levy_size is the racial base itself, never corrected.
OWN_KEYS = {"heritage_elven", "heritage_dwarven", "heritage_gnomish", "heritage_kobold"}

RACE_NAMES = {"elven": "Elven", "dwarven": "Dwarven", "gnomish": "Gnomish", "kobold": "Kobold"}
SHARE_TEXT = {
    "elven": "a quarter", "dwarven": "three fifths", "gnomish": "half", "kobold": "one and a half times",
}

"""Hand-made fields for the Cannor great projects; kept verbatim across re-imports of cannor.py.

HAND[eu4_key] may replace barony, category, desc, levels, gate, gate_desc and notes wholesale, and may hold
`tiers`: a list of 3 dicts (block name -> {ck3 key: value}) merged over the imported tier blocks key by key
(a value of None removes the key).
"""

HAND = {}

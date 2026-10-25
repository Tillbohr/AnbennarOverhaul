"""Data for tools/build_rie_elves.py: Realms in Exile's elven holding and elf buildings, renamed for Anbennar as the
Elven Haven (spec docs/superpowers/specs/2026-10-25-rie-elves-design.md).

Paths are relative to RiE's mod folder; edit the data, then rerun the generator."""

from data import rie_dwarves as _dwarves

RIE_BUILDINGS_FILE = "common/buildings/lotr_buildings/lotr_elven_buildings.txt"
RIE_SETTLEMENT_FILE = "common/buildings/lotr_buildings/lotr_elven_settlement_holdings.txt"
RIE_HOLDINGS_FILE = "common/holdings/lotr_holdings.txt"
RIE_TRIGGERS_FILE = "common/scripted_triggers/lotr_scripted_triggers/lotr_building_requirement_triggers.txt"

# Included building lines -> RiE's level count (spec Section 3), in the Haven's build list order.
LINES = {
    "elven_agriculture": 7, "elven_port": 7, "elven_mine": 7, "elven_forestry": 7, "elven_hunting_grounds": 7,
    "elven_markets": 7, "elven_forges": 7, "elven_barracks": 7, "elven_fletchers": 7, "elven_stables": 7,
    "tree_flet": 7, "elven_library": 5, "elven_guild": 5, "elven_embassy": 5, "elven_mustering_grounds": 5,
    "elven_sanctuary": 5, "elven_citadel": 5, "hall_of_lords": 2, "elven_armament": 2,
    "hall_of_music_and_tales": 3, "crafting_enclaves": 3, "sentinel_keeps": 3, "warriors_enclave": 3,
    "sanctuary_groves": 3,
}
SETTLEMENT_LEVELS = 7

# Haven level -> the castle level whose models (tools/build_holding_models.py output) it shows.
HAVEN_ASSET_BAND = {1: "castle_01", 2: "castle_01", 3: "castle_02", 4: "castle_02", 5: "castle_03", 6: "castle_03",
                    7: "castle_04"}
# Castle level (building_requirement_castle_city_church LEVEL) -> the Haven level that counts as it.
CASTLE_EQUIVALENT = {1: 1, 2: 3, 3: 5, 4: 7}
# Elf building_gfx key -> (picture for levels 1-5, picture for levels 6-7), RiE's refuge illustrations.
ILLUSTRATIONS = {
    "aov_high_elf_building_gfx": ("gfx/interface/illustrations/holding_types/refuge_calaquendi.dds",
                                  "gfx/interface/illustrations/holding_types/refuge_calaquendi2.dds"),
    "aov_wood_elf_building_gfx": ("gfx/interface/illustrations/holding_types/refuge_sindarin.dds",
                                  "gfx/interface/illustrations/holding_types/refuge_sindarin.dds"),
}
# RiE interface icon -> ours, both under gfx/interface/icons/ (the holding tab icon, holding_types_tab/<holding>.dds).
UI_ICONS = {"holding_types_tab/elven_holding.dds": "holding_types_tab/elven_holding.dds"}

# --- conversion (aov_convert_to_elven_haven_effect) ---
LEVEL_MAP = {"castle_01": 1, "castle_02": 3, "castle_03": 5, "castle_04": 7, "tribe_01": 1, "tribe_02": 2}
# Vanilla building line -> the elven line that replaces it at the same level.
BUILDING_MAP = {
    "cereal_fields": "elven_agriculture", "farm_estates": "elven_agriculture", "pastures": "elven_agriculture",
    "hill_farms": "elven_agriculture", "hunting_grounds": "elven_hunting_grounds", "logging_camps": "elven_forestry",
    "quarries": "elven_mine", "common_tradeport": "elven_port", "barracks": "elven_barracks",
    "military_camps": "elven_barracks", "regimental_grounds": "elven_stables",
}
# Overhaul buildings a Haven lists too and a conversion keeps (with the 15 RiE mines).
KEEP_ON_CONVERSION = ("artificer_academy_01", "battlemage_academy_01")
MINE_BUILDINGS = _dwarves.MINE_BUILDINGS

# --- rewrite rules (tools/rie_dwarf_rewrite.rewrite_block with rules=this module) ---
TOKEN_RENAMES = {
    "is_elf": "is_elvish_culture",
    "building_requirement_elven": "aov_rie_elf_holder_trigger",
    "building_elven_agriculture_requirement_terrain": "aov_rie_elven_agriculture_terrain_trigger",
    "building_elven_hunting_grounds_requirement_terrain": "aov_rie_elven_hunting_grounds_terrain_trigger",
    "building_elven_tree_flats_requirement_terrain": "aov_rie_elven_tree_flet_terrain_trigger",
}
# RiE trigger -> our trigger: bodies copied from RIE_TRIGGERS_FILE, terrains Anbennar and the game lack dropped.
COPIED_TRIGGERS = {rie: ours for rie, ours in TOKEN_RENAMES.items() if ours.endswith("_terrain_trigger")}
# Regexes of whole statements to remove (a block left empty goes with them).
DROP_STATEMENTS = (
    r"is_valinor_maiar_character\s*=\s*yes",
    r"building_requirement_tribal\s*=\s*no",  # tribal elves (the Deepwoods) may raise their Havens
    r"building_requirement_tribal_holding_in_county\s*=\s*yes",
    r"county_is_elven\s*=\s*yes",
    r"is_wastelands\s*=\s*no",
    r"add_elven_hope_effect\s*=\s*\{[^{}]*\}",
    r"has_dynasty_perk\s*=\s*lotr_\w+",
)
# (regex of a whole statement or block, its replacement; backreferences allowed), matched over code.
BLOCK_REPLACEMENTS = (
    # RiE's hope gate (its elven hope mechanic): removed whole, or it would become "only when the top liege is not an elf".
    (r"OR\s*=\s*\{\s*scope:holder(?:\.top_liege)?\s*=\s*\{\s*has_\w+_hope_or_higher\s*=\s*yes\s*\}"
     r"(?:\s*scope:holder\.top_liege\s*=\s*\{\s*(?:has_\w+_hope_or_higher\s*=\s*yes|is_elf\s*=\s*no)\s*\})*\s*\}", ""),
    # RiE's guild needs one Haven level less with its next_level_elf_guild parameter, which Anbennar lacks.
    (r"trigger_if\s*=\s*\{\s*limit\s*=\s*\{\s*NOT\s*=\s*\{\s*culture\s*=\s*\{\s*has_cultural_parameter\s*=\s*"
     r"next_level_elf_guild\s*\}\s*\}\s*\}\s*(has_building_or_higher\s*=\s*elven_settlement_\d\d)\s*\}\s*"
     r"trigger_else\s*=\s*\{\s*culture\s*=\s*\{\s*has_cultural_parameter\s*=\s*next_level_elf_guild\s*\}\s*"
     r"has_building_or_higher\s*=\s*elven_settlement_\d\d\s*\}", r"\1"),
    # RiE's high elves (Calaquendi) are Anbennar's moon and sun elves.
    (r"has_cultural_pillar\s*=\s*heritage_calaquendi", "OR = { this = culture:moon_elvish this = culture:sun_elvish }"),
)
DROP_BLOCKS = ("province_dynasty_modifier",)
DROP_EFFECT_DESC = r"_artifact_crafting_buff$"

# --- localization ---
CONCEPT_REPLACEMENTS = dict(_dwarves.CONCEPT_REPLACEMENTS, elves="elves", elven="elven", elvish="elvish",
                            elf="elf", ardaconcept="Halann")
LOC_OVERRIDES = {}
FORBIDDEN_LORE = (_dwarves.FORBIDDEN_LORE + r"|L[oó]rien|Ulmo|Orom[eë]|Valinor|F[eë]anor|[Tt]elain|\bTalan\b|"
                  r"Sindar|Noldor|Calaquendi|M[ií]rdain|Onodrim|Laew|Arphen|Hador|Ngelaidh|Eldar|Silvan|Nandor")

# The holding's own keys (as the dwarven hold has them).
HOLDING_LOC = {
    "elven_holding": "Elven Haven",
    "elven_holding_concept_key": "Elven Haven",
    "elven_holding_build_speed": "Elven Haven [buildings|E] Construction Time",
    "elven_holding_build_gold_cost": "Elven Haven [buildings|E] Construction Cost",
    "elven_holding_build_piety_cost": "Elven Haven [buildings|E] Piety Cost",
    "elven_holding_build_prestige_cost": "Elven Haven [buildings|E] Prestige Cost",
    "elven_holding_holding_build_speed": "Elven Haven [holding|E] Construction Time",
    "elven_holding_holding_build_gold_cost": "Elven Haven [holding|E] Construction Cost",
    "elven_holding_holding_build_piety_cost": "Elven Haven [holding|E] Piety Cost",
    "elven_holding_holding_build_prestige_cost": "Elven Haven [holding|E] Prestige Cost",
}


def _line(line: str, type_name: str, type_desc: str, *levels) -> dict:
    """NAMES entries of one line: building_type_<line>_01 and every <line>_NN as (name, description)."""
    out = {f"building_type_{line}_01": (type_name, type_desc)}
    out.update({f"{line}_{n:02d}": level for n, level in enumerate(levels, 1)})
    return out


# key -> (name, description): the Haven levels, every level of every line and each line's type (spec Section 5).
NAMES = {
    "building_type_elven_settlement_01": (
        "Elven Haven", "A haven of the elves, the long-lived exiles of fallen Aelantir, raised among gardens and old "
        "trees and kept by folk who measure their memories in centuries."),
    "elven_settlement_01": (
        "Haven Glade", "A handful of elven families have made this glade their home. Their halls are few, but the "
        "flowers bloom out of season and the birds sing at every hour."),
    "elven_settlement_02": (
        "Flowering Haven", "Elven dwellings now dot the land around the haven, linked by shaded paths. Travellers "
        "speak of lanterns hung in the branches and music in the evenings."),
    "elven_settlement_03": (
        "Haven Hold", "The haven has grown into a hold of white stone and living wood, with estates, libraries and "
        "fountained courts for the elves who gather here."),
    "elven_settlement_04": (
        "Renowned Haven Hold", "The name of this hold is known throughout the region. More elves arrive every year, "
        "drawn by its halls and the patience of its lords."),
    "elven_settlement_05": (
        "High Haven Hold", "Tall towers and slender walls ring this great hold. Within lie works of peerless craft and "
        "lore carried across the sea from Aelantir."),
    "elven_settlement_06": (
        "Haven City", "A city of the elves, its spires rising above the trees. Few places in Cannor shelter so many of "
        "the Fair Folk, and fewer still hold such learning."),
    "elven_settlement_07": (
        "Shining Haven City", "Unrivalled in size and majesty, this haven is the pride of the elves in exile, an echo "
        "of the cities that stood in Aelantir before its ruin."),
}
NAMES.update(_line(
    "elven_agriculture", "Elven Gardens",
    "The elves tend the land rather than master it. Their gardens and orchards yield more than human fields while "
    "seeming hardly to be farmed at all.",
    ("Foraging Bands", "Elven families range the countryside, gathering what the land gives freely. There is little "
     "here that a human farmer would call agriculture."),
    ("Homestead Gardens", "Small gardens surround the elven homesteads, planted with herbs, fruit and grain in careful "
     "harmony."),
    ("Terraced Gardens", "Gardens climb the slopes in green terraces, watered by channels the elves cut and keep with "
     "great care."),
    ("Silverleaf Orchards", "Orchards of pale-barked trees bear fruit through the long seasons, tended by gardeners "
     "who planted them generations ago."),
    ("Grand Gardens", "The gardens of the haven are a wonder of the region, as beautiful as they are bountiful."),
    ("Elven Vineyards", "Vines planted by long-dead hands yield wines that human nobles pay fortunes to taste."),
    ("Gardens of Lost Aelantir", "The gardeners grow plants whose seeds crossed the sea from Aelantir. In their "
     "shade the elves remember a homeland most of them never saw."),
))
NAMES.update(_line(
    "elven_port", "Elven Harbour",
    "The elves came to Cannor across the sea, and they have not forgotten how to build ships or the harbours "
    "that shelter them.",
    ("Fisher Flotillas", "Fishing boats put out from wooden wharves along the shore, their sails painted with the "
     "sigils of elven families."),
    ("Stone Quays", "The old wharves have given way to quays of fitted stone, built to outlast the elves who laid "
     "them."),
    ("Merchant Wharves", "Merchant ships from human ports now tie up beside elven vessels to trade for fine goods."),
    ("Elven Drydocks", "Swan-prowed ships are built and mended here by shipwrights who learned their craft over "
     "centuries."),
    ("Harbourmaster's Spire", "A slender tower watches over the harbour, its lamp guiding ships in through fog and "
     "storm."),
    ("Sea-Gates", "Great gates of stone and bronze guard the harbour mouth, opened only for friends of the haven."),
    ("Harbour of the Crossing", "The elves say this harbour is built as the havens of Aelantir were, so that every "
     "ship that leaves it might one day find the way home."),
))
NAMES.update(_line(
    "elven_mine", "Elven Quarries",
    "Elves take stone and ore from the earth sparingly, closing each wound in the land when they are done.",
    ("Stone Cuttings", "Stone is cut from easy outcrops for the haven's buildings, and the scars are planted over."),
    ("Shallow Ore Pits", "Shallow pits yield iron and copper for the haven's smiths."),
    ("Watermills", "Watermills grind ore and saw stone, sparing the labour of many hands."),
    ("Great Quarries", "Larger quarries supply the white stone of the haven's halls."),
    ("Deep Mines", "The elves have followed the richest veins deep into the earth, shoring each tunnel with care."),
    ("Vast Quarries", "Whole hillsides yield their stone, yet the elves leave the land as green as they found it."),
    ("Songs of Stone", "The miners sing to the rock as they work. Dwarves scoff at the practice, but the elves seldom "
     "lose a tunnel to collapse."),
))
NAMES.update(_line(
    "elven_forestry", "Elven Woodwardens",
    "Elves harvest timber as a gardener prunes a tree: a little at a time, and always with an eye to what will "
    "grow back.",
    ("Careful Felling", "A few trees are felled where they will not be missed, and a sapling is planted for each."),
    ("Forester Bands", "Bands of foresters tend the woods, felling old and fallen timber for the haven's needs."),
    ("Wardens of the Wood", "The haven's lords appoint wardens to keep the woods, deciding which trees may be cut."),
    ("Speech of the Trees", "The foresters claim to know which trees are willing to be felled. Whatever the truth, the "
     "woods around the haven thrive."),
    ("Forest Reserves", "Great reserves of forest are kept for the haven's future, felled only in the direst need."),
    ("Teachings of the Fey", "Elven foresters have learned from the fey of the deep woods how to coax trees to grow "
     "tall and straight in a handful of years."),
    ("Cultivated Wildwoods", "The forests around the haven seem wild, yet every tree in them was planted or tended "
     "by elven hands."),
))
NAMES.update(_line(
    "elven_hunting_grounds", "Elven Hunting Grounds",
    "Elven hunters take what the land can spare and no more, and the game of their forests never dwindles.",
    ("Wildland Hunting", "Hunters roam the wilds alone or in pairs, taking what game they find."),
    ("Hunting Bands", "Bands of hunters range farther afield, bringing back venison and furs for the haven."),
    ("Hunt Masters", "Hunt masters decide where and when the bands may hunt, so that no herd is thinned too far."),
    ("Trappers and Trackers", "Trappers and trackers of rare skill keep the haven supplied with furs and feathers."),
    ("Keepers of the Herds", "The elves tend the wild herds as a shepherd tends his flock, culling only the old and "
     "the weak."),
    ("Hunters' Lodge", "A great lodge houses the haven's hunters, where the young learn the old ways of bow and "
     "trail."),
    ("The Wild Hunt", "Once a year the haven rides out on a great hunt through the forests, horns sounding under "
     "the moon, as the elves have done since before they crossed the sea."),
))
NAMES.update(_line(
    "elven_markets", "Elven Markets",
    "Elven goods are rare and fine, and the markets where they are sold draw merchants from far beyond the "
    "haven.",
    ("Gathering Markets", "Elves gather now and then to trade their crafts and share news, with little thought of "
     "profit."),
    ("Seasonal Fairs", "Fairs at the turning of the seasons draw human merchants hoping to buy elven wares."),
    ("Permanent Markets", "Permanent stalls and shaded arcades now line the haven's market square."),
    ("Linked Markets", "The haven's markets trade with those of other havens, moving goods along quiet roads."),
    ("Great Storehouses", "Great storehouses hold the haven's wealth of wine, cloth and craft against lean years."),
    ("Regional Markets", "The haven is the market of its region, where human and elf alike come to buy and sell."),
    ("Grand Markets of the Havens", "The haven's markets are famed across Cannor for goods found nowhere else, and "
     "their merchants are as patient as they are shrewd."),
))
NAMES.update(_line(
    "elven_forges", "Elven Forges",
    "Elven smiths work slowly, but what they make outlasts the hands of any human smith.",
    ("Elven Smithies", "Smiths scattered through the land make the nails, tools and horseshoes the haven needs."),
    ("Communal Forges", "The haven's smiths share forges, passing their craft from master to apprentice."),
    ("Apprentice Forges", "Young smiths train for decades before they may call themselves masters."),
    ("Grand Forges", "Great forges turn out blades and mail of a quality few human smiths can match."),
    ("Starmetal Forges", "The smiths work metal that falls from the night sky, forging blades that gleam even in "
     "darkness."),
    ("Precursor Techniques", "The smiths have recovered techniques of the precursor elves of Aelantir, lost for "
     "centuries."),
    ("Hall of the Master Smiths", "The greatest smiths of the elves work here, and their masterpieces are sought "
     "by kings."),
))
NAMES.update(_line(
    "elven_barracks", "Elven Barracks",
    "Elves who have lived for centuries have had time to master the arts of war, and they train their warriors "
    "with the same patience they give to any craft.",
    ("Militia Grounds", "Elven militia drill here in their free hours, learning the art of war."),
    ("Militia Armouries", "An armoury keeps weapons ready for the militia when the haven is threatened."),
    ("Warden Barracks", "Barracks house the haven's wardens, its standing guard."),
    ("Warden Storehouses", "Storehouses keep the wardens supplied through long campaigns."),
    ("Grand Barracks", "Grand barracks house a host of elven warriors trained over decades."),
    ("Barracks Complex", "A complex of barracks, yards and armouries keeps the haven's host ready for war."),
    ("Hall of the Host", "The haven's warriors gather in a great hall hung with the banners of wars fought before "
     "most humans' grandfathers were born."),
))
NAMES.update(_line(
    "elven_fletchers", "Elven Fletchers",
    "The elven bow is famed across Cannor, and the fletchers who make bow and arrow are honoured among the elves.",
    ("Hearth Fletchers", "Archers make their own arrows at home. The work is unorganised but sufficient."),
    ("Guard Fletchers", "Fletchers serve the haven's guard, keeping its archers supplied."),
    ("Spiral-Fletched Arrows", "The fletchers set their feathers in a spiral, so their arrows fly farther and "
     "truer."),
    ("Song-Shaped Bows", "Bowyers shape their bows to old songs, and claim the bows remember the tune."),
    ("Elf-Hair Bowstrings", "Strings woven from elven hair are said never to fray or snap in the cold."),
    ("Silvered Arrows", "Arrowheads chased with silver are made for the haven's finest archers."),
    ("Great Arrow Stores", "Great stores of arrows are kept against war, enough to darken the sky."),
))
NAMES.update(_line(
    "elven_stables", "Elven Stables",
    "Elven riders and their mounts are bred for grace and speed, and few human knights can catch them.",
    ("Local Riders", "The haven's folk have taken to horseback, and some ride better than any human."),
    ("Regional Stables", "Stables across the region breed horses for the haven's riders."),
    ("War Stables", "Horses are bred and trained for war, to carry elven riders into battle."),
    ("Armoured Riders", "The haven's riders now go to war in light, fine-wrought armour."),
    ("Farrier Smithies", "Smithies beside the stables shoe and armour the haven's horses."),
    ("Aelantiri Bloodlines", "The haven's horses are said to descend from steeds brought from Aelantir, and they "
     "are the swiftest in the land."),
    ("The Swift Host", "The haven's cavalry is famed for striking from nowhere and vanishing before its enemies can "
     "answer."),
))
NAMES.update(_line(
    "tree_flet", "Canopy Watchposts",
    "Platforms built high in the branches let the elves watch over their woods unseen, and rain arrows on any foe "
    "who passes beneath.",
    ("Canopy Lookout", "A single platform hidden high in the canopy keeps watch over the forest roads."),
    ("Canopy Garrison", "Platforms in the branches house a small garrison of archers."),
    ("Canopy Armoury", "An armoury in the treetops keeps bows and arrows ready above the forest floor."),
    ("Canopy Forge", "Even a forge has been raised in the branches, its smoke lost among the leaves."),
    ("Canopy Storehouses", "Storehouses in the canopy hold food and arrows for a long siege."),
    ("Canopy Town", "A whole town of bridges and platforms spans the treetops, home to many of the haven's folk."),
    ("City in the Boughs", "A city of lanterns and walkways hangs in the great trees, invisible from the ground "
     "until one is already within it."),
))
NAMES.update(_line(
    "elven_library", "Elven Library",
    "Elves remember much, but they write down more. Their libraries hold histories that human scholars thought "
    "lost.",
    ("Private Collections", "The haven's nobles have begun to gather their collections in a single building."),
    ("Ordered Library", "Librarians now catalogue the collection and copy its rarest works."),
    ("Specialised Wings", "Wings of the library are given over to history, magic, medicine and the stars."),
    ("Grand Library", "The library is among the greatest in Cannor, and scholars travel far to read in it."),
    ("Library of the Long Memory", "The library holds records of Aelantir and of the elves' first years in Cannor, "
     "kept by scholars who remember some of it themselves."),
))
NAMES.update(_line(
    "elven_guild", "Elven Guilds",
    "Elven crafters band together in guilds that keep the secrets of their crafts for centuries.",
    ("Hunters' Guild", "The haven's hunters and trappers have organised into a guild, rare among the elves."),
    ("Woodcarvers' Guild", "Woodcarvers band together to keep their craft, and their work adorns the haven's halls."),
    ("Stonewrights' Guild", "The stonewrights who shape the haven's halls keep their methods within their guild."),
    ("Glassmiths' Guild", "Glassmiths make coloured glass for the haven's windows and lamps."),
    ("Scribes' Guild", "The scribes' guild copies books and keeps the haven's records in a flowing hand."),
))
NAMES.update(_line(
    "elven_embassy", "Elven Gathering Halls",
    "The elves gather to sing, debate and celebrate, and their gatherings draw guests from near and far.",
    ("Hearth Hall", "A hall with a great hearth where minstrels play and neighbours meet."),
    ("Open-Air Forum", "A forum under the trees where the haven's folk debate its affairs."),
    ("Hall of Debate", "A hall where elves argue law and philosophy for days on end."),
    ("Festival Grounds", "Grounds for the haven's festivals, which last for weeks and draw guests from far away."),
    ("Elven Amphitheatre", "A great amphitheatre where plays and songs centuries old are performed."),
))
NAMES.update(_line(
    "elven_mustering_grounds", "Elven Musters",
    "When war comes, the haven calls its folk to arms, and every elf has had long years to learn the bow and "
    "blade.",
    ("Sparse Summons", "Riders carry the summons through the land, gathering what warriors they can."),
    ("Regional Camps", "Camps across the region train the haven's levies."),
    ("Warden Musters", "The haven's wardens muster and drill the levies each season."),
    ("Free Companies", "Companies of elven warriors serve the haven under captains of their own choosing."),
    ("Call of the Havens", "Beacons on the hills carry the haven's call to arms through the land in a single night, "
     "and the elves answer it at once."),
))
NAMES.update(_line(
    "elven_sanctuary", "Elven Sanctuary",
    "Quiet groves and houses of healing where elves rest, mend and meditate.",
    ("Secluded Groves", "Quiet groves are tended for rest and contemplation."),
    ("Healing Sanctuaries", "Healers tend the sick and wounded in the haven's sanctuaries."),
    ("Halls of Healing Dreams", "Healers guide the sick through dreams that mend body and mind alike."),
    ("Starlit Gardens", "Gardens laid out by the stars, where the elves walk and meditate under the night sky."),
    ("Gardens of Reverie", "Gardens of such peace that even the oldest elves find rest from their long memories."),
))
NAMES.update(_line(
    "elven_citadel", "Elven Citadel",
    "Elven fortifications are slender and graceful, yet they have broken many sieges.",
    ("Grand Redoubts", "Redoubts guard every approach to the haven, allowing a long defence."),
    ("High Citadel", "A high citadel rises over the haven, a last refuge in war."),
    ("Guarded Keep", "A keep guarded day and night by the haven's wardens."),
    ("Tall Bastion", "A tall bastion of white stone from which archers command the land around."),
    ("Unbroken Fortress", "The haven's fortress has never fallen, and its defenders mean to keep it so."),
))
NAMES.update(_line(
    "hall_of_lords", "Hall of Lords",
    "Where the haven's lords hear their people and govern their lands.",
    ("Audience Hall", "Nobles, merchants, smiths and commoners petition their lord here, or the lord's steward in "
     "their absence."),
    ("Palace of Governance", "A palace of offices and halls from which the haven's lords govern their lands with "
     "unhurried care."),
))
NAMES.update(_line(
    "elven_armament", "Elven Armament",
    "The haven's armouries and roads let its host march to war at speed.",
    ("Company of the Highborn", "The haven's noble houses keep companies of warriors armed and ready."),
    ("Hall of Banners", "A hall hung with the banners of every company of the haven, its armouries ringing with "
     "hammers day and night."),
))
NAMES.update(_line(
    "hall_of_music_and_tales", "Hall of Song",
    "A great hall where the elves keep their songs and stories, some older than any human kingdom.",
    ("Hall of Song", "A tall hall where even the softest voice carries to every corner, home to the duchy's "
     "minstrels."),
    ("The Echoing Vaults", "Vaults beneath the hall hold songs written down in centuries past, sung again on high "
     "days."),
    ("Choir of the Long Years", "The hall's choir sings songs of Aelantir in voices that have practised them for "
     "centuries."),
))
NAMES.update(_line(
    "crafting_enclaves", "Masters' Enclave",
    "An enclave where the finest elven crafters work, improving the duchy's buildings and arms alike.",
    ("The Hundred Masters", "Skilled engineers and smiths work on new methods for building and arming."),
    ("Elven Masterworks", "The enclave's works are prized throughout Cannor."),
    ("Secrets of Starfire", "The masters have learned to work starmetal, making blades that never dull."),
))
NAMES.update(_line(
    "sentinel_keeps", "Sentinel Keeps",
    "Keeps and watchtowers guard the borders of the duchy against raiders and worse.",
    ("Remote Outpost", "An outpost of a few score wardens patrols the roads and wilds."),
    ("Fortified Watchtower", "A watchtower of stone keeps a constant watch over the duchy's borders."),
    ("Vigilant Wardens", "The duchy's wardens are never caught unprepared."),
))
NAMES.update(_line(
    "warriors_enclave", "Warriors' Enclave",
    "Where the duchy's warriors train in the arts of war.",
    ("Training Fields", "Arenas and yards where soldiers learn to fight and march with speed and precision."),
    ("Archery Ranges", "Long ranges where the duchy's archers practise at great distances."),
    ("Formation Drills", "The duchy's warriors drill until they move as one."),
))
NAMES.update(_line(
    "sanctuary_groves", "Sanctuary Groves",
    "Forests set aside as sanctuaries, for reflection and reverence.",
    ("Great Forest Sanctuary", "A great forest is kept as a sanctuary, alive with birdsong and the calls of deer."),
    ("Fruit Groves", "Groves of fruit trees within the sanctuary feed the duchy's folk."),
    ("Groves of Meditation", "The duchy's elves walk these groves for days in silent meditation."),
))

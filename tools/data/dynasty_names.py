"""Data for tools/build_dynasty_names.py: Anbennar dynasty names for the culture name lists that still use
placeholders.

Most Anbennar name lists ship vanilla's English dynasty names (de Bohun, de Vere, Holland, Butler, ...) marked
`#TODO - replace placeholder dynasty names`, and the gnomish and halfling lists ship vanilla's Frisian ones (Abdena,
Allena, ...). The game names a dynasty from these lists whenever a lowborn character gains land, which happens at game
start for the 118 rulers Anbennar's history leaves without a dynasty, so those rulers start with English or Frisian
names.

NAME_LISTS gives each such name list the EU4 Anbennar cultures (or culture groups) whose dynasty names it takes, in
order; names repeated across sources are kept once. EU4_DYNASTY_NAMES holds those names, imported once from EU4
Anbennar's common/cultures/anb_cultures.txt with tools/eu4_import.py culture_dynasty_names() and committed; edit them
here, not in EU4. A CK3 culture with no EU4 namesake takes its parent's or its region's names (comment on each line).
"""

# CK3 name list -> EU4 cultures and culture groups whose dynasty names it takes.
NAME_LISTS = {
    # Alenic
    "name_list_alenic": ("alenic",),
    "name_list_old_alenic": ("old_alenic", "alenic"),
    "name_list_moorman": ("moorman", "alenic"),
    "name_list_wexonard": ("wexonard",),
    "name_list_vertesker": ("vertesker", "alenic"),
    "name_list_blue_reachman": ("blue_reachman", "alenic"),
    "name_list_boundsman": ("old_alenic", "alenic"),  # no EU4 culture; Old Alenic parent
    "name_list_gawedi": ("gawedi",),
    "name_list_marrodic": ("marrodic", "alenic"),
    # Damesheader
    "name_list_damerian": ("west_damerian", "east_damerian", "anbennarian"),
    "name_list_pearlsedger": ("pearlsedger", "anbennarian"),
    "name_list_esmari": ("esmari",),  # also Faranni
    "name_list_old_esmari": ("esmari",),  # Old Esmari, Ryalani, Havoric; EU4's Havoric list is a mis-encoded copy
    "name_list_vernid": ("vernman", "heartman"),  # Old Verne, before the Vernman split
    "name_list_vernman": ("vernman", "heartman"),
    "name_list_arannese": ("arannese", "anbennarian"),
    "name_list_crownsman": ("crownsman", "ionnic"),  # also Arami
    "name_list_arbarani": ("arbarani", "dhanaenno", "anbennarian"),
    "name_list_exwesser": ("exwesser", "anbennarian"),
    # Dostanorian
    "name_list_corvurian": ("corvurian", "ourdi", "dostanorian", "dostanorian_g"),  # Corvurian, Ourdi, Dostanorian
    "name_list_cardesti": ("dostanorian_g", "ravenmarcher_d"),  # no EU4 culture
    # Escanni
    "name_list_adenner": ("adenner", "escanni"),
    "name_list_white_reachman": ("white_reachman",),
    "name_list_black_castanorian": ("black_castanorian", "escanni"),
    "name_list_marcher": ("marcher", "escanni"),
    "name_list_castellyrian": ("castellyrian", "escanni"),  # also Castanite
    "name_list_castellyrian_elvenized": ("castellyrian", "farrani_half_elf"),
    "name_list_castanorian": ("castanorian", "escanni"),  # Castanorian and its Escanni offshoots
    "name_list_old_castanorian": ("castanorian", "escanni"),
    "name_list_balmirish": ("castellyrian", "escanni"),  # no EU4 culture; Castanite parent (also Morbani)
    "name_list_patrician": ("castellyrian", "escanni"),  # no EU4 culture; Castanite parent
    "name_list_adeanic": ("adenner", "escanni"),  # EU4's Adenner holds the Adean houses (Acengard, Rohibon, Aldainé)
    # Lencori
    "name_list_lorentish": ("high_lorentish", "low_lorentish", "lencori"),
    "name_list_roilsardi": ("roilsardi", "luciander", "lencori"),
    "name_list_derannic": ("derannic", "lencori"),
    "name_list_sormanni": ("sorncosti", "sornicandi", "lencori"),  # no EU4 culture; Sorncóst neighbours
    "name_list_iochander": ("iochander", "lencori"),
    "name_list_milcori": ("lencori", "anbennarian"),  # no EU4 culture
    # Elves, dwarves, gnomes, halflings
    "name_list_moon_elven": ("elven",),
    "name_list_sun_elven": ("sun_elf", "sunrise_elf"),
    "name_list_wood_elven": ("wood_elf",),
    "name_list_dwarven": ("dwarven", "ruby_dwarf", "silver_dwarf", "stone_dwarf", "iron_dwarf", "obsidian_dwarf",
                          "quartz_dwarf", "agate_dwarf", "opal_dwarf", "lead_dwarf", "marble_dwarf", "titanium_dwarf",
                          "citrine_dwarf", "garnet_dwarf", "diamond_dwarf"),
    "name_list_gnomish": ("gnomish",),  # not delta_gnome: EU4 gave it a copy of the Kheteratan list
    "name_list_halfling": ("halfling", "bluefoot_halfling", "redfoot_halfling", "imperial_halfling",
                           "visfoot_halfling"),
    # Gnolls
    "name_list_suncrown_gnoll": ("suncrown_gnoll",),
    "name_list_sandfang_gnoll": ("sandfang_gnoll",),
    "name_list_fieldstalker_gnoll": ("fieldstalker_gnoll",),
    # Elsewhere
    "name_list_akasi": ("akasi",),  # Akasi, Deshaki, Ekhasi, Khasani
    "name_list_fangaulan": ("ndurubu", "taafi", "mantimatu", "kaino", "tamajoba", "jiromji", "binwarji"),
    "name_list_yan": ("yan",),  # Beikling
}

# EU4 culture or culture group -> its dynasty names, imported once from EU4 Anbennar (see the module doc).
EU4_DYNASTY_NAMES = {
    "alenic": [
        "Gerwick", "of Vanbury", "Eaglecrest", "Fludd", "Lodan", "Feycombe", "Wightsgate", "Humbercroft", "Ginnfield",
        "Derwing", "Alainson", "Cottersea", "Leapdon", "Brontay", "Beron", "Cockerwall", "Edgemoor", "Fouler",
        "Lonevalley", "Greenley", "of Alenath", "Norleigh", "of Morban", "Jonsway", "Mossford", "Oudesker", "Wolfden",
        "Aldtempel", "Gardfort", "Drakesford", "Somberwold", "Westfield", "Baldfather", "Alenfield",
        "of the Greatmarch",
    ],
    "old_alenic": [
        "Adshaw", "of Rocky Road", "of Millburn", "Woodsman", "of Westley", "of Woodham", "of Bigbear", "of Busy Bend",
        "Vrorensson",
    ],
    "moorman": [
        "Cottersea", "Leapdon", "Brontay", "Beron", "Cockerwall", "Edgemoor", "Fouler", "of Lancre", "of Garn",
        "of Ripley", "of Seabrook", "of Midgley",
    ],
    "wexonard": [
        "síl Wex", "síl Rhinmond", "of Bisan", "of Indlebury", "of Magdalaire", "sina Wexton", "sina Varton",
        "síl na Casnaslíc", "sina Badgerbite", "of Drunkard's Drop", "of Easton", "of Hyland", "síl Neratin",
        "of Bridgeton", "of Holmwood", "of Sappington", "of Ingham", "of Kynaston", "of Linwood", "of Mutton",
        "of Hardwick", "síl Demelsvord", "síl na Dwarovcantir", "síl na Hondenophan", "of Gnollhide Gulch",
    ],
    "vertesker": [
        "Blacktower", "sina Crés", "sina Pírgasc", "sina Bog", "síl Alencestir", "of Stoneberry", "of Puddledrown",
        "of Wickham",
    ],
    "blue_reachman": [
        "of Goblin Pike", "of Hermit's Point", "of Milford", "of Owston", "of Newport",
    ],
    "gawedi": [
        "Gerwick", "of Vanbury", "Eaglecrest", "Fludd", "Lodan", "Feycombe", "Wightsgate", "Humbercroft", "Ginnfield",
        "Derwing", "Alainson", "Cottersea", "Leapdon", "Brontay", "Beron", "Cockerwall", "Edgemoor", "Fouler",
        "Lonevalley", "Greenley", "Brasslance", "Ramsgate", "of Alenath", "Norleigh", "of Morban", "Jonsway",
        "Mossford", "Oudesker", "Wolfden", "Aldtempel", "Gardfort", "Drakesford", "Somberwold", "Westfield",
        "Baldfather", "Alenfield", "of the Greatmarch", "of Beancroft", "of Grapeseed", "of Old Nag", "of Bakehouse",
        "of Farmington", "sina Wheatvalley", "sina Alehouse", "of Clifford", "of Ellsworth", "of Fairburn", "of Gadsby",
        "of Hamilton", "of Linton", "of Irving", "of Layton", "of Westley", "of Woodham", "of Bigbear", "of Busy Bend",
        "of Scalecloak", "of Lonetower", "of Easton", "of Horsefall",
    ],
    "marrodic": [
        "Griffonmark", "Griffonhill", "of Marrhold", "Marr", "Marrod", "Griffonsgate", "Marrhyl", "sina Marrton",
        "of Thadston", "of Falcon's Nest", "of Tailfeather", "of Endicott", "of Newton", "of Ridley", "of Winfield",
    ],
    "west_damerian": [
        "síl na Trísfer", "síl Gabelaire", "síl Wesdam", "síl Carneter", "síl Triancóst", "síl Ordóin", "síl Ilvan",
        "sílna Lence", "Woodwell", "Cliffman", "síl Auraire", "sina Cóst", "síl Jexisthíl", "of Dovesroost",
        "of Twoflower", "sina Petagvar", "sina Gabciobis", "síl na Gráidemele", "síl na Damesdemele", "sina Dameston",
        "sina Pantheonia", "síl na Lunith", "of Sentinel Hill", "sina Pírrahe of Steepcliff", "of Paredocks",
    ],
    "east_damerian": [
        "Silgarion", "Silistra", "síl Ricancas", "síl Silvelar", "síl Acrom", "Taxwick", "Plumwall", "síl Cestir",
        "sína Cymainé", "sína Lans", "síl Aranth", "sina Petagvar", "sina Gabciobis", "síl na Gráidemele",
        "síl na Damesdemele", "sina Dameston", "sina Pantheonia", "síl Obaithuan", "sina Lakebór", "sina Dhanvar",
        "sina Pírgab", "síl Munascestir", "síl Cúniacaire", "síl Píraire", "of Fowlbarn", "of Rigsby",
        "síl na Deir Stíal", "sina Cóst", "síl Jexisthíl", "of Dovesroost", "of Twoflower",
    ],
    "anbennarian": [
        "Silcalas", "Silnara", "Silebor", "Silurion", "Silistra", "Silgarion", "síl na Trísfer", "síl Gabelaire",
        "síl Wesdam", "síl Carneter", "síl Triancóst", "síl Ordóin", "síl Ilvan", "sílna Lence", "Woodwell", "Cliffman",
        "síl Auraire", "síl Gabmórionn", "síl Bennon", "síl Leslinpár", "síl Aranmas", "síl Terr", "síl Varainé",
        "Konwell", "síl Vivin", "síl Esta", "sína Gren", "sílna Hat", "síl Estadeir", "síl Seinathíl", "of Vanbury",
        "síl Arannen", "síl Marllin", "síl Varlosen", "síl Antirhalen", "síl Irmathras", "síl Vekt", "of Gisden",
        "Brinkwick", "sílna Pírvar", "síl Dhánaenn", "síl Crothán", "síl Cannéinn", "síl Freecestir", "síl Ricancas",
        "síl Silvelar", "síl Acrom", "Taxwick", "Plumwall", "síl Cestir", "sína Cymainé", "sína Lans", "síl Aranth",
    ],
    "pearlsedger": [
        "síl na Trísfer", "sílna Galvin", "síl Tretun", "síl Lanpool", "sina Dhantràs", "of Ettashall",
        "of Shell Shallows", "of Trollsbridge", "sina Píruan", "of Athana",
    ],
    "esmari": [
        "síl Themarenn", "síl Estallen", "síl Deamóine", "síl Gabmórionn", "síl Bennon", "síl Leslinpár", "síl Aranmas",
        "síl Terr", "Silurion", "síl Varainé", "Konwell", "Silistra", "síl Vivin", "síl Esta", "sína Gren", "sílna Hat",
        "síl Estadeir", "síl Seinathíl", "Seinpírártharn", "Farran", "sina Vartràs", "sina Vardemele", "sina Ciobispár",
        "síl na Kormistgrái", "of Dogwood", "of Roysamfloo", "of Arkfloat", "of Bargedock", "sina Lanassionn",
        "of Coraston", "of Carrotrows", "síl Esmarton", "sina Darovionn", "of Wincestir", "sina Gabnamm",
        "of Camirsville", "síl na Falahvar", "of Peargrove", "sina Dizâlstunad", "sina Yaddervanhoop", "sina Cúwbeloch",
        "of Weavers Rock", "of Erel", "sina Rhaebór", "síl Balgarionn", "of Builderstemple", "síl na Drominarsaraor",
        "of Maiden's Hill", "sina Quicksprout", "of Heartwood", "sina Brassblare", "of Heraldbrook",
    ],
    "vernman": [
        "síl Verne", "síl Galéinn", "síl Arca Lar", "of Heartsridge", "síl Menibór", "síl Thanallen", "Silnara",
        "Silebor", "of Patton", "of Redcliff", "of Merrill", "sina Eionecóst", "sina Núrgab", "sina Redcoast",
        "sina Pírton", "síl Treunaire", "of Beastsfall", "of Brickhut", "of Selby", "of Stoneford",
    ],
    "heartman": [
        "síl Verne", "síl Galéinn", "síl Arca Lar", "of Heartsridge", "síl Menibór", "síl Thanallen", "Silnara",
        "Silebor", "of Patton", "of Redcliff", "of Merrill", "sina Eionecóst", "sina Núrgab", "sina Redcoast",
        "sina Pírton", "síl Treunaire", "of Beastsfall", "of Brickhut", "of Selby", "of Stoneford",
    ],
    "arannese": [
        "síl Aen", "síl Ais", "síl na Loop", "síl Arannen", "síl Marllin", "síl Varlosen", "síl Antirhalen",
        "síl Irmathras", "síl Vekt", "of Gisden", "Brinkwick", "síl Cestirbridge", "síl Livergrave", "síl Gablainé",
        "sína Thíl", "síl Vivin", "í Deedaunt", "sina Fiarncestir", "of Pigpen", "sina Dhancel", "of Barleyton",
        "síl na Dithvar", "sina Ciobisenn",
    ],
    "crownsman": [
        "síl Crowne", "síl Aranmas", "síl Crothán", "síl Ebenaire", "síl Aramar", "sílna Gol", "of Ainway", "Silnara",
        "of Vanbury", "síl Gabmórionn", "síl Themarenn", "síl Estallen", "sina Demelecestir", "sina Varpár",
        "síl na Arademele", "síl na Arasùil", "sina Dhanmeweri", "sina Drasevionn", "síl Gabara", "síl Miosádh",
    ],
    "ionnic": [
        "síl Crowne", "síl Aranmas", "síl Crothán", "síl Ebenaire", "síl Aramar", "sílna Gol", "of Ainway", "Silnara",
        "of Vanbury", "síl Gabmórionn", "síl Themarenn", "síl Estallen", "sina Demelecestir", "sina Varpár",
        "síl na Arademele", "síl na Arasùil", "sina Dhanmeweri", "sina Drasevionn", "síl Gabara", "síl Miosádh",
    ],
    "arbarani": [
        "Silcalas", "Derwing", "sílna Pírvar", "síl Dhánaenn", "síl Crothán", "síl Cannéinn", "síl Aranmas",
        "síl Freecestir", "Silurion", "of Vanbury", "sina Fwinchéiri", "síl Orriccestir", "síl Calasaire",
        "of Casnafort", "sina Oatfields", "of Castanton", "sina Flaxbend",
    ],
    "dhanaenno": [
        "Silcalas", "Derwing", "sílna Pírvar", "síl Dhánaenn", "síl Crothán", "síl Cannéinn", "síl Aranmas",
        "síl Freecestir", "Silurion", "of Vanbury", "sina Fwinchéiri", "síl Orriccestir", "síl Calasaire",
        "of Casnafort", "sina Oatfields", "of Castanton", "sina Flaxbend",
    ],
    "exwesser": [
        "Silcalas", "sina Pírdemele", "sina Pírenn", "of Bigweed",
    ],
    "corvurian": [
        "síl Vivin", "sina Tchàvar", "sina Ciobiseán", "sina Casnarhae", "síl na Vulsinvar", "of Meekpeak", "sina Gasc",
        "sina Orricgasc", "sina Gascbór",
    ],
    "ourdi": [
        "of Aldwigard", "of Demonsfall", "of Ueleden", "of Withacen", "of Aldanhol", "of Blachyl", "of Landsend",
        "of Dostonath", "of Dostanesck", "of Humac's Island", "of Grenwoud", "of Fatherwell", "of Southtower",
        "of Silverpass", "of Akrad-til",
    ],
    "dostanorian": [
        "sina Tchàvar", "sina Ciobiseán", "sina Casnarhae", "síl na Vulsinvar", "of Meekpeak", "sina Gasc",
        "sina Orricgasc", "sina Gascbór", "sina Jaherionn", "of Tornsack", "of Haresend",
    ],
    "dostanorian_g": [
        "síl Vivin", "síl Gablainé", "síl Cannmarion", "síl Kortir", "síl Kaldere", "Karnoris", "síl Milcor", "Rackman",
        "Marchman", "Crowfellow", "Mire",
    ],
    "ravenmarcher_d": [
        "síl Vivin", "síl Gablainé", "síl Cannmarion", "síl Kortir", "síl Kaldere", "Karnoris", "síl Milcor",
        "sina Tchàvar", "sina Ciobiseán", "sina Casnarhae", "síl na Vulsinvar", "of Meekpeak", "sina Gasc",
        "sina Orricgasc", "sina Gascbór", "Rackman", "Marchman", "Crowfellow", "Mire",
    ],
    "adenner": [
        "Acengard", "síl Rohibon", "síl Aldainé", "Tiltwick", "Badeben", "síl Halansar", "Taranton", "síl Acenaire",
        "Gallopsway",
    ],
    "escanni": [
        "of Oldhaven", "síl Burnoll", "síl Cast", "síl Anor", "síl Acenthán", "Silurion", "síl Núrced", "síl Foarhal",
        "Elderlan", "Escer", "Kondunn", "síl Mintirley", "Venacvord", "Vernham", "síl Devaced", "síl Catelsvord",
        "Glitterdell", "Flaygarden", "síl Hare", "Grannvale", "síl Hendon", "Swapstoke", "Acengard", "síl Rohibon",
        "síl Aldainé", "Tiltwick", "Badeben", "síl Halansar", "Taranton", "síl Acenaire", "Gallopsway",
        "sílna Camircóst", "síl Ionntrás", "síl Medir", "sílna Ced", "síl Uanced", "sílna Fork", "síl Athfork",
        "sína Tencfor", "síl Vror", "Listfield", "sílna Jor", "síl Núrcestir", "síl Edillia", "sílna Ór", "síl Araionn",
        "síl Stalbór", "Griffonstone", "síl Alenor", "Wyvernheart", "síl Elikhand", "sílna EsThíl", "síl Rogieria",
        "síl Luciande", "síl na Toars", "sína Trás", "síl Ancard", "sína Rós", "síl Aldre", "Farran", "Adenner",
        "síl na Eán", "of Taranton", "of Aldham", "of Wideben", "of Lencord", "of Hightower", "of Hilton",
        "sina Foolscave", "of Lakeshire", "of Bilemarsh", "of Scepterton", "of Sweetbark", "of Refuge Point",
        "of Dwarovhul", "of Vazhabrok", "of Hylham", "of Dasmaham",
    ],
    "white_reachman": [
        "Foarhal", "Elderlan", "Escer", "Kondunn", "Mintirley", "Venacvord", "Vernham", "Devaced", "Catelsvord",
        "Glitterdell", "Flaygarden", "Hare", "Grannvale", "Swapstoke", "Acengard", "Rohibon", "Tiltwick", "Badeben",
        "Taranton", "Acenaire", "Gallopsway", "the Grey", "Medir", "Hendon", "Ced", "Uanced", "Fork", "Athfork",
        "Halansar", "of Rivsby", "of Eskerborg", "of Wudhal", "Vrorensson", "Listfield", "Moorton", "of Esald",
        "Alcarsson", "of Cedevik", "of Sondaar", "sina Crovanswood", "of Pyror", "of Cashtenham", "of Upton",
    ],
    "black_castanorian": [
        "Ebonfrost",
    ],
    "marcher": [
        "Vernham", "síl Devaced", "síl Catelsvord", "Glitterdell", "Flaygarden", "síl Hare", "Grannvale", "síl Hendon",
        "Swapstoke",
    ],
    "castellyrian": [
        "Silurion", "síl Núrced", "síl Foarhal", "Elderlan", "Escer", "Kondunn", "síl Mintirley", "Venacvord",
        "of Scepterton", "of Sweetbark", "of Refuge Point", "of Dwarovhul", "of Vazhabrok", "of Hylham", "of Dasmaham",
    ],
    "farrani_half_elf": [
        "síl na Eán", "Escin", "Crintheda", "Whistlehill", "Freetower", "Meléthsel", "Cursewood", "Stagborn",
        "Blackroot", "Forlorn", "Coldrest", "Hushdell", "Widor", "sina Rhaecestir", "of Deerpath", "of Shadegulch",
        "of Grand Hamlet", "of Quarrymill", "of Creeksvalley",
    ],
    "castanorian": [
        "Castan",
    ],
    "high_lorentish": [
        "Siloriel", "síl Rubenaire", "síl Kyliande", "síl Madelaire", "síl Eilísin", "síl Ionnidar", "síl na Ith",
        "síl Ainethán", "síl Casthíl", "síl Nurionn", "síl Pírcóst", "sílna Fox", "síl Laseán", "síl Ór Esta",
        "síl Roilsard", "síl Vivin", "of Ording", "sina Pírtràs", "sina Gabdarov", "sina Ciobismintír", "síl Adencóst",
        "sina Rósionn", "síl na Adensdemele", "síl na Minarsdemele", "síl Minarhydin", "síl Nammcestir",
        "síl Kormistgrái", "sina Littleforge", "of Betterflag", "of Troybroog", "of Harascilde", "of Nesdhumme",
        "síl Minartrás", "of Goldshire", "of Elwyn", "of Sexton", "sina Cúwmintír", "sina Casnaview",
    ],
    "low_lorentish": [
        "of Ording", "Greatfield", "Enteben", "síl Wesmar", "Haysfield", "sílna Sild", "síl Darom", "síl Rubenaire",
        "síl Kyliande", "síl Madelaire", "síl Eilísin", "síl Crovan", "sina Pírtràs", "sina Ciobismintír",
        "síl Adencóst", "sina Rósionn", "síl na Adensdemele", "síl na Minarsdemele", "síl Minarhydin",
        "síl Kormistgrái", "of Betterflag", "síl Minartrás", "of Goldshire", "of Elwyn", "of Sexton", "sina Cúwmintír",
        "sina Casnaview",
    ],
    "lencori": [
        "Siloriel", "síl Rubenaire", "síl Kyliande", "síl Madelaire", "síl Eilísin", "síl Ionnidar", "síl na Ith",
        "síl Ainethán", "síl Casthíl", "síl Nurionn", "síl Pírcóst", "sílna Fox", "síl Laseán", "síl Ór Esta",
        "síl Roilsard", "síl Vivin",
    ],
    "roilsardi": [
        "síl Roilsard", "síl Saloren", "síl Toarnaire", "síl na Loop", "síl Vivin", "sina Gabelf", "of Thorngully",
        "of Thornbrush", "of Basilfield",
    ],
    "luciander": [
        "síl Roilsard", "síl Saloren", "síl Toarnaire", "síl na Loop", "síl Vivin", "sina Gabelf", "of Thorngully",
        "of Thornbrush", "of Basilfield",
    ],
    "derannic": [
        "síl Deranne", "síl Darom", "síl Aelvar", "síl Rever", "sina Varuan", "of Rootcliff", "of Chalkvord",
        "sina Cúwmintír", "sina Casnaview",
    ],
    "sorncosti": [
        "síl Sorncóst", "sílna Fióncavin", "síl Ebenuel", "síl Coruan", "síl Ola", "sina Cúweàn", "síl Varcóst",
        "síl na Drominarin",
    ],
    "sornicandi": [
        "síl Sorncóst", "sílna Fióncavin", "síl Ebenuel", "síl Coruan", "síl Ola", "sina Cúweàn", "síl Varcóst",
        "síl na Drominarin", "síl Sornicande",
    ],
    "iochander": [
        "síl Carv", "Eldergreen", "sílna Port", "of Reverscar", "of Bloody Bend", "of Dragoncave", "of Halflingshill",
        "of Nammpoint", "of Zoosterlooven", "of Olhaarpi", "of Shildoud",
    ],
    "elven": [
        "Warsinger", "Bladedancer", "Moondance", "Moonblade", "Sunspear", "Redblade", "Redsun", "Shadowweaver",
        "Shadowdancer", "Shadowblade", "Crimsonspear", "Seadancer", "Seamoon", "Seasail", "Doomdancer", "Stronghunter",
        "Whiteblade", "Whitedagger", "Brightdagger", "Brighteyes", "Silverhair", "Silvereyes", "Moonhair", "Mooneye",
        "Moonspirit", "Whisperwind", "Shadowsong", "Sunstrider", "Stormrage", "Feathermoon", "Ravencrest", "Stagwalker",
        "Forestwalker", "Gladewalker", "Gladehunter", "Gladedancer", "Gladeblade", "Bladewalker", "Moonwalker",
        "Moondancer", "Felsong", "Bloodsong", "Moonsong", "Firesong", "Seasong", "Goodsong", "Silversong", "Goldsong",
        "Windrunner", "Windwalker", "Windblade", "Moonrunner", "Sunspirit", "Winddancer", "Windmoon", "Windsail",
        "Sunchaser", "Moonstrider", "Bloodsworn", "Moonsworn", "Lovesworn", "Bowsworn", "Bowfeather", "Bowmaster",
        "Stringhair", "Bowhair", "Longhair", "Longbow", "Longsword", "Daggerdancer", "Sunreaver", "Sunfury",
        "Shadowfury", "Moonwatcher", "Elderdream", "Spellseer", "Spelldancer", "Spellblade", "Spelldagger",
        "Spellweaver", "Spellrunner", "Spellstrider", "Magehand", "Silverhand", "Silverbow", "Silverblade",
        "Silverfury", "Silverseer", "Silverspell", "Hornblade", "Stargazer", "Stardancer", "Starblade", "Starwatcher",
        "Starweaver", "Sunstar", "Moonstar", "Leafhunter", "Nightbranch", "Duskblade", "Duskspear", "Duskrunner",
        "Duskdancer", "Duskhand", "Skydancer", "Skyblade", "Skyseeker", "Skyfury", "Skyspinner", "Silverarrow",
        "Goldarrow", "Blackarrow", "Shadowarrow", "Skyarrow", "Magearrow", "Elderarrow", "Sunarrow", "Redarrow",
        "Bluearrow", "Gladearrow", "Woodarrow", "Whitearrow", "Brightarrow", "Bloodarrow", "Searrow", "Windarrow",
        "Truearrow", "Truesight", "Trueblade", "Truehair", "Truebow", "Truespell", "Trueseer", "Truehunter", "Truehand",
    ],
    "sun_elf": [
        "Birzartanzuir", "Sarelzuir", "Irrliazuir", "Evranzuir", "Eletarzuir", "Thalanzuir", "Neztezuir", "Arfilzuir",
        "Kelazuir", "Elrazuir", "Kalinzuir", "Tirenzuir", "Varinzuir", "Panorzuir", "Denazuir", "Olozuir", "Zuirzuir",
        "Alarzuir", "Lezuir", "Iztrazuir", "Kalizuir", "Varazuir", "Vinzuir", "Dalzuir", "Kerzuir", "Urzuir", "Trizuir",
        "Erzuir", "Erelzuir", "Andrelzuir", "Kamzuir", "Radinzuir", "Kantazuir", "Zadrathilzuir", "Vindarzuir",
        "Adrazuir", "Varzamzuir", "Faranzuir", "Zunazuir",
    ],
    "sunrise_elf": [
        "Birzartanzuir", "Sarelzuir", "Irrliazuir", "Evranzuir", "Eletarzuir", "Thalanzuir", "Neztezuir", "Arfilzuir",
        "Kelazuir", "Elrazuir", "Kalinzuir", "Tirenzuir", "Varinzuir", "Panorzuir", "Denazuir", "Olozuir", "Zuirzuir",
        "Alarzuir", "Lezuir", "Iztrazuir", "Kalizuir", "Varazuir", "Vinzuir", "Dalzuir", "Kerzuir", "Urzuir", "Trizuir",
        "Erzuir", "Erelzuir", "Andrelzuir", "Kamzuir", "Hiderionzuir",
    ],
    "wood_elf": [
        "Warsinger", "Bladedancer", "Redblade", "Redsun", "Shadowweaver", "Shadowdancer", "Shadowblade", "Crimsonspear",
        "Seadancer", "Seasail", "Doomdancer", "Stronghunter", "Whiteblade", "Whitedagger", "Brightdagger", "Brighteyes",
        "Silverhair", "Whisperwind", "Shadowsong", "Stormrage", "Ravencrest", "Stagwalker", "Forestwalker",
        "Gladewalker", "Gladehunter", "Gladedancer", "Gladeblade", "Bladewalker", "Felsong", "Bloodsong", "Firesong",
        "Seasong", "Goodsong", "Goldsong", "Windrunner", "Windwalker", "Windblade", "Winddancer", "Windsail",
        "Bloodsworn", "Lovesworn", "Bowsworn", "Bowfeather", "Bowmaster", "Stringhair", "Bowhair", "Longhair",
        "Longbow", "Longsword", "Daggerdancer", "Shadowfury", "Elderdream", "Spellseer", "Spelldancer", "Spellblade",
        "Spelldagger", "Spellweaver", "Spellrunner", "Spellstrider", "Magehand", "Hornblade", "Stargazer", "Stardancer",
        "Starblade", "Starwatcher", "Starweaver", "Leafhunter", "Nightbranch", "Duskblade", "Duskspear", "Duskrunner",
        "Duskdancer", "Duskhand", "Skydancer", "Skyblade", "Skyseeker", "Skyfury", "Skyspinner", "Silverarrow",
        "Goldarrow", "Blackarrow", "Shadowarrow", "Skyarrow", "Magearrow", "Elderarrow", "Redarrow", "Bluearrow",
        "Gladearrow", "Woodarrow", "Whitearrow", "Brightarrow", "Bloodarrow", "Searrow", "Windarrow", "Truearrow",
        "Truesight", "Trueblade", "Truehair", "Truebow", "Truespell", "Trueseer", "Truehunter", "Truehand",
        "Farstrider", "Woodrunner", "Woodguard", "Woodguardian", "Woodbow", "Woodheart", "Woodfury", "Woodseer",
        "Woodspell", "Woodsinger", "Woodvale", "Woodriver", "Treewatcher", "Treerunner", "Treestalker", "Treespinner",
        "Treedancer", "Treeblade", "Treespirit", "Seedgrow", "Seedwatcher", "Seedhand", "Seedsong", "Seedhair",
        "Seedsinger", "Seedarrow", "Seedsight", "Seedbranch", "Oakheart", "Oakwatcher", "Oakfeather", "Oakstrider",
        "Leafarrow", "Leafbow", "Elderleaf", "Blackleaf", "Redleaf", "Leafblade", "Leafdagger", "Leafsinger",
        "Leafstrider", "Greenwind", "Greenarrow", "Greenleaf", "Greenseer", "Greenwatcher", "Greenrunner",
        "Greendreamer", "Greenbow", "Mosswind", "Mossrunner", "Mosshair", "Mosswhisper",
    ],
    "dwarven": [
        "az-Run", "Grommubanar", "Dimmal", "Dwinodum", "Dwinodar", "Grudanar", "Calnoraz", "Azduran", "Harrak", "Throm",
        "Throfrum", "Belarr", "Belarruz", "Bofgribal", "Thingribal", "az-Thingr", "Calikorbal", "Asra", "az-Mag",
        "az-Regund", "az-Hehod", "az-Dar", "az-Urgongr", "az-Shemdur", "az-Lelorn", "az-Modan", "Auirdûn", "Gromki",
        "Grimhammer", "az-Fiôbmhor", "Underheart", "Grôfgarth", "Battlehammer", "Axehammer", "Ettinkiller",
        "Minesmiter", "Minesmith", "Hammersmith", "Forgehammer", "Bloodsteel", "Earthfist", "Bronzebeard", "Goldbeard",
        "Stonebeard", "Hammerbeard", "Frostbeard", "Breakbeard", "Ringbeard", "Gembeard", "Ogreslayer", "Orcslayer",
        "Spiderslayer", "Goblinslayer", "Graybeard", "Greybeard", "Redbeard", "Warhorn", "Gemhorn", "Longbeard",
        "Truebellow", "Blackbellow", "Strongbellow", "Shalesmith", "Shaleaxe", "Shalehammer", "Shaleforger", "Heavyaxe",
        "Skullaxe", "Gemcraver", "Goodanvil", "Blackanvil", "Shaleanvil", "Forgeanvil", "Axeanvil", "Trueanvil",
        "Bloodanvil", "Firebane", "Hammerfist", "Slatehome", "Stonebreaker", "Steelarm",
    ],
    "ruby_dwarf": [
        "of Harascilde", "of Nesdhumme", "sina Gabdarov",
    ],
    "silver_dwarf": [
        "síl Balgarionn", "of Builderstemple", "síl na Drominarsaraor", "sina Dizâlstunad", "sina Darovionn",
    ],
    "stone_dwarf": [
        "of Dwarovhul", "of Vazhabrok",
    ],
    "iron_dwarf": [
        "of Dwarovhul", "of Vazhabrok",
    ],
    "obsidian_dwarf": [
        "Blackbarrel", "Bedrock", "Darkstone", "Shadowhammer", "Runebeard",
    ],
    "quartz_dwarf": [
        "Shalebeard", "Trollslayer", "Earthstriker", "Iceheart", "Frozenforge",
    ],
    "agate_dwarf": [
        "Asra", "az-Khug",
    ],
    "opal_dwarf": [
        "Forktongue",
    ],
    "lead_dwarf": [
        "Leadpipe",
    ],
    "marble_dwarf": [
        "Whitebeard", "Brightbeard",
    ],
    "titanium_dwarf": [
        "az-Bogig",
    ],
    "citrine_dwarf": [
        "az-Segh", "az-Hargûn", "Gemhorn", "Greybeard", "Ringbeard", "Forgehammer", "Heavyaxe", "Gemcraver",
    ],
    "garnet_dwarf": [
        "Slatecutter",
    ],
    "diamond_dwarf": [
        "Stormheart",
    ],
    "gnomish": [
        "Somberwazy", "Quintain", "Coddorran", "Widdebozer", "Iondo", "Lilman", "Erddan", "Sildain", "Royman",
        "Roypecker", "Peckering", "Madditmaker", "Cumberbazon", "Coddcosey", "Oddpopper", "Bobbenobben", "Lilposey",
        "Chander", "Chandman", "Chanding", "Lilchand", "Rodroy", "Podddoddddod", "Portfellow", "Portorran", "Namms",
        "Royvid", "Pecker", "Middanman", "Midding", "Bobbman", "Bobberton", "Dobobb", "Foddipeck", "Orannam", "Gib",
        "Aderbaz", "Wobblebox", "Trinkfellow", "Fizzlespell", "Clockscheme", "Tooltemper", "Cogspell", "Sparkleboss",
        "Tinktonker", "Fastsprocket", "Wigglestick", "Spannerfield", "Megnabber", "Totterblitz", "Voltberry",
        "Whistletossle", "Spindlelauncher", "Rivetwicket", "Baublegauge", "Tonks", "Augerdriver", "Chromewand",
        "Netherigger", "Runetonker", "Mindfidget", "Spitesprock", "Felglitch", "Doomwhistle", "Gallantfinger",
        "Doubledazzle", "Goodspark", "Allspark", "Halfbink", "Fussbolt", "Tiltpistol", "Shiftnozzle", "Quickfidget",
        "Whistlewheel", "Peckerwrecker", "Glitterbottom", "Cogturner", "Tinkerbottom", "Bottomturner", "Thinkthinker",
        "Feeblethink", "Oldspanner", "Redspanner", "Bluespanner", "Doublespanner", "Doublespark", "Triplespanner",
        "Quadruplespanner", "Manyspanner", "Quintuple", "Wotwocket", "Trueflux", "Aeonflux", "Shockturner",
        "Lightningrod", "Grindbottom", "Rotbottom", "Netherbottom", "Netherfinger", "Spincog", "Cogspin", "Clockworker",
        "Clockspinner", "Clocklooker", "Goodclock", "Timekeeper", "Timemaker", "Timeblitzer", "Blitzerberry",
        "Manbottom", "Tallspanner", "Tallguage", "Tonkbox", "Bopgadget", "Speartrinket", "Fidgetbottom", "Fidgetfinger",
        "Fidgetschemer", "Fidgetspinner", "Spinspanner", "Spannerman", "Artificerman", "Toolmaker", "Toolspringer",
        "Toolgrinder", "Toolkeeper", "Goodtool", "Toolscrew", "Screwberry", "Screwbottom", "Screwspell", "Spellspinner",
        "Glibgear",
    ],
    "halfling": [
        "Appleseed", "Bigwheat", "Thomsbridge", "Middlewood", "Barrows", "Hill", "Cand", "Merryfield", "Tip",
        "Wheatman", "Cowkeeper", "Brookspeaker", "of Roysfort", "Greenberry", "Marchfoot", "Copperburn", "Peartree",
        "Hardoak", "Grey", "Elkman", "Cobblefoot", "Norley", "Butters", "Roy", "Bravetree", "Lighthands", "Milktooth",
        "Brownlock", "Burrowtree", "Bag-ins", "Leafwhirl", "Flatbrow", "Roytide", "Freefoot", "Downroot", "Stillsong",
        "Darkdew", "Flightfoot", "Stormfoot", "Pinkfoot", "Sixfingers", "Heartbloom", "Bardbough", "Bardtree",
        "Bardfoot", "Songfoot", "Hillbranch", "Darkshot", "Silentgrain", "Forestbrand", "Rumblecrest", "Fumbletoes",
        "Eversword", "Smallknight", "Treeheart", "Bravefather", "Grandworth", "Fischer", "Smith", "Toysman", "Daygazer",
        "Stargazer", "Windcreek", "Pinehand", "Raincrest", "Rainfoot", "Raindagger", "Shadowhorn", "Shadowseeker",
        "Shadowbranch", "Shadowfoot", "Shadowlock", "Commonbough", "Keenflower", "Mistroot", "Blazeheart", "Trueheart",
        "Emberheart", "Embertree", "Emberfoot", "Cinderglade", "Frostfinger", "Frostblade", "Softbrook", "Brook",
        "Brightbend", "Brightheart", "Brighthorn", "Brightfoot", "Brightman", "Dewroot", "Dewfoot", "Dewfingers",
        "Breadmaker", "Breadeater", "Baker", "Pieman", "Piefoot", "Piehat", "Evenfoot", "Cliffdancer", "Brewer",
        "Swiftvale", "Featherstep", "Blossomfoot", "Grayblossom", "Greenblossom", "Leafworth", "Nevertrack",
        "Dirkblade", "Darkdrik", "Brightdirk", "Grin", "Smileheart", "Fortuneseeker", "Goldflower", "Goldbread",
        "Flourmaker", "Doughspinner", "Turnkeep", "Dushair", "Curlylock", "Brownlocks", "Silverlocks", "Goldilocks",
        "Redlocks", "Ravenlocks", "Locke", "Ashsinger",
    ],
    "bluefoot_halfling": [
        "Peartree", "Hardoak", "Grey", "Elkman", "Cobblefoot", "Norley", "Butters", "Roy", "Bravetree", "Lighthands",
        "Milktooth", "Brownlock", "Burrowtree", "Bag-ins", "Leafwhirl", "Flatbrow", "Roytide", "Freefoot", "Downroot",
        "Stillsong", "Darkdew", "Flightfoot", "Stormfoot", "Pinkfoot", "Sixfingers", "Heartbloom", "Bardbough",
        "Bardtree", "Bardfoot", "Songfoot", "Hillbranch", "Darkshot", "Silentgrain", "Forestbrand", "Rumblecrest",
        "Fumbletoes", "Eversword", "Smallknight", "Treeheart", "Bravefather", "Grandworth", "Fischer", "Smith",
        "Toysman", "Daygazer", "Stargazer", "Windcreek", "Pinehand", "Raincrest", "Rainfoot", "Raindagger",
        "Shadowhorn", "Shadowseeker", "Shadowbranch", "Shadowfoot", "Shadowlock", "Commonbough", "Keenflower",
        "Mistroot", "Blazeheart", "Trueheart", "Emberheart", "Embertree", "Emberfoot", "Cinderglade", "Frostfinger",
        "Frostblade", "Softbrook", "Brook", "Brightbend", "Brightheart", "Brighthorn", "Brightfoot", "Brightman",
        "Dewroot", "Dewfoot", "Dewfingers", "Breadmaker", "Breadeater", "Baker", "Pieman", "Piefoot", "Piehat",
        "Evenfoot", "Cliffdancer", "Brewer", "Swiftvale", "Featherstep", "Blossomfoot", "Grayblossom", "Greenblossom",
        "Leafworth", "Nevertrack", "Dirkblade", "Darkdrik", "Brightdirk", "Grin", "Smileheart", "Fortuneseeker",
        "Goldflower", "Goldbread", "Flourmaker", "Doughspinner", "Turnkeep", "Dushair", "Curlylock", "Brownlocks",
        "Silverlocks", "Goldilocks", "Redlocks", "Ravenlocks", "Locke", "Ashsinger",
    ],
    "redfoot_halfling": [
        "Appleseed", "Bigwheat", "Thomsbridge", "Middlewood", "Barrows", "Hill", "Cand", "Merryfield", "Tip",
        "Wheatman", "Cowkeeper", "Brookspeaker", "of Roysfort", "Greenberry", "Marchfoot", "Copperburn", "Roy",
        "Bravetree", "Lighthands", "Milktooth", "Brownlock", "Burrowtree", "Bag-ins", "Leafwhirl", "Flatbrow",
        "Roytide", "Freefoot", "Downroot", "Stillsong", "Darkdew", "Flightfoot", "Stormfoot", "Pinkfoot", "Sixfingers",
        "Heartbloom", "Bardbough", "Bardtree", "Bardfoot", "Songfoot", "Hillbranch", "Darkshot", "Silentgrain",
        "Forestbrand", "Rumblecrest", "Fumbletoes", "Eversword", "Smallknight", "Treeheart", "Bravefather",
        "Grandworth", "Fischer", "Smith", "Toysman", "Daygazer", "Stargazer", "Windcreek", "Pinehand", "Raincrest",
        "Rainfoot", "Raindagger", "Shadowhorn", "Shadowseeker", "Shadowbranch", "Shadowfoot", "Shadowlock",
        "Commonbough", "Keenflower", "Mistroot", "Blazeheart", "Trueheart", "Emberheart", "Embertree", "Emberfoot",
        "Cinderglade", "Frostfinger", "Frostblade", "Softbrook", "Brook", "Brightbend", "Brightheart", "Brighthorn",
        "Brightfoot", "Brightman", "Dewroot", "Dewfoot", "Dewfingers", "Breadmaker", "Breadeater", "Baker", "Pieman",
        "Piefoot", "Piehat", "Evenfoot", "Cliffdancer", "Brewer", "Swiftvale", "Featherstep", "Blossomfoot",
        "Grayblossom", "Greenblossom", "Leafworth", "Nevertrack", "Dirkblade", "Darkdrik", "Brightdirk", "Grin",
        "Smileheart", "Fortuneseeker", "Goldflower", "Goldbread", "Flourmaker", "Doughspinner", "Turnkeep", "Dushair",
        "Curlylock", "Brownlocks", "Silverlocks", "Goldilocks", "Redlocks", "Ravenlocks", "Locke", "Ashsinger",
    ],
    "imperial_halfling": [
        "of Bigweed", "Roy", "Bravetree", "Lighthands", "Milktooth", "Brownlock", "Burrowtree", "Bag-ins", "Leafwhirl",
        "Flatbrow", "Roytide", "Freefoot", "Downroot", "Stillsong", "Darkdew", "Flightfoot", "Stormfoot", "Pinkfoot",
        "Sixfingers", "Heartbloom", "Bardbough", "Bardtree", "Bardfoot", "Songfoot", "Hillbranch", "Darkshot",
        "Silentgrain", "Forestbrand", "Rumblecrest", "Fumbletoes", "Eversword", "Smallknight", "Treeheart",
        "Bravefather", "Grandworth", "Fischer", "Smith", "Toysman", "Daygazer", "Stargazer", "Windcreek", "Pinehand",
        "Raincrest", "Rainfoot", "Raindagger", "Shadowhorn", "Shadowseeker", "Shadowbranch", "Shadowfoot", "Shadowlock",
        "Commonbough", "Keenflower", "Mistroot", "Blazeheart", "Trueheart", "Emberheart", "Embertree", "Emberfoot",
        "Cinderglade", "Frostfinger", "Frostblade", "Softbrook", "Brook", "Brightbend", "Brightheart", "Brighthorn",
        "Brightfoot", "Brightman", "Dewroot", "Dewfoot", "Dewfingers", "Breadmaker", "Breadeater", "Baker", "Pieman",
        "Piefoot", "Piehat", "Evenfoot", "Cliffdancer", "Brewer", "Swiftvale", "Featherstep", "Blossomfoot",
        "Grayblossom", "Greenblossom", "Leafworth", "Nevertrack", "Dirkblade", "Darkdrik", "Brightdirk", "Grin",
        "Smileheart", "Fortuneseeker", "Goldflower", "Goldbread", "Flourmaker", "Doughspinner", "Turnkeep", "Dushair",
        "Curlylock", "Brownlocks", "Silverlocks", "Goldilocks", "Redlocks", "Ravenlocks", "Locke", "Ashsinger",
    ],
    "visfoot_halfling": [
        "síl Vis", "Appleseed", "Bigwheat", "Thomsbridge", "Middlewood", "Barrows", "Hill", "Cand", "Merryfield", "Tip",
        "Wheatman", "Cowkeeper", "Brookspeaker", "of Roysfort", "Greenberry", "Marchfoot", "Copperburn", "Peartree",
        "Hardoak", "Grey", "Elkman", "Cobblefoot", "Norley", "Butters", "Roy", "Bravetree", "Lighthands", "Milktooth",
        "Brownlock", "Burrowtree", "Bag-ins", "Leafwhirl", "Flatbrow", "Roytide", "Freefoot", "Downroot", "Stillsong",
        "Darkdew", "Flightfoot", "Stormfoot", "Pinkfoot", "Sixfingers", "Heartbloom", "Bardbough", "Bardtree",
        "Bardfoot", "Songfoot", "Hillbranch", "Darkshot", "Silentgrain", "Forestbrand", "Rumblecrest", "Fumbletoes",
        "Eversword", "Smallknight", "Treeheart", "Bravefather", "Grandworth", "Fischer", "Smith", "Toysman", "Daygazer",
        "Stargazer", "Windcreek", "Pinehand", "Raincrest", "Rainfoot", "Raindagger", "Shadowhorn", "Shadowseeker",
        "Shadowbranch", "Shadowfoot", "Shadowlock", "Commonbough", "Keenflower", "Mistroot", "Blazeheart", "Trueheart",
        "Emberheart", "Embertree", "Emberfoot", "Cinderglade", "Frostfinger", "Frostblade", "Softbrook", "Brook",
        "Brightbend", "Brightheart", "Brighthorn", "Brightfoot", "Brightman", "Dewroot", "Dewfoot", "Dewfingers",
        "Breadmaker", "Breadeater", "Baker", "Pieman", "Piefoot", "Piehat", "Evenfoot", "Cliffdancer", "Brewer",
        "Swiftvale", "Featherstep", "Blossomfoot", "Grayblossom", "Greenblossom", "Leafworth", "Nevertrack",
        "Dirkblade", "Darkdrik", "Brightdirk", "Grin", "Smileheart", "Fortuneseeker", "Goldflower", "Goldbread",
        "Flourmaker", "Doughspinner", "Turnkeep", "Dushair", "Curlylock", "Brownlocks", "Silverlocks", "Goldilocks",
        "Redlocks", "Ravenlocks", "Locke", "Ashsinger",
    ],
    "suncrown_gnoll": [
        "Architect-of-the-Garden", "Bringer-of-Beneficence", "Devourer-of-Darkness", "Guardian-of-Gold",
        "Harbinger-of-Blessings", "Herald-of-Dawn", "Light-of-Zuurakel", "Master-of-Magnanimity", "Patron-of-Plenty",
        "Widest-of-Grins", "Blessedheart", "Brighteye", "Brilliantpelt", "Dawnpaw", "Flowerplanter", "Giftgiver",
        "Glowtongue", "Goldcoat", "Greentender", "Joyclaw", "Lightmaw", "Nightchewer", "Palaceborn", "Radiantcrest",
        "Shiningfang", "Sunblessed", "Sunfur", "Templebuilder", "Wealthsniffer", "Winedrinker",
    ],
    "sandfang_gnoll": [
        "Bleeder-of-Flames", "Breaker-of-Men", "Bringer-of-Despair", "Cleaver-of-Realms", "Collector-of-Ears",
        "Devourer-of-Suns", "Herald-of-Pain", "Sacker-of-Cities", "Scourge-of-Bulwar", "Toppler-of-Ziggurats",
        "Barrenpaw", "Bloodlicker", "Bonechewer", "Cameleater", "Caravansplitter", "Deadclaw", "Drycoat", "Dunecrest",
        "Elfskinner", "Fleshbiter", "Grimsniffer", "Manbutcher", "Marketmauler", "Nightfang", "Palefur", "Sandmaw",
        "Shredclaw", "Skullchomper", "Sunstalker", "Wastewalker", "Cleaver-of-Mud", "Wearer-of-Chains",
        "Scourge-of-No-Seas", "Splitter-of-Rocks", "Queen-Under-Hill", "Empress-in-Name",
    ],
    "fieldstalker_gnoll": [
        "Breaker-of-Beasts", "Dancer-of-Death", "Deadliest-of-Predators", "Gifter-of-Chains", "Howler-of-Laughter",
        "Manufacturer-of-Death", "Fist-of-Iron", "Sharpest-of-Steel", "Slayer-of-Slayers", "Taker-of-Trophies",
        "Tongue-of-Silver", "Bonegnawer", "Burnthammer", "Coffeebreath", "Coppertooth", "Forgefang", "Ironpelt",
        "Junkborn", "Laughmaker", "Pitfighter", "Scrapclaw", "Smokehide", "Sooteye", "Spicetongue", "Spitepaw",
        "Steeljaw", "Trashjaw", "Trollkiller", "Twitcheye", "Wickedgrin", "Witherbane",
    ],
    "akasi": [
        "Khekasa", "Immaseg", "Ifanshug", "Kasikshug", "Rimseshug", "Ikhan-dusesh", "Khrodam", "Bhiashali",
        "Aijisigesh", "Akhatseg", "Rimsekhu", "Ijimasikir", "Tashalari", "Eishug", "Pesitschemsa", "Musitshka",
        "Jarmeshari",
    ],
    "ndurubu": [
        "Dounodugu", "Jallow", "Fofana", "Koroma", "Diaby", "Sidibe", "Sagasogo", "Sinnaban", "Vual",
    ],
    "taafi": [
        "Dounodugu", "Jallow", "Fofana", "Koroma", "Diaby", "Sidibe", "Sagasogo", "Sinnaban",
    ],
    "mantimatu": [
        "Sylla", "Iphito", "Garanke", "Misimuso", "Gesedala", "Bagenna", "Alke", "Areto", "Molpadia",
    ],
    "kaino": [
        "Modibo", "Sako", "Magassouba", "Jabby", "Dansouba", "Trawore", "Banni", "Trawally", "Sankareh", "Numum",
    ],
    "tamajoba": [
        "Koroma", "Kante", "Numum", "Siaki", "Diane", "Lolou", "Kanda", "Diakarida",
    ],
    "jiromji": [
        "Kolonkise", "Douno", "Danhou", "Dyitigi", "Krubaly", "Kora", "Kasi", "Tobi", "Wajibiya",
    ],
    "binwarji": [
        "Falibuwa", "Somono", "Jakite", "Koulibaly", "Tuma", "Zanga", "Jawara", "Camara", "Sako", "Nemaa", "Tilabaa",
        "Biakata",
    ],
    "yan": [
        "Zhu", "Wu", "Geng", "Shang", "Zheng", "Zhao", "Li", "Shi", "Liu", "Guo", "Yang", "Wang", "Qian", "Ma", "Meng",
        "Gao", "Chen", "Sun", "Sima", "Cao", "Xiao", "Qi", "Zu", "Zhou", "Huang", "Bai", "Qiu", "Tang", "Lu", "Xu",
        "Chang", "Feng", "Deng", "Hua", "Gu", "Fu", "Hu", "Mei", "Xue", "Liao", "Jin", "Ye", "He", "Lan", "Du", "Fang",
        "Mao", "Hao", "Kong", "Jiao", "Si", "Pan", "Zuo", "Ding", "Bao", "Yan", "Tan", "Han", "Luo", "Xie", "Yuan",
        "Qin", "Ruan", "Niu", "Zeng", "Dong", "Lin", "Shen", "Ouyang", "Su", "Yu", "Ren", "Chai", "Xia", "Mo", "Dai",
        "Jiang", "Yue", "Jia", "Xiong", "Cui", "Hang", "Hue", "Khang", "Soung", "Kue", "Lo", "Moua", "Pha", "Thao",
        "Cheng", "Chu", "Vang", "Vue",
    ],
}

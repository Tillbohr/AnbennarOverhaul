"""Hand-made fields for the Cannor great projects; kept verbatim across re-imports of cannor.py.

HAND[eu4_key] may replace barony, category, desc, levels, gate, gate_desc and notes wholesale, may set gate_mode
("or": on the new upper levels of an Anbennar chain the EU4 gate is an alternative to Anbennar's can_construct
instead of an extra requirement), and may hold
`tiers`: a list of 3 dicts (block name -> {ck3 key: value}) merged over the imported tier blocks key by key
(a value of None removes the key).
"""

HAND = {'aelcandar': {'desc': 'Aelcandar, another great work by Calasandur the Magnificent, was built to counter '
                       "Nichmer's terror campaign against the Wescanni halflings. The guardsmen fought night "
                       'and day to rebuff countless undead, grievously exhausted and injured. The stronghold '
                       'was pivotal for the Free Realms cavalry, offering refuge when the slavering hordes '
                       "grew too large. Aelcandar's name resounds among all Wescann halflings, especially "
                       "the Coppertowners. Central to Aelcandar's fame is Candor Ale, a glimmering pale "
                       'spirit only brewed in Coppertown copper kettles, and widely loved for its sweet '
                       'flavor and deceptive potency. The surrounding lands are home still to the half-elven '
                       'Aelcandari, descendants of the original Free Realms garrison. Initially enforcers '
                       'for Viswall, the Aelcandari have fought and died protecting halflings in every '
                       'Wescanni war. Nowadays, Aelcandari share much with their shorter brothers, espousing '
                       'the same love for adventure, pipeweed and good food. Though kin to the smallfolk, '
                       'the Aelcandari serve a mixed purpose as both protector and jailer over the halflings '
                       'of Lencenor.',
               'category': 'fortress'},
 'ascajar': {'desc': 'Nestled within the verdant coastal hill range of Busilar and overlooking prosperous '
                     'Port Jaher at the mouth of the Hapainé, the palace of Ascajar is truly deserving of '
                     "its moniker 'Citadel of Flowers'. Its origins can be traced to a fortification erected "
                     'in 488 AA by the rulers of Kišakur to secure their control over the vital port of '
                     'Abtanus, which would later become Port Jaher. After their descendants secured their '
                     'hold over Businor, the fortress was first expanded, then demolished in 672 AA. In its '
                     'place the palace of Azka-Ayaru, or Citadel of Flowers, was erected and became the '
                     'royal palace of Itrahureš for the following two centuries. Around 750AA, the famed '
                     'gardens of Ascajar were first established. After the fall of Itrahureš, Ascajar lost '
                     'its prominence for a time under the rule of Black Castanor, but it was restored to its '
                     'former glory under the Phoenix Empire and has since served as the favorite royal '
                     'retreat of the ruling Silnara dynasty of Busilar. The intricately decorated interior '
                     'of the palace and its soaring architecture, built in the unique Ilatani style, are '
                     'remarkable enough on their own, but even they are overshadowed by the vast palace '
                     'gardens, sprawling across a series of terraces surrounding the palace. A network of '
                     'pools and fountains ensure a balmy clime even during the heat of the summer months and '
                     'a stunning array of flowers from places as far away as Fangaula and Rahen bloom year '
                     'round. Here the spirit of Itrahureš lives on: combining disparate cultures to create '
                     'something better, stronger and infinitely more beautiful.',
             'category': 'palace',
             'tiers': [{'county_modifier': {'monthly_county_control_growth_add': 0.25}},
                       {'county_modifier': {'monthly_county_control_growth_add': 0.25}},
                       {'county_modifier': {'monthly_county_control_growth_add': 0.25}}],
             'notes': ['gate atom tag:A49 ignored (no CK3 equivalent)',
                       'Hand tiers: EU4 statewide_governing_cost -0.5 (dropped by the table as a states key) '
                       'is translated like local_governing_cost (county control growth +0.25) at every '
                       'level, so level 1 has an effect; the EU4 on_upgraded culture-province modifiers '
                       '(ascajar_culture_mod1/2) are not translated.']},
 'bal_dostan': {'desc': 'In 470, the Raven King and his tribesmen stumbled on the abandoned citadel of Bal '
                        'Dostan, its gates left wide open. In the high solar, the petty king found the '
                        'Sapphire Key badge of the Bal Dostan castellans, and seized it as divine favor for '
                        'his rule. For a time, the reign of the Korbarids was good. Nowadays, their '
                        'Corvurian descendants have the dubious honor of ruling over cow manure and dirt '
                        "farmers. Arca Corvur's vaults are beyond empty, the old Dragon Road that once "
                        'enriched the Korbarid Kings worn into a mud trail for herding livestock. Recently, '
                        'however, strange screeches are heard in the night above Corvuria. The yearly '
                        'Masquerades, which shrunk slowly over the ages, now seem to never end. The endless '
                        'feasts of Arca Corvur draw in impoverished nobles like flies. It is strange '
                        'however: After leaving, the partiers say the best wine in the Godshield is found '
                        'here, yet no one has ever seen a barrel leave the palace...',
                'notes': ['gate atom tag:Z07 ignored (no CK3 equivalent)',
                          'Gate decision: left open. The EU4 gate is an OR with alternatives that have no '
                          'CK3 equivalent (vampire estate, Castanor legacy, Escanni legacy monument, tag Z07 '
                          "Dostanor); a culture gate would be stricter than EU4's, so any holder may use "
                          'it.']},
 'bal_hyl': {'desc': 'During the Dragonwake, three Alenic Tribes fled pell-mell into the eastern Dameshead. '
                     'With Gawedi behind, and Damerians ahead, they turned to fight before the noose closed '
                     'completely. In a desperate gambit, they put Bal Hyl at their backs and armed every '
                     'man, woman and child. The Battle of the Hyl was so grave that their backline was '
                     'crushed against the castle walls. Afterwards, the castellan of Bal Hyl offered '
                     'vassalage but refused the tribesmen sanctuary. Surprisingly, the Wex played along: '
                     'scouts had found entrance into tunnels beneath Bal Hyl. As talks stalled above, '
                     'warriors delved deeper below. When Damenath fell, Wexonard braves boiled through the '
                     'catacombs and slaughtered the demoralized garrison. In victory, the Wex chieftain cast '
                     'the Damerian flag onto the pyre of his enemies, naming his conquest Wexkeep. Now, the '
                     'House sil Wex rules Wexkeep with an iron fist. The same labyrinth that doomed the '
                     'Damerians houses both supplies and spies, the full extent thereof known only to the '
                     'sil Wex line. The descendants of those bloodsoaked braves still man the walls.'},
 'bal_mire': {'desc': 'Bal Mire was built in 457 BA, in the marshlands of western Escann, to watch over the '
                      "unruly Alenic tribes to the west, long a thorn in Castanor's side. Acting as a bridge "
                      'over the Alen River as well as a fortress, Bal Mire is the youngest and smallest of '
                      "Balgar's Wonders. Some joke that all of Balgar's spirit had been spent on his other "
                      "works, but the truth regarding Bal Mire's diminutive size lies in the uneasy ground "
                      'it rests upon. Raising a fortress in such a dreadful location had been deemed '
                      "impossible, and that Balgar did so without affecting the Citadel's ability to serve "
                      'as an impenetrable gateway was nothing short of a miracle - one that secured '
                      "Castanor's dominion over the whole of the Middle Alen.",
              'notes': ['gate atom tag:A24 ignored (no CK3 equivalent)',
                        'Gate decision: left open. The EU4 gate is an OR with alternatives that have no CK3 '
                        'equivalent (Escanni wars culture check, Castanor legacy, Westmoors modifier, '
                        "development 14); a culture gate would be stricter than EU4's, so any holder may use "
                        'it.']},
 'bal_ouord': {'desc': 'Built atop the same Burning Hills where the Castanites once battled the terrible '
                       "First Gnoll Xhazobine, Bal Ouord's lone, gigantic central tower reaches far into the "
                       "sky, serving as both the Citadel's main keep and lighthouse. Balgar the Builder, not "
                       'content with merely building an unbreakable fortress, saw fit to carve for Bal Ouord '
                       'a harbor surpassed only by that of nearby Ovdal Tûngr. Tunnels and hallways lead '
                       'deep into the earth, converging upon a tremendous cavern against which the wind '
                       "batters and the waves break. Bal Ouord's bowels may have never been host to wealthy "
                       'merchant fleets, but at the height of the Empire of Castanor, they hosted an armada '
                       'that saw even the prideful Damerian Republic flinch.'},
 'bal_vertesk': {'desc': 'Over the Free City of Vertesk looms the Black Tower, a spire of sinister black '
                         'brick. Originally, it was built by Balgar from the same pale stone as the famed '
                         'White Walls. However, during his reign as master of the Vertesk Dominion, Venac '
                         'the Arrogant corrupted the tower to its very foundations, turning its stones as '
                         'black as night. This tower has survived three empires and two millennia, a '
                         'near-immortal symbol of fear and power. Countless lords of countless different '
                         'peoples and petty kingdoms have all ruled from the same high solar, sent out the '
                         'same agents with the same grim purpose: to vanish foolish dissenters behind the '
                         "black spire's yawning gates, their names never to be uttered aloud again. As kings "
                         'molder to dust and empires collapse like straw, the Black Tower stands as an '
                         'uncaring testament set to outlive all, including the upstart Empire of Anbennar.'},
 'bal_vroren': {'desc': "One of Balgar's Wonders, the Citadel of Bal Vroren was built in 546 BA by the "
                        'Empire of Castanor to defend against the Giants and their subjects to its north. '
                        "Nestled in a natural harbor along the Giant's Grave Sea, Bal Vroren would come to "
                        'serve as host to the fearsome Giantsbane Legion and as an important naval center '
                        'and staging ground from which Castanor influenced the whole of Gerudia. During the '
                        'events of the Dragonwake of 470 AA, centuries after its founding, tens of thousands '
                        "of refugees would seek shelter in Bal Vroren's mighty walls. But when the dragon "
                        "Elkaesal the White came to the Citadel's gates, all of them would be frozen to "
                        'death overnight. Ever since that harrowing event, Bal Vroren has attracted rumors '
                        'of curses and hauntings and has been left abandoned, with its ruined walls, towers, '
                        'and keeps serving as grim reminder of the terror that once afflicted Cannor. Seeing '
                        'Bal Vroren refurbished and fully manned would require significant effort, and it is '
                        'so thoroughly scarred and marred by would-be conquerors and invaders that most now '
                        "believe it can never be fully restored. If even a measure of Bal Vroren's former "
                        'glory were to be regained, however, it is certain that Cannor and Gerudia would '
                        'again be divided by the towering, impenetrable heights of the Vrorenswall...'},
 'baths_of_verinus': {'desc': 'Once the jewel of Eastbright, the Baths of Verinus remain one of the greatest '
                              'feats of Damerian engineering - albeit now slumbering beneath ivy-covered '
                              'arches and shattered domes. Commissioned in 97 AA by Cr. Verinus Erienticus, '
                              'a controversial Luminary from East Dameshead, the baths were part of a grand '
                              'vision: to elevate his standing and create a haven where the elite of the '
                              'Republic could gather to rest. Inaugurated in 101 AA and expanded over two '
                              'decades, the complex sprawled across multiple terraces above the Eastbright '
                              'springs, featuring over forty pools of varying temperatures, colonnaded '
                              'courtyards, domed pavilions, and stained-glass ceilings casting kaleidoscopic '
                              'light. Mosaics depicted civic virtue and conquest, while scroll-filled '
                              'libraries, banquet halls, and tranquil gardens made the Baths a sanctuary of '
                              'debate and intrigue. Heated by vast hypocaust systems and staffed by '
                              'hundreds, the Baths were a living theatre of power. As they symbolised the '
                              'very nature of the Republic, it was natural that they declined with it - the '
                              'entire complex was sundered after the invasion of the Three Tribes in the 5th '
                              'century shattered an already disorganised state.'},
 'bayvic_grandest_city_of_the_reach': {'category': 'market'},
 'beepeck_the_largest_small_city': {'category': 'market'},
 'black_iron_mine': {'desc': "The center of Gawed's iron production, the Black Iron Mine was established "
                             'first by the Castanorian Empire, but was later taken over by the Alenic '
                             "tribesmen, and expanded after Gawed's founding. The mine consists of a "
                             'honey-comb complex of tunnels and shafts buried deep into the moorlands '
                             'Vanbury is built upon, with reinforced eastern sides to prevent tunneling into '
                             'the Alen river. The site is known not only for the vast quantities of iron it '
                             'produces, but also for its impressive amount of smithies and forges. The '
                             'famous oath-rings of the Gawedi Great Lords are forged here, by the famed '
                             'Stone Dwarven clans of Vanbury.'},
 'bladeskeep_monument': {'desc': 'Sitting atop of Dragonsbane hill, the mighty Bladeskeep is a symbol of the '
                                 'glory days of Old Escann. It served as the training ground for some of '
                                 "Cannor's greatest warriors, who swore loyalty to Calindal, the Gleaming "
                                 'Blade and were entrusted to protect her, those amongst the warriors of the '
                                 'Keep who showed a great deal of martial proves would become worthy of '
                                 'wielding the sword, becoming thus the Stewards of the Blade. The '
                                 'Bladeskeep was founded by Elecast Dragonsbane, who was hailed as Blade '
                                 'King in 499 for his slaying of Alos the Copper. The Bladeskeep saw many '
                                 'periods of decadence and prosperity along the years, training generations '
                                 'of soldiers and generals that served throughout Escann and beyond. It was '
                                 'not until recently that the Keep saw an event that shook it to its core: '
                                 'Calindal, the Gleaming Blade destroyed during the Greentide, a traumatic '
                                 'event for this ancient institution. Bladeskeep however remains as a '
                                 'shining beacon of the Escann that once was and can still be.',
                         'notes': ['gate atom flag:semi_monstrous ignored (no CK3 equivalent)',
                                   'gate atom flag:no_longer_monstrous ignored (no CK3 equivalent)',
                                   'gate atom tag:B33 ignored (no CK3 equivalent)',
                                   'gate atom flag:bladeskeep_monument_is_worthy ignored (no CK3 equivalent)',
                                   'Gate decision: left open. The EU4 gate is an OR with alternatives that '
                                   'have no CK3 equivalent (tag B33 Blademarches (marcher), monstrous-nation '
                                   'flags, manpower buildings, an idea-group count, a worthiness flag); a '
                                   "culture gate would be stricter than EU4's, so any holder may use it."]},
 'bladeskeep_shaded_monument': {'desc': "In the shadow of Esthil's old halls stands a darker twin of "
                                        'Bladeskeep, where the blade-sworn train far from the eyes of the '
                                        'realm. Its walls are said to keep out the light as readily as its '
                                        'enemies.',
                                'notes': ['gate atom tag:B54 ignored (no CK3 equivalent)',
                                          'Gate decision: left open. EU4 requires tag B54 Esthil, whose '
                                          'primary culture aldresian is not in CK3.']},
 'blaiddscal_academy_monument': {'desc': 'Blaíddscal Academy was founded by Ladrinel Heartsworn, captain of '
                                         'the Princess Guard, whose history of captivity within the One Xia '
                                         'prompted the discovery of Diranbe. After leading their violent '
                                         'escape from captivity and spending time in the service of Jaher, '
                                         'Ladrinel returned to the Elfrealm of Ibevar, having spent more '
                                         'time apart from it than Ibevar had yet formally existed. She '
                                         'brought to bear her experiences as a famous general and adept of '
                                         "martial techniques, founding one of Cannor's most prestigious "
                                         'military institutions before retiring around the end of Prince '
                                         "Adrahel's reign. Since then, Blaíddscal has taught generations of "
                                         'officers from Ibevar and occasionally guests from further abroad, '
                                         'boasting a teaching staff intended to give a well rounded but '
                                         'military minded schooling, often hand-selected from previous '
                                         'generations of exemplary officers. Sometimes even mercenary adepts '
                                         'of Diranbe, known as Rhaidd, coming and being given a home in the '
                                         'gentle lands of the Elfrealm in return for teaching services. Many '
                                         'walk through its halls and come out ready to serve a truly modern '
                                         'army and build discipline from top down.'},
 'calascandar': {'desc': "Who doesn't know the legend of the crafty hero Calasandur the Magnificent and his "
                         'most famous castle Calascandar? Strategically positioned to protect North Esmaria '
                         'and the old Havoric lands, it is famed for holding back an invasion from Black '
                         'Castanor, giving the Free Realms time to break the siege and open the way into '
                         'Escanni heartlands. Calascandar is a name famed throughout the Empire of Anbennar '
                         'as the site of the founding of the famed Knights Magnificent and the original '
                         'headquarters of the Calasanni Trading Company. Calasandur himself ruled from this '
                         'fortress as founder of the affluent House of Silcalas, one of the brightest and '
                         'most fecund Silver families of the Empire. Nowadays, Calascandar still safeguards '
                         'the Ainsway, an immensely profitable trade route, but the CLSTC has since moved '
                         'their headquarters to Damescrown. The now sidelined Calascandar CSLTC branch eyes '
                         'the new headquarters with anger, but they continue their duty of turning one coin '
                         'into two.',
                 'category': 'castle',
                 'notes': ['gate atom tag:A25 ignored (no CK3 equivalent)',
                           'gate atom tag:A46 ignored (no CK3 equivalent)',
                           'gate atom tag:A40 ignored (no CK3 equivalent)',
                           'Gate decision: left open. The EU4 gate is an OR with alternatives that have no '
                           'CK3 equivalent (tags A25 Damescrown (crownsman), A46 Arbaran (half-elf, not in '
                           'CK3), A40 Exwes (exwesser), five merchants); a culture gate would be stricter '
                           "than EU4's, so any holder may use it."]},
 'damish_temple_moonmount_library': {'category': 'library',
                                     'tiers': [{'character_modifier': {'monthly_learning_lifestyle_xp_gain_mult': 0.025}},
                                               {},
                                               {}],
                                     'notes': ['Hand tier 1: EU4 tier 1 has only institution spread and '
                                               'advisor cost (no CK3 equivalent); level 1 gets half of level '
                                               "2's learning lifestyle XP so it has an effect."]},
 'derilde_s_gateway': {'desc': "Derhilde's Gateway, also known as the Middanroy Gateway, sits astride the "
                               'river mouth. Control over the entrance to the river is of vital economic '
                               'importance, as most trade with the Small Country coming from the west is '
                               'conducted via the Middanroy. It is said that Derhilde landed here, at '
                               'Westport, with her first conquest being the Entebenic and Iochander '
                               'garrisons of the area. The Gateway is guarded by two towers, one on each '
                               'side of the river, connected by a long chain that gives the rulers of '
                               'Deranne the ability to close the Gateway at will.',
                       'category': 'fortress'},
 'draculas_throne': {'category': 'palace'},
 'eborthil_toref_citadel': {'barony': 'b_arsencora',
                            'notes': ["Hand barony: b_toref_citadel holds Anbennar's toref_mines_01, so the "
                                      'citadel takes b_arsencora in the same county (c_toref_citadel).']},
 'elikhander_orbs': {'desc': 'The Elikhander kings of old raised these obelisks to gather and hold the power '
                             'of the land. Their carved runes still glow faintly at dusk, and scholars and '
                             'priests alike make the journey to read them.'},
 'elikhander_pyramid': {'desc': 'A great stepped tomb raised by the Elikhander in the first age of Escann. '
                                'Its sealed chambers are said to hold the bodies of dead kings together with '
                                'the treasures they refused to leave behind.'},
 'elikhander_sphinx': {'desc': 'A colossal guardian of carved stone keeps watch over Silvervord. Travellers '
                               'claim that it still asks riddles of anyone who would lay claim to the lands '
                               'it protects.'},
 'escandar': {'desc': 'Escandar has always guarded contested territory. It was first built by the famed '
                      'Calasandur the Magnificent as steward of the pass through the Khenak Mountains. As '
                      "the main fortress separating The Borders and Businor, it served to keep Businor's "
                      'gnoll infestation out of the southeastern Dameshead. Escandar has famously changed '
                      'hands many times. During the War of the Sorcerer King, the Wexonard warlord Magda síl '
                      'Magda was appointed to rule from the citadel, as duchess of the short-lived Duchy of '
                      "Escandar. In the time of Jaher's conquests, Escandar was a stronghold for his early "
                      'conquests in Southeast Cannor. When the Busilari Interregnum led to patchwork civil '
                      'wars between countless petty kings and squabbling warlords, Escandar was a safe '
                      'harbor for all peoples. In modern times, Escandar retains its original role of '
                      'keeping the diminished Hillthrone gnoll packs at bay. Courtiers grumble that its '
                      'garrison should finally wipe out the pests, and be reassigned to better things...',
              'category': 'fortress'},
 'freecestir_mustering_grounds': {'category': 'fortress'},
 'gawed_castle_gaweton': {'category': 'castle'},
 'grave_forest_of_ilvandet': {'desc': 'Deep in the primeval Deruwren, in the "groves of death" of Ilvandet '
                                      'and in the wilderness that separates them, the Carnetori druids '
                                      'gather, remnants of an ancient world. Keepers of ancient lore and '
                                      'secrets since before the first Castanorian colony in the region was '
                                      'founded, the druids use their powers, learned from the fey, to tend '
                                      'to the Gravetrees and protect the Grave Forest from would-be '
                                      'destroyers.',
                              'category': 'forest'},
 'humacs_tomb': {'desc': 'Father of Castan I the Progenitor, Humac was a foundational hero and military '
                         'commander of the Castanites, leading his troops to victory in countless battles '
                         'until he was personally slain by the First Xhazobine at the Battle of the Burning '
                         "Hill. His son Castan, not wanting his father's corpse and resting place defiled by "
                         'the gnolls, carried his remains all the way through the Lost Years in the '
                         'Deepwoods until they finally found friendly lands. There he buried his father, '
                         'along with all of his possessions save his holy mace, which he kept for himself. '
                         "As neither Castan I nor Castan II left any mortal remains behind, Humac's Tomb "
                         'became the most significant burial monument from the early Castanorian era, and '
                         'many later Castans would embellish the Tomb over the years, until it was finally '
                         'destroyed by the Greentide. Many Escanni believe that just as "elves" are named '
                         'after Venaan, the word "human" comes from Humac.',
                 'tiers': [{}, {}, {'county_modifier': {'tax_mult': 0.3}}],
                 'notes': ['Balance cap (ruling 7): county tax_mult reduced from 0.5 to 0.3 at level 3.']},
 'imperial_palace_anbenncost': {'desc': 'Castle Dameris crowns the highest hill of Anbenncóst, the seat of '
                                        "the Kings of Dameria above the City of the World's Desire. Its old "
                                        'keep has watched over the Damerian court for generations, and every '
                                        'hall and tower its lords add makes it a grander stage for the royal '
                                        "court and the realm's great nobles.",
                                'category': 'palace',
                                'notes': ['gate atom tag:Z01 ignored (no CK3 equivalent)',
                                          'gate atom flag:has_dismantled_the_hre ignored (no CK3 equivalent)',
                                          'Gate decision: left open. The EU4 gate is an OR with alternatives '
                                          'that have no CK3 equivalent (HRE membership, tag Z01 (east '
                                          'damerian, not in CK3), a dismantled-HRE flag); a culture gate '
                                          "would be stricter than EU4's, so any holder may use it.",
                                          'Hand tiers: EU4 gives this project no modifiers of its own; its '
                                          'on_upgraded adds event modifiers imperial_palace_modifier_tier_N '
                                          '(emperor: free_city_imperial_authority 0.1/0.25/0.5) and '
                                          'imperial_palace_prince_modifier_tier_N (HRE princes: '
                                          'monthly_favor_modifier 0.1/0.15/0.2, diplomatic_reputation 0/1/2, '
                                          'diplomatic_upkeep), translated through translation.py as country '
                                          'modifiers for the holder.',
                                          'Hand desc: the EU4 desc describes the later Imperial Palace, '
                                          'which does not exist in 1022.'],
                                'tiers': [{'character_modifier': {'monthly_prestige': 0.2,
                                                                  'vassal_opinion': 4}},
                                          {'character_modifier': {'monthly_prestige': 0.5,
                                                                  'vassal_opinion': 6,
                                                                  'diplomacy': 1}},
                                          {'character_modifier': {'monthly_prestige': 1,
                                                                  'vassal_opinion': 8,
                                                                  'diplomacy': 2}}]},
 'jag_radash_monument': {'desc': "Jag'Radash - 'Brave Battle' in Orcish - marks the centre of a vast hunting "
                                 'ground, set up in the wake of a population boom amongst some of the wilder '
                                 'animals after the Greentide swept across Escann. Traditional hunters '
                                 'across Human and Orc lines were busy in the fighting or fleeing depending '
                                 'on the phase of the conflict, and in their absence, natural predators '
                                 'proliferated. Now that the dust has settled and Orcish control over this '
                                 'area has been cemented, their kingdoms seen as equal to the Cannorians, '
                                 'this natural oasis of wildlife has been marked out, safe from destruction '
                                 'as a primitive or monstrous aberration, should it ever be occupied by the '
                                 "'civilised' realms. Orcs train against the wilds and bond with their "
                                 'fellows, gaining experience with the dangers of the wild without risking '
                                 'the full violence of battle.',
                         'category': 'forest'},
 'kazakesh_stingport': {'category': 'monument'},
 'lorenans_rest': {'desc': 'The final resting place of Lorenan the Great, his wife and his Linnati, this '
                           'mausoleum was built in the late years of his long reign, when the Ruby Crown '
                           'weighed heavily upon his shoulders. Excavated into the side of a hill and built '
                           'with white stone, it features a long nave that gives way to a circular chamber. '
                           'In its center, mirroring the ancient throne room in Lorentei, two thrones are '
                           'found, featuring statues of Lorenan and his wife, Elemia, with the tombs of the '
                           'couple directly under said statues. Around them, arranged in a circle, are the '
                           'statues and tombs of each of the eleven Linnati of Lorenan, guarding their '
                           'monarch in death as they did in life. A great equestrian statue of Lorenan armed '
                           'for battle stands in the plaza in front of the mausoleum commissioned by king '
                           "Lorevarn II of Lorent, Lorenan's descendant, crafted by the great artisans of "
                           'the Ruby Mountains.',
                   'category': 'tomb'},
 'marrhold_gate_to_the_serpentspine': {'category': 'fortress'},
 'minara_temple': {'desc': 'Minara, goddess of the lesser love, was raised to godhood by Ryala after Ryala '
                           'witnessed her skill in the art. Her temple celebrates pleasure and desire '
                           "openly, in contrast to the chaste halls of Ryala's followers."},
 'nimsnoms_theatre': {'desc': 'One of the oldest and greatest buildings in the old city of Portnamm, the '
                              'Nimsnoms Theatre represents the culmination of Creek Gnome and Iochander '
                              'culture and society. Theatre and comedy is an important aspect of Creek Gnome '
                              'and Iochander Lencori culture, to the point of it being a major aspect of '
                              'faith, with the theatre-temples of Iochand being found all across the old '
                              'kingdom. The Nimsnoms theatre is a place where plays are enacted, while '
                              'always paying homage to the three most important gods of the Iochanders: '
                              'Adean the Warrior, Minara the Lover, and Wip the Jester. The Nimsnoms also '
                              'serves as the main temple of Wip, the gnomish Regent Court god known as the '
                              'Jester of the Court, where they serve as minor god of actors, comedians and '
                              'tricksters. The theatre always leaves one isolated seat empty during every '
                              'play, to let Wip sit in to watch, judge and respond to any performance in the '
                              'theatre as they see fit.'},
 'oldhaven_memorial': {'desc': 'Long ago, Castan Beastbane purged the so-called monstrous races of Escann in '
                               'what he dubbed "The Great Cleansing". Not content to merely burn people, he '
                               'turned his wrath on the forest itself and burned the World Tree that stood '
                               'in Oldhaven. The resulting blaze deforested most of Escann and split the '
                               'Oldwoods into the Greatwoods and Deepwoods. This memorial reminds us of all '
                               'that was lost, and why we must never again give up the fight for our '
                               'homeland.',
                       'category': 'monument',
                       'notes': ['gate atom culture_group:centaur ignored (no CK3 equivalent)',
                                 'gate atom culture_group:goblin ignored (no CK3 equivalent)',
                                 'gate atom culture:forest_goblin ignored (no CK3 equivalent)',
                                 'gate atom culture:orvitzyen_goblin ignored (no CK3 equivalent)',
                                 'Gate decision: left open. The EU4 gate is an OR with alternatives that '
                                 'have no CK3 equivalent (goblin and centaur culture groups (no CK3 '
                                 'cultures) and a capital in the Deepwoods or Greatwoods); a culture gate '
                                 "would be stricter than EU4's, so any holder may use it."]},
 'palace_of_unity': {'desc': 'It is a fairytale thing, to tear down a building and remake it again elsewhere '
                             '- yet in such a spectacle, real meaning is found. Just as the borders of our '
                             'Empire superficially resemble the old, the Palace of Unity resembles the '
                             'Imperial Palace of old; yet it is a fundamentally different thing, a building '
                             'intended for an entirely different purpose. Once our Pashainéy envoys walked '
                             'the halls of this place as supplicants and wheedlers, cleverly building '
                             "influence and protecting their fragile realm - now, the people's clerks, "
                             'administrators and representatives work for the good of us all. The dynastic '
                             'feuding of old Anbennar has given way to a state which serves the many, not '
                             'the few. See every statue anew; take stock once more of each chamber. They '
                             'have been changed forever.',
                     'notes': ['gate atom tag:Z01 ignored (no CK3 equivalent)',
                               'gate atom flag:has_dismantled_the_hre ignored (no CK3 equivalent)',
                               'mission-spawned in EU4 (start province read from a commented start)',
                               'Gate decision: left open. The EU4 gate is an OR with alternatives that have '
                               'no CK3 equivalent (tag Z01 Empire of Anbennar (east damerian, not in CK3), a '
                               "dismantled-HRE flag); a culture gate would be stricter than EU4's, so any "
                               'holder may use it.',
                               'Hand tiers: EU4 gives only max_absolutism/max_revolutionary_zeal (no CK3 '
                               'equivalent) and, at tier 3, a flag for extra development in Anbennarian '
                               'provinces; the levels get modest palace effects instead (prestige, vassal '
                               'and county opinion) and, at level 3, county development growth for the '
                               'development flag.'],
                     'tiers': [{'character_modifier': {'monthly_prestige': 0.2, 'vassal_opinion': 4}},
                               {'character_modifier': {'monthly_prestige': 0.4,
                                                       'vassal_opinion': 6,
                                                       'county_opinion_add': 5}},
                               {'character_modifier': {'monthly_prestige': 0.6,
                                                       'vassal_opinion': 8,
                                                       'county_opinion_add': 10},
                                'county_modifier': {'development_growth_factor': 0.15}}]},
 'portnamm_portroy_merchants_guild': {'category': 'guild'},
 'rainbow_hall_north_monument': {'desc': 'During the eleventh century, a conflict tore fair Viswall. City '
                                         'politics saw the noble court of the síl Vis stuck into a '
                                         'push-and-pull relation with city hall and its burghers allies. A '
                                         'solution was found when, in typical halfling fashion, both sides '
                                         'were brought together: the buildings, situated on opposite banks '
                                         'of the river, became the dual launches for a unified '
                                         'bridge-palace, one governmental complex from which to govern both '
                                         'the city and the Kingdom. The Rainbow Hall remained the iconic '
                                         'symbol of the city until its destruction during the Viswall '
                                         'Rebellion. On the northern bank rests the Fuchsia Commons complex, '
                                         'city hall of Viswall, and from it a dwarven made bridge of white '
                                         'stone straddles the Widderoy. On top of it, a palace of bricks and '
                                         'cobblestones is painted in variegated hues: violet next to the '
                                         'common, then indigo and blue, and finally green in the middle '
                                         'before switching to the red tones of the southern side.'},
 'rainbow_hall_south_monument': {'desc': 'During the eleventh century, a conflict tore fair Viswall. City '
                                         'politics saw the noble court of the síl Vis stuck into a '
                                         'push-and-pull relation with city hall and its burghers allies. A '
                                         'solution was found when, in typical halfling fashion, both sides '
                                         'were brought together: the buildings, situated on opposite banks '
                                         'of the river, became the dual launches for a unified '
                                         'bridge-palace, one governmental complex from which to govern both '
                                         'the city and the Kingdom. The Rainbow Hall remained the iconic '
                                         'symbol of the city until its destruction during the Viswall '
                                         'Rebellion. On the southern bank lies the Carmine Court, once the '
                                         'heart of the Kingdom of Viswall, and from it a dwarven-made bridge '
                                         'of white stone straddles the Widderoy. On top of it, a palace of '
                                         'bricks and cobblestones is painted in variegated hues: red next to '
                                         'the court, then orange and yellow, and finally green in the middle '
                                         'before switching to the blue tones of the northern side.'},
 'ravioli_bastion': {'desc': 'A fortress-temple of the Ravelian theocracy, built around what its priests '
                             'insist is a fragment of a fallen god. Pilgrims and soldiers share its walls, '
                             'and neither will say what the fragment does.',
                     'notes': ['gate atom tag:Z97 ignored (no CK3 equivalent)',
                               'mission-spawned in EU4 (start province read from a commented start)',
                               'Gate decision: left open. EU4 requires tag Z97 Ravelian State, a theocracy '
                               'with no primary culture.']},
 'refuge_of_the_glasslords': {'desc': 'The dwarven clans of Bulghelovar are refugees thrice over: their '
                                      'ancestors fled first from their ancestral home of Orlghelovar to '
                                      'Gemisle; then from Gemisle to Rubyhold in the wake of the Onslaught, '
                                      'after they and their political allies were blamed for failing to '
                                      'adequately defend the island against the Deep Devils; and finally '
                                      'from Rubyhold in the 600s BA, after being given an ultimatum to '
                                      'reconvert to the Dwarven Pantheon or face exile. They chose the '
                                      'latter option, and settled in an abandoned Ruby Dwarf colony. From '
                                      'this refuge, they sold glassworks to the empires of antiquity. Over '
                                      'time, the wealth this brought attracted more and more humans to '
                                      'settle nearby. Though the dwarves would eventually become a minority '
                                      'in the city that was built around their refuge, the name of said city '
                                      '- Bottlepoint - serves as a reminder of its origins as a home of '
                                      'dwarven master glassblowers. Nowadays, the Refuge of the Glasslords '
                                      'forms a city within the city, a network of workshops, stores and '
                                      'homes for its dwarven inhabitants.',
                              'category': 'guild'},
 'silvelar_silver_spires': {'category': 'temple'},
 'the_lake_palace': {'desc': 'Near the northern shores of Lake Themarenn sits the Grand Lake Palace, calmly '
                             'watching over the city and the farm fields surrounding it. Built during the '
                             'apex of the Kingdom of Esmaria, this palace is a monument to Esmarian '
                             'ingenuity, splendor, and... decadence. Located outside the reach of noisy '
                             'streets and nosy priests and nobles of Esmaraine, the palace was originally '
                             'built as a fort - some of the walls and infrastructure being interconnected '
                             'with the modern castle of Themarenn to this day. However, its main purpose '
                             'changed with time. As prosperity reigned over Esmaria during the 12th century, '
                             'the palace was frequently used as a residence for the Kings of Esmaria and '
                             'their entourage. The structure itself was made in cooperation with gnomish '
                             'engineers, dwarven smiths, and elven architects. Those who have been '
                             'privileged enough to visit speak of its countless rooms of various sizes, no '
                             'less than four kitchens, a wine cellar the size of a small town, gargantuan '
                             'marble columns, and the magnificent Grand Courtroom in the middle of the '
                             "building. Another famous part of the building, The King's Terrace overlooking "
                             'the lake, was instead used for "less pressing matters" and additionally to '
                             'entertain more prestigious guests. The structure would however slowly wither '
                             'away with the dissolution of the Kingdom and then the Grand Duchy of Esmaria. '
                             'Many blueprints and finer details about the structure were lost, preventing '
                             'its inheritors from properly maintaining it, but hope might yet not be lost as '
                             'Cannor enters an Age of Rediscovery.'},
 'the_necropolis': {'desc': 'Across the river Cotumer from Corseton rises a bone-white limestone cliff '
                            'adorned with the cliff tombs of the ancient Milcorissian nobility, and atop it '
                            'the Neratic Necropolis - a sprawling complex of temples, ossuaries, crypts and '
                            'tombs stretching for miles along the cliff face and into the surrounding '
                            'woodlands. At its center lies the High Hall of Judgment, heart of the Neratic '
                            "faith, seat of Nerat's Council and the ultimate destination for bone "
                            'pilgrimages from all over Cannor. But as vast as the sacred precinct is above '
                            'ground, the Neratic priesthood ever-vigilant against necromantic defilement, it '
                            'is even more expansive below. A network of catacombs and subterranean chapels '
                            'has been hewn into the stone over the millennia, creating a veritable '
                            'labyrinth. It is rumored that even the Neratic priesthood is not entirely '
                            'familiar with the full extent of this maze, filled with corseted corpses, some '
                            'of whom seem to be aware of every sign of movement disturbing their rest.',
                    'gate_mode': 'or'},
 'the_north_citadel': {'desc': 'Built at the base of the Trialmount, the North Citadel served as the court '
                               "of Castanor's emperors for centuries. It was from here that they would begin "
                               'their journey up the Trialmount, undertaking the Trials of Castan, and it '
                               'was from here that many Castans ruled over one of the greatest empires the '
                               'world has ever seen and will ever see. Although the Great Aqueduct linking '
                               'the North Citadel to the City of Castonath has been destroyed and the '
                               'Citadel itself damaged during the Battle of Trialmount, the North Citadel '
                               'remains whole. If the Court of Castan were to be restored and its halls once '
                               'again crowded and roaring with life, perhaps some measure of the Empire of '
                               "Castanor's former glory can yet be found."},
 'the_north_citadel_morgurax_monument': {'desc': 'Morgurax is a fortress that hangs in the air above the '
                                                 'Stairs of Regency, raised by Castanorian sorcery as a '
                                                 "refuge for the empire's regents. It looks down on the "
                                                 'lands below as a sleepless watcher.',
                                         'tiers': [{},
                                                   {'province_modifier': {'fort_level': 4}},
                                                   {'province_modifier': {'fort_level': 4}}],
                                         'notes': ['gate atom tag:B54 ignored (no CK3 equivalent)',
                                                   'Gate decision: left open. EU4 requires tag B54 Esthil, '
                                                   'whose primary culture aldresian is not in CK3.',
                                                   'Balance cap (ruling 7): fort_level reduced from 5 (level '
                                                   '2) and 10 (level 3) to 4.']},
 'the_south_citadel': {'desc': 'Twin to the North Citadel at the foot of the Trialmount, the South Citadel '
                               'guarded the southern approaches to Castonath. It housed the legions that '
                               'kept the roads of the Empire of Castanor open.'},
 'thednakerja': {'desc': 'As the Era of Frost came to an end and the ice and snow receded, the body of the '
                         "Giants Grave's terror, the Leviathan, was revealed to the population. Its flesh, "
                         'never rotting, was used as food for generations to come. With the word spreading, '
                         'Skaldhyrric priests began the construction of the Thednakerja, a temple marking '
                         'the first thaw and the end of the terror that plagued the sea, using the '
                         "leviathan's body as a great frame. The interior of the temple boasts innumerable "
                         'stained glass constructions, built in a way that when used as a lens for '
                         'refractive magic, they project colorful light. The most famous of these '
                         "glassworks, 'To Slumber a City', spans the roof of the central part of the temple "
                         'and simulates an aurora into the sky. Designed by Skaldhyrric architects and '
                         'constructed with Reachman labor, the Thednakerja is a symbol of Reachman and '
                         'Gerudian collaboration.',
                 'category': 'temple'},
 'toncodden_lighthouse': {'desc': 'The Storm Isles have always been a dangerous place to reach, due to the '
                                  'very treacherous waters surrounding them. Storms constantly fill the '
                                  'skies, and the waters are filled with both dread creatures below the '
                                  'waves and hostile raider ships from abroad, threatening any ships '
                                  'travelling these seas. To help their ships navigate the dangerous waters '
                                  'around their home islands, the Storm Gnomes constructed a great towering '
                                  'lighthouse structure on the central island of Toncodd, so that their '
                                  'ships could reach their destination safer than before. For centuries, the '
                                  'Toncodden Lighthouse has been used by navigators familiar with local '
                                  'conditions to sail through these tempestuous waters and has allowed for '
                                  'far safer sea travel. As the gnomes of the Dragon Coast have further '
                                  'developed the art of Artificery and its application in the world, the '
                                  'Toncodden Lighthouse has gained a secondary purpose; as a lightning '
                                  'harvesting device. Using the great storms as a way to empower Artificery '
                                  'devices has found many applications across the Storm Isles.'},
 'well_of_majesty': {'desc': 'A deep spring in Treopyr whose waters are held to carry a trace of royal '
                             'blessing. Those who drink from it are said to leave with a more commanding '
                             'bearing.'}}

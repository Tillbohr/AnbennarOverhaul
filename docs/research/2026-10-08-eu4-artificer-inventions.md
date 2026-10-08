# EU4 Anbennar artificer inventions → CK3 mapping

Source: EU4 Anbennar (Workshop 1385440355), `common/estate_privileges/estate_artifice_privileges.txt` (each
invention is an Artificers-estate privilege), tier and category from
`common/scripted_triggers/anb_scripted_triggers_artifice.txt` (`has_active_all_<category>_tier_<n>_inventions`),
effects from each privilege's `benefits` plus the `add_country_modifier` it grants (`is_rajput_modifier = yes`
modifiers apply to EU4's artificer regiments). Capacity cost is 10 / 20 / 30 for tier 1 / 2 / 3 (a few exceptions).

The generic tier lists hold 95 inventions. 48 are universal (two of them, Prototype Tanks and War Golems, only
carry EU4 event-flag locks); 47 are locked to a culture group, race or religion. Only gnomes get the Artificery
tab, so this covers 60: the 48 universal ones, the 4 gnome-locked ones, and the 8 religion-locked ones whose
faith exists in CK3 Anbennar. The other 35 are listed at the end.

## Cross-cutting recommendations

- **One character modifier per invention** (`aov_invention_<key>`, `common/modifiers/`), added to the ruler when
  the invention is active and carried to the heir on succession. EU4 values become CK3 modifiers of similar weight:
  tier 1 ≈ +1 skill / 5-10 %, tier 2 ≈ 10-15 %, tier 3 ≈ 15-25 % or a structural bonus (domain limit, MaA unlock).
- **Artificer-regiment bonuses** (EU4 `is_rajput_modifier`) → `gunpowder_damage_mult` /
  `gunpowder_toughness_mult` (our `artificer_handgunners` have `type = gunpowder`; these also affect other
  gunpowder MaA, which only gnomish realms field in practice).
- **EU4 province modifiers** → `county_modifier` on the county holding the Artificer Academy (it cannot move),
  or `character_capital_county_monthly_development_growth_add` when the effect is about the capital.
- **No trade or navies in CK3:** trade effects → domain tax / income; naval effects → `naval_movement_speed_mult`,
  `embarkation_cost_mult`, `travel_*`. Naval-combat inventions are the weakest fits (flagged below).
- **Three inventions are best as MaA unlocks** rather than modifiers: Prototype Tanks, War Golems,
  Damestear Reactor Megacannon (`can_recruit` checks the invention, like `artificer_handgunners` checks the academy).
- **Era gate** (requested): tier 1 `culture_era_early_medieval`, tier 2 `culture_era_high_medieval`, tier 3
  `culture_era_late_medieval`, via `culture = { has_cultural_era_or_later = ... }`.
- **Filter** (requested): Economic / Military / Society = EU4's own three categories. EU4 files a few oddly
  (Box of Holding and Commercial Sky Galleons are "military", Chi Extraction Charms is "economic"); noted below.
- **Factions hook:** every EU4 invention adds influence to one artificer faction (`tec_mechanists_influence` 66,
  `tec_technomancy_influence` 49, `tec_brilliance_influence` 49). Worth reusing when the Factions tab is designed.

Modifier keys named below were checked against vanilla CK3 1.19 usage unless marked *(verify)*.

## Economic

| T | Invention | EU4 effect | CK3 implementation |
|---|---|---|---|
| 1 | Arcane Battery Capital-Complex | capital −25 % development cost | `character_capital_county_monthly_development_growth_add` (capital-focused, follows capital moves) |
| 1 | Automated Translator | +1 diplomat, +15 % improve relations | `diplomacy = 1`, `different_culture_opinion = 10` |
| 1 | Market Mender Victor.I.A.3 | +5 % tax, production, trade efficiency | `domain_tax_mult = 0.05`, `stewardship = 1` |
| 1 | Plane-of-Water Teleporter | trade steering, trade range | `naval_movement_speed_mult = 0.2`, `embarkation_cost_mult = -0.25` |
| 1 | Self Cleaning Parchment | +2.5 % administrative efficiency | `monthly_county_control_growth_add` (small) |
| 1 | Spell-In-A-Box | −2 % prestige decay | `monthly_prestige_gain_mult = 0.05` |
| 2 | Brass Prosthesis | +10 % manpower and sailor recovery | `levy_reinforcement_rate = 0.15`; optional decision letting a `maimed`/`one_legged` ruler offset the trait |
| 2 | Gene-Food Cultivation | +10 % goods produced | `development_growth_factor = 0.1`, `supply_limit_mult = 0.1` |
| 2 | Growth Beans | one province +15 % production | academy county: `tax_mult = 0.15`, `development_growth_factor = 0.1` |
| 2 | Subterrenes | −10 % build cost and time | `build_gold_cost = -0.1`, `build_speed = -0.1` (direct match) |
| 2 | Vendorless Stall | +15 % trade efficiency | `domain_tax_mult = 0.1` |
| 2 | Chi Extraction Charms *(faith: Devouring Path; EU4 "economic" but military effect)* | artificer +20 % morale damage | `gunpowder_damage_mult = 0.1`; consider re-filing as Military |
| 3 | Sparkdrive Locomotives | free policy, +10 % movement | `movement_speed = 0.1`, `travel_speed = 0.2`, `domain_limit = 1` |
| 3 | Pathway Transmutation | +10 % production, +10 % goods | `monthly_income_mult = 0.1` |
| 3 | Prefabricated City Constructors *(gnome)* | −10 % development cost | `development_growth_factor = 0.15`, `holding_build_gold_cost = -0.15` |
| 3 | T-Wave Transceivers | +1 diplomatic power/month | `diplomacy = 2`, `advantage = 2` (desc: coordinated campaigns) |

## Military

| T | Invention | EU4 effect | CK3 implementation |
|---|---|---|---|
| 1 | Artificer Exo Arms | artificer +10 % infantry power | `gunpowder_damage_mult = 0.1` |
| 1 | Box of Holding *(EU4 "military", economic effect)* | +40 % tariffs | `supply_duration = 0.25` (logistics reading of "shipping goods") |
| 1 | Commercial Sky Galleons *(EU4 "military", economic effect)* | naval morale, ship trade power | `travel_speed = 0.2`, `monthly_income_mult = 0.03` |
| 1 | Magic Missile Deployer | −10 % shock damage received | `gunpowder_toughness_mult = 0.1` |
| 1 | Portable Turrets | +10 % siege, artificer −10 % shock received | `siege_phase_time = -0.1`, `gunpowder_toughness_mult = 0.05` |
| 1 | Sparkdrive Rifles | artificer +20 % fire damage | `gunpowder_damage_mult = 0.15` |
| 1 | Vorpal Bullets | +7.5 % morale damage | `maa_damage_mult = 0.05` |
| 1 | Ancestral Guardian Golems *(faith: ancestor worship)* | +15 % fort defence | `fort_level = 1`, `defender_holding_advantage = 3` |
| 1 | Sunblessed Armaments *(faith: Bulwari sun cults)* | +20 % siege ability | `siege_phase_time = -0.2` |
| 2 | Arcane Blaster | artificer +20 % fire and shock | `gunpowder_damage_mult = 0.2` |
| 2 | Balloonboost Packs | +2 leader manoeuvre | `advantage = 3` |
| 2 | Prototype Tanks | +25 % cavalry fire, +15 % cavalry power | **new MaA** (heavy-cavalry-type war machine); fallback `heavy_cavalry_damage_mult = 0.15` |
| 2 | Wandlocks | artificer +15 % morale | `gunpowder_damage_mult = 0.1`, `gunpowder_toughness_mult = 0.05` |
| 2 | War Golems | artificer +25 % shock damage | **new MaA** (heavy-infantry-type golem); fallback `heavy_infantry_damage_mult = 0.2` |
| 2 | Coddorran Powered Exoskeleton *(gnome)* | artificer +20 % infantry power | `gunpowder_toughness_mult = 0.2` |
| 2 | G-U Boats *(gnome)* | disengage chance, fleet speed | `naval_movement_speed_mult = 0.2`, `embarkation_cost_mult = -0.25`, `retreat_losses = -0.15` |
| 2 | Avatar Supersoldier Serum *(faith: Cannorian pantheon)* | artificer +20 % infantry power | `gunpowder_toughness_mult = 0.15`, `knight_effectiveness_mult = 0.1` |
| 2 | Lullaby Cannon *(faith: Skaldhyrric)* | capture ships, sailor upkeep | weak fit (no naval combat): `advantage = 3` as a battlefield sleep-song |
| 3 | Artillery Autoloader | +15 % artillery | `siege_phase_time = -0.15` plus a siege-weapon MaA bonus *(verify key)* |
| 3 | Bioartificed Ascension | artificer −5 % fire, −15 % morale received | `gunpowder_toughness_mult = 0.25` |
| 3 | Black Damestear Bullets | +5 % discipline | `maa_damage_mult = 0.05`, `maa_toughness_mult = 0.05` |
| 3 | Damestear Reactor Megacannon | +1 military power/month | **new MaA** (gunpowder siege engine with high siege value); fallback `martial = 2` |
| 3 | Military Sky Galleons | heavy ships +15 %, fleet speed | `movement_speed = 0.15`, `advantage = 5` |
| 3 | Naval Mageshields | ship durability, sunk-ship morale | weak fit: `embarkation_cost_mult = -0.3`, `naval_movement_speed_mult = 0.1`; candidate to drop |
| 3 | Personal Mageshields | artificer −20 % shock received | `gunpowder_toughness_mult = 0.2`, ruler `health = 0.25` |
| 3 | Demonflame Flamethrowers *(faith: Xhazobkult)* | artificer +15 % fire | `gunpowder_damage_mult = 0.15`, `dread_decay_mult = -0.1` |

## Society

| T | Invention | EU4 effect | CK3 implementation |
|---|---|---|---|
| 1 | Apparitional Communicator | +1 prestige / legitimacy / devotion | `monthly_prestige = 1` |
| 1 | Centipedal Chests | −25 % envoy travel, −5 % shock received | `travel_speed = 0.15`, `travel_danger = -5` |
| 1 | Living Mirrors | −2 unrest, +2 accepted cultures | `cultural_acceptance_gain_mult = 0.25`, `county_opinion_add = 5` |
| 1 | Mystic Ciphers | +20 % spy defence and offence | `enemy_hostile_scheme_success_chance_add = -10`, `owned_hostile_scheme_success_chance_add = 5` |
| 1 | Sending Stones | +1 diplomat | `diplomacy = 1`, `councillor_opinion = 10` |
| 1 | Viewcatcher | +15 % reform progress | `monthly_dynasty_prestige_mult = 0.1` (portraits that preserve the house) |
| 1 | Conversation Calibrator *(gnome)* | −10 % aggressive expansion, +10 % relations | `different_culture_opinion = 10`, `general_opinion = 3` |
| 1 | Fey Spray *(faith: fey)* | −2 unrest, true-faith spread | `county_opinion_add = 5` |
| 2 | Arithmatons | +15 % tax, inflation and interest reduction | `domain_tax_mult = 0.1`, `vassal_tax_mult = 0.1` |
| 2 | Empire Engine | −10 % core creation | `title_creation_cost_mult = -0.15` |
| 2 | Miracle Detector 3000 | +2 % missionary strength | `faith_conversion_piety_cost_mult = -0.15`, `monthly_piety_gain_mult = 0.1` |
| 2 | Remedial Tinctures | +20 % morale recovery | `hard_casualty_modifier = -0.1`, ruler `health = 0.25` |
| 2 | Think-Thought Transmitters | +25 % improve relations | `general_opinion = 5`, `diplomacy = 1` |
| 2 | Game of the Khet *(faith: Khetism)* | meritocracy, estate loyalty, −2 unrest | `vassal_opinion = 5`, `county_opinion_add = 5` |
| 3 | The Bureaucratizer | +20 % governing capacity | `domain_limit = 1`, `vassal_limit = 10` |
| 3 | Crierless Crier Device | +1 administrative power/month | `stewardship = 2`, `monthly_county_control_growth_add` |
| 3 | Negotiation Nexus | −15 % province war-score cost | `diplomacy_per_prestige_level = 1` (no war-score cost modifier in CK3) |
| 3 | The Runethought Network | −33 % culture conversion cost and time | culture-conversion speed modifier *(verify key)*, plus `cultural_head_fascination_mult = 0.1` |

## Not carried over (35)

Locked to non-gnomish races or cultures, or to faiths that do not exist in CK3 Anbennar (Ravelian,
Feast of the Gods, Gods of the Taychend, Irdaeos, Accretive/Transmutative Path):
fine_print_obfuscator, pearl_cultivators, superfast_elevators, wine_ageifier, artificial_egg_surrogates,
city_maintenance_bots, prehensile_tail_attachments, artifice_powered_magnate_factories, high_velocity_irrigation,
weather_predicticator, antimagic_field_generator, believable_ruin_bomb, dragonscale_plating, power_fists,
predator_exoskeleton, scrap_mechs, vernman_hero_tonic, controlled_rage_serum, elemental_gunpowder,
eplusplus_compound, giantshape_warframe, gyrocopters, kaydhano_powered_vessels, platinum_warsuit,
veykoda_rune_protections, warfare_simulator, wind_invokers, chase_em_rockets, dragonblood_gene_warriors,
burrower_arms, god_fragment_decoder, talking_god_temples, divendancer_speedboat, great_processor, scrapperclaws.

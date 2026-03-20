"""
Combat resolution: stat-check encounters and boss fights.
OVERHAULED: Much deadlier. Injuries cause skill penalties. Night = death risk.
"""

import random
from db import queries

PHASE_THREAT = {
    "morning": 1.0,
    "afternoon": 1.4,
    "evening": 1.9,
    "midnight": 2.5,
}


def stat_check_combat(crew_member_id: int, base_threat: int = 10) -> dict:
    state = queries.get_game_state()
    char = queries.get_character(crew_member_id)
    bus = queries.get_bus()
    resources = queries.get_resources()

    if not char:
        return {"result": "error", "damage_taken": 0, "ammo_used": 0, "loot": {}}

    # Combat score: skill + weapon bonus + ammo bonus + randomness
    combat_skill = char["combat"]

    # Injury penalty: low HP reduces effectiveness
    hp_ratio = char["hp"] / max(1, char["hp_max"])
    injury_penalty = 0
    if hp_ratio < 0.3:
        injury_penalty = -3  # Severely wounded, barely functional
    elif hp_ratio < 0.5:
        injury_penalty = -2  # Wounded, impaired
    elif hp_ratio < 0.75:
        injury_penalty = -1  # Hurting, slightly off

    # Low stamina penalty
    stamina_penalty = 0
    if char["stamina"] < 20:
        stamina_penalty = -2
    elif char["stamina"] < 50:
        stamina_penalty = -1

    weapon_bonus = 0
    if queries.has_upgrade("roof_turret"):
        weapon_bonus += 3
    if queries.has_upgrade("cow_catcher"):
        weapon_bonus += 2

    has_ammo = resources.get("ammo", 0) > 0
    ammo_bonus = min(3, resources.get("ammo", 0)) if has_ammo else -2  # NO ammo = big penalty

    combat_score = (combat_skill + weapon_bonus + ammo_bonus +
                    injury_penalty + stamina_penalty + random.randint(-3, 3))

    # Threat: scales with phase AND global threat (harder scaling)
    phase_mult = PHASE_THREAT.get(state["current_phase"], 1.0)
    threat_mult = 1 + (state["threat_level"] - 1) * 0.15
    threat_rating = int(base_threat * phase_mult * threat_mult) + random.randint(-1, 3)

    margin = combat_score - threat_rating
    ammo_used = random.randint(1, 3) if has_ammo else 0

    if margin >= 8:
        result = {
            "result": "decisive_victory",
            "damage_taken": 0,
            "bus_damage": 0,
            "ammo_used": ammo_used,
            "stamina_cost": 10,
            "loot": _generate_loot(state["current_phase"], bonus=True),
        }
    elif margin >= 2:
        result = {
            "result": "victory",
            "damage_taken": random.randint(10, 25),
            "bus_damage": random.randint(2, 10),
            "ammo_used": ammo_used,
            "stamina_cost": 20,
            "loot": _generate_loot(state["current_phase"]),
        }
    elif margin >= -3:
        result = {
            "result": "pyrrhic",
            "damage_taken": random.randint(25, 45),
            "bus_damage": random.randint(8, 20),
            "ammo_used": ammo_used + random.randint(1, 2),
            "stamina_cost": 35,
            "loot": _generate_loot(state["current_phase"], reduced=True),
        }
    else:
        # DEFEAT — this should hurt
        dmg = random.randint(35, 65)
        # Midnight defeats can be lethal
        if state["current_phase"] == "midnight":
            dmg = random.randint(50, 85)
        result = {
            "result": "defeat",
            "damage_taken": dmg,
            "bus_damage": random.randint(15, 35),
            "ammo_used": ammo_used,
            "stamina_cost": 50,
            "loot": {},
            "resource_loss": _generate_resource_loss(),
        }

    # Apply consequences
    # Armor plating absorbs some crew damage
    from engine.bus_damage import apply_bus_damage
    absorption = queries.get_damage_absorption()
    absorbed = int(result["damage_taken"] * absorption)
    actual_crew_damage = result["damage_taken"] - absorbed
    result["damage_absorbed"] = absorbed

    if actual_crew_damage > 0:
        queries.damage_character(crew_member_id, actual_crew_damage)
    result["damage_taken"] = actual_crew_damage

    # Apply bus component damage
    result["component_result"] = None
    if result["bus_damage"] > 0:
        comp_result = apply_bus_damage(result["bus_damage"])
        result["component_result"] = comp_result
        result["bus_destroyed"] = not queries.can_bus_travel()

    actual_ammo = min(result["ammo_used"], resources.get("ammo", 0))
    if actual_ammo > 0:
        queries.update_resources(ammo=-actual_ammo)
    result["ammo_used"] = actual_ammo

    # Stamina drain
    new_stam = max(0, char["stamina"] - result["stamina_cost"])
    queries.update_character(crew_member_id, stamina=new_stam)

    # Apply loot
    if result["loot"]:
        queries.update_resources(**result["loot"])

    # Apply resource loss on defeat
    if "resource_loss" in result and result["resource_loss"]:
        queries.update_resources(**result["resource_loss"])

    # Collateral damage on defeat — random OTHER crew member takes splash damage
    result["collateral_damage"] = None
    if result["result"] == "defeat":
        crew = queries.get_alive_crew()
        others = [c for c in crew if c["id"] != crew_member_id and c["is_alive"]]
        if others and random.random() < 0.4:
            victim = random.choice(others)
            splash = random.randint(10, 25)
            queries.damage_character(victim["id"], splash)
            result["collateral_damage"] = {"name": victim["name"], "damage": splash}

    # Trust impact from combat outcomes
    if result["result"] == "defeat":
        for c in queries.get_alive_npcs():
            queries.change_trust(c["id"], random.randint(-5, -2))

    # ── INFECTION CHECK: bite chance on bad outcomes ──
    from engine.infection import try_infect_from_combat
    result["got_infected"] = False
    char_after = queries.get_character(crew_member_id)
    if char_after and char_after["is_alive"] and not char_after["infected"]:
        if try_infect_from_combat(crew_member_id, result["result"]):
            result["got_infected"] = True

    result["character_died"] = not char_after["is_alive"] if char_after else True
    result["character_name"] = char["name"]
    result["combat_score"] = combat_score
    result["threat_rating"] = threat_rating

    return result


def _generate_loot(phase: str, bonus: bool = False, reduced: bool = False) -> dict:
    # NERFED: much less generous loot
    phase_mult = {"morning": 0.6, "afternoon": 0.8, "evening": 1.0, "midnight": 1.4}
    mult = phase_mult.get(phase, 0.8)
    if bonus:
        mult *= 1.3
    if reduced:
        mult *= 0.4

    loot = {}
    if random.random() < 0.25 * mult:
        loot["scrap"] = random.randint(1, max(1, int(3 * mult)))
    if random.random() < 0.15 * mult:
        loot["ammo"] = random.randint(1, max(1, int(2 * mult)))
    if random.random() < 0.2 * mult:
        loot["food"] = random.randint(1, max(1, int(2 * mult)))
    if random.random() < 0.05 * mult:
        loot["medicine"] = 1
    if random.random() < 0.1 * mult:
        loot["fuel"] = random.randint(1, max(1, int(2 * mult)))
    return loot


def _generate_resource_loss() -> dict:
    """On defeat, you might lose resources (scattered, stolen, broken)."""
    loss = {}
    if random.random() < 0.5:
        loss["food"] = -random.randint(1, 3)
    if random.random() < 0.3:
        loss["scrap"] = -random.randint(1, 2)
    if random.random() < 0.2:
        loss["fuel"] = -random.randint(1, 3)
    return loss


def generate_combat_narrative(result: dict) -> str:
    """Generate visceral, graphic narrative for combat outcomes."""
    name = result["character_name"]
    narratives = {
        "decisive_victory": [
            f"{name} moves like something out of a nightmare — their nightmare. The first one loses its jaw to a sideways swing, teeth and black blood spraying across the asphalt. The second catches a blade through the temple. It drops mid-lunge. The third doesn't even get close. Clean. Surgical. Over.",
            f"Three of them come around the corner and {name} puts them down before the scream finishes leaving your throat. Head shots. Each one. The bodies hit the ground in sequence — thud, thud, thud — like a drumroll. {name} doesn't even check. Already moving on.",
            f"{name} handles it with a violence that's almost beautiful. The first one's skull caves in with a wet crunch. The second gets its throat opened from ear to ear, black ichor pouring down its chest in sheets. The third is already falling by the time {name} turns to face it. Not a scratch. Not a drop of wasted effort.",
        ],
        "victory": [
            f"{name} takes a claw across the forearm — three ragged lines that immediately well with bright red blood, skin peeling back in flaps. {name} screams, more anger than pain, and buries the blade in the thing's skull so hard it sticks. Yanks it free with a sound like pulling a boot out of mud. The zombie crumples. {name} grabs the wound, blood streaming between white-knuckled fingers.",
            f"A messy fight. One of them gets its teeth into {name}'s jacket — just the jacket, thank God — and {name} drives an elbow into its face hard enough to shatter what's left of the nasal bone. Rotting cartilage collapses inward. Another one rakes its nails down {name}'s back, leaving four parallel trenches in the skin that bloom red instantly. {name} spins, swings, connects. Bone snaps. It goes down.",
            f"The first one dies easy. The second one doesn't. It gets its hands around {name}'s throat and SQUEEZES — fingernails punching through skin, blood running down {name}'s collar in warm rivulets. {name}'s face goes red, then purple. A desperate knee to the thing's midsection does nothing. Finally, {name} jams both thumbs into its eye sockets — the eyes pop with a wet squelch — and the grip loosens enough to break free. {name} gasps, coughs blood, and crushes the thing's skull against the pavement.",
        ],
        "pyrrhic": [
            f"There are too many. {name} fights like an animal — snarling, swinging, taking hits that would drop a normal person. A zombie tears a chunk of flesh from {name}'s shoulder, a strip of meat and skin ripping free with a sound like velcro. {name} SCREAMS — a raw, throat-shredding howl — and keeps swinging. Blood pours down {name}'s arm, pooling at the elbow, dripping from the fingertips. By the time the last one falls, {name} is standing in a circle of corpses, swaying, painted head to toe in a mix of red and black.",
            f"One of them tackles {name} to the ground. Its mouth opens — the jaw unhinges wider than should be possible, rows of yellow teeth framed in blackened gums — and snaps down inches from {name}'s face. {name} gets an arm up just in time. The teeth sink into the forearm guard instead, cracking through plastic and into the padding beneath. Another one piles on, clawing at {name}'s legs, nails tearing through denim and into the flesh of the thigh. {name} thrashes, screams, drives a knee into the first one's chest cavity — ribs crack and give way with a sickening crunch — and rolls free. Standing hurts. Everything hurts.",
            f"The fight goes sideways fast. A zombie gets behind {name} and rakes its fingers across {name}'s face — a line of fire from temple to jawline, skin splitting open, blood sheeting into {name}'s left eye. Half-blind, {name} swings wild, connecting with something soft that bursts on impact. Another one slams into {name}'s side — the crack of a rib breaking is audible from the bus. {name} doubles over, vomits, and somehow keeps fighting. The zombies die. {name} lives. The word 'lives' is doing a lot of heavy lifting.",
        ],
        "defeat": [
            f"They swarm {name} like water over a rock. There are too many hands, too many mouths, too many broken fingers reaching and grabbing and tearing. {name} disappears under the pile — you catch glimpses through the mass of rotting bodies: a hand reaching up, fingers clawing at air, then dragged back down. The screaming is the worst part. It starts as words — \"HELP ME HELP ME\" — and becomes something wordless and raw. By the time you drag {name} free, the screaming has stopped. {name}'s clothes are shredded. Skin is visible underneath — torn, bitten, bleeding from a dozen wounds that look like mouths.",
            f"{name} goes down hard. A zombie drives {name}'s face into the concrete — the impact splits the skin above the eyebrow, and blood floods the left eye in a warm red curtain. More of them pile on. You hear fabric tearing, then the wetter sound of skin tearing, then {name}'s voice breaking apart into screams that don't sound human anymore. Boots kick. Hands claw. You see {name}'s arm at a wrong angle — dislocated or broken, impossible to tell through the blood. You drag {name} into the bus by the collar. {name}'s body leaves a smear on the steps.",
            f"A disaster. {name} is grabbed by three of them at once — one on each arm, one with its fingers hooked into {name}'s belt. They pull in different directions. {name}'s shoulder makes a sound like a chicken wing being torn apart. The scream that comes out of {name} is inhuman — a shriek so loud and raw it hurts your ears from inside the bus. Blood sprays from the shoulder where something has torn loose. You gun the engine, the bus lurches forward, and someone grabs {name}'s outstretched hand just in time. {name} is dragged aboard, sobbing, bleeding, shaking so hard the bus seat vibrates.",
        ],
    }
    options = narratives.get(result["result"], ["The fight resolves."])
    return random.choice(options)

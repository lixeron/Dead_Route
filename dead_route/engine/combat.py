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
    if result["damage_taken"] > 0:
        queries.damage_character(crew_member_id, result["damage_taken"])

    if result["bus_damage"] > 0:
        new_armor = queries.damage_bus(result["bus_damage"])
        result["bus_destroyed"] = new_armor <= 0

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
        # Everyone's morale takes a hit
        for c in queries.get_alive_npcs():
            queries.change_trust(c["id"], random.randint(-5, -2))

    char_after = queries.get_character(crew_member_id)
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
    name = result["character_name"]
    narratives = {
        "decisive_victory": [
            f"{name} doesn't even break a sweat. Clean kills, no wasted motion.",
            f"It's over in seconds. {name} moves like a machine.",
            f"{name} handles it with brutal efficiency. Not a scratch.",
        ],
        "victory": [
            f"{name} takes a hit but puts them down. Blood on the sleeve, but nothing critical.",
            f"A messy fight. {name} comes out on top, but not unscathed.",
            f"The zombies go down hard. {name} catches a claw across the arm. It bleeds freely.",
        ],
        "pyrrhic": [
            f"{name} barely makes it out. Torn clothes, deep wounds, shaking hands. The zombies are dead, but the cost is steep.",
            f"It's ugly. {name} goes down, gets back up, goes down again. The last one stops twitching, and {name} collapses against the bus.",
            f"Too many of them. {name} fights through but the bus takes a beating too. Dents, cracks, and something leaking underneath.",
        ],
        "defeat": [
            f"There are too many. {name} is overwhelmed. By the time backup arrives, blood is everywhere.",
            f"{name} fights hard but it's not enough. The horde surges forward. Supplies scatter across the ground as you barely pull {name} back to the bus.",
            f"A disaster. {name} is swarmed. The bus rocks on its axles as bodies slam into the sides. You floor it and don't look back.",
        ],
    }
    options = narratives.get(result["result"], ["The fight resolves."])
    return random.choice(options)

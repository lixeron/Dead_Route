"""
Combat resolution: stat-check encounters and boss fights.
"""

import random
from db import queries

# Phase risk multipliers
PHASE_THREAT = {
    "morning": 1.0,
    "afternoon": 1.3,
    "evening": 1.6,
    "midnight": 2.0,
}


def stat_check_combat(crew_member_id: int, base_threat: int = 10) -> dict:
    """
    Resolve a standard combat encounter via stat check.
    Returns dict with: result, damage_taken, ammo_used, loot, narrative_key
    """
    state = queries.get_game_state()
    char = queries.get_character(crew_member_id)
    bus = queries.get_bus()
    resources = queries.get_resources()

    if not char:
        return {"result": "error", "damage_taken": 0, "ammo_used": 0, "loot": {}}

    # Calculate combat score
    combat_skill = char["combat"]
    weapon_bonus = 0
    if queries.has_upgrade("roof_turret"):
        weapon_bonus += 3
    if queries.has_upgrade("cow_catcher"):
        weapon_bonus += 2

    # Ammo bonus
    ammo_bonus = min(3, resources.get("ammo", 0))  # up to +3 from ammo
    has_ammo = resources.get("ammo", 0) > 0

    combat_score = combat_skill + weapon_bonus + ammo_bonus + random.randint(-2, 3)

    # Calculate threat
    phase_mult = PHASE_THREAT.get(state["current_phase"], 1.0)
    threat_mult = 1 + (state["threat_level"] - 1) * 0.1
    threat_rating = int(base_threat * phase_mult * threat_mult) + random.randint(-2, 2)

    margin = combat_score - threat_rating
    ammo_used = 1 if has_ammo else 0

    if margin >= 8:
        # Decisive victory
        result = {
            "result": "decisive_victory",
            "damage_taken": 0,
            "bus_damage": 0,
            "ammo_used": ammo_used,
            "loot": _generate_loot(state["current_phase"], bonus=True),
        }
    elif margin >= 2:
        # Victory
        result = {
            "result": "victory",
            "damage_taken": random.randint(5, 15),
            "bus_damage": random.randint(0, 5),
            "ammo_used": ammo_used,
            "loot": _generate_loot(state["current_phase"]),
        }
    elif margin >= -3:
        # Pyrrhic victory
        result = {
            "result": "pyrrhic",
            "damage_taken": random.randint(15, 30),
            "bus_damage": random.randint(5, 15),
            "ammo_used": ammo_used + 1,
            "loot": _generate_loot(state["current_phase"], reduced=True),
        }
    else:
        # Defeat
        result = {
            "result": "defeat",
            "damage_taken": random.randint(25, 50),
            "bus_damage": random.randint(10, 25),
            "ammo_used": ammo_used,
            "loot": {},
        }

    # Apply consequences
    if result["damage_taken"] > 0:
        queries.damage_character(crew_member_id, result["damage_taken"])
    if result["bus_damage"] > 0:
        queries.damage_bus(result["bus_damage"])
    actual_ammo = min(result["ammo_used"], resources.get("ammo", 0))
    if actual_ammo > 0:
        queries.update_resources(ammo=-actual_ammo)
    result["ammo_used"] = actual_ammo

    # Apply loot
    loot = result["loot"]
    if loot:
        queries.update_resources(**loot)

    # Check for character death
    char_after = queries.get_character(crew_member_id)
    result["character_died"] = not char_after["is_alive"] if char_after else True
    result["character_name"] = char["name"]
    result["combat_score"] = combat_score
    result["threat_rating"] = threat_rating

    return result


def _generate_loot(phase: str, bonus: bool = False, reduced: bool = False) -> dict:
    """Generate loot based on phase and modifiers."""
    phase_mult = {"morning": 1.0, "afternoon": 1.25, "evening": 1.5, "midnight": 2.0}
    mult = phase_mult.get(phase, 1.0)
    if bonus:
        mult *= 1.5
    if reduced:
        mult *= 0.5

    loot = {}
    # Random loot rolls
    if random.random() < 0.4 * mult:
        loot["scrap"] = random.randint(1, int(4 * mult))
    if random.random() < 0.3 * mult:
        loot["ammo"] = random.randint(1, int(3 * mult))
    if random.random() < 0.2 * mult:
        loot["food"] = random.randint(1, int(3 * mult))
    if random.random() < 0.1 * mult:
        loot["medicine"] = random.randint(1, max(1, int(2 * mult)))
    if random.random() < 0.15 * mult:
        loot["fuel"] = random.randint(1, int(3 * mult))

    return loot


def generate_combat_narrative(result: dict) -> str:
    """Generate narrative text for a combat outcome."""
    name = result["character_name"]

    narratives = {
        "decisive_victory": [
            f"{name} doesn't even break a sweat. Three zombies down before they can get close. Clean kills.",
            f"It's over in seconds. {name} moves like they've done this a thousand times. Maybe they have.",
            f"{name} handles it with brutal efficiency. Not a scratch. You find some useful stuff on the bodies.",
        ],
        "victory": [
            f"{name} takes a hit but puts them down. Blood on the sleeve, but nothing serious.",
            f"A messy fight. {name} comes out on top, but not unscathed. Could've been worse.",
            f"The zombies go down hard. {name} catches a claw across the arm — just a scratch. Probably.",
        ],
        "pyrrhic": [
            f"{name} barely makes it out. Torn clothes, shallow wounds, and a haunted look. The zombies are dead, but at a cost.",
            f"It's ugly. {name} goes down, gets back up, goes down again. Finally the last one stops twitching. {name} limps back, bleeding.",
            f"Too many of them. {name} fights through it but takes serious hits. The bus needs patching too.",
        ],
        "defeat": [
            f"There are too many. {name} is overwhelmed almost immediately. By the time backup arrives, the damage is done.",
            f"{name} fights hard but it's not enough. The horde surges forward. You barely pull {name} back to the bus.",
            f"A disaster. {name} is swarmed. The bus takes hits from all sides. You floor it and don't look back.",
        ],
    }

    options = narratives.get(result["result"], ["The fight resolves."])
    return random.choice(options)

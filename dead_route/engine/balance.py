"""
Central balance configuration for Dead Route.

ALL tunable game numbers live here. No magic numbers scattered
across modules. When you want to adjust difficulty, this is the
only file you need to touch.

Three difficulty eras:
  Days 1-7:   BREATHING   — Learn the systems, find your crew
  Days 8-14:  THE SQUEEZE — Moral complexity, real consequences
  Days 15+:   ENDGAME     — Impossible choices, scarce everything
"""

from db import queries


def get_era(day: int = 0) -> str:
    """Get the current difficulty era."""
    if day <= 0:
        state = queries.get_game_state()
        day = state["current_day"]
    if day <= 7:
        return "breathing"
    elif day <= 14:
        return "squeeze"
    else:
        return "endgame"


# ── Starting Resources ─────────────────────────────────────

STARTING_RESOURCES = {
    "fuel": 20,
    "food": 8,
    "scrap": 4,
    "ammo": 5,
    "medicine": 1,
}

STARTING_PLAYER_STATS = {
    "base": 3,       # Base skill level
    "boosted": 6,    # Boosted skill from item choice
}


# ── Combat Encounter Rates ─────────────────────────────────
# Chance of combat when exploring, by phase and era.

COMBAT_CHANCE = {
    "breathing": {
        "morning": 0.15, "afternoon": 0.25,
        "evening": 0.40, "midnight": 0.65,
    },
    "squeeze": {
        "morning": 0.25, "afternoon": 0.40,
        "evening": 0.60, "midnight": 0.80,
    },
    "endgame": {
        "morning": 0.35, "afternoon": 0.50,
        "evening": 0.70, "midnight": 0.90,
    },
}


# ── Scavenging Yields ──────────────────────────────────────
# Multiplier on loot found when scavenging peacefully.

SCAVENGE_MULTIPLIER = {
    "breathing": 1.5,    # Generous early — player learns the loop
    "squeeze":   1.0,    # Normal
    "endgame":   0.65,   # Scarce — every find matters
}


# ── Combat Loot Multiplier ────────────────────────────────

COMBAT_LOOT_MULTIPLIER = {
    "breathing": 1.3,
    "squeeze":   1.0,
    "endgame":   0.7,
}


# ── Fuel Leak ──────────────────────────────────────────────

FUEL_LEAK = {
    "breathing": 1,     # Drip
    "squeeze":   2,     # Steady leak
    "endgame":   2,     # Same — endgame difficulty is choices, not numbers
}


# ── Food Drain ─────────────────────────────────────────────
# How many crew members per unit of food consumed per meal phase.

FOOD_DRAIN_RATIO = {
    "breathing": 3,     # 1 food per 3 crew per meal (lenient)
    "squeeze":   2,     # 1 food per 2 crew per meal (normal)
    "endgame":   2,     # Same ratio — food is scarce, not drain is harsh
}


# ── Scar Chance ────────────────────────────────────────────
# Probability of permanent scar after combat outcomes.

SCAR_CHANCE = {
    "breathing": {
        "pyrrhic": 0.0,     # No scars in learning phase
        "defeat":  0.0,
    },
    "squeeze": {
        "pyrrhic": 0.12,
        "defeat":  0.25,
    },
    "endgame": {
        "pyrrhic": 0.18,
        "defeat":  0.35,
    },
}


# ── Infection Chance ───────────────────────────────────────
# Probability of bite during combat.

INFECTION_CHANCE = {
    "breathing": {
        "pyrrhic": 0.0,     # No infections while learning
        "defeat":  0.0,
    },
    "squeeze": {
        "pyrrhic": 0.10,
        "defeat":  0.20,
    },
    "endgame": {
        "pyrrhic": 0.15,
        "defeat":  0.30,
    },
}


# ── Threat Escalation ─────────────────────────────────────

THREAT_ESCALATION_DAYS = 5      # Threat increases every N days
THREAT_COMBAT_SCALING = 0.12    # Per-level increase in combat difficulty


# ── Event Day Gates ────────────────────────────────────────
# Which events can appear in which era.

EVENT_DAY_GATES = {
    # Always available
    "roadside_stranger":     {"min_day": 1,  "max_day": 999},
    "abandoned_gas_station": {"min_day": 1,  "max_day": 999},
    "supply_cache":          {"min_day": 2,  "max_day": 999},
    "crew_argument":         {"min_day": 3,  "max_day": 999},

    # Squeeze era (moral complexity)
    "dying_scientist":       {"min_day": 8,  "max_day": 999},
    "infected_child":        {"min_day": 8,  "max_day": 999},
    "radio_signal":          {"min_day": 8,  "max_day": 999},
    "mercy_on_the_bridge":   {"min_day": 5,  "max_day": 999},

    # Endgame (darkest events)
    "meat_grinder_outpost":  {"min_day": 12, "max_day": 999},
    "the_nursery":           {"min_day": 10, "max_day": 999},
}


# ── Coin Flip Stakes Scaling ──────────────────────────────

COIN_REWARD_MULTIPLIER = {
    "breathing": 1.0,
    "squeeze":   1.0,
    "endgame":   1.3,    # Slightly better rewards to match the risk
}

COIN_PENALTY_MULTIPLIER = {
    "breathing": 0.7,    # Softer penalties while learning
    "squeeze":   1.0,
    "endgame":   1.2,    # Harsher penalties
}


# ── Rest Healing ───────────────────────────────────────────

REST_HEALING = {
    "breathing": {"morning": 12, "afternoon": 16, "evening": 22, "midnight": 28},
    "squeeze":   {"morning": 8,  "afternoon": 12, "evening": 18, "midnight": 22},
    "endgame":   {"morning": 6,  "afternoon": 10, "evening": 14, "midnight": 18},
}


# ── Random Event Frequency ────────────────────────────────

EVENT_CHANCE_PER_PHASE = {
    "breathing": 0.20,    # Fewer interruptions while learning
    "squeeze":   0.25,
    "endgame":   0.30,    # More events — the world is more chaotic
}


# ── Utility ────────────────────────────────────────────────

def get_balance(category: str, sub_key: str = None):
    """
    Quick access to any balance value for the current era.
    Usage:
        get_balance("COMBAT_CHANCE")["morning"]
        get_balance("SCAVENGE_MULTIPLIER")
        get_balance("SCAR_CHANCE")["pyrrhic"]
    """
    era = get_era()
    tables = {
        "COMBAT_CHANCE": COMBAT_CHANCE,
        "SCAVENGE_MULTIPLIER": SCAVENGE_MULTIPLIER,
        "COMBAT_LOOT_MULTIPLIER": COMBAT_LOOT_MULTIPLIER,
        "FUEL_LEAK": FUEL_LEAK,
        "FOOD_DRAIN_RATIO": FOOD_DRAIN_RATIO,
        "SCAR_CHANCE": SCAR_CHANCE,
        "INFECTION_CHANCE": INFECTION_CHANCE,
        "REST_HEALING": REST_HEALING,
        "EVENT_CHANCE_PER_PHASE": EVENT_CHANCE_PER_PHASE,
        "COIN_REWARD_MULTIPLIER": COIN_REWARD_MULTIPLIER,
        "COIN_PENALTY_MULTIPLIER": COIN_PENALTY_MULTIPLIER,
    }
    table = tables.get(category)
    if table is None:
        return None
    val = table.get(era, table.get("squeeze"))
    if sub_key and isinstance(val, dict):
        return val.get(sub_key)
    return val

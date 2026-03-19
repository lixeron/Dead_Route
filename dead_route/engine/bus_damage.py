"""
Localized bus damage system.
4 components (engine, windows, armor_plating, wheels) × 4 states.
Combat targets specific components. Repair costs scrap + time.
"""

import random
from db import queries


# Repair costs per state transition (repairing one level)
REPAIR_COSTS = {
    "destroyed": 8,   # destroyed -> damaged
    "damaged": 5,     # damaged -> worn
    "worn": 3,        # worn -> intact
}

# Weight for random targeting — armor gets hit most, engine least
TARGET_WEIGHTS = {
    "armor_plating": 40,
    "windows": 25,
    "wheels": 20,
    "engine": 15,
}


def apply_bus_damage(raw_damage: int) -> dict:
    """
    Apply damage to the bus by targeting a random component.
    Armor plating absorbs a percentage before the hit degrades a part.
    
    Returns dict with:
        component_hit, old_state, new_state, damage_absorbed,
        effective_damage, narrative
    """
    # Armor absorbs some damage first
    absorption = queries.get_damage_absorption()
    absorbed = int(raw_damage * absorption)
    effective = raw_damage - absorbed

    # Determine if a component degrades
    # Threshold: effective damage >= 10 always degrades,
    # lower damage has a proportional chance
    degrade_chance = min(1.0, effective / 15.0)

    result = {
        "damage_absorbed": absorbed,
        "effective_damage": effective,
        "component_hit": None,
        "old_state": None,
        "new_state": None,
        "narrative": "",
    }

    if effective <= 0:
        result["narrative"] = (
            "The armor plating takes the full impact. Dented, but holding."
        )
        return result

    if random.random() > degrade_chance:
        result["narrative"] = _minor_damage_narrative()
        return result

    # Pick a component to degrade (weighted random)
    component = _pick_target()
    old_state, new_state = queries.degrade_component(component)

    result["component_hit"] = component
    result["old_state"] = old_state
    result["new_state"] = new_state

    if old_state == new_state:
        # Already destroyed — damage bleeds through to crew
        result["narrative"] = _already_destroyed_narrative(component)
        result["bleed_through"] = True
    else:
        result["narrative"] = _degradation_narrative(component, old_state, new_state)

    return result


def _pick_target() -> str:
    """Weighted random component targeting."""
    components = list(TARGET_WEIGHTS.keys())
    weights = [TARGET_WEIGHTS[c] for c in components]

    # Bias toward already-damaged components (damaged things break more)
    all_comps = queries.get_all_components()
    for i, comp in enumerate(components):
        state = all_comps.get(comp, {}).get("state", "intact")
        if state == "worn":
            weights[i] = int(weights[i] * 1.2)
        elif state == "damaged":
            weights[i] = int(weights[i] * 1.4)
        elif state == "destroyed":
            weights[i] = max(1, weights[i] // 3)  # Less likely to hit already-destroyed

    total = sum(weights)
    roll = random.randint(1, total)
    cumulative = 0
    for i, w in enumerate(weights):
        cumulative += w
        if roll <= cumulative:
            return components[i]
    return components[-1]


def get_repair_options() -> list[dict]:
    """
    Get list of components that can be repaired with their costs.
    Returns list of dicts: {component, name, current_state, repair_to, cost}
    """
    all_comps = queries.get_all_components()
    options = []

    for comp_key, comp_data in all_comps.items():
        state = comp_data["state"]
        if state == "intact":
            continue  # Nothing to repair

        cost = REPAIR_COSTS.get(state, 5)
        state_idx = queries.COMPONENT_STATES.index(state)
        repair_to = queries.COMPONENT_STATES[state_idx - 1]

        options.append({
            "component": comp_key,
            "name": comp_data["name"],
            "current_state": state,
            "repair_to": repair_to,
            "cost": cost,
            "description": comp_data["stats"].get("desc", ""),
        })

    return options


def get_bus_status_text() -> list[str]:
    """Get formatted status lines for all bus components."""
    all_comps = queries.get_all_components()
    lines = []

    state_symbols = {
        "intact": ("OK", "green"),
        "worn": ("WORN", "yellow"),
        "damaged": ("DMG", "red"),
        "destroyed": ("XXX", "bright_red"),
    }

    for comp_key in ["engine", "armor_plating", "windows", "wheels"]:
        comp = all_comps.get(comp_key, {})
        name = comp.get("name", comp_key)
        state = comp.get("state", "intact")
        desc = comp.get("stats", {}).get("desc", "")
        symbol, _ = state_symbols.get(state, ("???", "white"))
        lines.append(f"{name}: [{symbol}] {desc}")

    return lines


def check_bus_immobilized() -> bool:
    """Check if the bus cannot move due to destroyed engine or wheels."""
    return not queries.can_bus_travel()


def get_passive_effects() -> dict:
    """
    Get all passive effects from component states.
    Called each phase by passive systems.
    """
    return {
        "fuel_multiplier": queries.get_fuel_multiplier(),
        "rest_multiplier": queries.get_rest_multiplier(),
        "damage_absorption": queries.get_damage_absorption(),
        "can_travel": queries.can_bus_travel(),
        "can_flee": queries.can_flee_combat(),
        "window_morale_drain": queries.get_window_morale_drain(),
    }


# ── Narrative generators ──────────────────────────────────

def _minor_damage_narrative() -> str:
    """Narrative for hits that don't degrade a component."""
    return random.choice([
        "The bus shudders from the impact. Dents, but nothing critical.",
        "Metal screams as something scrapes along the side. Cosmetic damage only.",
        "A hard jolt rocks the bus. Everything still seems to be working.",
        "Something crunches underneath. You hold your breath — systems still running.",
    ])


def _already_destroyed_narrative(component: str) -> str:
    """Narrative for hitting an already-destroyed component."""
    narrs = {
        "engine": "The engine takes another hit. It's already dead — the damage tears into the bus frame instead.",
        "windows": "Glass that isn't there can't break again. The wind howls through the open frames.",
        "armor_plating": "There's nothing left to absorb the blow. The impact goes straight through.",
        "wheels": "The shredded tires offer no cushion. Metal grinds against asphalt.",
    }
    return narrs.get(component, "The bus takes a hit where it hurts most.")


def _degradation_narrative(component: str, old_state: str, new_state: str) -> str:
    """Narrative for a component degrading one level."""
    key = f"{component}_{old_state}_to_{new_state}"

    narratives = {
        # Engine
        "engine_intact_to_worn":
            "Something under the hood pops. The engine stutters, catches, keeps running — but rougher now. You can feel it burning hotter.",
        "engine_worn_to_damaged":
            "A grinding sound erupts from the engine bay. Black smoke billows from the hood. She's still running, but barely. Fuel consumption is going to spike.",
        "engine_damaged_to_destroyed":
            "The engine makes a sound like a gunshot and dies. Silence. The bus rolls to a stop under its own momentum. The engine is gone.",

        # Windows
        "windows_intact_to_worn":
            "A web of cracks spiders across the side windows. They're holding, but one more solid hit and they're done.",
        "windows_worn_to_damaged":
            "Glass shatters inward, spraying the seats. Cold air and the stench of rot pour through the gaps. Resting won't be the same.",
        "windows_damaged_to_destroyed":
            "The last intact pane explodes. Every window is gone. The bus is open to the elements — and to anything that wants to reach inside.",

        # Armor Plating
        "armor_plating_intact_to_worn":
            "The welded plates buckle inward. Still attached, still protecting — but the next hit will be worse.",
        "armor_plating_worn_to_damaged":
            "A section of plating tears free and clatters onto the road. The bus's flank is exposed. You can see daylight through the gaps.",
        "armor_plating_damaged_to_destroyed":
            "The last armor plate rips away with a shriek of metal. The bus is naked. Every hit from now on goes straight through.",

        # Wheels
        "wheels_intact_to_worn":
            "The bus lurches as a tire takes damage. The tread is shredded on one side. Still rolling, but it's pulling hard to the right.",
        "wheels_worn_to_damaged":
            "A tire blows with a bang that sounds like a gunshot. The bus drops on one corner, grinding sparks. No way you're outrunning anything now.",
        "wheels_damaged_to_destroyed":
            "The rim collapses. The bus drops hard, metal scraping asphalt in a shower of sparks. You're not going anywhere until this is fixed.",
    }

    return narratives.get(key, f"The {queries.COMPONENTS[component]['name']} takes a hit. It's getting worse.")

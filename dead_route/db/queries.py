"""
All SQL read/write operations.
No game logic or display logic here — pure data access.
"""

import json
import sqlite3
from .database import get_connection


# ── Game State ─────────────────────────────────────────────

def create_game(player_name: str, pronouns: str, subj: str, obj: str, poss: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO game_state (id, player_name, pronouns, subj_pronoun, obj_pronoun, poss_pronoun) "
        "VALUES (1, ?, ?, ?, ?, ?)",
        (player_name, pronouns, subj, obj, poss)
    )
    conn.execute("INSERT INTO resources (id) VALUES (1)")
    conn.execute("INSERT INTO bus (id) VALUES (1)")
    conn.commit()
    conn.close()


def get_game_state() -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM game_state WHERE id = 1").fetchone()
    conn.close()
    if row:
        return dict(row)
    return {}


def update_game_state(**kwargs):
    conn = get_connection()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values())
    conn.execute(f"UPDATE game_state SET {sets} WHERE id = 1", vals)
    conn.commit()
    conn.close()


def advance_phase() -> tuple[int, str]:
    """Advance to the next phase. Returns (day, phase)."""
    phases = ["morning", "afternoon", "evening", "midnight"]
    state = get_game_state()
    current_idx = phases.index(state["current_phase"])

    if current_idx < 3:
        new_phase = phases[current_idx + 1]
        new_day = state["current_day"]
    else:
        new_phase = "morning"
        new_day = state["current_day"] + 1

    # Check threat escalation every 5 days
    new_threat = state["threat_level"]
    if new_day > state["current_day"] and new_day % 5 == 0:
        new_threat += 1

    update_game_state(
        current_day=new_day,
        current_phase=new_phase,
        threat_level=new_threat
    )
    return new_day, new_phase


# ── Resources ──────────────────────────────────────────────

def get_resources() -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM resources WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else {}


def update_resources(**kwargs):
    conn = get_connection()
    sets = ", ".join(f"{k} = MAX(0, {k} + ?)" for k in kwargs)
    vals = list(kwargs.values())
    conn.execute(f"UPDATE resources SET {sets} WHERE id = 1", vals)
    conn.commit()
    conn.close()


def set_resources(**kwargs):
    conn = get_connection()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values())
    conn.execute(f"UPDATE resources SET {sets} WHERE id = 1", vals)
    conn.commit()
    conn.close()


def has_resources(**kwargs) -> bool:
    res = get_resources()
    for k, v in kwargs.items():
        if res.get(k, 0) < v:
            return False
    return True


# ── Bus ────────────────────────────────────────────────────

def get_bus() -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM bus WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else {}


def update_bus(**kwargs):
    conn = get_connection()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values())
    conn.execute(f"UPDATE bus SET {sets} WHERE id = 1", vals)
    conn.commit()
    conn.close()


def damage_bus(amount: int) -> int:
    bus = get_bus()
    new_armor = max(0, bus["armor"] - amount)
    update_bus(armor=new_armor)
    return new_armor


def repair_bus(amount: int) -> int:
    bus = get_bus()
    new_armor = min(bus["armor_max"], bus["armor"] + amount)
    update_bus(armor=new_armor)
    return new_armor


# ── Characters ─────────────────────────────────────────────

def create_character(name: str, is_player: bool = False, **stats) -> int:
    conn = get_connection()
    defaults = {
        "hp": 100, "hp_max": 100, "stamina": 100, "stamina_max": 100,
        "combat": 3, "medical": 3, "mechanical": 3, "scavenging": 3,
        "trust": 100 if is_player else 50, "personality": "neutral",
        "backstory": "", "is_romanceable": 0, "recruited_day": 1
    }
    defaults.update(stats)

    cursor = conn.execute(
        "INSERT INTO characters (name, is_player, hp, hp_max, stamina, stamina_max, "
        "combat, medical, mechanical, scavenging, trust, personality, backstory, "
        "is_romanceable, recruited_day) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, int(is_player), defaults["hp"], defaults["hp_max"],
         defaults["stamina"], defaults["stamina_max"],
         defaults["combat"], defaults["medical"], defaults["mechanical"],
         defaults["scavenging"], defaults["trust"], defaults["personality"],
         defaults["backstory"], defaults["is_romanceable"], defaults["recruited_day"])
    )
    char_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return char_id


def get_character(char_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM characters WHERE id = ?", (char_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_player() -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM characters WHERE is_player = 1").fetchone()
    conn.close()
    return dict(row) if row else None


def get_alive_crew() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM characters WHERE is_alive = 1 ORDER BY is_player DESC, id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_alive_npcs() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM characters WHERE is_alive = 1 AND is_player = 0 ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_character(char_id: int, **kwargs):
    conn = get_connection()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values())
    vals.append(char_id)
    conn.execute(f"UPDATE characters SET {sets} WHERE id = ?", vals)
    conn.commit()
    conn.close()


def change_trust(char_id: int, delta: int) -> int:
    char = get_character(char_id)
    if not char:
        return 0
    new_trust = max(1, min(100, char["trust"] + delta))
    update_character(char_id, trust=new_trust)
    return new_trust


def damage_character(char_id: int, amount: int) -> int:
    char = get_character(char_id)
    if not char:
        return 0
    new_hp = max(0, char["hp"] - amount)
    updates = {"hp": new_hp}
    if new_hp == 0:
        updates["is_alive"] = 0
    update_character(char_id, **updates)
    return new_hp


def heal_character(char_id: int, amount: int) -> int:
    char = get_character(char_id)
    if not char:
        return 0
    new_hp = min(char["hp_max"], char["hp"] + amount)
    update_character(char_id, hp=new_hp)
    return new_hp


def crew_count() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as cnt FROM characters WHERE is_alive = 1").fetchone()
    conn.close()
    return row["cnt"]


# ── Map ────────────────────────────────────────────────────

def create_map_node(name: str, node_type: str, description: str = "",
                    fuel_cost: int = 5, days_to_clear: int = 1,
                    is_fork: bool = False, is_meridian: bool = False,
                    node_order: int = 0) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO map_nodes (name, node_type, description, fuel_cost, days_to_clear, "
        "is_fork, is_meridian_path, node_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (name, node_type, description, fuel_cost, days_to_clear,
         int(is_fork), int(is_meridian), node_order)
    )
    node_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return node_id


def create_map_edge(from_id: int, to_id: int, description: str = "",
                    requires_fragment: bool = False):
    conn = get_connection()
    conn.execute(
        "INSERT INTO map_edges (from_node_id, to_node_id, description, requires_map_fragment) "
        "VALUES (?, ?, ?, ?)",
        (from_id, to_id, description, int(requires_fragment))
    )
    conn.commit()
    conn.close()


def get_current_node() -> dict | None:
    state = get_game_state()
    if not state.get("current_node_id"):
        return None
    conn = get_connection()
    row = conn.execute("SELECT * FROM map_nodes WHERE id = ?",
                       (state["current_node_id"],)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_next_nodes(from_node_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT mn.*, me.description as edge_description, me.requires_map_fragment "
        "FROM map_edges me JOIN map_nodes mn ON me.to_node_id = mn.id "
        "WHERE me.from_node_id = ? ORDER BY mn.id",
        (from_node_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_node_visited(node_id: int):
    conn = get_connection()
    conn.execute("UPDATE map_nodes SET is_visited = 1 WHERE id = ?", (node_id,))
    conn.commit()
    conn.close()


# ── Choice Flags ───────────────────────────────────────────

def set_flag(key: str, value: bool = True):
    state = get_game_state()
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO choice_flags (flag_key, flag_value, set_on_day) VALUES (?, ?, ?)",
        (key, int(value), state.get("current_day", 1))
    )
    conn.commit()
    conn.close()


def get_flag(key: str) -> bool:
    conn = get_connection()
    row = conn.execute("SELECT flag_value FROM choice_flags WHERE flag_key = ?", (key,)).fetchone()
    conn.close()
    return bool(row["flag_value"]) if row else False


def get_all_flags() -> dict:
    conn = get_connection()
    rows = conn.execute("SELECT flag_key, flag_value FROM choice_flags").fetchall()
    conn.close()
    return {r["flag_key"]: bool(r["flag_value"]) for r in rows}


# ── Event Log ──────────────────────────────────────────────

def log_event(event_key: str, choice: str, outcome: str):
    state = get_game_state()
    conn = get_connection()
    conn.execute(
        "INSERT INTO event_log (event_key, fired_on_day, choice_made, outcome) VALUES (?, ?, ?, ?)",
        (event_key, state.get("current_day", 1), choice, outcome)
    )
    conn.commit()
    conn.close()


def event_fired(event_key: str) -> bool:
    conn = get_connection()
    row = conn.execute("SELECT id FROM event_log WHERE event_key = ?", (event_key,)).fetchone()
    conn.close()
    return row is not None


def get_event_count(event_key: str) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM event_log WHERE event_key = ?", (event_key,)
    ).fetchone()
    conn.close()
    return row["cnt"]


# ── Bus Upgrades ───────────────────────────────────────────

def install_upgrade(upgrade_key: str):
    state = get_game_state()
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO bus_upgrades (upgrade_key, installed_day) VALUES (?, ?)",
        (upgrade_key, state.get("current_day", 1))
    )
    conn.commit()
    conn.close()


def has_upgrade(upgrade_key: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM bus_upgrades WHERE upgrade_key = ?", (upgrade_key,)
    ).fetchone()
    conn.close()
    return row is not None


def get_installed_upgrades() -> list[str]:
    conn = get_connection()
    rows = conn.execute("SELECT upgrade_key FROM bus_upgrades ORDER BY installed_day").fetchall()
    conn.close()
    return [r["upgrade_key"] for r in rows]


# ── Injuries & Morale ─────────────────────────────────────

INJURY_TYPES = {
    "none":       {"label": "Healthy",       "skill_penalty": 0,  "hp_drain": 0},
    "scratched":  {"label": "Scratched",     "skill_penalty": 0,  "hp_drain": 0},
    "wounded":    {"label": "Wounded",        "skill_penalty": 1,  "hp_drain": 3},
    "badly_hurt": {"label": "Badly Hurt",    "skill_penalty": 2,  "hp_drain": 5},
    "critical":   {"label": "Critical",      "skill_penalty": 3,  "hp_drain": 8},
    "infected":   {"label": "INFECTED",      "skill_penalty": 2,  "hp_drain": 12},
}


def set_injury(char_id: int, injury: str):
    update_character(char_id, injury=injury)


def get_effective_skill(char: dict, skill_name: str) -> int:
    """Get skill value after injury and morale penalties."""
    base = char.get(skill_name, 1)
    injury_data = INJURY_TYPES.get(char.get("injury", "none"), INJURY_TYPES["none"])
    penalty = injury_data["skill_penalty"]

    # Morale penalty
    morale = char.get("morale", 60)
    if morale < 20:
        penalty += 2
    elif morale < 40:
        penalty += 1

    # Trust penalty for NPCs
    if not char.get("is_player"):
        trust = char.get("trust", 50)
        if trust <= 20:
            penalty += 2
        elif trust <= 40:
            penalty += 1

    return max(1, base - penalty)


def apply_injury_hp_drain():
    """Apply HP drain to all injured characters. Called once per phase."""
    crew = get_alive_crew()
    died = []
    for c in crew:
        injury = c.get("injury", "none")
        drain = INJURY_TYPES.get(injury, {}).get("hp_drain", 0)
        if drain > 0:
            new_hp = damage_character(c["id"], drain)
            if new_hp <= 0:
                died.append(c["name"])
    return died


def apply_starvation():
    """
    Apply hunger effects. Called once per phase.
    Returns dict with what happened.
    """
    resources = get_resources()
    crew = get_alive_crew()
    crew_count_val = len(crew)

    result = {
        "food_consumed": 0,
        "starving": False,
        "morale_hit": False,
        "hp_lost": 0,
    }

    # Food drain: 1 food per 2 crew members per phase (rounded up)
    food_needed = max(1, (crew_count_val + 1) // 2)

    if resources["food"] >= food_needed:
        update_resources(food=-food_needed)
        result["food_consumed"] = food_needed
    elif resources["food"] > 0:
        # Partial food — eat what we have but still hurting
        update_resources(food=-resources["food"])
        result["food_consumed"] = resources["food"]
        result["starving"] = True
        result["morale_hit"] = True
        # Starvation damage
        for c in crew:
            damage_character(c["id"], 3)
            change_morale(c["id"], -5)
        result["hp_lost"] = 3
    else:
        # No food at all
        result["starving"] = True
        result["morale_hit"] = True
        for c in crew:
            damage_character(c["id"], 8)
            change_morale(c["id"], -10)
        result["hp_lost"] = 8

    return result


def apply_fuel_leak() -> int:
    """Apply passive fuel leak. Returns fuel lost."""
    bus = get_bus()
    leak = bus.get("fuel_leak", 0)
    if leak <= 0:
        return 0

    resources = get_resources()
    # Leak happens once per day (only on morning phase)
    state = get_game_state()
    if state["current_phase"] != "morning":
        return 0

    actual_loss = min(leak, resources["fuel"])
    if actual_loss > 0:
        update_resources(fuel=-actual_loss)
    return actual_loss


def change_morale(char_id: int, delta: int) -> int:
    char = get_character(char_id)
    if not char:
        return 0
    new_morale = max(0, min(100, char.get("morale", 60) + delta))
    update_character(char_id, morale=new_morale)
    return new_morale


def apply_morale_decay():
    """Passive morale decay each phase. Worse at higher threat levels."""
    state = get_game_state()
    threat = state.get("threat_level", 1)
    decay = 1 + (threat - 1)  # 1 at threat 1, 2 at threat 2, etc.

    crew = get_alive_npcs()
    for c in crew:
        change_morale(c["id"], -decay)


# ── Bus Components ─────────────────────────────────────────

COMPONENT_STATES = ["intact", "worn", "damaged", "destroyed"]

COMPONENTS = {
    "engine": {
        "name": "Engine",
        "intact":    {"fuel_mult": 1.0,  "desc": "Running steady"},
        "worn":      {"fuel_mult": 1.15, "desc": "Knocking and rough"},
        "damaged":   {"fuel_mult": 1.40, "desc": "Misfiring badly"},
        "destroyed": {"fuel_mult": 999,  "desc": "DEAD — cannot travel"},
    },
    "windows": {
        "name": "Windows",
        "intact":    {"rest_mult": 1.0,  "morale_drain": 0, "desc": "Sealed and secure"},
        "worn":      {"rest_mult": 0.75, "morale_drain": 0, "desc": "Cracked, drafty"},
        "damaged":   {"rest_mult": 0.50, "morale_drain": 2, "desc": "Shattered, exposed"},
        "destroyed": {"rest_mult": 0.0,  "morale_drain": 5, "desc": "GONE — no shelter"},
    },
    "armor_plating": {
        "name": "Armor Plating",
        "intact":    {"absorb": 0.40, "desc": "Solid protection"},
        "worn":      {"absorb": 0.25, "desc": "Dented and bent"},
        "damaged":   {"absorb": 0.10, "desc": "Barely holding"},
        "destroyed": {"absorb": 0.0,  "desc": "STRIPPED — no protection"},
    },
    "wheels": {
        "name": "Wheels",
        "intact":    {"travel_mult": 1.0,  "can_flee": True,  "desc": "Solid rubber, good tread"},
        "worn":      {"travel_mult": 1.20, "can_flee": True,  "desc": "Tread wearing thin"},
        "damaged":   {"travel_mult": 1.50, "can_flee": False, "desc": "Rim damage, can't flee"},
        "destroyed": {"travel_mult": 999,  "can_flee": False, "desc": "FLAT — cannot travel"},
    },
}


def init_bus_components():
    """Initialize all 4 bus components at 'intact'. Called on new game."""
    conn = get_connection()
    for comp in COMPONENTS:
        conn.execute(
            "INSERT OR IGNORE INTO bus_components (component, state) VALUES (?, 'intact')",
            (comp,)
        )
    conn.commit()
    conn.close()


def get_component(component: str) -> dict:
    """Get a component's current state and stats."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM bus_components WHERE component = ?", (component,)
    ).fetchone()
    conn.close()
    if not row:
        return {"component": component, "state": "intact"}
    return dict(row)


def get_all_components() -> dict[str, dict]:
    """Get all components with their current states and stat effects."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM bus_components").fetchall()
    conn.close()

    result = {}
    for r in rows:
        comp_name = r["component"]
        state = r["state"]
        comp_data = COMPONENTS.get(comp_name, {})
        state_data = comp_data.get(state, {})
        result[comp_name] = {
            "component": comp_name,
            "name": comp_data.get("name", comp_name),
            "state": state,
            "stats": state_data,
        }
    return result


def degrade_component(component: str) -> tuple[str, str]:
    """
    Degrade a component by one state level.
    Returns (old_state, new_state).
    """
    current = get_component(component)
    old_state = current["state"]
    idx = COMPONENT_STATES.index(old_state)

    if idx >= len(COMPONENT_STATES) - 1:
        return old_state, old_state  # Already destroyed

    new_state = COMPONENT_STATES[idx + 1]
    conn = get_connection()
    conn.execute(
        "UPDATE bus_components SET state = ? WHERE component = ?",
        (new_state, component)
    )
    conn.commit()
    conn.close()
    return old_state, new_state


def repair_component(component: str) -> tuple[str, str]:
    """
    Repair a component by one state level.
    Returns (old_state, new_state).
    """
    current = get_component(component)
    old_state = current["state"]
    idx = COMPONENT_STATES.index(old_state)

    if idx <= 0:
        return old_state, old_state  # Already intact

    new_state = COMPONENT_STATES[idx - 1]
    conn = get_connection()
    conn.execute(
        "UPDATE bus_components SET state = ? WHERE component = ?",
        (new_state, component)
    )
    conn.commit()
    conn.close()
    return old_state, new_state


def set_component_state(component: str, state: str):
    """Force-set a component to a specific state."""
    conn = get_connection()
    conn.execute(
        "UPDATE bus_components SET state = ? WHERE component = ?",
        (state, component)
    )
    conn.commit()
    conn.close()


def get_fuel_multiplier() -> float:
    """Get total fuel cost multiplier from engine + wheels."""
    comps = get_all_components()
    engine_mult = comps.get("engine", {}).get("stats", {}).get("fuel_mult", 1.0)
    wheel_mult = comps.get("wheels", {}).get("stats", {}).get("travel_mult", 1.0)

    # If either is destroyed, travel is impossible
    if engine_mult >= 999 or wheel_mult >= 999:
        return 999

    return engine_mult * wheel_mult


def get_rest_multiplier() -> float:
    """Get rest effectiveness multiplier from windows."""
    comps = get_all_components()
    return comps.get("windows", {}).get("stats", {}).get("rest_mult", 1.0)


def get_damage_absorption() -> float:
    """Get damage absorption percentage from armor plating."""
    comps = get_all_components()
    return comps.get("armor_plating", {}).get("stats", {}).get("absorb", 0.0)


def can_bus_travel() -> bool:
    """Check if the bus is capable of traveling (engine + wheels not destroyed)."""
    comps = get_all_components()
    engine_state = comps.get("engine", {}).get("state", "intact")
    wheels_state = comps.get("wheels", {}).get("state", "intact")
    return engine_state != "destroyed" and wheels_state != "destroyed"


def can_flee_combat() -> bool:
    """Check if wheels are good enough to flee."""
    comps = get_all_components()
    return comps.get("wheels", {}).get("stats", {}).get("can_flee", True)


def get_window_morale_drain() -> int:
    """Get passive morale drain from damaged/destroyed windows."""
    comps = get_all_components()
    return comps.get("windows", {}).get("stats", {}).get("morale_drain", 0)


# ── Infection Tracking ─────────────────────────────────────

def infect_character(char_id: int):
    """Mark a character as infected. Starts the clock."""
    state = get_game_state()
    update_character(
        char_id,
        infected=1,
        infection_day=state["current_day"],
        infection_stage=0
    )


def advance_infection(char_id: int) -> int:
    """Advance infection by one stage. Returns new stage (0-4)."""
    char = get_character(char_id)
    if not char or not char["infected"]:
        return 0
    new_stage = min(4, char["infection_stage"] + 1)
    update_character(char_id, infection_stage=new_stage)
    return new_stage


def get_infected_crew() -> list[dict]:
    """Get all living infected crew members."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM characters WHERE infected = 1 AND is_alive = 1 ORDER BY infection_stage DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def cure_infection(char_id: int):
    """Remove infection entirely (if medicine works)."""
    update_character(char_id, infected=0, infection_stage=0, infection_day=0)


def delay_infection(char_id: int):
    """Push infection back one stage (medicine buys time)."""
    char = get_character(char_id)
    if not char or not char["infected"]:
        return
    new_stage = max(0, char["infection_stage"] - 1)
    update_character(char_id, infection_stage=new_stage)

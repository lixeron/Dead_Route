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

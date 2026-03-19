"""
Database initialization and connection management.
Creates the SQLite schema on first run.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dead_route.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS game_state (
            id              INTEGER PRIMARY KEY DEFAULT 1,
            player_name     TEXT NOT NULL,
            pronouns        TEXT NOT NULL DEFAULT 'they/them',
            subj_pronoun    TEXT NOT NULL DEFAULT 'they',
            obj_pronoun     TEXT NOT NULL DEFAULT 'them',
            poss_pronoun    TEXT NOT NULL DEFAULT 'their',
            current_day     INTEGER NOT NULL DEFAULT 1,
            current_phase   TEXT NOT NULL DEFAULT 'morning',
            current_node_id INTEGER DEFAULT NULL,
            threat_level    INTEGER NOT NULL DEFAULT 1,
            romance_target_id INTEGER DEFAULT NULL,
            game_over       INTEGER NOT NULL DEFAULT 0,
            ending_type     TEXT DEFAULT NULL,
            intro_complete  INTEGER NOT NULL DEFAULT 0,
            tutorial_flags  TEXT NOT NULL DEFAULT '{}',
            CHECK (id = 1)
        );

        CREATE TABLE IF NOT EXISTS resources (
            id       INTEGER PRIMARY KEY DEFAULT 1,
            fuel     INTEGER NOT NULL DEFAULT 15,
            food     INTEGER NOT NULL DEFAULT 5,
            scrap    INTEGER NOT NULL DEFAULT 3,
            ammo     INTEGER NOT NULL DEFAULT 4,
            medicine INTEGER NOT NULL DEFAULT 1,
            CHECK (id = 1)
        );

        CREATE TABLE IF NOT EXISTS bus (
            id                INTEGER PRIMARY KEY DEFAULT 1,
            armor             INTEGER NOT NULL DEFAULT 35,
            armor_max         INTEGER NOT NULL DEFAULT 50,
            fuel_efficiency   REAL NOT NULL DEFAULT 1.2,
            storage_capacity  INTEGER NOT NULL DEFAULT 50,
            crew_capacity     INTEGER NOT NULL DEFAULT 4,
            fuel_leak         INTEGER NOT NULL DEFAULT 1,
            CHECK (id = 1)
        );

        CREATE TABLE IF NOT EXISTS characters (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            is_player       INTEGER NOT NULL DEFAULT 0,
            hp              INTEGER NOT NULL DEFAULT 100,
            hp_max          INTEGER NOT NULL DEFAULT 100,
            stamina         INTEGER NOT NULL DEFAULT 100,
            stamina_max     INTEGER NOT NULL DEFAULT 100,
            combat          INTEGER NOT NULL DEFAULT 3,
            medical         INTEGER NOT NULL DEFAULT 3,
            mechanical      INTEGER NOT NULL DEFAULT 3,
            scavenging      INTEGER NOT NULL DEFAULT 3,
            trust           INTEGER NOT NULL DEFAULT 50,
            personality     TEXT NOT NULL DEFAULT 'neutral',
            backstory       TEXT NOT NULL DEFAULT '',
            is_alive        INTEGER NOT NULL DEFAULT 1,
            is_romanceable  INTEGER NOT NULL DEFAULT 0,
            recruited_day   INTEGER NOT NULL DEFAULT 1,
            injury          TEXT NOT NULL DEFAULT 'none',
            morale          INTEGER NOT NULL DEFAULT 60
        );

        CREATE TABLE IF NOT EXISTS bus_upgrades (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            upgrade_key   TEXT UNIQUE NOT NULL,
            installed_day INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS map_nodes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            node_type       TEXT NOT NULL,
            description     TEXT NOT NULL DEFAULT '',
            fuel_cost       INTEGER NOT NULL DEFAULT 5,
            days_to_clear   INTEGER NOT NULL DEFAULT 1,
            is_fork         INTEGER NOT NULL DEFAULT 0,
            is_visited      INTEGER NOT NULL DEFAULT 0,
            is_meridian_path INTEGER NOT NULL DEFAULT 0,
            node_order      INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS map_edges (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            from_node_id          INTEGER NOT NULL REFERENCES map_nodes(id),
            to_node_id            INTEGER NOT NULL REFERENCES map_nodes(id),
            description           TEXT NOT NULL DEFAULT '',
            requires_map_fragment INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS choice_flags (
            flag_key   TEXT PRIMARY KEY,
            flag_value INTEGER NOT NULL DEFAULT 0,
            set_on_day INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS event_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            event_key   TEXT NOT NULL,
            fired_on_day INTEGER NOT NULL,
            choice_made TEXT NOT NULL DEFAULT '',
            outcome     TEXT NOT NULL DEFAULT ''
        );
    """)
    conn.commit()
    conn.close()


def reset_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()


def db_exists() -> bool:
    return os.path.exists(DB_PATH)

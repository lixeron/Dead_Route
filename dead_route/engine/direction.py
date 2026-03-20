"""
Direction and progress system.

Gives the player a sense of where they are, where they're going,
and what they're working toward. Solves the "aimless wandering" problem.

Systems:
  - Map progress: how far to Haven (node count)
  - Milestone narration: story beats at progress thresholds
  - Meridian awareness: breadcrumb system for the secret ending
  - NPC route hints: crew comments on what's needed
"""

import random
from db import queries
from ui.style import Color, Theme, styled, print_styled
from ui.narration import narrator_text, status_update


# ── Map Progress ───────────────────────────────────────────

def get_progress() -> dict:
    """
    Calculate how far the player is along the route.
    Returns {current_node, total_nodes, nodes_visited, pct, haven_distance, era_label}
    """
    state = queries.get_game_state()
    current_id = state.get("current_node_id", 1)

    from db.database import get_connection
    conn = get_connection()

    # Count total main-path nodes (non-meridian)
    total = conn.execute(
        "SELECT COUNT(*) as c FROM map_nodes WHERE is_meridian_path = 0"
    ).fetchone()["c"]

    visited = conn.execute(
        "SELECT COUNT(*) as c FROM map_nodes WHERE is_visited = 1 AND is_meridian_path = 0"
    ).fetchone()["c"]

    # Estimate distance to Haven
    current_order = 0
    if current_id:
        row = conn.execute(
            "SELECT node_order FROM map_nodes WHERE id = ?", (current_id,)
        ).fetchone()
        if row:
            current_order = row["node_order"]

    haven_row = conn.execute(
        "SELECT node_order FROM map_nodes WHERE name = 'Haven'"
    ).fetchone()
    haven_order = haven_row["node_order"] if haven_row else total

    conn.close()

    distance = max(0, haven_order - current_order)
    pct = int((current_order / max(1, haven_order)) * 100)

    from engine.balance import get_era
    era = get_era()
    era_labels = {
        "breathing": "The Road Ahead",
        "squeeze": "The Long Middle",
        "endgame": "The Final Stretch",
    }

    return {
        "current_order": current_order,
        "haven_order": haven_order,
        "total_nodes": total,
        "nodes_visited": visited,
        "distance_to_haven": distance,
        "progress_pct": pct,
        "era_label": era_labels.get(era, "Unknown"),
    }


def show_progress_bar():
    """Display a route progress bar in the HUD."""
    prog = get_progress()
    pct = prog["progress_pct"]
    dist = prog["distance_to_haven"]

    # Build the progress bar
    bar_width = 30
    filled = int(bar_width * pct / 100)
    empty = bar_width - filled

    bus_icon = ">"
    haven_icon = "H"

    # Color based on progress
    if pct >= 75:
        bar_color = Theme.SUCCESS
    elif pct >= 40:
        bar_color = Theme.WARNING
    else:
        bar_color = Theme.MUTED

    bar = (
        f"  {styled('Route:', Color.GRAY)} "
        f"{bar_color}{'=' * filled}{bus_icon}{'·' * empty}{Color.RESET}"
        f" {styled(haven_icon, Theme.SUCCESS + Color.BOLD)}"
        f"  {styled(f'{pct}%', bar_color)} "
        f"({styled(f'~{dist} stops to Haven', Color.GRAY)})"
    )
    print(bar)


# ── Milestone Narration ────────────────────────────────────
# Story beats at specific progress thresholds.

MILESTONES = {
    10: {
        "text": "The road signs are getting harder to read — sun-bleached, bullet-riddled, overgrown. But they still point east. East is where Haven is. East is where you're going.",
        "flag": "milestone_10",
    },
    25: {
        "text": "You pass through what used to be a town. The welcome sign says 'Population 4,200.' Now it's population zero. But on the outskirts, someone has spray-painted an arrow and the word 'HAVEN' in bright orange. Someone else came this way. Someone else believed.",
        "flag": "milestone_25",
    },
    40: {
        "text": "For the first time, you see tire tracks that aren't yours. Fresh ones, heading east. Other survivors. Other buses, other cars, other desperate people chasing the same rumor. You're not alone on this road. That's either comforting or terrifying.",
        "flag": "milestone_40",
    },
    50: {
        "text": "Halfway. You've been counting nodes, counting days, counting the dead. Halfway feels like it should mean something. It doesn't, really. The road ahead is just as long as the road behind. But you've survived this far. That has to count for something.",
        "flag": "milestone_50",
    },
    65: {
        "text": "The radio picks up something. Faint, buried in static, but unmistakable: a human voice repeating coordinates. The coordinates match your heading. Haven is broadcasting. It's real. It's REAL.",
        "flag": "milestone_65",
    },
    80: {
        "text": "You can see the smoke on the horizon. Not wildfire smoke — chimney smoke. Controlled, deliberate. Someone is burning fuel to stay warm, which means someone has fuel to spare. Haven is close. You can smell civilization.",
        "flag": "milestone_80",
    },
    90: {
        "text": "A military checkpoint. Abandoned, but recently — the sandbags are fresh, the razor wire is shiny. Someone maintained this. The road beyond it is clearer, the wrecks pushed aside. You're in Haven's territory now. The final stretch.",
        "flag": "milestone_90",
    },
}


def check_milestone() -> str | None:
    """Check if a milestone should fire. Returns narrative text or None."""
    prog = get_progress()
    pct = prog["progress_pct"]

    for threshold, data in sorted(MILESTONES.items()):
        if pct >= threshold and not queries.get_flag(data["flag"]):
            queries.set_flag(data["flag"], True)
            return data["text"]
    return None


# ── Meridian Awareness ─────────────────────────────────────
# Breadcrumbs toward the secret ending. Builds through specific triggers.

AWARENESS_FLAGS = {
    "nadia_cure_motivation":  20,    # Nadia mentions "the facility"
    "used_radio":             15,    # Player used radio antenna
    "found_firebase":         15,    # Firebase Valkyrie discovered
    "found_journal":          10,    # Lore journal found
    "radio_signal_heard":     10,    # Radio signal event fired
    "has_map_fragment":       100,   # Full reveal from dying scientist
}


def get_meridian_awareness() -> int:
    """Calculate current Meridian awareness (0-100+)."""
    total = 0
    for flag, value in AWARENESS_FLAGS.items():
        if queries.get_flag(flag):
            total += value
    return min(100, total)


def get_meridian_hint() -> str | None:
    """Get an awareness-appropriate hint about Meridian, or None."""
    awareness = get_meridian_awareness()

    if awareness <= 0:
        return None
    elif awareness < 20:
        hints = [
            "Sometimes, in the static between radio stations, you catch fragments. A word. 'Meridian.' Then it's gone.",
            "Nadia keeps scribbling a word in her notebook margins: 'MERIDIAN.' When you ask, she changes the subject.",
        ]
    elif awareness < 40:
        hints = [
            "Rumors circulate among survivors about a place where LAZARUS started. A government facility. Nobody knows where it is.",
            "You find graffiti on an overpass: 'MERIDIAN IS REAL. THE CURE EXISTS.' Below it, in different handwriting: 'LIES.'",
        ]
    elif awareness < 60:
        hints = [
            "A facility called Meridian keeps coming up. Military broadcasts mention it in coded language. Nadia says it's where the pathogen was engineered.",
            "The pieces are forming a picture. Meridian. A black-site lab. LAZARUS. If the disease was made there, the cure might be there too.",
        ]
    elif awareness < 100:
        hints = [
            "You're close to finding Meridian. The dying scientist's words echo: the cure is there. You just need the map.",
            "Everything points to Meridian. The coordinates exist somewhere — in a sealed case, carried by someone who knows the truth.",
        ]
    else:
        return None  # Player has the map fragment — no more hints needed

    # Only show hints occasionally (30% chance)
    if random.random() > 0.30:
        return None

    return random.choice(hints)


# ── NPC Route Hints ────────────────────────────────────────
# Crew members comment on what's needed based on game state.

def get_npc_hint() -> str | None:
    """Get a context-sensitive survival hint from an NPC. ~20% chance."""
    if random.random() > 0.20:
        return None

    resources = queries.get_resources()
    bus = queries.get_bus()
    crew = queries.get_alive_crew()
    npcs = queries.get_alive_npcs()
    state = queries.get_game_state()

    if not npcs:
        return None

    hints = []

    # Resource warnings
    if resources["fuel"] <= 8:
        hints.extend([
            "{name} glances at the fuel gauge and says nothing. The silence says everything.",
            "\"{name}: \"We need fuel before the next stretch or we're walking. And walking means dying.\"",
        ])
    if resources["food"] <= 3:
        hints.extend([
            "{name} eyes the empty shelves where the food used to be. \"We can't fight on empty stomachs. We can barely stand.\"",
        ])
    if resources["ammo"] <= 2:
        hints.extend([
            "{name}: \"We're almost out of ammo. Next fight, we're using fists and prayers.\"",
        ])
    if resources["medicine"] <= 0:
        hints.extend([
            "{name}: \"No medicine. If someone gets hurt bad... or bitten...\" The sentence doesn't need finishing.",
        ])

    # Bus condition warnings
    try:
        comps = queries.get_all_components()
        damaged = [c for c in comps.values() if c["state"] in ("damaged", "destroyed")]
        if damaged:
            comp_name = damaged[0]["name"]
            hints.extend([
                f"{{name}} kicks the bus tire. \"The {comp_name.lower()} is in bad shape. We should fix it before it kills us.\"",
            ])
    except Exception:
        pass

    # Progress hints
    prog = get_progress()
    if prog["distance_to_haven"] <= 5:
        hints.extend([
            "{name}: \"Haven is close. I can feel it. We just need to hold on a little longer.\"",
            "{name}: \"Almost there. Don't do anything stupid now. We're too close.\"",
        ])
    elif prog["distance_to_haven"] <= 10:
        hints.extend([
            "{name}: \"We're making progress. Keep the bus moving and we might actually make it.\"",
        ])

    # Infected crew warning
    infected = queries.get_infected_crew()
    if infected:
        hints.extend([
            "{name} keeps glancing at the back of the bus where the infected are sitting. The unspoken question hangs in the air.",
        ])

    if not hints:
        return None

    # Pick a random NPC to deliver the hint
    npc = random.choice(npcs)
    hint = random.choice(hints)
    return hint.replace("{name}", npc["name"])


# ── Era Transition Narration ──────────────────────────────

ERA_TRANSITIONS = {
    8: {
        "flag": "era_squeeze",
        "text": (
            "Something has shifted. You can feel it in the air, in the road, "
            "in the way the infected move. The easy days — if any of them were "
            "easy — are over. The choices ahead are going to cost more. The "
            "mistakes are going to hurt worse.\n\n"
            "The road doesn't care about your feelings. It just goes on."
        ),
    },
    15: {
        "flag": "era_endgame",
        "text": (
            "You've been on this bus for over two weeks. Two weeks of blood, "
            "rationing, arguments, loss. The crew that started this journey "
            "isn't the same crew sitting here now — some faces are gone, some "
            "are scarred, all of them are harder.\n\n"
            "The world outside has gotten worse too. Thicker hordes. Emptier "
            "towns. The feeling that you're running out of road and the road "
            "is running out of mercy.\n\n"
            "Whatever happens next, it happens fast."
        ),
    },
}


def check_era_transition() -> str | None:
    """Check if an era transition narration should fire."""
    state = queries.get_game_state()
    day = state["current_day"]

    for threshold, data in ERA_TRANSITIONS.items():
        if day >= threshold and not queries.get_flag(data["flag"]):
            queries.set_flag(data["flag"], True)
            return data["text"]
    return None

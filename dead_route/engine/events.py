"""
Event engine: loads events from JSON, checks preconditions, resolves outcomes.
"""

import json
import os
import random
from db import queries

EVENTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "events.json")
DARK_EVENTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "dark_events.json")

_event_cache = None


def load_events() -> list[dict]:
    global _event_cache
    if _event_cache is None:
        _event_cache = []
        # Load base events
        with open(EVENTS_PATH) as f:
            data = json.load(f)
        _event_cache.extend(data.get("events", []))
        # Load dark events
        if os.path.exists(DARK_EVENTS_PATH):
            with open(DARK_EVENTS_PATH) as f:
                dark = json.load(f)
            _event_cache.extend(dark.get("dark_events", []))
    return _event_cache


def get_eligible_events() -> list[dict]:
    """Return events whose preconditions are met, including day-gating from balance config."""
    events = load_events()
    state = queries.get_game_state()
    crew = queries.get_alive_crew()
    flags = queries.get_all_flags()

    # Import day gates from balance config
    try:
        from engine.balance import EVENT_DAY_GATES
    except ImportError:
        EVENT_DAY_GATES = {}

    eligible = []

    for event in events:
        pre = event.get("preconditions", {})

        # Balance config day-gate override (takes priority)
        gate = EVENT_DAY_GATES.get(event["id"])
        if gate:
            if state["current_day"] < gate.get("min_day", 0):
                continue
            if state["current_day"] > gate.get("max_day", 999):
                continue

        # JSON precondition day check
        if state["current_day"] < pre.get("min_day", 0):
            continue
        if "max_day" in pre and state["current_day"] > pre["max_day"]:
            continue

        # Crew size check
        if "max_crew_pct" in pre:
            bus = queries.get_bus()
            if len(crew) >= int(bus["crew_capacity"] * pre["max_crew_pct"]):
                continue

        if "min_crew" in pre and len(crew) < pre["min_crew"]:
            continue

        # Node type check
        if "not_node_type" in pre:
            node = queries.get_current_node()
            if node and node["node_type"] == pre["not_node_type"]:
                continue

        # Flag checks
        if "flag_true" in pre and not flags.get(pre["flag_true"], False):
            continue
        if "flag_false" in pre and flags.get(pre["flag_false"], False):
            continue

        # Chance check
        if "chance" in pre and random.random() > pre["chance"]:
            continue

        # Cooldown check
        if event.get("cooldown", 0) > 0:
            count = queries.get_event_count(event["id"])
            if count > 0:
                # Simple cooldown: skip if fired before
                # (For MVP, most story events fire once)
                if event["cooldown"] >= 999:
                    continue

        eligible.append(event)

    return eligible


def pick_random_event() -> dict | None:
    """Pick a random eligible event, or None."""
    eligible = get_eligible_events()
    if not eligible:
        return None
    # Weighted: story events get priority
    story = [e for e in eligible if e["type"] == "story"]
    if story and random.random() < 0.6:
        return random.choice(story)
    return random.choice(eligible)


def resolve_choice(event: dict, choice_index: int) -> dict:
    """
    Resolve the player's choice for an event.
    Returns: {text, effects, outcome, skill_passed}
    """
    choice = event["choices"][choice_index]
    skill_check = choice.get("skill_check")
    state = queries.get_game_state()
    crew = queries.get_alive_crew()

    passed = True
    if skill_check:
        # Use the best crew member's skill for the check
        skill_name = skill_check["skill"]
        difficulty = skill_check["difficulty"]
        best_skill = max(c.get(skill_name, 1) for c in crew)
        roll = best_skill + random.randint(-2, 3)
        passed = roll >= difficulty

    if passed:
        result = choice["success"]
    else:
        result = choice.get("failure", choice["success"])

    # Apply effects
    effects = result.get("effects", {})
    _apply_effects(effects, state, crew)

    # Log it
    queries.log_event(event["id"], choice.get("label", ""), result.get("outcome", ""))

    return {
        "text": _interpolate(result["text"], state),
        "effects": effects,
        "outcome": result.get("outcome", ""),
        "skill_passed": passed,
        "had_skill_check": skill_check is not None,
    }


def _apply_effects(effects: dict, state: dict, crew: list[dict]):
    """Apply event effects to game state."""
    resource_keys = {"fuel", "food", "scrap", "ammo", "medicine"}
    resource_changes = {}

    for key, val in effects.items():
        if key in resource_keys:
            resource_changes[key] = val
        elif key == "trust_all":
            for c in crew:
                if not c["is_player"]:
                    queries.change_trust(c["id"], val)
        elif key == "damage_random_crew":
            target = random.choice(crew)
            queries.damage_character(target["id"], val)
        elif key == "trust_random_crew":
            npcs = [c for c in crew if not c["is_player"]]
            if npcs:
                target = random.choice(npcs)
                queries.change_trust(target["id"], val)
        elif key.startswith("set_flag"):
            queries.set_flag(val, True)
        elif key == "flag":
            queries.set_flag(val, True)
        elif key == "recruit_random":
            pass  # Handled by the game loop after event resolution
        elif key == "recruit_random2":
            pass  # Second recruit, also handled by game loop
        elif key == "advance_phase":
            pass  # Handled by the game loop
        elif key == "remove_random_crew":
            # A crew member is taken/lost (meat grinder, etc.)
            npcs = [c for c in crew if not c["is_player"] and c["is_alive"]]
            if npcs:
                victim = random.choice(npcs)
                queries.update_character(victim["id"], is_alive=0)
        elif key == "damage_all_crew":
            for c in crew:
                queries.damage_character(c["id"], val)
        elif key == "bus_damage":
            from engine.bus_damage import apply_bus_damage
            apply_bus_damage(val)

    if resource_changes:
        queries.update_resources(**resource_changes)


def _interpolate(text: str, state: dict) -> str:
    """Replace {player_name}, {pronoun} etc. in text."""
    replacements = {
        "{player_name}": state.get("player_name", "Survivor"),
        "{they}": state.get("subj_pronoun", "they"),
        "{them}": state.get("obj_pronoun", "them"),
        "{their}": state.get("poss_pronoun", "their"),
        "{They}": state.get("subj_pronoun", "they").capitalize(),
        "{Them}": state.get("obj_pronoun", "them").capitalize(),
        "{Their}": state.get("poss_pronoun", "their").capitalize(),
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

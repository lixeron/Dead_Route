#!/usr/bin/env python3
"""
DEAD ROUTE — Zombie Oregon Trail on a School Bus
Entry point. Thin wrapper: init DB, run intro, start game loop.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database import reset_db
from db import queries
from engine.intro import run_intro
from engine.travel import generate_map
from engine import game_loop
from ui.style import Theme, clear_screen, print_styled


def create_player(intro_result: dict):
    """Create the player character and initialize game state from intro."""
    queries.create_game(
        player_name=intro_result["player_name"],
        pronouns=intro_result["pronouns"],
        subj=intro_result["subj"],
        obj=intro_result["obj"],
        poss=intro_result["poss"],
    )
    queries.set_resources(fuel=15, food=5, scrap=2, ammo=4, medicine=1)

    skill = intro_result["starting_skill"]
    stats = {"combat": 3, "medical": 3, "mechanical": 3, "scavenging": 3}
    stats[skill] = 6

    queries.create_character(name=intro_result["player_name"], is_player=True, **stats)

    start_node_id = generate_map()
    queries.update_game_state(current_node_id=start_node_id, intro_complete=1)
    queries.mark_node_visited(start_node_id)


def post_intro_transition():
    """Brief transition from intro to gameplay, introducing the HUD."""
    from ui.narration import narrator_text, dramatic_pause, scene_break, status_update
    from ui.input import press_enter
    from ui.display import show_hud
    from ui.style import print_blank

    state = queries.get_game_state()
    name = state["player_name"]

    clear_screen()
    print_blank(1)
    scene_break("DAY 1 — MORNING")

    narrator_text(
        f"The sun is low on the horizon. {name} grips the steering wheel "
        f"and squints at the road ahead. The bus rattles along, every pothole "
        f"a jolt through the spine."
    )
    dramatic_pause(0.5)

    narrator_text(
        "The fuel gauge needle is uncomfortably close to the red. The glove "
        "compartment has a single granola bar, already split three ways by "
        "the time you found it. This is the state of things."
    )
    dramatic_pause(0.5)

    status_update("Systems check... supplies are critically low.")
    dramatic_pause(0.5)
    show_hud()

    narrator_text(
        "You need fuel. You need food. You need to find other people — or "
        "pray you don't. The road to Haven is long, and this bus won't get "
        "there on hope alone."
    )
    press_enter()


def main():
    """Main entry point. Run intro -> game loop, repeat on death."""
    while True:
        reset_db()
        result = run_intro()

        if result.get("quit"):
            clear_screen()
            print_styled("\n  Thanks for playing Dead Route.\n", Theme.MUTED)
            sys.exit(0)

        create_player(result)
        post_intro_transition()
        game_loop.run()


if __name__ == "__main__":
    main()

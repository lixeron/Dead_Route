"""
All ending sequences: Haven, Meridian, game over, run statistics.
"""

import random
from db import queries
from ui.style import Color, Theme, print_styled, clear_screen, print_blank
from ui.narration import narrator_text, dramatic_pause, scene_break
from ui.input import press_enter
from engine.audio import audio


def handle_haven_arrival():
    """Handle arriving at Haven — good/neutral ending."""
    audio.play_music("haven")
    crew = queries.get_alive_crew()
    bus = queries.get_bus()

    clear_screen()
    print_blank(2)
    scene_break("HAVEN")

    narrator_text(
        "The walls rise out of the haze. Concrete and steel, razor wire, "
        "watchtowers with actual electric lights. You'd forgotten what "
        "electric lights looked like."
    )
    dramatic_pause(1.5)

    state = queries.get_game_state()
    narrator_text(f"\"Open the gate. We're survivors. {len(crew)} of us.\"")
    dramatic_pause(1.0)
    narrator_text("The gates open.")
    dramatic_pause(2.0)

    if len(crew) >= bus["crew_capacity"] * 0.6:
        queries.update_game_state(game_over=1, ending_type="good")
    else:
        queries.update_game_state(game_over=1, ending_type="neutral")
    press_enter()


def handle_meridian_arrival():
    """Secret ending placeholder."""
    queries.update_game_state(game_over=1, ending_type="secret")
    clear_screen()
    print_blank(2)
    scene_break("MERIDIAN")
    narrator_text("The facility looms ahead. This is where it all started.")
    narrator_text("[Secret ending — to be fully implemented in Phase 3]")
    press_enter()


def handle_game_over():
    """Display the game over / ending screen with run statistics."""
    state = queries.get_game_state()
    ending = state.get("ending_type", "bad")
    if ending in ("bad", "neutral"):
        audio.play_music("gameover")
    clear_screen()
    print_blank(3)

    name = state["player_name"]

    if ending == "bad":
        print_styled("  ╔══════════════════════════════════╗", Theme.DAMAGE)
        print_styled("  ║           GAME  OVER             ║", Theme.DAMAGE + Color.BOLD)
        print_styled("  ╚══════════════════════════════════╝", Theme.DAMAGE)
        print()
        death_messages = [
            f"{name}'s journey ends here. The road claims another.",
            f"The dead don't mourn. They just keep walking. {name} won't.",
            f"Somewhere out there, Haven still stands. {name} will never see it.",
        ]
        narrator_text(random.choice(death_messages))
    elif ending == "neutral":
        print_styled("  ╔══════════════════════════════════╗", Theme.WARNING)
        print_styled("  ║       YOU REACHED HAVEN          ║", Theme.WARNING + Color.BOLD)
        print_styled("  ╚══════════════════════════════════╝", Theme.WARNING)
        print()
        narrator_text(
            f"{name} made it. But the empty seats on the bus are louder "
            f"than any celebration. Survival has a price."
        )
    elif ending == "good":
        print_styled("  ╔══════════════════════════════════╗", Theme.SUCCESS)
        print_styled("  ║       HAVEN — TRIUMPHANT         ║", Theme.SUCCESS + Color.BOLD)
        print_styled("  ╚══════════════════════════════════╝", Theme.SUCCESS)
        print()
        narrator_text(
            f"{name} and the crew roll through the gates to cheers. "
            f"The bus — battered, scarred, held together by spite and scrap metal — "
            f"has carried them to safety. Against all odds."
        )
    elif ending == "secret":
        print_styled("  ╔══════════════════════════════════╗", Theme.TITLE)
        print_styled("  ║      MERIDIAN — THE CURE         ║", Theme.TITLE + Color.BOLD)
        print_styled("  ╚══════════════════════════════════╝", Theme.TITLE)
        print()
        narrator_text("The cure exists. And now, so does hope.")

    # Run stats
    print_blank(2)
    print_styled("  ── RUN STATISTICS ──", Color.BOLD + Color.BRIGHT_WHITE)
    print()
    print(f"   Days survived:     {state['current_day']}")
    print(f"   Threat level:      {state['threat_level']}")
    crew = queries.get_alive_crew()
    print(f"   Surviving crew:    {len(crew)}")
    upgrades = queries.get_installed_upgrades()
    print(f"   Bus upgrades:      {len(upgrades)}")
    flags = queries.get_all_flags()
    print(f"   Key decisions:     {len(flags)}")
    resources = queries.get_resources()
    print(
        f"   Final resources:   F:{resources['fuel']} Fd:{resources['food']} "
        f"S:{resources['scrap']} A:{resources['ammo']} M:{resources['medicine']}"
    )

    print_blank(2)
    press_enter("Press Enter to return to title screen...")
    audio.stop_music()

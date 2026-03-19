"""
Main game loop: phase cycle, day transitions, banter, random events.
Orchestrates all other engine modules.
"""

import random
from db import queries
from engine.passive import run_passive_systems
from engine.crisis import check_forced_events
from engine.actions import (
    do_explore, do_upgrade, do_rest, do_interact, do_travel,
    handle_recruitment_from_event
)
from engine.endings import handle_haven_arrival, handle_meridian_arrival, handle_game_over
from engine.banter import get_ambient_banter, get_context
from engine.events import pick_random_event, resolve_choice
from engine.infection import (
    tick_infections, handle_turning, present_infection_choice,
    get_infection_hud_warning, STAGES
)
from engine.audio import audio, play_phase_music
from ui.style import Color, Theme, styled, print_styled, clear_screen, print_blank
from ui.narration import narrator_text, dramatic_pause, scene_break, status_update
from ui.input import get_choice, press_enter
from ui.display import show_hud, show_crew_status, show_location_description, show_bus_status


def display_warnings(warnings: list[str]):
    """Show passive system warnings with appropriate drama."""
    if not warnings:
        return
    print()
    for w in warnings:
        if "!!" in w or "DESTROYED" in w or "DEAD" in w:
            print_styled(f"  !! {w}", Theme.DAMAGE + Color.BOLD)
            dramatic_pause(1.0)
        elif "starv" in w.lower() or "stole" in w.lower():
            print_styled(f"  ! {w}", Theme.WARNING)
            dramatic_pause(0.5)
        else:
            print(f"  {Theme.MUTED}> {w}{Color.RESET}")
    print()
    dramatic_pause(0.3)


def maybe_show_banter():
    """50% chance of crew banter, 15% chance of quiet moment."""
    from engine.deep_dialogue import get_quiet_moment

    state = queries.get_game_state()
    crew = queries.get_alive_crew()

    # Try quiet moment first (rarer, more meaningful)
    moment = get_quiet_moment(crew, state)
    if moment:
        print()
        for speaker, text in moment["text"]:
            if speaker == "narrator":
                from ui.narration import narrator_text as nt
                nt(text)
        return

    # Standard banter
    if random.random() > 0.5:
        return
    resources = queries.get_resources()
    context = get_context(state, resources)
    banter = get_ambient_banter(context)
    if banter:
        print()
        print(f"  {Theme.MUTED}{Color.ITALIC}{banter}{Color.RESET}")
        from ui.narration import _interruptible_sleep
        _interruptible_sleep(0.4)


def check_random_event():
    """Roll for a random event to fire (25% per phase)."""
    if random.random() > 0.25:
        return

    event = pick_random_event()
    if not event:
        return

    audio.play_music("event")
    clear_screen()
    print_blank(1)
    scene_break("EVENT")

    narrator_text(event["description"])

    labels = [c["label"] for c in event["choices"]]
    idx = get_choice(labels, prompt="What do you do?")

    result = resolve_choice(event, idx)

    print()
    narrator_text(result["text"])

    if result.get("had_skill_check"):
        if result["skill_passed"]:
            status_update("Skill check: PASSED")
        else:
            print_styled("  ! Skill check: FAILED", Theme.WARNING)

    # Handle recruitment
    handle_recruitment_from_event(result.get("effects", {}))

    press_enter()


def check_special_arrival(node_name: str) -> bool:
    """Check if arriving at a node triggers an ending. Returns True if game ends."""
    if node_name == "Haven":
        handle_haven_arrival()
        return True
    if node_name == "Meridian Research Facility":
        handle_meridian_arrival()
        return True
    return False


def run():
    """Main gameplay loop — one phase at a time."""
    while True:
        state = queries.get_game_state()

        if state["game_over"]:
            handle_game_over()
            return

        # ── Run passive systems ──
        warnings = run_passive_systems()

        # ── Tick infections (once per day, morning) ──
        infection_events = tick_infections()
        for ie in infection_events:
            if ie["new_stage"] == 4:
                # TURNING — emergency event
                clear_screen()
                print_blank(1)
                scene_break("THE TURNING")

                char = queries.get_character(ie["char_id"])
                if char:
                    turning_result = handle_turning(char)
                    narrator_text(turning_result["narrative"])
                    dramatic_pause(1.5)
                    print()
                    for cas in turning_result["casualties"]:
                        print_styled(
                            f"  !! {cas['name']} takes {cas['damage']} damage !!",
                            Theme.DAMAGE
                        )
                    dramatic_pause(1.0)
                    narrator_text(
                        f"When it's over, what used to be {ie['name']} "
                        f"lies still on the bus floor. The seats are soaked "
                        f"in something dark. The smell will never come out."
                    )
                    press_enter()
            elif ie["narrative"]:
                warnings.append(f"INFECTION: {ie['name']} — Stage {ie['new_stage']}: {ie['stage_name']}")

        # Re-check game over after passive systems + infections
        state = queries.get_game_state()
        if state["game_over"]:
            if warnings:
                display_warnings(warnings)
                press_enter()
            handle_game_over()
            return

        # ── Display ──
        clear_screen()
        show_hud()

        # ── Phase music ──
        play_phase_music(state["current_phase"])

        # Show infection warnings on HUD
        infected_crew = queries.get_infected_crew()
        for ic in infected_crew:
            warning = get_infection_hud_warning(ic)
            if warning:
                if ic["infection_stage"] >= 3:
                    print_styled(f"  {warning}", Theme.DAMAGE + Color.BOLD)
                elif ic["infection_stage"] >= 2:
                    print_styled(f"  {warning}", Theme.DAMAGE)
                else:
                    print_styled(f"  {warning}", Theme.WARNING)

        if warnings:
            display_warnings(warnings)

        # Show infection progression narratives (stages 1-3)
        for ie in infection_events:
            if ie["new_stage"] < 4 and ie["narrative"]:
                print()
                scene_break(f"INFECTION — {ie['name'].upper()}")
                narrator_text(ie["narrative"])
                dramatic_pause(0.5)

                # Present choice at stage 2+
                if ie["new_stage"] >= 2:
                    char = queries.get_character(ie["char_id"])
                    if char and char["is_alive"]:
                        present_infection_choice(char)
                        state = queries.get_game_state()
                        if state["game_over"]:
                            handle_game_over()
                            return

        show_location_description()

        # ── Crew banter ──
        maybe_show_banter()

        # ── Forced crisis events ──
        check_forced_events()
        state = queries.get_game_state()
        if state["game_over"]:
            handle_game_over()
            return

        # ── Player action ──
        phase = state["current_phase"]
        phase_warning = ""
        if phase == "midnight":
            phase_warning = styled(" [EXTREME DANGER]", Theme.DAMAGE + Color.BOLD)
        elif phase == "evening":
            phase_warning = styled(" [HIGH DANGER]", Theme.WARNING)

        actions = [
            f"Explore — Scavenge for supplies{phase_warning}",
            "Upgrade / Repair — Improve or fix the bus",
            "Rest — Recover HP and stamina (costs Food)",
            "Interact — Talk to a crew member",
            "Check Crew — View detailed crew status",
            "Check Bus — View bus component status",
            "Travel — Move to the next location",
        ]

        choice = get_choice(actions, prompt="What do you do this phase?")

        if choice == 0:
            do_explore()
        elif choice == 1:
            do_upgrade()
        elif choice == 2:
            do_rest()
        elif choice == 3:
            do_interact()
        elif choice == 4:
            show_crew_status()
            press_enter()
            continue  # Don't advance phase
        elif choice == 5:
            show_bus_status()
            press_enter()
            continue  # Don't advance phase
        elif choice == 6:
            did_travel = do_travel()
            if not did_travel:
                continue

            # Check for special arrivals
            node = queries.get_current_node()
            if node and check_special_arrival(node["name"]):
                state = queries.get_game_state()
                if state["game_over"]:
                    handle_game_over()
                    return

        # ── Advance phase ──
        old_day = state["current_day"]
        new_day, new_phase = queries.advance_phase()

        # Day transition
        if new_phase == "morning" and new_day > old_day:
            clear_screen()
            print_blank(1)

            day_texts = [
                f"Day {new_day}. The sun crawls over the horizon like it's not sure it wants to.",
                f"Day {new_day}. Another morning. You're still breathing. Don't take it for granted.",
                f"Day {new_day} begins. The road stretches on. So do the dead.",
            ]
            scene_break(f"DAY {new_day} — MORNING")
            narrator_text(random.choice(day_texts))

            new_state = queries.get_game_state()
            if new_state["threat_level"] > state["threat_level"]:
                print()
                print_styled(
                    f"  !! THREAT LEVEL {new_state['threat_level']} !!",
                    Theme.DAMAGE + Color.BOLD
                )
                threat_texts = [
                    "More of them. Faster. Hungrier. Whatever LAZARUS does, it's getting worse.",
                    "The hordes are thicker now. You can hear them even during the day.",
                    "Something's changed. The infected are more aggressive. More coordinated.",
                ]
                narrator_text(random.choice(threat_texts))

            press_enter()

        # ── Random event ──
        check_random_event()

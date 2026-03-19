#!/usr/bin/env python3
"""
DEAD ROUTE — Zombie Oregon Trail on a School Bus
Entry point. Initializes DB, runs intro, starts game loop.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database import init_db, reset_db, db_exists
from db import queries
from engine.intro import run_intro
from engine.travel import generate_map
from ui.style import Color, Theme, clear_screen, print_styled, print_blank
from ui.narration import scene_break, narrator_text, dramatic_pause, status_update
from ui.input import get_choice, press_enter
from ui.display import show_hud, show_crew_status, show_location_description


def create_player(intro_result: dict):
    """Create the player character and initialize game state from intro results."""

    # Initialize game state
    queries.create_game(
        player_name=intro_result["player_name"],
        pronouns=intro_result["pronouns"],
        subj=intro_result["subj"],
        obj=intro_result["obj"],
        poss=intro_result["poss"],
    )

    # Set starting resources (first drive costs 3 fuel)
    queries.set_resources(fuel=27)

    # Create player character with boosted starting skill
    skill = intro_result["starting_skill"]
    stats = {"combat": 4, "medical": 4, "mechanical": 4, "scavenging": 4}
    stats[skill] = 7  # Boosted skill from item choice

    queries.create_character(
        name=intro_result["player_name"],
        is_player=True,
        **stats
    )

    # Generate the map
    start_node_id = generate_map()
    queries.update_game_state(current_node_id=start_node_id, intro_complete=1)
    queries.mark_node_visited(start_node_id)


def post_intro_transition():
    """The brief transition between intro and gameplay, introducing first mechanics."""
    state = queries.get_game_state()
    name = state["player_name"]

    clear_screen()
    print_blank(1)

    scene_break("DAY 1 — MORNING")

    narrator_text(
        f"The sun is low on the horizon. {name} grips the steering wheel "
        f"and squints at the road ahead. The bus rattles along, every pothole "
        f"a reminder of how fragile this lifeline really is."
    )
    dramatic_pause(0.5)

    narrator_text(
        "You pull over at what used to be a rest stop. Vending machines smashed, "
        "bathrooms trashed, but the parking lot gives you a clear view in every "
        "direction. Safe enough for now."
    )
    dramatic_pause(0.5)

    # Show HUD for the first time
    status_update("Systems online. Checking supplies...")
    dramatic_pause(0.8)

    show_hud()

    narrator_text(
        "The fuel gauge is dropping. You'll need to find more soon, or this "
        "road trip ends real fast."
    )

    press_enter()


def game_phase_loop():
    """Main gameplay loop — one phase at a time."""
    while True:
        state = queries.get_game_state()

        if state["game_over"]:
            handle_game_over(state)
            return

        # Show HUD
        clear_screen()
        show_hud()
        show_location_description()

        # Core action choice
        actions = [
            "Explore — Scavenge the area for supplies",
            "Upgrade — Improve the bus or train skills",
            "Rest — Recover HP and stamina (costs Food)",
            "Interact — Talk to a crew member",
            "Check Crew — View detailed crew status",
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
            continue  # Don't advance phase for checking status
        elif choice == 5:
            did_travel = do_travel()
            if not did_travel:
                continue  # Don't advance phase if travel was cancelled

        # Advance to next phase
        new_day, new_phase = queries.advance_phase()

        # Check for day transition narration
        if new_phase == "morning" and new_day > state["current_day"]:
            clear_screen()
            print_blank(1)
            scene_break(f"DAY {new_day} — MORNING")
            narrator_text("A new day dawns. The world hasn't gotten any better overnight.")

            # Threat escalation notification
            new_state = queries.get_game_state()
            if new_state["threat_level"] > state["threat_level"]:
                print()
                print_styled(
                    f"  !! THREAT LEVEL INCREASED TO {new_state['threat_level']} !!",
                    Theme.DAMAGE + Color.BOLD
                )
                narrator_text(
                    "The infected are getting worse. More of them. Faster. Stronger. "
                    "Whatever LAZARUS does to them, it's accelerating."
                )

            press_enter()

        # Random event check (30% chance per phase)
        _check_random_event()


def do_explore():
    """Handle the Explore action."""
    from engine.combat import stat_check_combat, generate_combat_narrative
    import random

    crew = queries.get_alive_crew()
    state = queries.get_game_state()
    node = queries.get_current_node()

    # Pick who goes
    if len(crew) > 1:
        names = [f"{c['name']} (Combat:{c['combat']} Scav:{c['scavenging']})" for c in crew]
        idx = get_choice(names, prompt="Who leads the expedition?")
        explorer = crew[idx]
    else:
        explorer = crew[0]

    narrator_text(
        f"{explorer['name']} heads out to search the area. "
        f"{'The morning light offers some safety.' if state['current_phase'] == 'morning' else ''}"
        f"{'The shadows are getting long.' if state['current_phase'] == 'evening' else ''}"
        f"{'It is pitch black. This is insane.' if state['current_phase'] == 'midnight' else ''}"
    )
    dramatic_pause(0.5)

    # Determine if combat happens
    combat_chances = {
        "morning": 0.2, "afternoon": 0.35,
        "evening": 0.55, "midnight": 0.75,
    }
    combat_chance = combat_chances.get(state["current_phase"], 0.3)

    if random.random() < combat_chance:
        # Combat encounter
        narrator_text("Movement in the shadows. They're not alone out there.")
        dramatic_pause(0.5)

        result = stat_check_combat(explorer["id"])
        narrative = generate_combat_narrative(result)
        narrator_text(narrative)

        if result["damage_taken"] > 0:
            from ui.narration import damage_display
            damage_display(explorer["name"], result["damage_taken"])
        if result["bus_damage"] > 0:
            from ui.narration import damage_display
            damage_display("The Bus", result["bus_damage"])
        if result["loot"]:
            from ui.narration import loot_display
            loot_display(result["loot"])
        if result["character_died"]:
            print()
            print_styled(
                f"  {explorer['name']} didn't make it back.",
                Theme.DAMAGE + Color.BOLD
            )
            dramatic_pause(1.5)
    else:
        # Peaceful scavenging
        scav_skill = explorer.get("scavenging", 3)
        loot = {}
        if random.random() < 0.3 + scav_skill * 0.05:
            loot["fuel"] = random.randint(2, 4 + scav_skill)
        if random.random() < 0.4 + scav_skill * 0.05:
            loot["food"] = random.randint(1, 3 + scav_skill // 2)
        if random.random() < 0.3 + scav_skill * 0.04:
            loot["scrap"] = random.randint(1, 3 + scav_skill // 2)
        if random.random() < 0.15:
            loot["ammo"] = random.randint(1, 2)
        if random.random() < 0.08:
            loot["medicine"] = 1

        if loot:
            location_descs = [
                "an overturned truck", "a ransacked convenience store",
                "an abandoned house", "a wrecked police car",
                "a camping supplies store", "a church basement",
            ]
            narrator_text(
                f"{explorer['name']} finds {random.choice(location_descs)} "
                f"and comes back with supplies."
            )
            queries.update_resources(**loot)
            from ui.narration import loot_display
            loot_display(loot)
        else:
            narrator_text(
                f"{explorer['name']} searches the area but comes back empty-handed. "
                f"\"Nothing. Place has been picked clean.\""
            )

    press_enter()


def do_upgrade():
    """Handle the Upgrade action."""
    import json

    upgrades_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "upgrades.json")
    with open(upgrades_path) as f:
        upgrade_data = json.load(f)["upgrades"]

    resources = queries.get_resources()
    installed = queries.get_installed_upgrades()

    # Filter to available upgrades
    available = []
    for key, data in upgrade_data.items():
        if key in installed:
            continue
        prereq = data.get("prerequisite")
        if prereq and prereq not in installed:
            continue
        available.append((key, data))

    if not available:
        narrator_text("Nothing to upgrade right now. The bus is as good as it gets — for now.")
        press_enter()
        return

    options = []
    for key, data in available:
        cost = data["cost_scrap"]
        affordable = "  [CAN AFFORD]" if resources["scrap"] >= cost else "  [Need more scrap]"
        options.append(f"{data['name']} — {cost} Scrap{affordable}")
    options.append("Cancel — Go back")

    narrator_text("You assess the bus and consider what could be improved.")
    idx = get_choice(options, prompt="Available upgrades:")

    if idx == len(available):
        return  # Cancelled

    key, data = available[idx]
    cost = data["cost_scrap"]

    if resources["scrap"] < cost:
        narrator_text(f"Not enough Scrap. Need {cost}, have {resources['scrap']}.")
        press_enter()
        return

    # Install upgrade
    queries.update_resources(scrap=-cost)
    queries.install_upgrade(key)

    # Apply effects
    bus = queries.get_bus()
    effects = data.get("effects", {})
    bus_updates = {}
    for eff_key, eff_val in effects.items():
        if eff_key == "armor_max":
            bus_updates["armor_max"] = bus["armor_max"] + eff_val
        elif eff_key == "armor":
            bus_updates["armor"] = min(bus["armor"] + eff_val,
                                       bus_updates.get("armor_max", bus["armor_max"]))
        elif eff_key == "fuel_efficiency":
            bus_updates["fuel_efficiency"] = round(bus["fuel_efficiency"] + eff_val, 2)
        elif eff_key == "storage_capacity":
            bus_updates["storage_capacity"] = bus["storage_capacity"] + eff_val
        elif eff_key == "crew_capacity":
            bus_updates["crew_capacity"] = bus["crew_capacity"] + eff_val

    if bus_updates:
        queries.update_bus(**bus_updates)

    narrator_text(f"Upgrade installed: {data['name']}.")
    narrator_text(data["description"])
    status_update(f"-{cost} Scrap")
    press_enter()


def do_rest():
    """Handle the Rest action."""
    crew = queries.get_alive_crew()
    resources = queries.get_resources()
    food_cost = len(crew)

    if resources["food"] < food_cost:
        narrator_text(
            f"Not enough food to feed everyone. Need {food_cost} Food, "
            f"have {resources['food']}."
        )
        narrator_text("Resting on empty stomachs won't help much.")
        press_enter()
        return

    # Consume food
    queries.update_resources(food=-food_cost)

    # Recover HP/Stamina based on phase
    recovery = {
        "morning": 10, "afternoon": 15,
        "evening": 20, "midnight": 25,
    }
    state = queries.get_game_state()
    heal_amount = recovery.get(state["current_phase"], 15)

    for c in crew:
        queries.heal_character(c["id"], heal_amount)

    narrator_text("The crew rests. Food is shared. Wounds are tended.")
    if state["current_phase"] in ("evening", "midnight"):
        narrator_text(
            "Resting through the dangerous hours. Smart, but you're missing "
            "whatever's out there."
        )

    status_update(f"-{food_cost} Food consumed")
    status_update(f"+{heal_amount} HP restored to all crew")
    press_enter()


def do_interact():
    """Handle the Interact action."""
    from engine.crew import get_interaction_options

    npcs = queries.get_alive_npcs()

    if not npcs:
        narrator_text("There's nobody else on the bus to talk to. Just you and the road.")
        press_enter()
        return

    # Pick who to talk to
    names = [f"{c['name']} (Trust: {c['trust']})" for c in npcs]
    idx = get_choice(names, prompt="Who do you want to talk to?")
    target = npcs[idx]

    # Get dialogue options
    options = get_interaction_options(target)
    labels = [o["label"] for o in options]
    labels.append("Nevermind")

    dial_idx = get_choice(labels, prompt=f"Talking to {target['name']}...")

    if dial_idx == len(options):
        return  # Cancelled

    option = options[dial_idx]
    import random

    # Cost check for gifts
    if "cost" in option:
        res = queries.get_resources()
        for k, v in option["cost"].items():
            if res.get(k, 0) < v:
                narrator_text(f"You don't have enough {k} for that.")
                press_enter()
                return
        queries.update_resources(**{k: -v for k, v in option["cost"].items()})

    # Determine outcome
    trust_delta = option.get("trust_delta", 0)
    if trust_delta < 0 or random.random() < 0.3:  # 30% chance of negative reaction
        response = option.get("response_negative") or option["response_positive"]
        if trust_delta > 0:
            trust_delta = max(-5, -trust_delta // 2)
    else:
        response = option["response_positive"]

    new_trust = queries.change_trust(target["id"], trust_delta)

    # Display
    narrator_text(response)

    if trust_delta > 0:
        status_update(f"{target['name']}'s trust increased. ({new_trust})")
    elif trust_delta < 0:
        print_styled(
            f"  ! {target['name']}'s trust decreased. ({new_trust})",
            Theme.WARNING
        )
    press_enter()


def do_travel():
    """Handle traveling to the next node."""
    from engine.travel import travel_to_node

    state = queries.get_game_state()
    current_node_id = state.get("current_node_id")

    if not current_node_id:
        narrator_text("You're not sure where to go from here.")
        press_enter()
        return False

    next_nodes = queries.get_next_nodes(current_node_id)

    if not next_nodes:
        narrator_text("The road ends here. There's nowhere left to go.")
        press_enter()
        return False

    # Filter out nodes requiring map fragment if player doesn't have it
    has_fragment = queries.get_flag("has_map_fragment")
    visible_nodes = [
        n for n in next_nodes
        if not n["requires_map_fragment"] or has_fragment
    ]

    if not visible_nodes:
        narrator_text("No accessible routes forward.")
        press_enter()
        return False

    # Build choice display
    bus = queries.get_bus()
    options = []
    for n in visible_nodes:
        fuel_cost = max(1, int(n["fuel_cost"] * bus["fuel_efficiency"]))
        desc = n.get("edge_description", f"Head to {n['name']}")
        node_type = n["node_type"].replace("_", " ").title()
        options.append(f"{desc}\n       [{node_type}] — Fuel cost: {fuel_cost}")
    options.append("Stay here for now")

    idx = get_choice(options, prompt="Where to next?")

    if idx == len(visible_nodes):
        return False  # Cancelled

    target = visible_nodes[idx]
    result = travel_to_node(target["id"])

    if not result["success"]:
        if result["reason"] == "no_fuel_dead_zone":
            clear_screen()
            print_blank(3)
            narrator_text(
                "The engine sputters. Coughs. Dies."
            )
            dramatic_pause(1.5)
            narrator_text(
                "You're stranded. In the middle of a dead zone. The groaning "
                "starts almost immediately."
            )
            dramatic_pause(1.5)
            print()
            print_styled("  The dead are coming. There is no escape.", Theme.DAMAGE + Color.BOLD)
            dramatic_pause(2.0)
        elif result["reason"] == "no_fuel":
            narrator_text(
                f"Not enough fuel. Need {result['fuel_cost']}, "
                f"have {queries.get_resources()['fuel']}."
            )
        press_enter()
        return result["reason"] == "no_fuel_dead_zone"

    # Successful travel
    narrator_text(f"The bus rumbles forward, burning {result['fuel_cost']} fuel.")
    status_update(f"Arrived at {target['name']}")
    status_update(f"Fuel remaining: {result['fuel_remaining']}")

    # Check for Haven arrival (end of game)
    if target["name"] == "Haven":
        handle_haven_arrival()
        return True

    if target["name"] == "Meridian Research Facility":
        handle_meridian_arrival()
        return True

    press_enter()
    return True


def handle_haven_arrival():
    """Handle arriving at Haven — good/neutral ending."""
    crew = queries.get_alive_crew()
    total_crew = len(crew)
    bus = queries.get_bus()

    clear_screen()
    print_blank(2)
    scene_break("HAVEN")

    narrator_text(
        "The walls rise out of the haze like a mirage. Concrete and steel, "
        "topped with razor wire and manned watchtowers. Searchlights sweep "
        "the perimeter."
    )
    dramatic_pause(1.0)

    narrator_text("A voice crackles over a megaphone: \"Identify yourselves.\"")
    dramatic_pause(0.5)

    state = queries.get_game_state()
    narrator_text(
        f"\"{state['player_name']}. We have {total_crew} survivors on a school bus. "
        f"We're not infected. We just want in.\""
    )
    dramatic_pause(1.5)

    narrator_text("The gates open.")
    dramatic_pause(2.0)

    # Determine ending tier
    if total_crew >= bus["crew_capacity"] * 0.6:
        queries.update_game_state(game_over=1, ending_type="good")
    else:
        queries.update_game_state(game_over=1, ending_type="neutral")

    press_enter()


def handle_meridian_arrival():
    """Placeholder for secret ending."""
    queries.update_game_state(game_over=1, ending_type="secret")
    clear_screen()
    print_blank(2)
    scene_break("MERIDIAN")
    narrator_text("The facility looms ahead. This is where it all started.")
    narrator_text("[Secret ending content — to be implemented in Phase 3]")
    press_enter()


def handle_game_over(state: dict):
    """Display the game over / ending screen."""
    clear_screen()
    print_blank(3)

    ending = state.get("ending_type", "bad")
    name = state["player_name"]

    if ending == "bad":
        print_styled("  ╔══════════════════════════════╗", Theme.DAMAGE)
        print_styled("  ║        GAME OVER             ║", Theme.DAMAGE + Color.BOLD)
        print_styled("  ╚══════════════════════════════╝", Theme.DAMAGE)
        print()
        narrator_text(f"{name}'s journey ends here. The road claims another.")
    elif ending == "neutral":
        print_styled("  ╔══════════════════════════════╗", Theme.WARNING)
        print_styled("  ║     YOU REACHED HAVEN        ║", Theme.WARNING + Color.BOLD)
        print_styled("  ╚══════════════════════════════╝", Theme.WARNING)
        print()
        narrator_text(
            f"{name} made it. But the empty seats on the bus tell their own story. "
            f"Survival came at a price."
        )
    elif ending == "good":
        print_styled("  ╔══════════════════════════════╗", Theme.SUCCESS)
        print_styled("  ║     HAVEN — TRIUMPHANT       ║", Theme.SUCCESS + Color.BOLD)
        print_styled("  ╚══════════════════════════════╝", Theme.SUCCESS)
        print()
        narrator_text(
            f"{name} and the crew roll through the gates to cheers. "
            f"The bus — battered, scarred, held together by scrap and stubbornness — "
            f"has carried them to safety."
        )
    elif ending == "secret":
        print_styled("  ╔══════════════════════════════╗", Theme.TITLE)
        print_styled("  ║    MERIDIAN — THE CURE       ║", Theme.TITLE + Color.BOLD)
        print_styled("  ╚══════════════════════════════╝", Theme.TITLE)
        print()
        narrator_text("The cure exists. And now, so does hope.")

    # Show run stats
    print_blank(2)
    print_styled("  -- RUN STATISTICS --", Color.BOLD + Color.BRIGHT_WHITE)
    print(f"  Days survived: {state['current_day']}")
    print(f"  Final threat level: {state['threat_level']}")
    crew = queries.get_alive_crew()
    print(f"  Surviving crew: {len(crew)}")
    upgrades = queries.get_installed_upgrades()
    print(f"  Bus upgrades: {len(upgrades)}")
    flags = queries.get_all_flags()
    print(f"  Key decisions: {len(flags)}")

    print_blank(2)
    press_enter("Press Enter to return to title screen...")


def _check_random_event():
    """Roll for a random event to fire this phase."""
    import random
    from engine.events import pick_random_event, resolve_choice

    if random.random() > 0.30:
        return  # No event this phase

    event = pick_random_event()
    if not event:
        return

    clear_screen()
    print_blank(1)
    scene_break("EVENT")

    narrator_text(event["description"])

    # Present choices
    labels = [c["label"] for c in event["choices"]]
    idx = get_choice(labels, prompt="What do you do?")

    result = resolve_choice(event, idx)

    # Display outcome
    print()
    narrator_text(result["text"])

    if result.get("had_skill_check"):
        if result["skill_passed"]:
            status_update("Skill check: PASSED")
        else:
            print_styled("  ! Skill check: FAILED", Theme.WARNING)

    # Check for recruitment effect
    effects = result.get("effects", {})
    if effects.get("recruit_random"):
        from engine.crew import recruit_next_npc
        new_npc = recruit_next_npc()
        if new_npc:
            print()
            narrator_text(f"A new survivor joins the bus: {new_npc['name']}.")
            # Show their intro dialogue
            templates = None
            import json
            chars_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "data", "characters.json"
            )
            with open(chars_path) as f:
                templates = json.load(f).get("npc_templates", [])
            for t in templates:
                if t["name"] == new_npc["name"]:
                    from ui.narration import dialogue
                    dialogue(new_npc["name"], t.get("intro_dialogue", "..."))
                    break

    press_enter()


# ── MAIN ─────────────────────────────────────────────────

def main():
    """Main entry point."""
    while True:
        # Fresh start each run
        reset_db()

        # Run intro
        result = run_intro()

        if result.get("quit"):
            clear_screen()
            print_styled("\n  Thanks for playing Dead Route.\n", Theme.MUTED)
            sys.exit(0)

        # Create player and game state
        create_player(result)

        # Post-intro transition
        post_intro_transition()

        # Main game loop
        game_phase_loop()

        # After game over, loop back to title


if __name__ == "__main__":
    main()

"""
The Lucky Coin: A 50/50 gamble mechanic inspired by Fear & Hunger.

The coin removes optimization. You can't calculate the best choice.
You pick heads or tails, watch the flip, and live with the result.

Discovery: A scripted event before day 7 introduces the coin through
narrative. After that, certain high-stakes moments offer a "flip the
coin" option alongside normal choices.

Design rules:
  - 4-6 coin moments per run maximum (rare enough to feel significant)
  - The coin is always TRULY 50/50 (no hidden modifiers)
  - Rewards are generous, punishments are cruel
  - The flip animation builds tension
  - The player always has a non-coin choice (never forced to gamble)
"""

import random
import time
import sys
from db import queries
from ui.style import Color, Theme, styled, print_styled, print_blank, clear_screen
from ui.narration import (
    narrator_text, dramatic_pause, scene_break, status_update, _interruptible_sleep
)
from ui.input import get_choice, press_enter, flush_input
from engine.audio import audio


# ── Coin Discovery Event ───────────────────────────────────

DISCOVERY_EVENT = {
    "id": "lucky_coin_discovery",
    "type": "story",
    "description": (
        "You're searching a gas station when your boot kicks something "
        "that clinks against the tile. A coin. Old, heavy, silver — not "
        "the cheap zinc kind. One side shows a woman's face, worn almost "
        "smooth. The other side has an eagle, one wing chipped.\n\n"
        "It's just a coin. But something about the weight of it in your "
        "palm feels... deliberate. Like it was waiting here."
    ),
    "preconditions": {"min_day": 2, "max_day": 7, "flag_false": "has_coin", "chance": 0.35},
}


def check_coin_discovery() -> bool:
    """Check if the coin discovery event should fire. Returns True if it did."""
    state = queries.get_game_state()
    day = state["current_day"]

    if queries.get_flag("has_coin"):
        return False
    if day < 2 or day > 7:
        return False
    if random.random() > 0.35:
        return False

    _run_discovery()
    return True


def _run_discovery():
    """Play the coin discovery scene."""
    clear_screen()
    print_blank(1)
    scene_break("DISCOVERY")

    narrator_text(DISCOVERY_EVENT["description"])
    dramatic_pause(0.5)

    choices = [
        "Pocket it. Can't hurt.",
        "Flip it once. See how it feels.",
        "Leave it. It's just a coin.",
    ]
    idx = get_choice(choices, prompt="")

    if idx == 0:
        narrator_text(
            "You slide the coin into your pocket. It's heavier than it "
            "should be. The metal is warm — body temperature, as if someone "
            "was holding it just moments ago.\n\n"
            "Nobody was."
        )
        queries.set_flag("has_coin", True)
        status_update("Acquired: The Lucky Coin")

    elif idx == 1:
        narrator_text("You balance it on your thumb. The weight is perfect.")
        dramatic_pause(0.5)

        # Mini flip — no stakes, just introduction
        result = _animate_flip()

        narrator_text(
            f"It lands on {result}. You don't know why that feels "
            f"important. You pocket it anyway."
        )
        queries.set_flag("has_coin", True)
        status_update("Acquired: The Lucky Coin")

    else:
        narrator_text(
            "You leave the coin on the floor. Three steps later, you "
            "stop. Turn around. Pick it up.\n\n"
            "You're not sure why. But leaving it felt wrong in a way "
            "you can't explain."
        )
        queries.set_flag("has_coin", True)
        status_update("Acquired: The Lucky Coin")

    press_enter()


# ── The Flip ───────────────────────────────────────────────

COIN_FRAMES = [
    ("  ┌─────────┐", "  │  HEADS  │", "  │    ♛    │", "  └─────────┘"),
    ("  ┌─────────┐", "  │  TAILS  │", "  │    ★    │", "  └─────────┘"),
    ("  ┌─────────┐", "  │ ╱╱╱╱╱╱╱ │", "  │ ╲╲╲╲╲╲╲ │", "  └─────────┘"),
    ("   ┌───────┐ ", "   │ ░░░░░ │ ", "   │ ░░░░░ │ ", "   └───────┘ "),
    ("    ┌─────┐  ", "    │ ▒▒▒ │  ", "    │ ▒▒▒ │  ", "    └─────┘  "),
    ("     ┌───┐   ", "     │ █ │   ", "     │ █ │   ", "     └───┘   "),
    ("      ┌─┐    ", "      │▓│    ", "      │▓│    ", "      └─┘    "),
    ("       │     ", "       ─     ", "       │     ", "             "),
]


def _animate_flip() -> str:
    """
    Animate a coin flip in the terminal.
    Returns 'heads' or 'tails'.
    """
    result = random.choice(["heads", "tails"])

    # Spinning animation
    print()
    for i in range(3):  # 3 full rotations
        for frame_idx in range(len(COIN_FRAMES)):
            # Move cursor up 4 lines and redraw
            if i > 0 or frame_idx > 0:
                sys.stdout.write(f"\033[4A")  # Move up 4 lines

            frame = COIN_FRAMES[frame_idx]
            speed = 0.04 + (i * 0.03)  # Slowing down each rotation
            color = Color.YELLOW if frame_idx < 2 else Color.GRAY

            for line in frame:
                print(f"{color}{line}{Color.RESET}")

            time.sleep(speed)

    # Final slowdown
    for frame_idx in [5, 4, 3, 2]:
        sys.stdout.write(f"\033[4A")
        frame = COIN_FRAMES[frame_idx]
        for line in frame:
            print(f"{Color.GRAY}{line}{Color.RESET}")
        time.sleep(0.12)

    # Land on result
    sys.stdout.write(f"\033[4A")
    if result == "heads":
        final = COIN_FRAMES[0]
        color = Color.BRIGHT_YELLOW + Color.BOLD
    else:
        final = COIN_FRAMES[1]
        color = Color.BRIGHT_CYAN + Color.BOLD

    for line in final:
        print(f"{color}{line}{Color.RESET}")

    time.sleep(0.5)
    print()

    # Dramatic result text
    if result == "heads":
        print_styled(f"              ♛  HEADS  ♛", Color.BRIGHT_YELLOW + Color.BOLD)
    else:
        print_styled(f"              ★  TAILS  ★", Color.BRIGHT_CYAN + Color.BOLD)

    print()
    time.sleep(0.8)

    return result


def offer_coin_flip(
    description: str,
    heads_reward: dict,
    heads_text: str,
    tails_penalty: dict,
    tails_text: str,
    safe_option_text: str = "Play it safe. No coin.",
    safe_result: dict | None = None,
    safe_result_text: str = "You pocket the coin. Some gambles aren't worth taking.",
) -> dict:
    """
    Present a coin flip choice to the player.

    Returns dict with:
        flipped: bool (did they flip)
        result: 'heads' | 'tails' | 'safe'
        effects: dict of resource/stat changes
        text: narrative text
    """
    if not queries.get_flag("has_coin"):
        # No coin — can't flip
        return {"flipped": False, "result": "safe", "effects": safe_result or {}, "text": safe_result_text}

    print()
    narrator_text(description)
    dramatic_pause(0.3)

    # Show the stakes
    print()
    print_styled("  ╔══════════════════════════════════════╗", Color.YELLOW)
    print_styled("  ║        THE COIN WHISPERS...          ║", Color.YELLOW + Color.BOLD)
    print_styled("  ╚══════════════════════════════════════╝", Color.YELLOW)
    print()
    print_styled("  Heads: " + _format_effects(heads_reward), Theme.SUCCESS)
    print_styled("  Tails: " + _format_effects(tails_penalty), Theme.DAMAGE)
    print()

    choices = [
        "Flip the coin. 50/50. All or nothing.",
        safe_option_text,
    ]
    idx = get_choice(choices, prompt="Do you trust the coin?")

    if idx == 1:
        narrator_text(safe_result_text)
        return {
            "flipped": False,
            "result": "safe",
            "effects": safe_result or {},
            "text": safe_result_text,
        }

    # ── THE FLIP ──
    narrator_text("You pull the coin from your pocket. The silver catches the light.")
    dramatic_pause(0.5)

    flush_input()
    pick = get_choice(["Heads", "Tails"], prompt="Call it.")

    player_call = "heads" if pick == 0 else "tails"

    narrator_text("You flick it into the air. It spins, catching light and shadow in equal measure.")
    dramatic_pause(0.5)

    result = _animate_flip()

    won = (result == player_call)

    if won:
        # Victory
        print_styled("  You called it.", Theme.SUCCESS + Color.BOLD)
        dramatic_pause(0.5)
        narrator_text(heads_text)
        _apply_coin_effects(heads_reward)
        return {
            "flipped": True,
            "result": "heads",
            "won": True,
            "effects": heads_reward,
            "text": heads_text,
        }
    else:
        # Loss
        print_styled("  Wrong call.", Theme.DAMAGE + Color.BOLD)
        dramatic_pause(0.5)
        narrator_text(tails_text)
        _apply_coin_effects(tails_penalty)
        return {
            "flipped": True,
            "result": "tails",
            "won": False,
            "effects": tails_penalty,
            "text": tails_text,
        }


# ── Predefined Coin Moments ───────────────────────────────
# These are injected into specific game situations.

COIN_MOMENTS = {
    "blocked_road": {
        "description": (
            "A collapsed overpass blocks the road. There are two gaps — "
            "one on the left, one on the right. Both are narrow. One is "
            "clear. The other is a dead end with a horde behind the rubble. "
            "You can't see which is which from here."
        ),
        "heads_reward": {"fuel": 0},  # Just safe passage
        "heads_text": (
            "The left gap opens into clear road. You thread the bus through "
            "with inches to spare. The coin knew."
        ),
        "tails_penalty": {"bus_damage": 15, "damage_all_crew": 10},
        "tails_text": (
            "Dead end. The bus slams to a stop against a concrete wall. "
            "And then you hear them — pouring over the rubble behind you. "
            "You reverse blind, scraping the bus along both walls, the horde "
            "hammering the rear. You make it out. Barely."
        ),
        "safe_option_text": "Turn back and find another route (costs 5 fuel).",
        "safe_result": {"fuel": -5},
        "safe_result_text": "You take the long way around. Safer. More expensive.",
    },

    "mysterious_crate": {
        "description": (
            "A crate sits in the middle of the road. Unmarked. Sealed. "
            "Could be military supplies. Could be bait. Could be nothing. "
            "The coin feels warm in your pocket."
        ),
        "heads_reward": {"ammo": 8, "medicine": 3, "scrap": 6},
        "heads_text": (
            "Military grade. Ammunition, medical supplies, spare parts — "
            "someone was hoarding the good stuff. Today, the universe gives back."
        ),
        "tails_penalty": {"damage_random_crew": 30, "ammo": -3},
        "tails_text": (
            "Booby-trapped. The lid triggers a shotgun blast that catches "
            "whoever opened it square in the chest. The crate is empty "
            "except for the trap mechanism and a note that says 'STAY AWAY.'"
        ),
        "safe_option_text": "Leave it. Not worth the risk.",
        "safe_result_text": "You drive around it. Curiosity kills.",
    },

    "survivor_standoff": {
        "description": (
            "An armed group blocks the road. Six of them, all pointing "
            "guns at the bus. Their leader steps forward.\n\n"
            "\"Toll road. Everything in the bus, or we shoot.\"\n\n"
            "You notice one of them is shaking. They're scared. This "
            "could go either way."
        ),
        "heads_reward": {"food": 5, "ammo": 4, "scrap": 3},
        "heads_text": (
            "You step out with the coin held high. \"One flip. Heads, "
            "you let us pass AND give us supplies. Tails, we give you "
            "everything.\"\n\n"
            "The leader laughs. \"You're insane.\" But he agrees.\n\n"
            "Heads. His face falls. A deal is a deal — even at the "
            "end of the world. You drive away richer."
        ),
        "tails_penalty": {"food": -4, "scrap": -5, "ammo": -3},
        "tails_text": (
            "Tails. The leader grins. \"A deal's a deal.\"\n\n"
            "They take almost everything. Food, scrap, ammunition. Your "
            "crew watches in silent fury as weeks of scavenging walks away "
            "in someone else's bags."
        ),
        "safe_option_text": "Ram through them (costs bus armor, risks crew damage).",
        "safe_result": {"bus_damage": 20, "damage_random_crew": 15},
        "safe_result_text": (
            "You floor it. Bodies scatter. Gunshots crack the windows. The "
            "bus takes hits but punches through. Behind you, shouting "
            "fades into distance."
        ),
    },

    "last_medicine": {
        "description": (
            "Two of your crew are hurt. Bad. You have one dose of medicine. "
            "Not enough for both. You could split it — half-dose each, "
            "probably not enough to save either. Or you could flip the coin "
            "and let fate pick who gets the full dose."
        ),
        "heads_reward": {"heal_first_wounded": 50},
        "heads_text": (
            "The coin chooses. The medicine goes to the first one. Full dose. "
            "They'll make it. The other watches from across the bus, and you "
            "can't meet their eyes."
        ),
        "tails_penalty": {"heal_second_wounded": 50},
        "tails_text": (
            "The coin chooses. The medicine goes to the second one. Full dose. "
            "The first stares at the empty syringe and says nothing. What "
            "is there to say?"
        ),
        "safe_option_text": "Split the dose evenly (half-heal both).",
        "safe_result": {"heal_all_wounded": 20},
        "safe_result_text": (
            "Half a dose each. It might not be enough. But at least the "
            "choice wasn't yours."
        ),
    },

    "the_bridge_gamble": {
        "description": (
            "The bridge ahead is crumbling. The supports are rusted, the "
            "deck is cracked, and the river below is a seventy-foot drop "
            "into rocks. The bus is heavy. Heavier with the upgrades.\n\n"
            "It might hold. It might not. There's no way to know without "
            "driving onto it."
        ),
        "heads_reward": {"fuel": 0},
        "heads_text": (
            "The bridge groans. Screams. Pieces of concrete fall away "
            "beneath the wheels. But the bus keeps moving, and the far "
            "side gets closer, and then you're across and the bridge "
            "collapses behind you into the river.\n\n"
            "Nobody speaks for five minutes."
        ),
        "tails_penalty": {"bus_damage": 25, "damage_all_crew": 15, "fuel": -8},
        "tails_text": (
            "The bridge gives. Not all at once — slowly, sickeningly. The "
            "rear axle drops through the deck. The bus tilts at a nightmare "
            "angle. Everyone screams. You gun the engine and the front "
            "wheels claw at the breaking concrete and somehow, somehow, "
            "the bus lurches forward onto solid ground.\n\n"
            "The back half of the bridge falls into the gorge. The bus is "
            "damaged. Everyone is hurt. But you're on the other side."
        ),
        "safe_option_text": "Find another crossing (costs a full day + fuel).",
        "safe_result": {"fuel": -10},
        "safe_result_text": (
            "You turn the bus around and spend an entire day finding a "
            "crossing that isn't trying to kill you. It costs fuel you "
            "can barely spare. But everyone's alive."
        ),
    },
}


def get_random_coin_moment() -> dict | None:
    """
    Get a random coin flip moment. ~15% chance per explore at eligible phases.
    Returns None if no coin or wrong conditions.
    """
    if not queries.get_flag("has_coin"):
        return None

    state = queries.get_game_state()

    # Don't offer too many flips per run
    flip_count = _get_flip_count()
    if flip_count >= 5:
        return None

    # 15% base chance
    if random.random() > 0.15:
        return None

    # Pick a moment that hasn't been used
    used = set()
    all_flags = queries.get_all_flags()
    for key in COIN_MOMENTS:
        if all_flags.get(f"coin_used_{key}"):
            used.add(key)

    available = [k for k in COIN_MOMENTS if k not in used]
    if not available:
        return None

    key = random.choice(available)
    queries.set_flag(f"coin_used_{key}", True)
    return COIN_MOMENTS[key]


def _get_flip_count() -> int:
    """Count how many coin flips have happened this run."""
    flags = queries.get_all_flags()
    return sum(1 for k in flags if k.startswith("coin_used_") and flags[k])


def _apply_coin_effects(effects: dict):
    """Apply coin flip effects to game state."""
    resource_keys = {"fuel", "food", "scrap", "ammo", "medicine"}
    resource_changes = {}

    for key, val in effects.items():
        if key in resource_keys:
            resource_changes[key] = val
        elif key == "damage_random_crew":
            crew = queries.get_alive_crew()
            if crew:
                target = random.choice(crew)
                queries.damage_character(target["id"], val)
                status_update(f"{target['name']} takes {val} damage")
        elif key == "damage_all_crew":
            for c in queries.get_alive_crew():
                queries.damage_character(c["id"], val)
            status_update(f"All crew take {val} damage")
        elif key == "bus_damage":
            from engine.bus_damage import apply_bus_damage
            result = apply_bus_damage(val)
            if result.get("narrative"):
                narrator_text(result["narrative"])
        elif key == "heal_first_wounded":
            wounded = [c for c in queries.get_alive_crew() if c["hp"] < c["hp_max"]]
            if wounded:
                queries.heal_character(wounded[0]["id"], val)
                queries.update_resources(medicine=-1)
                status_update(f"{wounded[0]['name']} healed for {val} HP")
        elif key == "heal_second_wounded":
            wounded = [c for c in queries.get_alive_crew() if c["hp"] < c["hp_max"]]
            if len(wounded) > 1:
                queries.heal_character(wounded[1]["id"], val)
                queries.update_resources(medicine=-1)
                status_update(f"{wounded[1]['name']} healed for {val} HP")
        elif key == "heal_all_wounded":
            queries.update_resources(medicine=-1)
            for c in queries.get_alive_crew():
                if c["hp"] < c["hp_max"]:
                    queries.heal_character(c["id"], val)
            status_update(f"All wounded crew healed for {val} HP")

    if resource_changes:
        queries.update_resources(**resource_changes)
        for k, v in resource_changes.items():
            if v > 0:
                status_update(f"+{v} {k.capitalize()}")
            elif v < 0:
                print_styled(f"  ! -{abs(v)} {k.capitalize()}", Theme.WARNING)


def _format_effects(effects: dict) -> str:
    """Format effects dict into a readable string."""
    parts = []
    names = {
        "fuel": "Fuel", "food": "Food", "scrap": "Scrap",
        "ammo": "Ammo", "medicine": "Medicine",
        "damage_random_crew": "Crew damage",
        "damage_all_crew": "All crew damage",
        "bus_damage": "Bus damage",
    }
    for key, val in effects.items():
        name = names.get(key, key)
        if isinstance(val, int):
            if val > 0 and key not in ("damage_random_crew", "damage_all_crew", "bus_damage"):
                parts.append(f"+{val} {name}")
            elif val < 0:
                parts.append(f"{val} {name}")
            elif key in ("damage_random_crew", "damage_all_crew", "bus_damage"):
                parts.append(f"{val} {name}")
        elif key.startswith("heal"):
            parts.append(f"Heal {val} HP")
    return ", ".join(parts) if parts else "Safe passage"

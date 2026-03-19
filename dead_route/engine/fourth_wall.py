"""
The Breach: A 4th wall breaking event.

IMPORTANT SECURITY NOTE:
    This module does NOTHING outside the terminal.
    No popups, no file access, no system calls, no network.
    Everything is ANSI escape codes and print() statements.
    The "crash" is fake text. The "glitch" is unicode characters.
    It's theater. The IT department will not care.

Triggers after the player makes enough dark choices.
The game "notices" and responds.
"""

import random
import time
import sys
import os
from db import queries
from ui.style import Color, Theme, print_styled, print_blank, clear_screen, flush_input
from ui.input import press_enter, get_choice
from engine.audio import audio


# ── Glitch Characters ──────────────────────────────────────
# Zalgo-style corruption. Just unicode. Looks terrifying in a terminal.

GLITCH_CHARS = "̴̵̶̷̸̡̢̧̨̛̖̗̘̙̜̝̞̟̠̣̤̥̦̩̪̫̬̭̮̯̰̱̲̳̹̺̻̼"
CORRUPT_CHARS = "▓░▒█▌▐╪╫╬┼┤├┬┴═║╣╠╦╩╬▀▄■□"
CREEPY_FONT = {
    "a": "ą", "b": "ɓ", "c": "ȼ", "d": "đ", "e": "ɇ",
    "f": "ƒ", "g": "ǥ", "h": "ħ", "i": "ɨ", "j": "ɉ",
    "k": "ƙ", "l": "ł", "m": "ɱ", "n": "ɲ", "o": "ø",
    "p": "ƥ", "q": "ʠ", "r": "ɍ", "s": "ȿ", "t": "ŧ",
    "u": "ʉ", "v": "ʋ", "w": "ɯ", "x": "χ", "y": "ɏ",
    "z": "ʑ",
}


def _zalgo(text: str, intensity: int = 2) -> str:
    """Add zalgo-style corruption to text."""
    result = []
    for char in text:
        result.append(char)
        for _ in range(random.randint(0, intensity)):
            result.append(random.choice(GLITCH_CHARS))
    return "".join(result)


def _corrupt_text(text: str, corruption: float = 0.3) -> str:
    """Replace random characters with glitch symbols."""
    result = []
    for char in text:
        if random.random() < corruption and char.strip():
            result.append(random.choice(CORRUPT_CHARS))
        else:
            result.append(char)
    return "".join(result)


def _creepy_case(text: str) -> str:
    """aLtErNaTiNg CaSe for unsettling effect."""
    result = []
    upper = False
    for char in text:
        if char.isalpha():
            result.append(char.upper() if upper else char.lower())
            upper = not upper
        else:
            result.append(char)
    return "".join(result)


def _creepy_font(text: str) -> str:
    """Replace letters with creepy unicode equivalents."""
    return "".join(CREEPY_FONT.get(c.lower(), c) for c in text)


# ── Dark Choice Tracking ──────────────────────────────────

DARK_FLAGS = [
    "robbed_family",
    "mercy_kill",
    "meat_grinder_sacrifice",
    "abandoned_stranger_count",
    "ignored_family",
    "blaze_of_glory",
    "failed_meat_grinder",
]


def get_darkness_score() -> int:
    """Count how many dark choices the player has made."""
    score = 0
    for flag in DARK_FLAGS:
        if queries.get_flag(flag):
            score += 1
    return score


def should_trigger() -> bool:
    """Check if the 4th wall event should fire."""
    state = queries.get_game_state()
    # Don't fire before day 10
    if state["current_day"] < 10:
        return False
    # Don't fire if already happened
    if queries.get_flag("fourth_wall_triggered"):
        return False
    # Need at least 2 dark choices
    darkness = get_darkness_score()
    if darkness < 2:
        return False
    # Chance scales with darkness: 2 flags = 5%, 3 = 10%, 4+ = 15%
    chance = 0.05 * (darkness - 1)
    return random.random() < chance


# ── The Event ──────────────────────────────────────────────

def run_fourth_wall_event():
    """
    The Breach. The game notices you.

    Everything in this function is print() and time.sleep().
    No file access, no OS calls, no popups. Terminal only.
    """
    state = queries.get_game_state()
    player_name = state["player_name"]

    queries.set_flag("fourth_wall_triggered", True)

    audio.play_music("horror_ambient")

    # ── Phase 1: Subtle wrongness ──
    clear_screen()
    print_blank(2)

    # Normal-looking game text that's slightly off
    print_styled(
        f"  Day {state['current_day']} — {state['current_phase'].upper()}",
        Color.BRIGHT_WHITE
    )
    time.sleep(1.0)

    # A character says something they shouldn't know
    crew = queries.get_alive_npcs()
    if crew:
        speaker = random.choice(crew)
        print()
        print(f"  {Theme.NPC_NAME}{speaker['name']}:{Color.RESET}")
        time.sleep(0.5)

        # The dialogue starts normal then derails
        _type_slow(f'    "Hey, {player_name}. Can I ask you something?"')
        time.sleep(1.0)
        _type_slow(f'    "Do you ever feel like... someone is watching?"')
        time.sleep(1.5)
        _type_slow(f'    "Not the infected. Something else. Something above us."')
        time.sleep(1.5)

        # Speaker looks directly at the player
        _type_slow(f'    "Something that makes choices for us."')
        time.sleep(2.0)

    # ── Phase 2: The glitch ──
    print()
    time.sleep(0.5)

    # Text starts corrupting
    for i in range(4):
        line = f"  Day {state['current_day']} — {state['current_phase'].upper()}"
        corruption = 0.1 * (i + 1)
        print(f"\r  {_corrupt_text(line, corruption)}", end="", flush=True)
        time.sleep(0.3)

    print()
    time.sleep(0.5)

    # Screen floods with glitch
    for _ in range(6):
        width = random.randint(40, 70)
        line = "".join(random.choice(CORRUPT_CHARS) for _ in range(width))
        print(f"  {Color.RED}{line}{Color.RESET}")
        time.sleep(0.08)

    time.sleep(0.5)
    clear_screen()

    # ── Phase 3: The "crash" ──
    # Fake Python traceback — looks real but is just text
    time.sleep(0.3)
    fake_crash = f"""Traceback (most recent call last):
  File "dead_route/engine/game_loop.py", line 107, in run
    state = queries.get_game_state()
  File "dead_route/db/queries.py", line 34, in get_game_state
    row = conn.execute("SELECT * FROM game_state WHERE id = 1").fetchone()
sqlite3.OperationalError: database is locked

During handling of the above exception, another exception occurred:

  File "dead_route/engine/events.py", line 89, in resolve_choice
    _apply_effects(effects, state, crew)
  File "dead_route/engine/events.py", line 142, in _apply_effects
    ??? = ???.???("W̷̤̑H̸̭͝O̵̙͗ ̶̣̈I̷̘̊S̶̗͂ ̸͇̈P̴̰͝L̷̨̂Å̴̲Y̷̰̐İ̴̘N̶̤̊G̶̣̚")
RuntimeError: {_creepy_case("something is wrong")}"""

    for line in fake_crash.split("\n"):
        print(f"{Color.RED}{line}{Color.RESET}")
        time.sleep(0.06)

    time.sleep(2.0)

    # ── Phase 4: The message ──
    clear_screen()
    time.sleep(1.5)

    # Build the creepy message based on player's dark choices
    darkness = get_darkness_score()
    messages = _get_messages(player_name, darkness, state)

    for msg in messages:
        # Print character by character with random pauses
        for char in msg:
            sys.stdout.write(f"{Color.BRIGHT_RED}{char}{Color.RESET}")
            sys.stdout.flush()
            if char == " ":
                time.sleep(random.uniform(0.02, 0.08))
            elif char in ".?!":
                time.sleep(random.uniform(0.3, 0.8))
            else:
                time.sleep(random.uniform(0.04, 0.12))
        print()
        time.sleep(random.uniform(0.5, 1.5))

    time.sleep(2.0)

    # ── Phase 5: Direct address ──
    print()
    time.sleep(1.0)

    # This part is the gut punch — it knows the player's name
    final = _creepy_case(f"I see you, {player_name}.")
    print(f"\n  {Color.BRIGHT_RED}{Color.BOLD}{final}{Color.RESET}")
    time.sleep(3.0)

    final2 = _creepy_case("Every choice you made. I felt all of them.")
    print(f"  {Color.BRIGHT_RED}{final2}{Color.RESET}")
    time.sleep(2.0)

    # ── Phase 6: The "recovery" ──
    clear_screen()
    time.sleep(1.0)

    # Looks like a system reboot
    print(f"{Color.GRAY}  Recovering game state...{Color.RESET}")
    time.sleep(0.5)
    print(f"{Color.GRAY}  Database integrity: OK{Color.RESET}")
    time.sleep(0.3)
    print(f"{Color.GRAY}  Restoring from last save...{Color.RESET}")
    time.sleep(0.8)
    print(f"{Color.GRAY}  Done.{Color.RESET}")
    time.sleep(1.0)

    # Resume as if nothing happened
    clear_screen()
    print_blank(2)

    # But one last thing — a crew member comments on it
    if crew:
        speaker = random.choice(crew)
        print(f"  {Theme.NPC_NAME}{speaker['name']}:{Color.RESET}")
        _type_slow(f'    "...did the lights just flicker?"')
        time.sleep(1.0)
        _type_slow(f'    "Probably nothing."')
        time.sleep(0.5)

    print()

    flush_input()
    press_enter()

    # Resume normal phase music
    from engine.audio import play_phase_music
    play_phase_music(state["current_phase"], state["current_day"])


def _get_messages(player_name: str, darkness: int, state: dict) -> list[str]:
    """Generate the creepy messages based on what the player has done."""
    messages = []

    if queries.get_flag("mercy_kill"):
        messages.append(
            f"  You pulled the trigger. You told yourself it was mercy."
        )
        messages.append(
            f"  Was it?"
        )

    if queries.get_flag("robbed_family") or queries.get_flag("ignored_family"):
        messages.append(
            f"  The child. You remember the child."
        )
        messages.append(
            f"  I remember too."
        )

    if queries.get_flag("meat_grinder_sacrifice"):
        messages.append(
            f"  You fed someone to the machine."
        )
        messages.append(
            f"  You knew. You KNEW. And you did it anyway."
        )

    if not messages:
        messages = [
            f"  You think this is a game.",
            f"  You think the choices don't matter.",
            f"  They do. They all do.",
        ]

    # Always end with this
    messages.append("")
    messages.append(f"  {_creepy_case('why did you do this to me?')}")

    return messages


def _type_slow(text: str, base_delay: float = 0.035):
    """Type text slowly — used for the 4th wall dialogue."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(base_delay)
    print()

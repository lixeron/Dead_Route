"""
Intro sequence: text crawl, character creation, bus discovery.
This is the player's first experience with the game.
"""

import time
from ui.style import Color, Theme, styled, print_styled, print_blank, clear_screen
from ui.narration import (
    crawl_text, narrator_text, dialogue, scene_break,
    title_card, reveal_text, dramatic_pause, status_update
)
from ui.input import get_text_input, get_choice, press_enter
from db import queries


PRONOUN_MAP = {
    "He/Him":    ("he", "him", "his"),
    "She/Her":   ("she", "her", "her"),
    "They/Them": ("they", "them", "their"),
}


def run_intro() -> dict:
    """
    Run the complete intro sequence.
    Returns dict with player_name, pronouns, starting_skill.
    """
    # ── TITLE SCREEN ──
    title_card("DEAD ROUTE", "A Zombie Survival Roguelite")
    dramatic_pause(1.0)

    choice = get_choice(
        ["New Game", "Quit"],
        prompt="",
    )
    if choice == 1:
        return {"quit": True}

    # ── TEXT CRAWL ──
    clear_screen()
    print_blank(2)

    crawl_text([
        "It started with a cough.",
        "",
        "That's what they said on the news, anyway. A cough, then a fever,",
        "then something worse. The government called it LAZARUS — a weaponized",
        "pathogen that escaped a black-site lab in the Nevada desert.",
        "",
        "Within 72 hours, the major cities fell.",
    ], delay_per_line=0.03, pause_between=0.6, style=Theme.NARRATOR)

    press_enter()
    clear_screen()
    print_blank(2)

    crawl_text([
        "The infected don't just die. They come back.",
        "Faster. Hungrier. Wrong.",
        "",
        "The military held out for three weeks. Then the bases went dark,",
        "one by one, like candles in a hurricane. The last emergency",
        "broadcast was six months ago. Since then — static.",
        "",
        "Now it's just scattered survivors, empty highways,",
        "and the dead. Always the dead.",
    ], delay_per_line=0.03, pause_between=0.6, style=Theme.NARRATOR)

    press_enter()
    clear_screen()
    print_blank(2)

    crawl_text([
        "You've been surviving alone for weeks.",
        "Scavenging. Hiding. Running.",
        "",
        "But today, something changes.",
    ], delay_per_line=0.04, pause_between=0.8, style=Theme.NARRATOR)

    dramatic_pause(2.0)

    # ── CHARACTER CREATION ──
    clear_screen()
    print_blank(2)

    narrator_text("You catch your reflection in a cracked window. Dirty. Tired. But alive.")
    dramatic_pause(1.0)

    # Name
    player_name = ""
    while not player_name:
        player_name = get_text_input("What's your name, survivor?")
        if not player_name:
            print_styled("  You must have a name. Everyone does.", Theme.MUTED)

    print()
    narrator_text(f"{player_name}. You say it out loud, just to remember what it sounds like.")
    dramatic_pause(0.8)

    # Pronouns
    scene_break()
    pronoun_choice = get_choice(
        ["He / Him", "She / Her", "They / Them", "Custom"],
        prompt="How should people refer to you?",
    )

    if pronoun_choice == 3:
        subj = get_text_input("Subject pronoun (e.g., 'he', 'she', 'they'):") or "they"
        obj = get_text_input("Object pronoun (e.g., 'him', 'her', 'them'):") or "them"
        poss = get_text_input("Possessive pronoun (e.g., 'his', 'her', 'their'):") or "their"
        pronoun_label = f"{subj}/{obj}"
    else:
        labels = ["He/Him", "She/Her", "They/Them"]
        pronoun_label = labels[pronoun_choice]
        subj, obj, poss = PRONOUN_MAP[pronoun_label]

    dramatic_pause(0.5)

    # ── BUS DISCOVERY ──
    clear_screen()
    print_blank(2)

    scene_break("LATER THAT DAY")

    narrator_text(
        "You're cutting through the parking lot of an abandoned elementary school "
        "when you see it."
    )
    dramatic_pause(1.0)

    narrator_text(
        "A school bus. Yellow paint peeling, windows cracked, tires low but not flat. "
        "It's been sitting here since the outbreak — abandoned mid-evacuation, judging "
        "by the tiny backpacks scattered across the asphalt."
    )
    dramatic_pause(0.8)

    narrator_text(
        "But the engine block is intact. You can see that even from here. And the "
        "fuel gauge, barely visible through the grimy windshield, shows a quarter tank."
    )
    dramatic_pause(1.0)

    print()
    narrator_text(
        "A quarter tank. That's more fuel than you've seen in weeks."
    )
    dramatic_pause(1.0)

    narrator_text(
        "You climb the steps. The driver's seat creaks under your weight. The key is "
        "still in the ignition."
    )

    # First choice — really just one option (teaches "the bus is central")
    get_choice(
        ["Turn the key."],
        prompt="",
    )

    print()
    narrator_text("You turn the key.")
    dramatic_pause(1.5)

    narrator_text("Nothing.")
    dramatic_pause(1.0)

    narrator_text("You try again.")
    dramatic_pause(1.0)

    # Sound effect via text
    print()
    print_styled("  ...", Theme.MUTED)
    time.sleep(0.8)
    print_styled("  ...rrrr...", Theme.MUTED)
    time.sleep(0.8)
    print_styled("  ...RRRRRRVVVVVV—", Theme.WARNING)
    time.sleep(0.5)
    print()

    reveal_text("The engine catches.", style=Theme.SUCCESS + Color.BOLD)
    dramatic_pause(1.0)

    narrator_text(
        "The bus shudders to life, coughing black smoke. The dashboard lights "
        "flicker on — most of them warnings. But it's running."
    )

    narrator_text(
        "For the first time in months, you have wheels."
    )
    dramatic_pause(1.0)

    # ── STARTING SKILL CHOICE (disguised as narrative) ──
    scene_break()

    narrator_text(
        "Before you pull out of the lot, you glance at the seats behind you. "
        "There's some gear left behind — you can only grab one thing before "
        "the noise attracts attention."
    )

    skill_choice = get_choice(
        [
            "A heavy crowbar wedged under a seat  (Combat)",
            "A battered first-aid kit in the overhead rack  (Medical)",
            "A toolbox with wrenches and duct tape  (Mechanical)",
            "A camping backpack stuffed with supplies  (Scavenging)",
        ],
        prompt="What do you grab?",
    )

    skill_map = {
        0: ("combat", "crowbar", "The crowbar feels good in your hands. Solid. Dependable."),
        1: ("medical", "first-aid kit", "Bandages, antiseptic, painkillers. Worth more than gold now."),
        2: ("mechanical", "toolbox", "Wrenches, pliers, duct tape. You can keep this bus running."),
        3: ("scavenging", "backpack", "Flashlight, rope, pry bar, empty containers. A scavenger's dream kit."),
    }

    skill_name, item_name, item_text = skill_map[skill_choice]

    print()
    narrator_text(f"You grab the {item_name}.")
    narrator_text(item_text)
    dramatic_pause(0.5)

    # ── FIRST DRIVE ──
    scene_break()

    narrator_text(
        "You throw the bus into gear and roll out of the parking lot. "
        "The steering is sluggish, the brakes squeal, and something under "
        "the hood is making a sound that can't be good."
    )
    dramatic_pause(0.5)

    narrator_text("But you're moving. And right now, moving is everything.")
    dramatic_pause(1.0)

    # Show fuel consumption for the first time
    status_update("Fuel consumed: 3")
    status_update("Fuel remaining: 27")
    dramatic_pause(0.5)

    narrator_text(
        "The road stretches out ahead. Cracked asphalt, abandoned cars, "
        "overgrown medians. Somewhere out there, people say there's a "
        "safe zone — a walled settlement called Haven."
    )
    dramatic_pause(0.5)

    narrator_text("You don't know if it's real. But it's a direction. And that's enough.")

    press_enter()

    # ── CREATE GAME STATE ──
    clear_screen()
    print_blank(2)
    reveal_text("Your story begins.", style=Theme.TITLE + Color.BOLD)
    dramatic_pause(1.5)

    return {
        "quit": False,
        "player_name": player_name,
        "pronouns": pronoun_label,
        "subj": subj,
        "obj": obj,
        "poss": poss,
        "starting_skill": skill_name,
    }

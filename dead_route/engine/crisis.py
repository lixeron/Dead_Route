"""
Crisis events: forced hard choices triggered by desperate situations.
Rationing, mutiny, triage — situations with no good answers.
"""

import random
from db import queries
from ui.style import Color, Theme, styled, print_styled
from ui.narration import (
    narrator_text, dramatic_pause, scene_break, status_update, dialogue
)
from ui.input import get_choice, get_choice_with_details, press_enter


def check_forced_events():
    """Check for crisis situations that force hard decisions."""
    resources = queries.get_resources()
    crew = queries.get_alive_crew()
    npcs = queries.get_alive_npcs()

    # Rationing: food critically low with 3+ crew
    if resources["food"] <= 2 and len(crew) >= 3 and random.random() < 0.5:
        _rationing_event(crew, resources)

    # Mutiny: multiple low-trust NPCs
    low_trust = [c for c in npcs if c["trust"] <= 25]
    if len(low_trust) >= 2 and random.random() < 0.25:
        _mutiny_event(low_trust)

    # Triage: multiple badly wounded, only 1 medicine
    wounded = [c for c in crew if c["hp"] < 30 and c["is_alive"]]
    if len(wounded) >= 2 and resources["medicine"] == 1:
        _triage_event(wounded)


def _rationing_event(crew: list, resources: dict):
    """Force the player to decide who eats."""
    from ui.style import clear_screen, print_blank
    clear_screen()
    print_blank(1)
    scene_break("CRISIS — RATIONING")

    narrator_text(
        f"There's barely any food left. {resources['food']} units for "
        f"{len(crew)} people. Someone isn't eating tonight."
    )
    dramatic_pause(0.5)

    options = [
        {"label": "Split it evenly — everyone gets a little",
         "description": "Nobody starves, but nobody heals either. Everyone stays hungry."},
        {"label": "Feed the wounded first",
         "description": "Injured crew get food. Healthy members go without. Healthy crew trust drops."},
        {"label": "Feed whoever is most useful",
         "description": "Prioritize best fighters and scavengers. The others notice."},
        {"label": "You skip your own meal",
         "description": "Lead by example. You take damage, but crew trust increases."},
    ]
    idx = get_choice_with_details(options, prompt="What do you do?")

    if idx == 0:
        narrator_text(
            "You divide what's left into tiny, unsatisfying portions. "
            "Nobody complains. Nobody's happy either."
        )
        for c in crew:
            if not c["is_player"]:
                queries.change_trust(c["id"], -1)
    elif idx == 1:
        wounded = [c for c in crew if c["hp"] < c["hp_max"] * 0.6]
        healthy = [c for c in crew if c["hp"] >= c["hp_max"] * 0.6 and not c["is_player"]]
        narrator_text("The wounded eat. The rest watch with hollow eyes.")
        for c in wounded:
            queries.heal_character(c["id"], 10)
        for c in healthy:
            queries.change_trust(c["id"], -5)
            queries.damage_character(c["id"], 5)
    elif idx == 2:
        narrator_text(
            "You make the cold calculus. The best survive. The rest tighten their belts."
        )
        npcs = queries.get_alive_npcs()
        npcs_sorted = sorted(npcs, key=lambda c: c["combat"] + c["scavenging"], reverse=True)
        for i, c in enumerate(npcs_sorted):
            if i < len(npcs_sorted) // 2:
                queries.change_trust(c["id"], 2)
            else:
                queries.change_trust(c["id"], -8)
                queries.damage_character(c["id"], 5)
    elif idx == 3:
        narrator_text(
            "You push your share toward the others. Your stomach screams, "
            "but the look on their faces is worth it. Maybe."
        )
        player = queries.get_player()
        if player:
            queries.damage_character(player["id"], 12)
        for c in queries.get_alive_npcs():
            queries.change_trust(c["id"], 5)

    press_enter()


def _mutiny_event(low_trust_npcs: list):
    """Low-trust crew members confront the player."""
    from ui.style import clear_screen, print_blank
    clear_screen()
    print_blank(1)
    scene_break("CRISIS — CONFRONTATION")

    names = " and ".join(c["name"] for c in low_trust_npcs[:2])
    narrator_text(
        f"{names} corner you at the back of the bus. Their body language says "
        f"this has been building for a while."
    )

    ringleader = low_trust_npcs[0]
    dialogue(
        ringleader["name"],
        "We need to talk. About how things are being run. About whether "
        "we're even going the right direction. About whether you're the "
        "right person to be making these calls."
    )

    options = [
        {"label": "Hear them out and make concessions",
         "description": "Give them more say. Trust recovers, but you lose resources."},
        {"label": "Stand firm — this isn't a democracy",
         "description": "Assert dominance. They back down or leave."},
        {"label": "Offer to share leadership responsibilities",
         "description": "Compromise. Moderate trust recovery."},
    ]
    idx = get_choice_with_details(options, prompt="How do you respond?")

    if idx == 0:
        narrator_text(
            "You listen. You concede some points. It costs you pride, but it buys you time."
        )
        for c in low_trust_npcs:
            queries.change_trust(c["id"], 15)
        queries.update_resources(food=-1, ammo=-1)
        status_update("Shared 1 Food and 1 Ammo as a gesture of goodwill")
    elif idx == 1:
        narrator_text(
            "\"I'm keeping this bus moving and you're all still alive. "
            "That's my resume. You don't like it? The door is right there.\""
        )
        dramatic_pause(0.5)
        if random.random() < 0.4:
            leaver = random.choice(low_trust_npcs)
            queries.update_character(leaver["id"], is_alive=0)
            narrator_text(
                f"{leaver['name']} grabs their pack and walks off the bus without a word."
            )
            dramatic_pause(1.0)
        else:
            narrator_text(
                "They back down. For now. But you can feel the tension "
                "like a wire about to snap."
            )
            for c in low_trust_npcs:
                queries.change_trust(c["id"], -5)
    elif idx == 2:
        narrator_text(
            "You offer a seat at the table. It's not everything they want, "
            "but it's something."
        )
        for c in low_trust_npcs:
            queries.change_trust(c["id"], 8)

    press_enter()


def _triage_event(wounded: list):
    """Only 1 medicine, multiple wounded — who gets it?"""
    from ui.style import clear_screen, print_blank
    clear_screen()
    print_blank(1)
    scene_break("CRISIS — TRIAGE")

    narrator_text(
        f"One dose of medicine. {len(wounded)} people who need it. "
        f"Someone has to make the call."
    )

    options = []
    for c in wounded:
        skill_best = max(c["combat"], c["medical"], c["mechanical"], c["scavenging"])
        options.append(
            f"Give it to {c['name']} (HP: {c['hp']}/{c['hp_max']}, Best skill: {skill_best})"
        )
    options.append("Save it — nobody gets it right now")

    idx = get_choice(options, prompt="Who receives the medicine?")

    if idx < len(wounded):
        recipient = wounded[idx]
        others = [c for c in wounded if c["id"] != recipient["id"]]

        queries.update_resources(medicine=-1)
        queries.heal_character(recipient["id"], 35)
        narrator_text(
            f"You administer the medicine to {recipient['name']}. "
            f"Relief washes over their face."
        )
        for c in others:
            if not c["is_player"]:
                queries.change_trust(c["id"], -8)
                narrator_text(
                    f"{c['name']} watches in silence. You can feel the resentment."
                )
    else:
        narrator_text(
            "You pocket the medicine. \"Not yet.\" Nobody argues, but nobody agrees either."
        )

    press_enter()

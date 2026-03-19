"""
Crew management: recruitment, trust, skill checks, interactions.
"""

import json
import os
import random
from db import queries

CHARS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "characters.json")

_char_cache = None
_recruited_indices = set()


def load_npc_templates() -> list[dict]:
    global _char_cache
    if _char_cache is None:
        with open(CHARS_PATH) as f:
            data = json.load(f)
        _char_cache = data.get("npc_templates", [])
    return _char_cache


def recruit_next_npc() -> dict | None:
    """Recruit the next available NPC template. Returns the character dict or None."""
    templates = load_npc_templates()
    state = queries.get_game_state()
    bus = queries.get_bus()

    # Check capacity
    current = queries.crew_count()
    if current >= bus["crew_capacity"]:
        return None

    # Find next unrecruited template
    available = []
    recruited_names = {c["name"] for c in queries.get_alive_crew()}
    for t in templates:
        if t["name"] not in recruited_names:
            available.append(t)

    if not available:
        return None

    template = available[0]  # Take the first available (ordered by design)

    char_id = queries.create_character(
        name=template["name"],
        is_player=False,
        combat=template["combat"],
        medical=template["medical"],
        mechanical=template["mechanical"],
        scavenging=template["scavenging"],
        trust=45,
        personality=template["personality"],
        backstory=template["backstory"],
        is_romanceable=template["is_romanceable"],
        recruited_day=state["current_day"],
    )

    return {
        "id": char_id,
        **template,
        "trust": 45,
    }


def get_trust_status(trust: int) -> str:
    if trust <= 20:
        return "Hostile"
    elif trust <= 40:
        return "Wary"
    elif trust <= 60:
        return "Neutral"
    elif trust <= 80:
        return "Loyal"
    else:
        return "Devoted"


def get_trust_color_name(trust: int) -> str:
    if trust <= 20:
        return "red"
    elif trust <= 40:
        return "orange"
    elif trust <= 60:
        return "gray"
    elif trust <= 80:
        return "blue"
    else:
        return "green"


def skill_check(crew: list[dict], skill_name: str, difficulty: int) -> tuple[bool, int, dict]:
    """
    Perform a skill check using the best crew member.
    Returns (passed, roll, crew_member_used).
    """
    best = max(crew, key=lambda c: c.get(skill_name, 1))
    skill_val = best.get(skill_name, 1)

    # Trust modifier
    trust_mod = 0
    if not best.get("is_player"):
        trust = best.get("trust", 50)
        if trust >= 81:
            trust_mod = 2
        elif trust >= 61:
            trust_mod = 1
        elif trust <= 20:
            trust_mod = -2
        elif trust <= 40:
            trust_mod = -1

    roll = skill_val + trust_mod + random.randint(-2, 3)
    return roll >= difficulty, roll, best


def get_interaction_options(char: dict) -> list[dict]:
    """Get dialogue options for interacting with a character."""
    trust = char["trust"]
    personality = char["personality"]

    options = [
        {
            "label": f"Ask {char['name']} how they're holding up",
            "type": "small_talk",
            "trust_delta": random.randint(3, 8),
            "response_positive": _get_small_talk(char, positive=True),
            "response_negative": _get_small_talk(char, positive=False),
        },
        {
            "label": f"Share supplies with {char['name']}",
            "type": "gift",
            "trust_delta": random.randint(8, 15),
            "cost": {"food": 1},
            "response_positive": f"{char['name']} accepts the food with a grateful nod. \"Thanks. That means something out here.\"",
            "response_negative": None,
        },
        {
            "label": f"Ask {char['name']} about their past",
            "type": "backstory",
            "trust_delta": random.randint(2, 6) if trust >= 40 else random.randint(-5, 2),
            "response_positive": _get_backstory_dialogue(char, trust),
            "response_negative": f"{char['name']} looks away. \"Maybe another time.\" The silence that follows says enough.",
        },
    ]

    # Add combat training option
    options.append({
        "label": f"Train with {char['name']}",
        "type": "train",
        "trust_delta": random.randint(2, 5),
        "response_positive": f"You spend the phase sparring and drilling. {char['name']} shows you a few tricks.",
        "response_negative": None,
    })

    return options


def _get_small_talk(char: dict, positive: bool) -> str:
    personality = char["personality"]
    name = char["name"]

    responses = {
        "gruff": {
            True: f"{name} grunts. \"Still breathing. That's the bar these days, right?\" A pause. \"...Thanks for asking.\"",
            False: f"{name} barely looks up. \"I'm fine.\" Clearly not fine. But pushing won't help.",
        },
        "cautious": {
            True: f"{name} considers the question carefully. \"Better than yesterday. Worse than last week. Average for the apocalypse.\"",
            False: f"{name} tenses up. \"Why? Did something happen? What aren't you telling me?\"",
        },
        "reckless": {
            True: f"{name} grins. \"Living the dream, boss. Literally — I dreamed about this as a kid. Minus the smell.\"",
            False: f"{name} shrugs it off too quickly. \"Fine. Always fine. What's next?\"",
        },
        "intellectual": {
            True: f"{name} pauses their writing. \"Psychologically? Somewhere between hypervigilance and cautious optimism. So, normal.\"",
            False: f"{name} gives you a measured look. \"I appreciate the concern, but I'd rather discuss our route.\"",
        },
        "optimist": {
            True: f"{name} smiles — actually smiles. \"We're still here. We're still together. That's something, right?\"",
            False: f"{name}'s smile flickers. \"I'm good. Great. Totally...\" The voice trails off.",
        },
        "stoic": {
            True: f"{name} meets your eyes briefly. \"Holding.\" Just the one word. But from {name}, that's a lot.",
            False: f"{name} says nothing. Just a slow shake of the head. Not now.",
        },
    }

    default = {
        True: f"{name} nods. \"Hanging in there.\"",
        False: f"{name} doesn't seem interested in talking.",
    }

    return responses.get(personality, default)[positive]


def _get_backstory_dialogue(char: dict, trust: int) -> str:
    name = char["name"]
    if trust < 40:
        return f"{name} shuts that down immediately. \"We don't know each other like that.\" Fair enough."
    elif trust < 60:
        return f"{name} shares a fragment. A hometown. A job that doesn't exist anymore. Small pieces of a bigger picture."
    elif trust < 80:
        return f"{name} opens up more than usual. You learn about who they lost, and why they keep going. It's heavy, but it matters."
    else:
        return f"{name} tells you everything. The full story. It's raw and honest and you understand them in a way you didn't before."

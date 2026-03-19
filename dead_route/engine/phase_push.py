"""
Phase Push system: Time as a cost.

Some actions take longer than expected, consuming the current phase
AND pushing into the next one. This creates gut-punch moments where
a choice that seemed smart costs you hours and dumps you into
Evening or Midnight territory.

Phase order: morning -> afternoon -> evening -> midnight -> (new day morning)

A phase push:
  - Advances the phase clock WITHOUT giving the player another action
  - Shows narration about time passing
  - Can chain: a push from afternoon lands in evening, which is more dangerous
  - The player sees the risk BEFORE choosing (when we know the cost)
"""

import random
from db import queries
from ui.style import Color, Theme, styled, print_styled
from ui.narration import narrator_text, dramatic_pause, status_update
from engine.audio import audio, play_phase_music

PHASES = ["morning", "afternoon", "evening", "midnight"]

PHASE_TRANSITION_NARRATION = {
    ("morning", "afternoon"): [
        "Hours pass. The sun climbs overhead and the shadows shorten. It's afternoon now.",
        "By the time you're done, the morning is gone. The heat of the day presses down.",
    ],
    ("afternoon", "evening"): [
        "The sun drops below the treeline. Long shadows creep across the road. Evening.",
        "You look up and the sky is orange. Where did the afternoon go? It's getting dark.",
        "The light is failing. The temperature drops. The sounds from the darkness start earlier today.",
    ],
    ("evening", "midnight"): [
        "Night falls like a door slamming shut. The darkness is absolute. It's midnight.",
        "The last light dies. The moon isn't out tonight. You can hear them now — closer than before.",
        "You've lost the light. The bus sits in total darkness. Every sound is amplified. Every shadow moves.",
    ],
    ("midnight", "morning"): [
        "You push through the night. Somehow. Dawn breaks grey and cold. A new day. You survived.",
        "The longest night of your life ends with a pale sunrise. Everything hurts. But you're still here.",
    ],
}


def push_phase(reason: str = "") -> dict:
    """
    Advance the phase by one without giving the player an action.
    Returns {old_phase, new_phase, new_day, day_changed, narration, threat_increased}.
    """
    state = queries.get_game_state()
    old_phase = state["current_phase"]
    old_day = state["current_day"]

    old_idx = PHASES.index(old_phase)

    if old_idx < 3:
        new_phase = PHASES[old_idx + 1]
        new_day = old_day
    else:
        new_phase = "morning"
        new_day = old_day + 1

    # Check threat escalation
    new_threat = state["threat_level"]
    threat_increased = False
    if new_day > old_day and new_day % 5 == 0:
        new_threat += 1
        threat_increased = True

    queries.update_game_state(
        current_phase=new_phase,
        current_day=new_day,
        threat_level=new_threat
    )

    # Update music
    play_phase_music(new_phase)

    # Pick transition narration
    key = (old_phase, new_phase)
    narr_pool = PHASE_TRANSITION_NARRATION.get(key, [])
    narration = random.choice(narr_pool) if narr_pool else f"Time passes. It's {new_phase} now."

    return {
        "old_phase": old_phase,
        "new_phase": new_phase,
        "new_day": new_day,
        "day_changed": new_day > old_day,
        "narration": narration,
        "reason": reason,
        "threat_increased": threat_increased,
    }


def display_phase_push(result: dict):
    """Show the phase push to the player with appropriate drama."""
    old = result["old_phase"].upper()
    new = result["new_phase"].upper()

    # Escalating severity in display
    if result["new_phase"] in ("evening", "midnight"):
        color = Theme.DAMAGE
    elif result["new_phase"] == "afternoon":
        color = Theme.WARNING
    else:
        color = Theme.INFO

    print()
    print_styled(f"  >> TIME PASSES: {old} -> {new} <<", color + Color.BOLD)
    if result["reason"]:
        print_styled(f"     ({result['reason']})", Theme.MUTED)
    print()

    narrator_text(result["narration"])

    if result["threat_increased"]:
        state = queries.get_game_state()
        print()
        print_styled(
            f"  !! THREAT LEVEL {state['threat_level']} !!",
            Theme.DAMAGE + Color.BOLD
        )

    dramatic_pause(0.5)


def warn_phase_push(phases_cost: int = 1) -> str:
    """
    Generate a warning string about how a choice will push the clock.
    Used in choice descriptions so the player sees the time cost before choosing.
    """
    state = queries.get_game_state()
    current_idx = PHASES.index(state["current_phase"])
    landing_idx = min(3, current_idx + phases_cost)
    landing_phase = PHASES[landing_idx]

    if landing_phase == state["current_phase"]:
        return ""

    danger_labels = {
        "afternoon": "Afternoon (Medium risk)",
        "evening": "EVENING (High risk)",
        "midnight": "MIDNIGHT (EXTREME risk)",
    }

    label = danger_labels.get(landing_phase, landing_phase)

    if landing_phase == "midnight":
        return styled(f"[Takes time — pushes to {label}]", Theme.DAMAGE + Color.BOLD)
    elif landing_phase == "evening":
        return styled(f"[Takes time — pushes to {label}]", Theme.DAMAGE)
    else:
        return styled(f"[Takes time — pushes to {label}]", Theme.WARNING)


# ── Explore Push Events ────────────────────────────────────
# These are special exploration outcomes that cost time.

PUSH_EXPLORE_EVENTS = [
    {
        "id": "locked_pharmacy",
        "description": (
            "Behind the pharmacy counter, you spot a reinforced vault door. "
            "Through the glass you can see shelves of medicine — real medicine, "
            "not expired aspirin. The lock is heavy-duty."
        ),
        "choices": [
            {
                "label": "Blow the lock (loud, fast, risky)",
                "description": "Use 2 ammo as makeshift explosive. Instant, but may trigger combat and destroy some medicine.",
                "push": False,
                "cost": {"ammo": 2},
                "success_chance": 0.6,
                "success_reward": {"medicine": 2},
                "success_text": "The blast rips the door open. Most of the medicine survived. You grab what you can.",
                "failure_text": "The explosion is too strong. Half the shelves are shattered, and the noise brings company.",
                "failure_penalty": {"medicine": 1, "triggers_combat": True},
            },
            {
                "label": "Pry it open carefully",
                "description": "Guaranteed medicine, but it takes HOURS.",
                "push": True,
                "push_reason": "Prying open the pharmacy vault",
                "cost": {},
                "success_chance": 1.0,
                "success_reward": {"medicine": 3},
                "success_text": (
                    "It takes forever. Your arms ache, your fingers bleed, and the "
                    "sun moves across the sky while you work. But the door finally "
                    "gives. Three full doses of medicine. Worth it. Maybe."
                ),
            },
            {
                "label": "Leave it. Not worth the time or noise.",
                "description": "Walk away.",
                "push": False,
                "cost": {},
                "success_chance": 1.0,
                "success_reward": {},
                "success_text": "You leave the medicine behind. It hurts, but staying alive hurts more.",
            },
        ],
    },
    {
        "id": "trapped_survivor",
        "description": (
            "You hear banging from inside a collapsed building. Someone is alive "
            "in there, screaming for help. The rubble is thick — moving it will "
            "take serious time and effort."
        ),
        "choices": [
            {
                "label": "Dig them out",
                "description": "It will take hours. Guaranteed recruit if they survive.",
                "push": True,
                "push_reason": "Digging through rubble",
                "cost": {},
                "success_chance": 0.8,
                "success_reward": {"recruit": True},
                "success_text": (
                    "Hours of backbreaking work. Pulling concrete, bending rebar, "
                    "hands raw and bleeding. But you get them out — bloody, broken, "
                    "but breathing. They owe you their life."
                ),
                "failure_text": (
                    "You dig for hours. When you finally break through, the silence "
                    "tells you everything. They didn't make it. The rubble shifted "
                    "while you were working. All that time. Wasted."
                ),
                "failure_penalty": {},
            },
            {
                "label": "Shout encouragement and keep moving",
                "description": "Tell them to hold on. Maybe someone else will find them.",
                "push": False,
                "cost": {},
                "success_chance": 1.0,
                "success_reward": {},
                "success_text": (
                    "\"Hold on! Someone will come!\" you shout. You don't believe it. "
                    "They probably don't either. The banging gets quieter as you walk away."
                ),
            },
        ],
    },
    {
        "id": "fuel_tanker",
        "description": (
            "A jackknifed fuel tanker blocks the road. The tank is intact — "
            "there could be hundreds of gallons in there. But the valve is "
            "rusted shut and the tanker is crawling with infected hiding "
            "underneath."
        ),
        "choices": [
            {
                "label": "Clear the infected, then siphon fuel",
                "description": "Fight first, then spend time siphoning. Big fuel reward.",
                "push": True,
                "push_reason": "Clearing infected and siphoning fuel",
                "cost": {"ammo": 2},
                "success_chance": 0.75,
                "success_reward": {"fuel": 15},
                "success_text": (
                    "The fight is ugly but brief. Then the real work starts — "
                    "wrestling the rusted valve open, rigging a siphon from a "
                    "garden hose, filling every container on the bus. Hours of work "
                    "for a full tank. The bus drinks deep."
                ),
                "failure_text": (
                    "There are more of them under there than you thought. The fight "
                    "drags on and by the time it's done, you barely have the energy "
                    "to siphon. You get some fuel, but not what you hoped."
                ),
                "failure_penalty": {"fuel": 5, "triggers_combat": True},
            },
            {
                "label": "Quick grab — fill one container and run",
                "description": "Fast, small reward, dangerous.",
                "push": False,
                "cost": {},
                "success_chance": 0.5,
                "success_reward": {"fuel": 5},
                "success_text": "Quiet, fast, in and out. You fill a single jerry can before the infected notice.",
                "failure_text": "They notice. You drop the can and run. Nothing gained, almost something lost.",
                "failure_penalty": {"triggers_combat": True},
            },
            {
                "label": "Too dangerous. Drive around.",
                "description": "Costs 3 extra fuel to detour.",
                "push": False,
                "cost": {"fuel": 3},
                "success_chance": 1.0,
                "success_reward": {},
                "success_text": "You find a side road around the wreck. It costs fuel, but nobody dies.",
            },
        ],
    },
]


def get_push_explore_event() -> dict | None:
    """Randomly select a push-enabled explore event. ~20% chance per explore."""
    if random.random() > 0.20:
        return None
    state = queries.get_game_state()
    # Don't fire push events at midnight (nowhere to push to meaningfully)
    if state["current_phase"] == "midnight":
        return None
    return random.choice(PUSH_EXPLORE_EVENTS)


def resolve_push_event(event: dict, choice_idx: int) -> dict:
    """
    Resolve a push explore event choice.
    Returns {text, reward, pushed, push_result, combat_triggered}
    """
    choice = event["choices"][choice_idx]
    result = {
        "text": "",
        "reward": {},
        "pushed": False,
        "push_result": None,
        "combat_triggered": False,
    }

    # Pay costs
    cost = choice.get("cost", {})
    resource_cost = {k: -v for k, v in cost.items() if k != "triggers_combat"}
    if resource_cost:
        # Check affordability
        resources = queries.get_resources()
        for k, v in cost.items():
            if k != "triggers_combat" and resources.get(k, 0) < v:
                result["text"] = f"Not enough {k}."
                return result
        queries.update_resources(**resource_cost)

    # Roll for success
    if random.random() < choice.get("success_chance", 1.0):
        result["text"] = choice.get("success_text", "Success.")
        reward = dict(choice.get("success_reward", {}))

        # Handle recruit
        if reward.pop("recruit", False):
            from engine.crew import recruit_next_npc
            npc = recruit_next_npc()
            if npc:
                result["recruited"] = npc

        # Apply resource rewards
        resource_reward = {k: v for k, v in reward.items() if isinstance(v, int)}
        if resource_reward:
            queries.update_resources(**resource_reward)
            result["reward"] = resource_reward
    else:
        result["text"] = choice.get("failure_text", "It didn't work out.")
        penalty = choice.get("failure_penalty", {})

        if penalty.get("triggers_combat"):
            result["combat_triggered"] = True

        resource_penalty = {k: v for k, v in penalty.items()
                          if isinstance(v, int) and k != "triggers_combat"}
        if resource_penalty:
            queries.update_resources(**resource_penalty)
            result["reward"] = resource_penalty

    # Apply phase push
    if choice.get("push"):
        push_result = push_phase(reason=choice.get("push_reason", "Time-consuming action"))
        result["pushed"] = True
        result["push_result"] = push_result

    return result

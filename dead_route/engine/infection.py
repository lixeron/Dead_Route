"""
The Slow Rot: LAZARUS infection system.

Bitten crew don't die instantly. They deteriorate over 4 stages across
multiple days. Stats degrade, paranoia sets in, crew reacts with fear
and revulsion. If not treated or euthanized, they turn and attack.

Stages:
  0 - BITTEN:       Fresh wound. Person seems shaken but functional.
  1 - FEVER:        Sweating, pale, trembling. Stats begin to drop.
  2 - DETERIORATION: Skin blackens. The smell starts. Confusion, aggression.
  3 - TERMINAL:     Body visibly rotting while still alive. Barely conscious.
  4 - TURNED:       They're gone. What's left attacks the crew.
"""

import random
from db import queries
from ui.style import Color, Theme, styled, print_styled, print_blank
from ui.narration import (
    narrator_text, dramatic_pause, scene_break, status_update, dialogue
)
from ui.input import get_choice, get_choice_with_details, press_enter
from engine.audio import audio


# ── Stage Definitions ──────────────────────────────────────

STAGES = {
    0: {
        "name": "Bitten",
        "stat_penalty": 0,
        "hp_drain": 0,
        "combat_able": True,
        "description": "Fresh bite wound. Bandaged and holding.",
    },
    1: {
        "name": "Fever",
        "stat_penalty": 1,
        "hp_drain": 3,
        "combat_able": True,
        "description": "Running a fever. Skin is clammy and pale.",
    },
    2: {
        "name": "Deteriorating",
        "stat_penalty": 2,
        "hp_drain": 8,
        "combat_able": False,
        "description": "Skin is discoloring. The smell has started.",
    },
    3: {
        "name": "Terminal",
        "stat_penalty": 4,
        "hp_drain": 15,
        "combat_able": False,
        "description": "Body is shutting down. Barely conscious.",
    },
    4: {
        "name": "Turned",
        "stat_penalty": 99,
        "hp_drain": 0,
        "combat_able": False,
        "description": "Gone.",
    },
}


# ── Progression Narratives ─────────────────────────────────
# These should make the player feel sick. That's the point.

PROGRESSION_NARRATIVE = {
    0: [
        "{name} examines the bite on {their} forearm. The edges are ragged, "
        "already swelling purple. {They} wrap it tight with a bandage and "
        "force a grin. \"Just a scratch.\" Nobody believes {them}.",

        "The teeth marks on {name}'s shoulder are deep. Blood seeps through "
        "the gauze almost as fast as it can be applied. {name} sits very still, "
        "staring at nothing. Everyone on the bus knows what this means.",
    ],

    1: [
        "{name} can't stop shaking. Sweat runs down {their} face in rivulets "
        "even though the bus is freezing. When you touch {their} forehead, the "
        "heat radiates like a furnace. {Their} eyes are glassy, pupils dilated. "
        "\"I'm fine,\" {they} whisper through chattering teeth. \"I'm fine.\"",

        "The fever hits {name} like a wall. One moment {they}'re standing, the "
        "next {they}'re on the floor of the bus, curled into a ball, moaning. "
        "{Their} skin has gone the color of old candle wax. The bite wound "
        "has turned black at the edges, and something yellowish weeps from it.",
    ],

    2: [
        "The smell hits you before you see it. Something sweet and rotten, "
        "like fruit left to decay in the sun. {name}'s bite wound has split "
        "open, the flesh around it turning a mottled grey-green. Dark veins "
        "spider out from the wound like cracks in porcelain, visible through "
        "skin that has become almost translucent. {name} doesn't seem to notice. "
        "{They} keep scratching at {their} arms, muttering about things that "
        "aren't there.",

        "Nobody wants to sit near {name} anymore. The stench is unbearable — "
        "a thick, cloying rot that clings to the back of your throat and won't "
        "leave. {Their} fingernails have turned black. Patches of {their} skin "
        "have begun to slough off in wet strips, revealing something dark and "
        "glistening underneath. {name} alternates between fits of weeping and "
        "sudden, violent outbursts. During one, {they} don't recognize anyone "
        "on the bus for almost a minute.",
    ],

    3: [
        "What's happening to {name} isn't dying. It's worse than dying. "
        "{Their} body is rotting from the inside out while {they}'re still "
        "breathing. The skin on {their} arms has split in places, hanging in "
        "loose flaps that expose grey, stringy tissue underneath. One eye has "
        "clouded over completely — a milky, sightless marble. The other still "
        "tracks you, and in rare moments of clarity, you can see the terror in "
        "it. {They} know what's happening. {They} can feel it.\n\n"
        "The sounds {they} make aren't words anymore. Wet, gurgling moans "
        "interspersed with sharp, animal shrieks. {Their} jaw works constantly, "
        "teeth clacking together with a sound that makes everyone flinch. The "
        "smell has become something beyond description — sweet and foul and "
        "alive, as if the infection itself has its own stench, separate from "
        "the body it's consuming.\n\n"
        "There isn't much time left.",

        "{name} hasn't spoken in hours. {Their} breathing is a rattling, wet "
        "sound, like someone drowning in slow motion. The bite wound has become "
        "something else entirely — a pulsing, blackened crater in {their} flesh "
        "that seems to move on its own, the tissue underneath contracting and "
        "expanding in a rhythm that has nothing to do with {name}'s heartbeat. "
        "The veins visible through {their} paper-thin skin have turned black, "
        "forming a web that reaches from the wound across {their} entire body.\n\n"
        "Everyone keeps their distance. Even breathing the same air feels "
        "dangerous. The bus reeks of something ancient and wrong — not just "
        "death, but something that was never supposed to exist.\n\n"
        "Whatever {name} was is almost gone. What's replacing it doesn't sleep.",
    ],
}

TURNING_NARRATIVE = [
    "It happens at {phase}.\n\n"
    "One moment, {name} is still. The rattling breath has stopped. For a "
    "heartbeat, everyone thinks it's over — that {they}'ve finally gone. "
    "Someone reaches for a blanket.\n\n"
    "Then {name}'s eyes open. Both of them. But they're not {name}'s eyes "
    "anymore. They're flat, empty, hunger-driven things — clouded and yellow "
    "and locked onto the nearest warm body.\n\n"
    "The sound that comes out of {their} throat isn't human. It's a wet, "
    "shredding shriek, like vocal cords being torn apart from the inside. "
    "{name}'s body lurches upright with a speed and violence that doesn't "
    "match the ruin it's become — bones cracking, skin splitting, black fluid "
    "spraying from the wounds.\n\n"
    "It lunges.",

    "{name} turns in {their} sleep. Or what passes for sleep.\n\n"
    "The first sign is the sound — a low, guttural clicking that builds "
    "into a growl. Then the body begins to convulse, back arching at an "
    "impossible angle, fingers clawing at the seat hard enough to tear "
    "the upholstery. The bandages around the bite wound burst apart as "
    "the flesh underneath swells and reshapes itself.\n\n"
    "When the eyes open, there's nothing behind them. Nothing human. "
    "Just hunger.\n\n"
    "Someone screams. It lunges.",
]


# ── Crew Reaction Dialogue ────────────────────────────────

CREW_REACTIONS = {
    "gruff": {
        0: "Marcus looks at the bite, then at {name}. His jaw tightens. He doesn't say anything. He doesn't need to.",
        1: "\"We all know how this ends,\" Marcus says quietly, not looking at anyone. His hand rests on his wrench.",
        2: "Marcus ties a rag over his nose and mouth. \"We need to make a decision. Soon.\"",
        3: "Marcus pulls you aside. His voice is barely a whisper. \"If you can't do it, I will. But it needs to happen. Now.\"",
    },
    "cautious": {
        0: "Elena cleans the wound with practiced hands, but her eyes give her away. She knows what this is.",
        1: "\"The pathogen is in the bloodstream,\" Elena says, clinical and flat. Her hands are shaking. \"Median time to full onset is 72 hours.\"",
        2: "Elena has stopped going near {name}. She stands at the far end of the bus, arms wrapped around herself. \"I can't watch this again.\"",
        3: "Elena is crying. Silently, with her back to the group. When she turns around, her face is hard. \"It's time. Please.\"",
    },
    "reckless": {
        0: "Dex tries to play it cool. \"Hey, you're tough, you'll fight it off.\" His smile doesn't reach his eyes.",
        1: "For once, Dex has nothing funny to say. He sits at the front of the bus cleaning his rifle, not meeting anyone's gaze.",
        2: "\"How long?\" Dex asks you privately. \"How long do we let this go on?\" His usual bravado is gone. He looks young.",
        3: "Dex chambers a round. His hands are steady. His voice isn't. \"Just tell me when.\"",
    },
    "intellectual": {
        0: "Nadia examines the wound clinically. She writes down the time, the location, the depth. Data. She retreats into data because the alternative is feeling it.",
        1: "\"Based on the progression rate, we have approximately 48 hours,\" Nadia says. She pauses. \"I'm sorry. I don't know what else to say.\"",
        2: "Nadia has filled an entire notebook with observations about {name}'s deterioration. It's her way of coping. The last entry just says: \"I can't do this.\"",
        3: "\"From a scientific perspective, {they}'re already gone,\" Nadia says. Her voice cracks on 'gone.' \"The body is just... running on something else now.\"",
    },
    "optimist": {
        0: "Tommy squeezes {name}'s shoulder. \"We've got medicine. We'll figure this out.\" He believes it. He has to.",
        1: "Tommy is quiet. Tommy is never quiet. He sits next to {name}, holding {their} hand, not saying a word.",
        2: "Tommy finally breaks. \"There has to be something we can do. There HAS to be.\" Nobody answers him.",
        3: "Tommy can't look at {name} anymore. He sits at the front of the bus, face in his hands. His optimism has hit a wall it can't climb.",
    },
    "stoic": {
        0: "Rhea sees the bite. Her expression doesn't change. She checks her weapon, checks the exits, checks the locks. Preparing.",
        1: "Rhea has positioned herself between {name} and the rest of the crew. Not aggressively. Just... ready.",
        2: "\"I've seen this before,\" Rhea says. Six words. Each one carrying the weight of a memory she'll never share.",
        3: "Rhea stands over {name} with her sidearm drawn. She looks at you. Waiting. She's done this before.",
    },
}


# ── Core Functions ─────────────────────────────────────────

def try_infect_from_combat(char_id: int, combat_result: str) -> bool:
    """
    Roll for infection after combat. Higher chance on worse outcomes.
    Returns True if character was infected.
    """
    char = queries.get_character(char_id)
    if not char or char["infected"]:
        return False

    # Infection chance by combat outcome
    chances = {
        "decisive_victory": 0.0,
        "victory": 0.02,
        "pyrrhic": 0.12,
        "defeat": 0.25,
    }
    chance = chances.get(combat_result, 0.0)

    # Armor plating reduces bite chance
    absorption = queries.get_damage_absorption()
    chance *= (1.0 - absorption * 0.5)

    if random.random() < chance:
        queries.infect_character(char_id)
        return True
    return False


def tick_infections() -> list[dict]:
    """
    Progress all infections by one stage. Called once per day (morning phase).
    Returns list of events: {char_id, name, old_stage, new_stage, narrative}
    """
    state = queries.get_game_state()
    if state["current_phase"] != "morning":
        return []

    infected = queries.get_infected_crew()
    events = []

    for char in infected:
        old_stage = char["infection_stage"]
        if old_stage >= 4:
            continue  # Already turned — shouldn't be alive

        new_stage = queries.advance_infection(char["id"])

        # Apply stat degradation
        stage_data = STAGES.get(new_stage, {})
        hp_drain = stage_data.get("hp_drain", 0)
        if hp_drain > 0:
            queries.damage_character(char["id"], hp_drain)

        # Generate narrative
        narrative = _get_progression_narrative(char, new_stage, state)

        events.append({
            "char_id": char["id"],
            "name": char["name"],
            "old_stage": old_stage,
            "new_stage": new_stage,
            "narrative": narrative,
            "stage_name": stage_data.get("name", "Unknown"),
        })

    return events


def handle_turning(char: dict) -> dict:
    """
    Handle a character turning into a zombie on the bus.
    Returns damage dealt to crew.
    """
    state = queries.get_game_state()
    phase_names = {
        "morning": "dawn", "afternoon": "midday",
        "evening": "dusk", "midnight": "midnight"
    }
    phase = phase_names.get(state["current_phase"], "an ungodly hour")

    # Generate turning narrative
    narrative = random.choice(TURNING_NARRATIVE)
    narrative = _interpolate(narrative, char, state, phase)

    # The turned character dies
    queries.update_character(char["id"], is_alive=0)

    # Damage to nearby crew
    crew = queries.get_alive_crew()
    casualties = []
    for c in crew:
        damage = random.randint(15, 35)
        queries.damage_character(c["id"], damage)
        casualties.append({"name": c["name"], "damage": damage})
        if not c["is_player"]:
            queries.change_trust(c["id"], random.randint(-12, -5))

    return {
        "narrative": narrative,
        "casualties": casualties,
        "turned_name": char["name"],
    }


def present_infection_choice(char: dict):
    """
    Present the euthanasia decision for an infected crew member.
    Triggered at stage 2+ or when the player checks infected crew.
    """
    from ui.style import clear_screen
    clear_screen()
    print_blank(1)
    scene_break("THE QUESTION")

    stage = char["infection_stage"]
    stage_data = STAGES.get(stage, {})
    name = char["name"]
    state = queries.get_game_state()
    poss = state.get("poss_pronoun", "their")

    narrator_text(
        f"{name} is at Stage {stage}: {stage_data['name']}. "
        f"{stage_data['description']}"
    )
    dramatic_pause(0.5)

    # Crew reactions
    npcs = queries.get_alive_npcs()
    for npc in npcs:
        if npc["id"] == char["id"]:
            continue
        reaction_pool = CREW_REACTIONS.get(npc["personality"], {})
        reaction = reaction_pool.get(stage)
        if reaction:
            narrator_text(_interpolate(reaction, char, state))
            dramatic_pause(0.3)

    # Build options based on stage and resources
    resources = queries.get_resources()
    options = []

    if resources["medicine"] > 0 and stage < 3:
        options.append({
            "label": f"Use Medicine to buy time (1 Medicine)",
            "description": f"Pushes the infection back one stage. "
                          f"Delays the inevitable. Maybe long enough to find a cure.",
        })
    elif resources["medicine"] > 0 and stage >= 3:
        options.append({
            "label": f"Use Medicine to ease {poss} pain (1 Medicine)",
            "description": f"Too far gone to reverse. But you can make what's left hurt less.",
        })

    options.append({
        "label": f"End it now. Quickly.",
        "description": f"A bullet. Clean. Before {name} becomes something else. "
                      f"The crew will remember this.",
    })

    if stage < 3:
        options.append({
            "label": "Do nothing. Wait and see.",
            "description": "Maybe they'll fight it off. Nobody ever has, but maybe.",
        })

    if stage >= 2:
        options.append({
            "label": f"Let {name} go out fighting",
            "description": f"Send them against the next horde alone. "
                          f"A warrior's death. Guaranteed kill, but...",
        })

    idx = get_choice_with_details(
        options, prompt=f"What do you do about {name}?"
    )

    chosen = options[idx]
    _resolve_infection_choice(char, chosen, stage, state)


def _resolve_infection_choice(char: dict, choice: dict, stage: int, state: dict):
    """Resolve the player's choice about an infected crew member."""
    name = char["name"]
    label = choice["label"]

    if "Medicine to buy time" in label:
        queries.update_resources(medicine=-1)
        queries.delay_infection(char["id"])
        narrator_text(
            f"You kneel beside {name} and administer the last of the dose. "
            f"The effect is almost immediate — the shaking subsides, the color "
            f"returns to {state.get('poss_pronoun', 'their')} face. For a moment, "
            f"{name} looks almost normal. Almost."
        )
        narrator_text(
            f"\"Thank you,\" {name} whispers. {state.get('subj_pronoun', 'They').capitalize()} "
            f"know it's temporary. You both do."
        )
        status_update(f"-1 Medicine. Infection pushed back one stage.")

    elif "ease" in label.lower() and "pain" in label.lower():
        queries.update_resources(medicine=-1)
        narrator_text(
            f"The medicine can't save {name}. Not anymore. But it softens the edges. "
            f"The moaning quiets to a murmur. The convulsions gentle into tremors. "
            f"{name}'s one good eye finds yours, and for a fraction of a second, "
            f"there's gratitude in it. Then it clouds over again."
        )
        status_update("-1 Medicine. Pain eased, but the end is coming.")

    elif "End it now" in label:
        _euthanize(char, state)

    elif "Do nothing" in label:
        narrator_text(
            f"You decide to wait. {name} is still in there — you can see it "
            f"in the moments of clarity. Maybe the infection will slow. "
            f"Maybe medicine will turn up.\n\n"
            f"Nobody on the bus agrees with you. But nobody stops you either."
        )
        for npc in queries.get_alive_npcs():
            if npc["id"] != char["id"]:
                queries.change_trust(npc["id"], -3)

    elif "go out fighting" in label:
        _blaze_of_glory(char, state)

    press_enter()


def _euthanize(char: dict, state: dict):
    """Handle mercy killing an infected crew member."""
    name = char["name"]
    they = state.get("subj_pronoun", "they")
    them = state.get("obj_pronoun", "them")
    their = state.get("poss_pronoun", "their")

    queries.update_character(char["id"], is_alive=0)
    queries.update_resources(ammo=-1)
    queries.set_flag("mercy_kill", True)

    narrator_text(
        f"You ask everyone to step outside the bus."
    )
    dramatic_pause(1.0)

    narrator_text(
        f"It's just you and {name}. The bus is quiet except for "
        f"{their} breathing — that wet, labored sound that "
        f"hasn't stopped for hours."
    )
    dramatic_pause(1.0)

    narrator_text(
        f"You take the pistol from the dashboard. {name}'s "
        f"eyes — the one that still works — finds you. And for "
        f"a moment, the fog clears. {name} is there. Really there."
    )
    dramatic_pause(1.5)

    narrator_text(
        f"\"{name}.\"\n\n"
        f"A nod. Small, deliberate. Permission."
    )
    dramatic_pause(2.0)

    audio.play_sfx("gunshot")
    narrator_text(
        f"The sound is loud in the empty bus. Then silence. "
        f"Real silence, for the first time in days."
    )
    dramatic_pause(1.5)

    narrator_text(
        f"You wrap {name} in a blanket — the cleanest one left. "
        f"You carry {them} out yourself. Nobody helps. Nobody needs to."
    )
    dramatic_pause(0.5)

    status_update(f"{name} is gone. -1 Ammo.")

    # Crew reactions — massive trust impact
    for npc in queries.get_alive_npcs():
        personality = npc["personality"]
        if personality in ("stoic", "gruff"):
            # They understand. Respect.
            queries.change_trust(npc["id"], 3)
        elif personality == "cautious":
            # Elena knows it was necessary
            queries.change_trust(npc["id"], 1)
        elif personality in ("optimist", "reckless"):
            # Harder to accept
            queries.change_trust(npc["id"], -5)
        else:
            queries.change_trust(npc["id"], -3)


def _blaze_of_glory(char: dict, state: dict):
    """Send the infected out to fight one last time."""
    name = char["name"]
    their = state.get("poss_pronoun", "their")

    queries.update_character(char["id"], is_alive=0)
    queries.set_flag("blaze_of_glory", True)

    narrator_text(
        f"{name} stands up. It takes everything {they_from(state)} "
        f"have. The bones creak. The ruined skin stretches and splits. "
        f"But {they_from(state)} stand."
    )
    dramatic_pause(0.5)

    narrator_text(
        f"\"Give me the machete.\"\n\n"
        f"The voice is wrecked — gravel and fluid and something that "
        f"isn't entirely human anymore. But the words are clear. "
        f"The intent is unmistakable."
    )
    dramatic_pause(1.0)

    narrator_text(
        f"{name} walks off the bus and into the dark. You hear the "
        f"first impact — metal on meat. Then another. Then screaming — "
        f"not {name}'s screaming, the other kind. The inhuman kind. "
        f"{name} is tearing through them."
    )
    dramatic_pause(1.0)

    narrator_text(
        f"The sounds go on for a long time. Longer than should be "
        f"possible. Then they stop.\n\n"
        f"When the sun comes up, you find what's left. {name} "
        f"went down surrounded by a ring of corpses — real corpses, "
        f"the kind that don't get back up. {their.capitalize()} face is "
        f"frozen in something between a snarl and a smile.\n\n"
        f"You count the bodies. Fourteen."
    )
    dramatic_pause(1.5)

    # Mechanical reward: clears nearby threat for the day
    status_update(f"{name}'s last stand killed 14 infected. Area is clear for now.")

    # Everyone's trust is affected — but complex
    for npc in queries.get_alive_npcs():
        personality = npc["personality"]
        if personality == "reckless":
            queries.change_trust(npc["id"], 8)  # Dex respects this
        elif personality == "stoic":
            queries.change_trust(npc["id"], 5)  # Rhea understands
        elif personality == "optimist":
            queries.change_trust(npc["id"], -3)  # Tommy is horrified
        elif personality == "cautious":
            queries.change_trust(npc["id"], -2)  # Elena sees it as waste
        else:
            queries.change_trust(npc["id"], 1)


# ── Display Functions ──────────────────────────────────────

def get_infection_status_text(char: dict) -> str:
    """Get a display string for a character's infection state."""
    if not char.get("infected"):
        return ""
    stage = char["infection_stage"]
    stage_data = STAGES.get(stage, {})
    return f"[INFECTED - Stage {stage}: {stage_data.get('name', '?')}]"


def get_infection_hud_warning(char: dict) -> str | None:
    """Get a HUD warning for infected characters."""
    if not char.get("infected"):
        return None
    stage = char["infection_stage"]
    if stage == 0:
        return f"{char['name']} was bitten. Watch for symptoms."
    elif stage == 1:
        return f"{char['name']} is running a fever. The infection is spreading."
    elif stage == 2:
        return f"{char['name']} is deteriorating. A decision must be made."
    elif stage == 3:
        return f"!! {char['name']} is terminal. {char['name'].upper()} WILL TURN SOON !!"
    return None


# ── Helpers ────────────────────────────────────────────────

def they_from(state: dict) -> str:
    return state.get("subj_pronoun", "they")


def _interpolate(text: str, char: dict, state: dict, phase: str = "") -> str:
    """Replace {name}, {they}, {them}, {their}, {They}, {phase} in text."""
    replacements = {
        "{name}": char["name"],
        "{they}": state.get("subj_pronoun", "they"),
        "{them}": state.get("obj_pronoun", "them"),
        "{their}": state.get("poss_pronoun", "their"),
        "{They}": state.get("subj_pronoun", "they").capitalize(),
        "{Their}": state.get("poss_pronoun", "their").capitalize(),
        "{phase}": phase,
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def _get_progression_narrative(char: dict, new_stage: int, state: dict) -> str:
    """Get narrative text for an infection stage progression."""
    pool = PROGRESSION_NARRATIVE.get(new_stage, [])
    if not pool:
        return f"{char['name']}'s condition has worsened."
    text = random.choice(pool)
    return _interpolate(text, char, state)

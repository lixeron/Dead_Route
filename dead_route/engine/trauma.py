"""
Trauma & Scars system.

After pyrrhic victories or defeats, crew members can suffer permanent
debuffs. These stack and are never removed. By late game, veteran
survivors are limping wrecks who are still more useful than fresh recruits.

Scars:
  Physical — stat penalties that never heal.
  Psychological — behavioral restrictions and morale effects.
"""

import random
from db import queries
from ui.style import Color, Theme, styled, print_styled
from ui.narration import narrator_text, dramatic_pause


# ── Scar Definitions ──────────────────────────────────────

PHYSICAL_SCARS = [
    {
        "id": "lost_eye",
        "name": "Lost Eye",
        "description": "A claw took it. Depth perception gone.",
        "effect": {"scavenging": -2},
        "narrative": [
            "{name} screams, hand clamped over {their} face. Blood streams "
            "between {their} fingers. When {they} finally pull {their} hand away, "
            "there's a ruin where {their} left eye used to be. The socket is a "
            "raw, weeping mess. {name} stares at you with the one that's left — "
            "shock, pain, and something worse. The knowledge that this is permanent.",

            "The infected's fingers found {name}'s eye socket before anyone could "
            "react. The sound {name} makes isn't a scream — it's something more "
            "primal, a howl that echoes off the bus walls. When the bleeding "
            "finally stops, {name} ties a strip of cloth over the empty socket "
            "and says nothing for the rest of the day.",
        ],
    },
    {
        "id": "crushed_hand",
        "name": "Crushed Hand",
        "description": "Fingers mangled beyond repair. Can barely grip.",
        "effect": {"mechanical": -2, "combat": -1},
        "narrative": [
            "{name}'s hand got caught — between teeth, between metal, between "
            "something that wasn't letting go. The fingers bent in directions "
            "fingers aren't supposed to bend. By the time {they} wrench free, "
            "three fingers on {their} right hand are shattered. They'll heal, "
            "but they'll never straighten again.",

            "The crunch is audible from across the bus. {name} looks down at "
            "{their} hand and sees something that doesn't look like a hand "
            "anymore. Swollen, purple, the bones visibly misaligned under skin "
            "stretched tight. {name} cradles it against {their} chest and bites "
            "back a sound that nobody wants to hear.",
        ],
    },
    {
        "id": "torn_shoulder",
        "name": "Torn Shoulder",
        "description": "Rotator cuff destroyed. Limited arm mobility.",
        "effect": {"combat": -2},
        "narrative": [
            "Something in {name}'s shoulder tears with a wet pop. {Their} arm "
            "drops to {their} side, limp and useless. The joint is dislocated "
            "at best, destroyed at worst. Even after Elena does what she can, "
            "{name} can barely raise {their} arm above the waist.",
        ],
    },
    {
        "id": "shattered_knee",
        "name": "Shattered Knee",
        "description": "Kneecap broken. Permanent limp.",
        "effect": {"scavenging": -1, "combat": -1},
        "narrative": [
            "{name}'s knee buckles sideways with a crack that makes everyone "
            "wince. The kneecap is shattered — you can see the fragments "
            "shifting under the skin when {they} try to move. {name} will walk "
            "again, eventually. But {they} will never run.",

            "One of them hit {name} in the knee with something — a pipe, a bone, "
            "hard to tell. The joint explodes inward. {name} drops, grabbing the "
            "leg, teeth bared. The knee swells immediately, grotesquely, turning "
            "the color of an overripe plum.",
        ],
    },
    {
        "id": "facial_scarring",
        "name": "Facial Scarring",
        "description": "Deep lacerations across the face. Unsettling to look at.",
        "effect": {"scavenging": -1},  # Harder to approach strangers
        "narrative": [
            "The claws rake across {name}'s face in three parallel lines from "
            "forehead to jaw. The cuts are deep — through skin, through muscle, "
            "down to bone in places. They'll heal into thick, ropy scars that "
            "pull the skin tight. {name} will spend the rest of {their} life "
            "making people flinch.",
        ],
    },
    {
        "id": "nerve_damage",
        "name": "Nerve Damage",
        "description": "Chronic numbness and tremors. Hands shake constantly.",
        "effect": {"medical": -2, "mechanical": -1},
        "narrative": [
            "The infection from the wound does something to {name}'s nerves. "
            "The tremors start small — a twitch in the fingers, a flutter in the "
            "eyelid. Within hours, {name}'s hands shake constantly, a fine "
            "vibration that makes precision work impossible. Threading a needle, "
            "turning a screw, steady aim — all gone.",
        ],
    },
]

PSYCHOLOGICAL_SCARS = [
    {
        "id": "ptsd_night",
        "name": "Night Terror PTSD",
        "description": "Refuses midnight actions. Paralyzing flashbacks in the dark.",
        "effect": {"refuses_midnight": True},
        "narrative": [
            "Something broke in {name} during that fight. Not a bone — something "
            "deeper. Now, when darkness falls, {they} freeze. Eyes wide, breathing "
            "shallow, pupils blown. {name} can't go out there at night anymore. "
            "Not won't. Can't. The body simply refuses.",

            "{name} wakes up screaming every night now. The same dream — the "
            "horde closing in, the sound of teeth on bone, the feeling of being "
            "dragged into the dark. During the day, {they}'re functional. But "
            "when the sun goes down, {name} sits in the corner of the bus with "
            "{their} knees drawn up and doesn't speak until morning.",
        ],
    },
    {
        "id": "ptsd_combat",
        "name": "Combat Paralysis",
        "description": "Freezes during ambushes. -3 Combat when caught off guard.",
        "effect": {"combat": -3, "combat_condition": "ambush"},
        "narrative": [
            "The ambush rewired something in {name}'s brain. Now, when combat "
            "starts without warning — a sudden attack, a zombie bursting from "
            "a doorway — {name} locks up. Muscles rigid, eyes glazed, "
            "completely unresponsive for seconds that feel like hours. By the "
            "time {they} snap out of it, the fight is already half over.",
        ],
    },
    {
        "id": "paranoia",
        "name": "Severe Paranoia",
        "description": "Trusts no one. Constant vigilance drains stamina.",
        "effect": {"stamina_drain": 3, "trust_ceiling": 60},
        "narrative": [
            "{name} doesn't sleep anymore. Not really. {They} doze — fifteen "
            "minutes here, twenty there — with one hand on a weapon and both "
            "eyes barely closed. {name} watches the others constantly. Checking "
            "for bites. Checking for lies. Checking, always checking. The "
            "paranoia is eating {them} alive, but {they} can't stop. Stopping "
            "means trusting, and trusting means dying.",
        ],
    },
    {
        "id": "survivors_guilt",
        "name": "Survivor's Guilt",
        "description": "Morale permanently suppressed. Takes unnecessary risks.",
        "effect": {"morale_cap": 40},
        "narrative": [
            "Something in {name} went quiet after the fight. Not peaceful quiet. "
            "Empty quiet. {They} eat when told, move when told, fight when told. "
            "But the light behind {their} eyes has dimmed. {name} volunteers for "
            "every dangerous task now. Not out of bravery — out of a belief that "
            "{they} should have been the one who didn't make it.",
        ],
    },
]

ALL_SCARS = PHYSICAL_SCARS + PSYCHOLOGICAL_SCARS


# ── Core Functions ─────────────────────────────────────────

def roll_for_scar(char_id: int, combat_result: str) -> dict | None:
    """
    Roll for a permanent scar after combat.
    Higher chance on worse outcomes. Returns scar dict or None.
    """
    char = queries.get_character(char_id)
    if not char or not char["is_alive"]:
        return None

    # Base chance by outcome — scales with era
    from engine.balance import get_balance
    era_chances = get_balance("SCAR_CHANCE")
    chance = era_chances.get(combat_result, 0.0) if era_chances else 0.0

    if chance <= 0 or random.random() > chance:
        return None

    # Get character's existing scars
    existing = _get_char_scars(char)
    existing_ids = {s["id"] for s in existing}

    # Filter to scars they don't already have
    available = [s for s in ALL_SCARS if s["id"] not in existing_ids]
    if not available:
        return None  # Already has every scar (poor soul)

    # Weighted: physical scars more common than psychological
    physical = [s for s in available if s in PHYSICAL_SCARS]
    psychological = [s for s in available if s in PSYCHOLOGICAL_SCARS]

    if physical and (not psychological or random.random() < 0.65):
        scar = random.choice(physical)
    elif psychological:
        scar = random.choice(psychological)
    else:
        return None

    # Apply the scar
    _apply_scar(char_id, scar, char)

    return scar


def _apply_scar(char_id: int, scar: dict, char: dict):
    """Apply a scar's permanent stat penalties."""
    effects = scar.get("effect", {})
    updates = {}

    for key, val in effects.items():
        if key in ("combat", "medical", "mechanical", "scavenging"):
            current = char.get(key, 3)
            updates[key] = max(1, current + val)  # val is negative
        # Boolean/special effects stored as flags
        elif key == "refuses_midnight":
            queries.set_flag(f"scar_{char_id}_refuses_midnight", True)
        elif key == "trust_ceiling":
            queries.set_flag(f"scar_{char_id}_trust_ceiling_{val}", True)
        elif key == "morale_cap":
            queries.set_flag(f"scar_{char_id}_morale_cap_{val}", True)
        elif key == "stamina_drain":
            queries.set_flag(f"scar_{char_id}_stamina_drain_{val}", True)

    if updates:
        queries.update_character(char_id, **updates)

    # Store the scar itself as a flag for tracking
    queries.set_flag(f"scar_{char_id}_{scar['id']}", True)


def _get_char_scars(char: dict) -> list[dict]:
    """Get all scars for a character by checking flags."""
    char_id = char["id"]
    scars = []
    for scar in ALL_SCARS:
        if queries.get_flag(f"scar_{char_id}_{scar['id']}"):
            scars.append(scar)
    return scars


def get_character_scars(char_id: int) -> list[dict]:
    """Public API: get all scars for a character."""
    char = queries.get_character(char_id)
    if not char:
        return []
    return _get_char_scars(char)


def present_scar(char: dict, scar: dict):
    """Display the scar narrative dramatically."""
    state = queries.get_game_state()
    name = char["name"]

    print()
    print_styled(
        f"  ╔══════════════════════════════════════╗",
        Theme.DAMAGE
    )
    print_styled(
        f"  ║  PERMANENT INJURY: {scar['name']:<18}║",
        Theme.DAMAGE + Color.BOLD
    )
    print_styled(
        f"  ╚══════════════════════════════════════╝",
        Theme.DAMAGE
    )
    print()

    # Pick and interpolate narrative
    narrative = random.choice(scar["narrative"])
    narrative = _interpolate(narrative, char, state)
    narrator_text(narrative)
    dramatic_pause(1.0)

    # Show mechanical effect
    effects = scar.get("effect", {})
    stat_names = {
        "combat": "Combat", "medical": "Medical",
        "mechanical": "Mechanical", "scavenging": "Scavenging"
    }
    for key, val in effects.items():
        if key in stat_names and val < 0:
            print_styled(
                f"  {name}: {stat_names[key]} permanently reduced by {abs(val)}",
                Theme.WARNING
            )
        elif key == "refuses_midnight":
            print_styled(
                f"  {name} can no longer participate in midnight actions",
                Theme.WARNING
            )
        elif key == "stamina_drain":
            print_styled(
                f"  {name} suffers +{val} stamina drain per phase from hypervigilance",
                Theme.WARNING
            )
        elif key == "morale_cap":
            print_styled(
                f"  {name}'s morale can never rise above {val}",
                Theme.WARNING
            )
        elif key == "trust_ceiling":
            print_styled(
                f"  {name}'s trust can never rise above {val}",
                Theme.WARNING
            )

    print()
    dramatic_pause(0.5)


def get_scar_display_lines(char_id: int) -> list[str]:
    """Get formatted scar lines for crew status display."""
    scars = get_character_scars(char_id)
    if not scars:
        return []
    lines = []
    for s in scars:
        lines.append(f"{styled(s['name'], Theme.DAMAGE)}: {s['description']}")
    return lines


def character_refuses_midnight(char_id: int) -> bool:
    """Check if a character has night terror PTSD."""
    return queries.get_flag(f"scar_{char_id}_refuses_midnight")


def get_scar_stamina_drain(char_id: int) -> int:
    """Get extra stamina drain from paranoia scar."""
    for val in [1, 2, 3, 4, 5]:
        if queries.get_flag(f"scar_{char_id}_stamina_drain_{val}"):
            return val
    return 0


# ── Helpers ────────────────────────────────────────────────

def _interpolate(text: str, char: dict, state: dict) -> str:
    replacements = {
        "{name}": char["name"],
        "{they}": state.get("subj_pronoun", "they"),
        "{them}": state.get("obj_pronoun", "them"),
        "{their}": state.get("poss_pronoun", "their"),
        "{They}": state.get("subj_pronoun", "they").capitalize(),
        "{Their}": state.get("poss_pronoun", "their").capitalize(),
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

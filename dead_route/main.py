#!/usr/bin/env python3
"""
DEAD ROUTE — Zombie Oregon Trail on a School Bus
Entry point. Full game loop with difficulty overhaul.
"""

import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database import init_db, reset_db, db_exists
from db import queries
from engine.intro import run_intro
from engine.travel import generate_map
from engine.banter import get_ambient_banter, get_context
from ui.style import Color, Theme, clear_screen, print_styled, print_blank, styled
from ui.narration import (
    scene_break, narrator_text, dramatic_pause, status_update,
    loot_display, damage_display, dialogue
)
from ui.input import get_choice, get_choice_with_details, press_enter, confirm
from ui.display import show_hud, show_crew_status, show_location_description


# ── CONSTANTS ──────────────────────────────────────────────

# Passive food drain per phase (crew eats constantly)
FOOD_PER_PHASE_PER_PERSON = 0.25  # 1 food per person per full day (4 phases)
# Fuel leak per day until repaired
FUEL_LEAK_PER_DAY = 2
# Starvation damage per phase when food = 0
STARVATION_DAMAGE = 8
# Stamina drain per phase (fatigue)
STAMINA_DRAIN_PER_PHASE = 5


def create_player(intro_result: dict):
    """Create the player character and initialize game state."""
    queries.create_game(
        player_name=intro_result["player_name"],
        pronouns=intro_result["pronouns"],
        subj=intro_result["subj"],
        obj=intro_result["obj"],
        poss=intro_result["poss"],
    )

    # NERFED starting resources — you start desperate
    queries.set_resources(fuel=15, food=5, scrap=2, ammo=4, medicine=1)

    skill = intro_result["starting_skill"]
    stats = {"combat": 3, "medical": 3, "mechanical": 3, "scavenging": 3}
    stats[skill] = 6

    queries.create_character(
        name=intro_result["player_name"],
        is_player=True,
        **stats
    )

    start_node_id = generate_map()
    queries.update_game_state(current_node_id=start_node_id, intro_complete=1)
    queries.mark_node_visited(start_node_id)


def post_intro_transition():
    state = queries.get_game_state()
    name = state["player_name"]

    clear_screen()
    print_blank(1)
    scene_break("DAY 1 — MORNING")

    narrator_text(
        f"The sun is low on the horizon. {name} grips the steering wheel "
        f"and squints at the road ahead. The bus rattles along, every pothole "
        f"a jolt through the spine."
    )
    dramatic_pause(0.5)

    narrator_text(
        "The fuel gauge needle is uncomfortably close to the red. The glove "
        "compartment has a single granola bar, already split three ways by "
        "the time you found it. This is the state of things."
    )
    dramatic_pause(0.5)

    status_update("Systems check... supplies are critically low.")
    dramatic_pause(0.5)

    show_hud()

    narrator_text(
        "You need fuel. You need food. You need to find other people — or "
        "pray you don't. The road to Haven is long, and this bus won't get "
        "there on hope alone."
    )

    press_enter()


# ── PASSIVE SYSTEMS (run every phase) ──────────────────────

def run_passive_systems() -> list[str]:
    """Run all passive drain/damage systems. Returns list of warnings."""
    warnings = []
    state = queries.get_game_state()
    resources = queries.get_resources()
    crew = queries.get_alive_crew()
    crew_count = len(crew)

    # ── FOOD DRAIN ──
    # Fractional: we track it by consuming 1 food per person per full day
    # So each phase, check if food should tick down
    if state["current_phase"] in ("morning", "evening"):
        # Food consumed twice per day (morning + evening)
        food_cost = max(1, crew_count // 2)
        if resources["food"] >= food_cost:
            queries.update_resources(food=-food_cost)
            warnings.append(f"-{food_cost} Food (crew meals)")
        else:
            # STARVATION — no food left
            queries.set_resources(food=0)
            warnings.append("NO FOOD — Crew is starving!")
            for c in crew:
                queries.damage_character(c["id"], STARVATION_DAMAGE)
                if not c["is_player"]:
                    queries.change_trust(c["id"], -3)
            warnings.append(f"All crew take {STARVATION_DAMAGE} starvation damage")

    # ── FUEL LEAK ──
    if state["current_phase"] == "morning" and not queries.has_upgrade("fuel_efficiency_kit"):
        if resources["fuel"] > 0:
            leak = min(FUEL_LEAK_PER_DAY, resources["fuel"])
            queries.update_resources(fuel=-leak)
            warnings.append(f"-{leak} Fuel (engine leak — needs repair upgrade)")

    # ── STAMINA DRAIN ──
    for c in crew:
        new_stam = max(0, c["stamina"] - STAMINA_DRAIN_PER_PHASE)
        queries.update_character(c["id"], stamina=new_stam)

    # ── LOW TRUST CONSEQUENCES ──
    for c in crew:
        if c["is_player"]:
            continue
        if c["trust"] <= 15 and c["is_alive"]:
            # Chance of abandoning the bus
            if random.random() < 0.3:
                queries.update_character(c["id"], is_alive=0)
                warnings.append(f"!! {c['name']} has abandoned the bus in the night !!")
        elif c["trust"] <= 25 and random.random() < 0.15:
            # Sabotage or argument
            stolen = random.choice(["food", "ammo", "scrap"])
            amount = random.randint(1, 2)
            queries.update_resources(**{stolen: -amount})
            warnings.append(f"{c['name']} stole {amount} {stolen} — trust is dangerously low")

    # ── CHECK BUS DESTRUCTION ──
    bus = queries.get_bus()
    if bus["armor"] <= 0:
        queries.update_game_state(game_over=1, ending_type="bad")
        warnings.append("THE BUS IS DESTROYED")

    # ── CHECK ALL DEAD ──
    alive = queries.get_alive_crew()
    player = queries.get_player()
    if not player or not player["is_alive"]:
        queries.update_game_state(game_over=1, ending_type="bad")
        warnings.append("YOU ARE DEAD")

    return warnings


def display_warnings(warnings: list[str]):
    """Show passive system warnings dramatically."""
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
    """50% chance of showing crew banter between phases."""
    if random.random() > 0.5:
        return
    state = queries.get_game_state()
    resources = queries.get_resources()
    context = get_context(state, resources)
    banter = get_ambient_banter(context)
    if banter:
        print()
        print(f"  {Theme.MUTED}{Color.ITALIC}{banter}{Color.RESET}")
        dramatic_pause(0.4)


# ── FORCED CHOICE EVENTS ───────────────────────────────────

def check_forced_events():
    """Check for crisis situations that force hard decisions."""
    resources = queries.get_resources()
    crew = queries.get_alive_crew()
    npcs = queries.get_alive_npcs()

    # ── RATIONING EVENT: Food critically low with 3+ crew ──
    if resources["food"] <= 2 and len(crew) >= 3 and random.random() < 0.5:
        _rationing_event(crew, resources)

    # ── MUTINY: Multiple low-trust NPCs ──
    low_trust = [c for c in npcs if c["trust"] <= 25]
    if len(low_trust) >= 2 and random.random() < 0.25:
        _mutiny_event(low_trust)

    # ── INJURY TRIAGE: Multiple badly wounded ──
    wounded = [c for c in crew if c["hp"] < 30 and c["is_alive"]]
    if len(wounded) >= 2 and resources["medicine"] == 1:
        _triage_event(wounded)


def _rationing_event(crew: list, resources: dict):
    """Force the player to decide who eats."""
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
         "description": "Prioritize your best fighters and scavengers. The others notice."},
        {"label": "You skip your own meal",
         "description": "Lead by example. You take damage, but crew trust increases."},
    ]
    idx = get_choice_with_details(options, prompt="What do you do?")

    if idx == 0:
        narrator_text("You divide what's left into tiny, unsatisfying portions. Nobody complains. Nobody's happy either.")
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
        narrator_text("You make the cold calculus. The best survive. The rest tighten their belts.")
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
    clear_screen()
    print_blank(1)
    scene_break("CRISIS — CONFRONTATION")

    names = " and ".join(c["name"] for c in low_trust_npcs[:2])
    narrator_text(
        f"{names} corner you at the back of the bus. Their body language says "
        f"this has been building for a while."
    )

    ringleader = low_trust_npcs[0]
    dialogue(ringleader["name"],
             "We need to talk. About how things are being run. About whether "
             "we're even going the right direction. About whether you're the "
             "right person to be making these calls.")

    options = [
        {"label": "Hear them out and make concessions",
         "description": "Give them more say. Trust recovers, but you lose some authority."},
        {"label": "Stand firm — this isn't a democracy",
         "description": "Assert dominance. They back down or leave."},
        {"label": "Offer to share leadership responsibilities",
         "description": "Compromise. Moderate trust recovery."},
    ]
    idx = get_choice_with_details(options, prompt="How do you respond?")

    if idx == 0:
        narrator_text("You listen. You concede some points. It costs you pride, but it buys you time.")
        for c in low_trust_npcs:
            queries.change_trust(c["id"], 15)
        # Give up some resources as concession
        queries.update_resources(food=-1, ammo=-1)
        status_update("Shared 1 Food and 1 Ammo as a gesture of goodwill")
    elif idx == 1:
        narrator_text(
            f"\"I'm keeping this bus moving and you're all still alive. "
            f"That's my resume. You don't like it? The door is right there.\""
        )
        dramatic_pause(0.5)
        # One might actually leave
        if random.random() < 0.4:
            leaver = random.choice(low_trust_npcs)
            queries.update_character(leaver["id"], is_alive=0)
            narrator_text(f"{leaver['name']} grabs their pack and walks off the bus without a word.")
            dramatic_pause(1.0)
        else:
            narrator_text("They back down. For now. But you can feel the tension like a wire about to snap.")
            for c in low_trust_npcs:
                queries.change_trust(c["id"], -5)
    elif idx == 2:
        narrator_text("You offer a seat at the table. It's not everything they want, but it's something.")
        for c in low_trust_npcs:
            queries.change_trust(c["id"], 8)

    press_enter()


def _triage_event(wounded: list):
    """Only 1 medicine, multiple wounded — who gets it?"""
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
        narrator_text(f"You administer the medicine to {recipient['name']}. Relief washes over their face.")

        for c in others:
            if not c["is_player"]:
                queries.change_trust(c["id"], -8)
                narrator_text(f"{c['name']} watches in silence. You can feel the resentment.")
    else:
        narrator_text("You pocket the medicine. \"Not yet.\" Nobody argues, but nobody agrees either.")

    press_enter()


# ── CORE ACTIONS ───────────────────────────────────────────

def do_explore():
    from engine.combat import stat_check_combat, generate_combat_narrative

    crew = queries.get_alive_crew()
    state = queries.get_game_state()

    if len(crew) > 1:
        names = []
        for c in crew:
            hp_pct = int(c["hp"] / c["hp_max"] * 100)
            warn = " [WOUNDED]" if hp_pct < 40 else ""
            names.append(f"{c['name']} (Cmbt:{c['combat']} Scav:{c['scavenging']} HP:{hp_pct}%{warn})")
        idx = get_choice(names, prompt="Who leads the expedition?")
        explorer = crew[idx]
    else:
        explorer = crew[0]

    # Warn about danger level
    if state["current_phase"] == "midnight":
        narrator_text(
            "It's pitch black. You can hear them out there — shuffling, groaning, "
            "scratching. Exploring now is borderline suicidal."
        )
        if not confirm("Send them out anyway?", default_yes=False):
            return
    elif state["current_phase"] == "evening":
        narrator_text(
            "The sun is setting. Shadows are getting long and things are moving in them."
        )

    narrator_text(f"{explorer['name']} heads out into the unknown.")
    dramatic_pause(0.5)

    # Combat chance — MUCH higher at night
    combat_chances = {
        "morning": 0.25, "afternoon": 0.40,
        "evening": 0.60, "midnight": 0.80,
    }
    combat_chance = combat_chances.get(state["current_phase"], 0.35)

    # Threat level increases encounter odds
    combat_chance = min(0.95, combat_chance + state["threat_level"] * 0.03)

    if random.random() < combat_chance:
        narrator_text("Movement. Close. Too close.")
        dramatic_pause(0.5)

        result = stat_check_combat(explorer["id"])
        narrative = generate_combat_narrative(result)
        narrator_text(narrative)

        if result["damage_taken"] > 0:
            damage_display(explorer["name"], result["damage_taken"])
        if result["bus_damage"] > 0:
            damage_display("The Bus", result["bus_damage"])
        if result.get("collateral_damage"):
            cd = result["collateral_damage"]
            narrator_text(f"In the chaos, {cd['name']} catches a stray hit.")
            damage_display(cd["name"], cd["damage"])
        if result.get("resource_loss"):
            loss = result["resource_loss"]
            for k, v in loss.items():
                if v < 0:
                    print_styled(f"  ! Lost {abs(v)} {k} in the chaos", Theme.WARNING)
        if result["loot"]:
            loot_display(result["loot"])
        if result["character_died"]:
            print()
            print_styled(
                f"  {explorer['name']} is dead.",
                Theme.DAMAGE + Color.BOLD
            )
            narrator_text("The bus goes quiet. Someone pulls a blanket over what's left.")
            dramatic_pause(2.0)
            # Trust impact
            for c in queries.get_alive_npcs():
                queries.change_trust(c["id"], random.randint(-8, -3))
        if result.get("bus_destroyed"):
            return  # Game over handled by passive systems
    else:
        # Scavenging — NERFED yields
        scav_skill = explorer.get("scavenging", 3)
        hp_ratio = explorer["hp"] / max(1, explorer["hp_max"])
        effective_scav = scav_skill if hp_ratio > 0.5 else max(1, scav_skill - 2)

        loot = {}
        if random.random() < 0.2 + effective_scav * 0.04:
            loot["fuel"] = random.randint(1, 2 + effective_scav // 3)
        if random.random() < 0.3 + effective_scav * 0.04:
            loot["food"] = random.randint(1, 2 + effective_scav // 3)
        if random.random() < 0.25 + effective_scav * 0.03:
            loot["scrap"] = random.randint(1, 2 + effective_scav // 3)
        if random.random() < 0.10:
            loot["ammo"] = random.randint(1, 2)
        if random.random() < 0.05:
            loot["medicine"] = 1

        # Stamina cost for exploring
        queries.update_character(explorer["id"], stamina=max(0, explorer["stamina"] - 15))

        if loot:
            location_descs = [
                "an overturned truck", "a ransacked convenience store",
                "an abandoned house", "a wrecked cruiser",
                "a looted camping store", "a church basement",
                "a crashed ambulance", "a burned-out diner",
            ]
            narrator_text(
                f"{explorer['name']} picks through {random.choice(location_descs)} "
                f"and comes back with what they could carry."
            )
            queries.update_resources(**loot)
            loot_display(loot)
        else:
            empty_descs = [
                "Nothing. Picked clean. Someone was here before you.",
                "Empty shelves, empty drawers, empty hope. The area's been stripped.",
                "Cobwebs and dust. Whatever was here is long gone.",
            ]
            narrator_text(f"{explorer['name']} comes back empty-handed. {random.choice(empty_descs)}")

    press_enter()


def do_upgrade():
    import json
    upgrades_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "upgrades.json")
    with open(upgrades_path) as f:
        upgrade_data = json.load(f)["upgrades"]

    resources = queries.get_resources()
    installed = queries.get_installed_upgrades()

    available = []
    for key, data in upgrade_data.items():
        if key in installed:
            continue
        prereq = data.get("prerequisite")
        if prereq and prereq not in installed:
            continue
        available.append((key, data))

    if not available:
        narrator_text("Nothing to upgrade right now. The bus is maxed out — for now.")
        press_enter()
        return

    options = []
    for key, data in available:
        cost = data["cost_scrap"]
        tag = styled("[CAN AFFORD]", Theme.SUCCESS) if resources["scrap"] >= cost else styled("[Need more scrap]", Theme.DAMAGE)
        options.append(f"{data['name']} — {cost} Scrap  {tag}\n       {data['description']}")
    options.append("Cancel")

    narrator_text("You assess the bus. What could be improved?")
    idx = get_choice(options, prompt="Available upgrades:")

    if idx == len(available):
        return

    key, data = available[idx]
    cost = data["cost_scrap"]

    if resources["scrap"] < cost:
        narrator_text(f"Not enough Scrap. Need {cost}, have {resources['scrap']}.")
        press_enter()
        return

    queries.update_resources(scrap=-cost)
    queries.install_upgrade(key)

    bus = queries.get_bus()
    effects = data.get("effects", {})
    bus_updates = {}
    for eff_key, eff_val in effects.items():
        if eff_key == "armor_max":
            bus_updates["armor_max"] = bus["armor_max"] + eff_val
        elif eff_key == "armor":
            bus_updates["armor"] = min(bus["armor"] + eff_val, bus_updates.get("armor_max", bus["armor_max"]))
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

    # Banter about upgrade
    npcs = queries.get_alive_npcs()
    if npcs:
        mechanic = next((c for c in npcs if c["personality"] == "gruff"), None)
        if mechanic:
            dialogue(mechanic["name"], "Not bad. She's a little tougher now. Emphasis on 'little.'")

    press_enter()


def do_rest():
    crew = queries.get_alive_crew()
    resources = queries.get_resources()
    state = queries.get_game_state()

    # Rest heals HP and stamina but costs food
    food_cost = max(1, len(crew))

    if resources["food"] < food_cost:
        narrator_text(
            f"Not enough food for a proper rest. Need {food_cost} Food, "
            f"have {resources['food']}. You can rest hungry, but it won't heal much."
        )
        food_cost = resources["food"]  # Use what you have

    if food_cost > 0:
        queries.update_resources(food=-food_cost)

    recovery = {"morning": 8, "afternoon": 12, "evening": 18, "midnight": 22}
    heal_amount = recovery.get(state["current_phase"], 12)

    # If no food, recovery is drastically reduced
    if food_cost == 0:
        heal_amount = 3
        narrator_text("You rest on empty stomachs. It barely helps.")
    else:
        narrator_text("The crew rests. Food is shared. Wounds are tended.")

    # Stamina recovery is always decent during rest
    for c in crew:
        queries.heal_character(c["id"], heal_amount)
        new_stam = min(c["stamina_max"], c["stamina"] + 25)
        queries.update_character(c["id"], stamina=new_stam)

    if state["current_phase"] in ("evening", "midnight"):
        narrator_text(
            "Resting through the dangerous hours. You hear them outside — "
            "scratching, moaning. But the bus holds. For now."
        )

    if food_cost > 0:
        status_update(f"-{food_cost} Food consumed")
    status_update(f"+{heal_amount} HP and +25 Stamina restored")
    press_enter()


def do_interact():
    from engine.crew import get_interaction_options

    npcs = queries.get_alive_npcs()
    if not npcs:
        narrator_text("There's nobody else on the bus. Just you and the road. And the dead.")
        press_enter()
        return

    names = []
    for c in npcs:
        trust = c["trust"]
        if trust <= 20:
            tag = styled("[HOSTILE]", Theme.DAMAGE)
        elif trust <= 40:
            tag = styled("[WARY]", Theme.WARNING)
        elif trust <= 60:
            tag = ""
        elif trust <= 80:
            tag = styled("[LOYAL]", Theme.INFO)
        else:
            tag = styled("[DEVOTED]", Theme.SUCCESS)
        names.append(f"{c['name']} — Trust: {trust} {tag}")
    names.append("Cancel")

    idx = get_choice(names, prompt="Who do you want to talk to?")
    if idx == len(npcs):
        return

    target = npcs[idx]
    options = get_interaction_options(target)
    labels = [o["label"] for o in options]
    labels.append("Nevermind")

    dial_idx = get_choice(labels, prompt=f"Talking to {target['name']}...")
    if dial_idx == len(options):
        return

    option = options[dial_idx]

    if "cost" in option:
        res = queries.get_resources()
        for k, v in option["cost"].items():
            if res.get(k, 0) < v:
                narrator_text(f"You don't have enough {k} for that.")
                press_enter()
                return
        queries.update_resources(**{k: -v for k, v in option["cost"].items()})

    trust_delta = option.get("trust_delta", 0)
    if trust_delta > 0 and random.random() < 0.25:
        response = option.get("response_negative") or option["response_positive"]
        trust_delta = max(-5, -trust_delta // 2)
    else:
        response = option["response_positive"]

    new_trust = queries.change_trust(target["id"], trust_delta)

    narrator_text(response)

    if trust_delta > 0:
        status_update(f"{target['name']}'s trust: {new_trust} (+{trust_delta})")
    elif trust_delta < 0:
        print_styled(f"  ! {target['name']}'s trust: {new_trust} ({trust_delta})", Theme.WARNING)
    press_enter()


def do_travel():
    from engine.travel import travel_to_node

    state = queries.get_game_state()
    current_node_id = state.get("current_node_id")

    if not current_node_id:
        narrator_text("You're not sure where to go.")
        press_enter()
        return False

    next_nodes = queries.get_next_nodes(current_node_id)
    if not next_nodes:
        narrator_text("The road ends here.")
        press_enter()
        return False

    has_fragment = queries.get_flag("has_map_fragment")
    visible_nodes = [
        n for n in next_nodes
        if not n["requires_map_fragment"] or has_fragment
    ]

    if not visible_nodes:
        narrator_text("No accessible routes forward.")
        press_enter()
        return False

    bus = queries.get_bus()
    resources = queries.get_resources()
    options = []
    for n in visible_nodes:
        fuel_cost = max(1, int(n["fuel_cost"] * bus["fuel_efficiency"]))
        desc = n.get("edge_description", f"Head to {n['name']}")
        node_type = n["node_type"].replace("_", " ").title()
        affordable = "" if resources["fuel"] >= fuel_cost else styled(" [NOT ENOUGH FUEL]", Theme.DAMAGE)
        options.append(f"{desc}\n       [{node_type}] — Fuel cost: {fuel_cost}{affordable}")
    options.append("Stay here")

    idx = get_choice(options, prompt="Where to next?")
    if idx == len(visible_nodes):
        return False

    target = visible_nodes[idx]
    result = travel_to_node(target["id"])

    if not result["success"]:
        if result["reason"] == "no_fuel_dead_zone":
            clear_screen()
            print_blank(3)
            narrator_text("The engine sputters. Coughs. Dies.")
            dramatic_pause(2.0)
            narrator_text(
                "Silence. Then the groaning starts. From every direction. Getting closer."
            )
            dramatic_pause(2.0)
            print_styled("  There is no escape.", Theme.DAMAGE + Color.BOLD)
            dramatic_pause(2.0)
            queries.update_game_state(game_over=1, ending_type="bad")
        elif result["reason"] == "no_fuel":
            narrator_text(f"Not enough fuel. Need {result['fuel_cost']}.")
        press_enter()
        return result.get("reason") == "no_fuel_dead_zone"

    narrator_text(f"The bus rumbles forward. {result['fuel_cost']} fuel burned.")
    status_update(f"Arrived at {target['name']}")
    status_update(f"Fuel remaining: {result['fuel_remaining']}")

    if target["name"] == "Haven":
        handle_haven_arrival()
        return True
    if target["name"] == "Meridian Research Facility":
        handle_meridian_arrival()
        return True

    press_enter()
    return True


# ── ENDINGS ────────────────────────────────────────────────

def handle_haven_arrival():
    crew = queries.get_alive_crew()
    bus = queries.get_bus()

    clear_screen()
    print_blank(2)
    scene_break("HAVEN")

    narrator_text(
        "The walls rise out of the haze. Concrete and steel, razor wire, "
        "watchtowers with actual electric lights. You'd forgotten what "
        "electric lights looked like."
    )
    dramatic_pause(1.5)

    state = queries.get_game_state()
    narrator_text(f"\"Open the gate. We're survivors. {len(crew)} of us.\"")
    dramatic_pause(1.0)
    narrator_text("The gates open.")
    dramatic_pause(2.0)

    if len(crew) >= bus["crew_capacity"] * 0.6:
        queries.update_game_state(game_over=1, ending_type="good")
    else:
        queries.update_game_state(game_over=1, ending_type="neutral")
    press_enter()


def handle_meridian_arrival():
    queries.update_game_state(game_over=1, ending_type="secret")
    clear_screen()
    print_blank(2)
    scene_break("MERIDIAN")
    narrator_text("The facility looms ahead. This is where it all started.")
    narrator_text("[Secret ending — to be fully implemented in Phase 3]")
    press_enter()


def handle_game_over(state: dict):
    clear_screen()
    print_blank(3)

    ending = state.get("ending_type", "bad")
    name = state["player_name"]

    if ending == "bad":
        print_styled("  ╔══════════════════════════════════╗", Theme.DAMAGE)
        print_styled("  ║           GAME  OVER             ║", Theme.DAMAGE + Color.BOLD)
        print_styled("  ╚══════════════════════════════════╝", Theme.DAMAGE)
        print()
        death_messages = [
            f"{name}'s journey ends here. The road claims another.",
            f"The dead don't mourn. They just keep walking. {name} won't.",
            f"Somewhere out there, Haven still stands. {name} will never see it.",
        ]
        narrator_text(random.choice(death_messages))
    elif ending == "neutral":
        print_styled("  ╔══════════════════════════════════╗", Theme.WARNING)
        print_styled("  ║       YOU REACHED HAVEN          ║", Theme.WARNING + Color.BOLD)
        print_styled("  ╚══════════════════════════════════╝", Theme.WARNING)
        print()
        narrator_text(
            f"{name} made it. But the empty seats on the bus are louder "
            f"than any celebration. Survival has a price."
        )
    elif ending == "good":
        print_styled("  ╔══════════════════════════════════╗", Theme.SUCCESS)
        print_styled("  ║       HAVEN — TRIUMPHANT         ║", Theme.SUCCESS + Color.BOLD)
        print_styled("  ╚══════════════════════════════════╝", Theme.SUCCESS)
        print()
        narrator_text(
            f"{name} and the crew roll through the gates to cheers. "
            f"The bus — battered, scarred, held together by spite and scrap metal — "
            f"has carried them to safety. Against all odds."
        )
    elif ending == "secret":
        print_styled("  ╔══════════════════════════════════╗", Theme.TITLE)
        print_styled("  ║      MERIDIAN — THE CURE         ║", Theme.TITLE + Color.BOLD)
        print_styled("  ╚══════════════════════════════════╝", Theme.TITLE)
        print()
        narrator_text("The cure exists. And now, so does hope.")

    # Run stats
    print_blank(2)
    print_styled("  ── RUN STATISTICS ──", Color.BOLD + Color.BRIGHT_WHITE)
    print()
    print(f"   Days survived:     {state['current_day']}")
    print(f"   Threat level:      {state['threat_level']}")
    crew = queries.get_alive_crew()
    print(f"   Surviving crew:    {len(crew)}")
    upgrades = queries.get_installed_upgrades()
    print(f"   Bus upgrades:      {len(upgrades)}")
    flags = queries.get_all_flags()
    print(f"   Key decisions:     {len(flags)}")
    resources = queries.get_resources()
    print(f"   Final resources:   F:{resources['fuel']} Fd:{resources['food']} S:{resources['scrap']} A:{resources['ammo']} M:{resources['medicine']}")

    print_blank(2)
    press_enter("Press Enter to return to title screen...")


# ── MAIN GAME LOOP ─────────────────────────────────────────

def game_phase_loop():
    while True:
        state = queries.get_game_state()

        if state["game_over"]:
            handle_game_over(state)
            return

        # ── Run passive systems ──
        warnings = run_passive_systems()

        # Re-check game over after passive systems
        state = queries.get_game_state()
        if state["game_over"]:
            if warnings:
                display_warnings(warnings)
                press_enter()
            handle_game_over(state)
            return

        # ── Display ──
        clear_screen()
        show_hud()

        # Show warnings from passive systems
        if warnings:
            display_warnings(warnings)

        show_location_description()

        # ── Crew banter (50% chance) ──
        maybe_show_banter()

        # ── Check for forced crisis events ──
        check_forced_events()
        state = queries.get_game_state()
        if state["game_over"]:
            handle_game_over(state)
            return

        # ── Core action choice ──
        phase = state["current_phase"]
        phase_warning = ""
        if phase == "midnight":
            phase_warning = styled(" [EXTREME DANGER]", Theme.DAMAGE + Color.BOLD)
        elif phase == "evening":
            phase_warning = styled(" [HIGH DANGER]", Theme.WARNING)

        actions = [
            f"Explore — Scavenge for supplies{phase_warning}",
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
            continue  # Don't advance phase
        elif choice == 5:
            did_travel = do_travel()
            if not did_travel:
                continue

        # ── Advance phase ──
        old_day = state["current_day"]
        new_day, new_phase = queries.advance_phase()

        # Day transition
        if new_phase == "morning" and new_day > old_day:
            clear_screen()
            print_blank(1)

            phase_texts = [
                f"Day {new_day}. The sun crawls over the horizon like it's not sure it wants to.",
                f"Day {new_day}. Another morning. You're still breathing. Don't take it for granted.",
                f"Day {new_day} begins. The road stretches on. So do the dead.",
            ]
            scene_break(f"DAY {new_day} — MORNING")
            narrator_text(random.choice(phase_texts))

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
                    "Something's changed. The infected are more aggressive. More coordinated. That shouldn't be possible.",
                ]
                narrator_text(random.choice(threat_texts))

            press_enter()

        # ── Random event check (25% per phase) ──
        _check_random_event()


def _check_random_event():
    from engine.events import pick_random_event, resolve_choice

    if random.random() > 0.25:
        return

    event = pick_random_event()
    if not event:
        return

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

    effects = result.get("effects", {})
    if effects.get("recruit_random"):
        from engine.crew import recruit_next_npc
        import json
        new_npc = recruit_next_npc()
        if new_npc:
            print()
            narrator_text(f"A new survivor joins the bus: {new_npc['name']}.")

            chars_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "characters.json")
            with open(chars_path) as f:
                templates = json.load(f).get("npc_templates", [])
            for t in templates:
                if t["name"] == new_npc["name"]:
                    dialogue(new_npc["name"], t.get("intro_dialogue", "..."))
                    break

            status_update(f"Crew size: {queries.crew_count()}")

    press_enter()


# ── ENTRY POINT ────────────────────────────────────────────

def main():
    while True:
        reset_db()
        result = run_intro()

        if result.get("quit"):
            clear_screen()
            print_styled("\n  Thanks for playing Dead Route.\n", Theme.MUTED)
            sys.exit(0)

        create_player(result)
        post_intro_transition()
        game_phase_loop()


if __name__ == "__main__":
    main()

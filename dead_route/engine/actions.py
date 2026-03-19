"""
The 4 core actions + travel.
Each function handles one player action per phase.
"""

import os
import json
import random
from db import queries
from engine.combat import stat_check_combat, generate_combat_narrative
from engine.crew import get_interaction_options, recruit_next_npc
from engine.audio import audio
from ui.style import Color, Theme, styled, print_styled, clear_screen, print_blank
from ui.narration import (
    narrator_text, dramatic_pause, status_update,
    loot_display, damage_display, dialogue, scene_break
)
from ui.input import get_choice, get_choice_with_details, press_enter, confirm

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def do_explore():
    """Handle the Explore action."""
    crew = queries.get_alive_crew()
    state = queries.get_game_state()

    # Pick who goes
    if len(crew) > 1:
        from engine.trauma import character_refuses_midnight, get_character_scars
        names = []
        for c in crew:
            hp_pct = int(c["hp"] / c["hp_max"] * 100)
            warn = " [WOUNDED]" if hp_pct < 40 else ""
            # Show PTSD warning at midnight
            if state["current_phase"] == "midnight" and character_refuses_midnight(c["id"]):
                warn += styled(" [PTSD — REFUSES]", Theme.DAMAGE)
            # Show scar count
            scars = get_character_scars(c["id"])
            if scars:
                warn += styled(f" [{len(scars)} scar{'s' if len(scars)>1 else ''}]", Theme.WARNING)
            names.append(
                f"{c['name']} (Cmbt:{c['combat']} Scav:{c['scavenging']} HP:{hp_pct}%{warn})"
            )
        idx = get_choice(names, prompt="Who leads the expedition?")
        explorer = crew[idx]

        # PTSD midnight refusal
        if state["current_phase"] == "midnight" and character_refuses_midnight(explorer["id"]):
            narrator_text(
                f"{explorer['name']} tries to stand up. {explorer['name']}'s hands "
                f"are shaking. The breathing goes shallow, rapid, ragged. "
                f"Eyes locked on something nobody else can see."
            )
            narrator_text(
                f"\"I can't.\" The words come out broken. \"I can't go out there. "
                f"Not in the dark. I'm sorry. I can't.\""
            )
            narrator_text(
                f"{explorer['name']} sits back down. There's no point pushing it."
            )
            press_enter()
            return
    else:
        explorer = crew[0]

    # Danger warnings
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

    # ── PHASE PUSH EVENT CHECK (~20% chance) ──
    from engine.phase_push import (
        get_push_explore_event, resolve_push_event,
        display_phase_push, warn_phase_push
    )
    push_event = get_push_explore_event()
    if push_event:
        _resolve_push_explore(explorer, push_event)
        press_enter()
        return

    # Combat chance — MUCH higher at night
    combat_chances = {
        "morning": 0.25, "afternoon": 0.40,
        "evening": 0.60, "midnight": 0.80,
    }
    combat_chance = combat_chances.get(state["current_phase"], 0.35)
    combat_chance = min(0.95, combat_chance + state["threat_level"] * 0.03)

    if random.random() < combat_chance:
        _resolve_explore_combat(explorer)
    else:
        _resolve_explore_scavenge(explorer)

    press_enter()


def _resolve_explore_combat(explorer: dict):
    """Combat encounter during exploration."""
    audio.play_music("combat")
    narrator_text("Movement. Close. Too close.")
    dramatic_pause(0.5)

    result = stat_check_combat(explorer["id"])
    narrative = generate_combat_narrative(result)
    narrator_text(narrative)

    if result["damage_taken"] > 0:
        damage_display(explorer["name"], result["damage_taken"])
    if result.get("damage_absorbed", 0) > 0:
        status_update(f"Armor plating absorbed {result['damage_absorbed']} damage")
    if result.get("component_result") and result["component_result"].get("narrative"):
        comp = result["component_result"]
        narrator_text(comp["narrative"])
        if comp.get("component_hit") and comp["old_state"] != comp["new_state"]:
            comp_name = queries.COMPONENTS[comp["component_hit"]]["name"]
            print_styled(
                f"  !! {comp_name}: {comp['old_state']} -> {comp['new_state']}",
                Theme.WARNING + Color.BOLD
            )
    if result.get("collateral_damage"):
        cd = result["collateral_damage"]
        narrator_text(f"In the chaos, {cd['name']} catches a stray hit.")
        damage_display(cd["name"], cd["damage"])
    if result.get("resource_loss"):
        for k, v in result["resource_loss"].items():
            if v < 0:
                print_styled(f"  ! Lost {abs(v)} {k} in the chaos", Theme.WARNING)
    if result["loot"]:
        loot_display(result["loot"])
    if result["character_died"]:
        print()
        print_styled(f"  {explorer['name']} is dead.", Theme.DAMAGE + Color.BOLD)
        narrator_text("The bus goes quiet. Someone pulls a blanket over what's left.")
        dramatic_pause(2.0)
        for c in queries.get_alive_npcs():
            queries.change_trust(c["id"], random.randint(-8, -3))
    elif result.get("got_infected"):
        print()
        dramatic_pause(0.5)
        audio.play_sfx("bite")
        print_styled(
            f"  !! {explorer['name']} WAS BITTEN !!",
            Theme.DAMAGE + Color.BOLD
        )
        narrator_text(
            f"In the struggle, one of them sank its teeth into "
            f"{explorer['name']}'s forearm. The wound is deep — ragged "
            f"and already turning an angry purple at the edges. Blood "
            f"wells up thick and dark."
        )
        narrator_text(
            f"{explorer['name']} stares at the bite. Everyone stares "
            f"at the bite. Nobody says what they're all thinking."
        )
        dramatic_pause(1.5)

    # ── SCAR CHECK: permanent trauma from brutal combat ──
    if not result["character_died"] and result["result"] in ("pyrrhic", "defeat"):
        from engine.trauma import roll_for_scar, present_scar
        updated_explorer = queries.get_character(explorer["id"])
        if updated_explorer and updated_explorer["is_alive"]:
            scar = roll_for_scar(explorer["id"], result["result"])
            if scar:
                present_scar(updated_explorer, scar)


def _resolve_explore_scavenge(explorer: dict):
    """Peaceful scavenging during exploration."""
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
        audio.play_sfx("loot")
        loot_display(loot)
    else:
        empty_descs = [
            "Nothing. Picked clean. Someone was here before you.",
            "Empty shelves, empty drawers, empty hope. The area's been stripped.",
            "Cobwebs and dust. Whatever was here is long gone.",
        ]
        narrator_text(
            f"{explorer['name']} comes back empty-handed. {random.choice(empty_descs)}"
        )


def _resolve_push_explore(explorer: dict, event: dict):
    """Handle a phase-push exploration event."""
    from engine.phase_push import (
        resolve_push_event, display_phase_push, warn_phase_push
    )
    from engine.combat import stat_check_combat, generate_combat_narrative

    narrator_text(event["description"])
    dramatic_pause(0.5)

    # Build choices with time warnings
    options = []
    for c in event["choices"]:
        label = c["label"]
        desc_parts = [c.get("description", "")]
        if c.get("push"):
            time_warn = warn_phase_push(1)
            if time_warn:
                desc_parts.append(time_warn)
        options.append({"label": label, "description": " ".join(desc_parts)})

    idx = get_choice_with_details(options, prompt="What do you do?")

    result = resolve_push_event(event, idx)

    # Display outcome
    narrator_text(result["text"])

    # Show loot
    if result.get("reward"):
        loot_only = {k: v for k, v in result["reward"].items() if isinstance(v, int) and v > 0}
        if loot_only:
            audio.play_sfx("loot")
            loot_display(loot_only)

    # Show phase push
    if result["pushed"] and result["push_result"]:
        display_phase_push(result["push_result"])

    # Handle recruit
    if result.get("recruited"):
        npc = result["recruited"]
        narrator_text(f"A new survivor joins the bus: {npc['name']}.")
        status_update(f"Crew size: {queries.crew_count()}")

    # Handle triggered combat
    if result.get("combat_triggered"):
        narrator_text("The noise brought them. They're coming.")
        dramatic_pause(0.5)
        audio.play_music("combat")
        combat_result = stat_check_combat(explorer["id"])
        narrative = generate_combat_narrative(combat_result)
        narrator_text(narrative)
        if combat_result["damage_taken"] > 0:
            damage_display(explorer["name"], combat_result["damage_taken"])
        if combat_result.get("component_result", {}).get("narrative"):
            narrator_text(combat_result["component_result"]["narrative"])


def do_upgrade():
    """Handle the Upgrade action: install upgrades OR repair damaged components."""
    from engine.bus_damage import get_repair_options

    # First: choose between upgrade and repair
    repair_opts = get_repair_options()
    has_repairs = len(repair_opts) > 0

    if has_repairs:
        mode_choice = get_choice(
            ["Install an upgrade", "Repair a damaged component", "Cancel"],
            prompt="The bus needs work. What's the priority?"
        )
        if mode_choice == 2:
            return
        if mode_choice == 1:
            _do_repair(repair_opts)
            return

    _do_install_upgrade()


def _do_repair(repair_opts: list[dict]):
    """Handle repairing a damaged bus component."""
    resources = queries.get_resources()

    state_colors = {
        "destroyed": Theme.DAMAGE + Color.BOLD,
        "damaged": Theme.DAMAGE,
        "worn": Theme.WARNING,
    }

    options = []
    for opt in repair_opts:
        cost = opt["cost"]
        tag = (styled("[CAN AFFORD]", Theme.SUCCESS)
               if resources["scrap"] >= cost
               else styled("[Need more scrap]", Theme.DAMAGE))
        state_color = state_colors.get(opt["current_state"], Color.GRAY)
        options.append(
            f"Repair {opt['name']}  — {cost} Scrap  {tag}\n"
            f"       {styled(opt['current_state'].upper(), state_color)} -> "
            f"{styled(opt['repair_to'].upper(), Theme.SUCCESS)}  "
            f"({opt['description']})"
        )
    options.append("Cancel")

    narrator_text("You crawl under the bus and assess the damage.")
    idx = get_choice(options, prompt="What needs fixing?")

    if idx == len(repair_opts):
        return

    opt = repair_opts[idx]
    cost = opt["cost"]

    if resources["scrap"] < cost:
        narrator_text(f"Not enough Scrap. Need {cost}, have {resources['scrap']}.")
        press_enter()
        return

    queries.update_resources(scrap=-cost)
    old_state, new_state = queries.repair_component(opt["component"])

    repair_narratives = {
        "engine": "You wrestle with rusted bolts and frayed wires. The engine coughs, sputters — then smooths out. Better.",
        "windows": "You fit scavenged plexiglass and chain-link mesh over the gaps. Not pretty, but it'll keep things out.",
        "armor_plating": "Scrap metal, a blowtorch, and prayers. The new plating is ugly but solid.",
        "wheels": "You jack up the bus and work on the wheel assembly. It takes everything you've got, but she's rolling again.",
    }
    narrator_text(repair_narratives.get(opt["component"], "You make the repairs."))
    status_update(f"-{cost} Scrap")
    status_update(f"{opt['name']}: {old_state} -> {new_state}")

    npcs = queries.get_alive_npcs()
    mechanic = next((c for c in npcs if c["personality"] == "gruff"), None)
    if mechanic:
        dialogue(mechanic["name"], "That'll hold. For now.")

    press_enter()


def _do_install_upgrade():
    """Handle installing a new bus upgrade."""
    upgrades_path = os.path.join(DATA_DIR, "upgrades.json")
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
        tag = (styled("[CAN AFFORD]", Theme.SUCCESS)
               if resources["scrap"] >= cost
               else styled("[Need more scrap]", Theme.DAMAGE))
        options.append(
            f"{data['name']} — {cost} Scrap  {tag}\n       {data['description']}"
        )
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

    # Apply stat effects
    bus = queries.get_bus()
    effects = data.get("effects", {})
    bus_updates = {}
    for eff_key, eff_val in effects.items():
        if eff_key == "armor_max":
            bus_updates["armor_max"] = bus["armor_max"] + eff_val
        elif eff_key == "armor":
            bus_updates["armor"] = min(
                bus["armor"] + eff_val,
                bus_updates.get("armor_max", bus["armor_max"])
            )
        elif eff_key == "fuel_efficiency":
            bus_updates["fuel_efficiency"] = round(bus["fuel_efficiency"] + eff_val, 2)
        elif eff_key == "storage_capacity":
            bus_updates["storage_capacity"] = bus["storage_capacity"] + eff_val
        elif eff_key == "crew_capacity":
            bus_updates["crew_capacity"] = bus["crew_capacity"] + eff_val
    if bus_updates:
        queries.update_bus(**bus_updates)

    narrator_text(f"Upgrade installed: {data['name']}.")
    audio.play_sfx("upgrade")
    narrator_text(data["description"])
    status_update(f"-{cost} Scrap")

    npcs = queries.get_alive_npcs()
    mechanic = next((c for c in npcs if c["personality"] == "gruff"), None)
    if mechanic:
        dialogue(mechanic["name"], "Not bad. She's a little tougher now. Emphasis on 'little.'")

    press_enter()


def do_rest():
    """Handle the Rest action."""
    crew = queries.get_alive_crew()
    resources = queries.get_resources()
    state = queries.get_game_state()

    food_cost = max(1, len(crew))

    if resources["food"] < food_cost:
        narrator_text(
            f"Not enough food for a proper rest. Need {food_cost} Food, "
            f"have {resources['food']}. You can rest hungry, but it won't heal much."
        )
        food_cost = resources["food"]

    if food_cost > 0:
        queries.update_resources(food=-food_cost)

    recovery = {"morning": 8, "afternoon": 12, "evening": 18, "midnight": 22}
    heal_amount = recovery.get(state["current_phase"], 12)

    if food_cost == 0:
        heal_amount = 3
        narrator_text("You rest on empty stomachs. It barely helps.")
    else:
        narrator_text("The crew rests. Food is shared. Wounds are tended.")

    # Window condition affects rest quality
    rest_mult = queries.get_rest_multiplier()
    heal_amount = int(heal_amount * rest_mult)

    if rest_mult <= 0:
        heal_amount = 0
        narrator_text(
            "With every window gone, the bus offers no shelter. The cold, "
            "the stench, the sounds — nobody sleeps. Nobody heals."
        )
    elif rest_mult < 1.0:
        narrator_text(
            "The broken windows let the cold in. Rest is fitful at best."
        )

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
    """Handle the Interact action. Uses deep dialogue when available."""
    from engine.deep_dialogue import get_deep_scene

    npcs = queries.get_alive_npcs()
    if not npcs:
        narrator_text(
            "There's nobody else on the bus. Just you and the road. And the dead."
        )
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

    # Build interaction options
    base_options = get_interaction_options(target)
    labels = [o["label"] for o in base_options]

    # Check for deep dialogue scene
    deep_scene = get_deep_scene(target["name"], target["trust"], "small_talk")
    deep_backstory = get_deep_scene(target["name"], target["trust"], "backstory")
    deep_meal = get_deep_scene(target["name"], target["trust"], "share_meal")

    # Add deep dialogue options if available
    deep_options = []
    if deep_scene:
        labels.append(f"Sit with {target['name']} (Deep conversation)")
        deep_options.append(("small_talk", deep_scene))
    if deep_backstory:
        labels.append(f"Ask {target['name']} about their past (Story)")
        deep_options.append(("backstory", deep_backstory))
    if deep_meal and queries.get_resources().get("food", 0) >= 1:
        labels.append(f"Share a meal with {target['name']} (Costs 1 Food)")
        deep_options.append(("share_meal", deep_meal))

    labels.append("Nevermind")

    dial_idx = get_choice(labels, prompt=f"Talking to {target['name']}...")

    # Cancel
    if dial_idx == len(labels) - 1:
        return

    # Deep dialogue option selected
    base_count = len(base_options)
    if dial_idx >= base_count:
        deep_idx = dial_idx - base_count
        if deep_idx < len(deep_options):
            trigger_type, scene = deep_options[deep_idx]
            _play_deep_scene(target, scene)
            return

    # Fallback to generic interaction
    if dial_idx >= len(base_options):
        return

    option = base_options[dial_idx]

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
        print_styled(
            f"  ! {target['name']}'s trust: {new_trust} ({trust_delta})", Theme.WARNING
        )
    press_enter()


def _play_deep_scene(char: dict, scene: dict):
    """Render a deep dialogue scene with typewriter narration and dialogue."""
    from ui.narration import dialogue as show_dialogue

    # Pay costs if any
    cost = scene.get("cost")
    if cost:
        queries.update_resources(**{k: -v for k, v in cost.items()})
        for k, v in cost.items():
            status_update(f"-{v} {k.capitalize()}")

    # Play scene lines
    for speaker, text in scene["text"]:
        if speaker == "narrator":
            narrator_text(text)
        else:
            show_dialogue(speaker, text)
        dramatic_pause(0.3)

    # Apply trust
    trust_delta = scene.get("trust_delta", 0)
    if trust_delta:
        new_trust = queries.change_trust(char["id"], trust_delta)
        if trust_delta > 0:
            status_update(f"{char['name']}'s trust: {new_trust} (+{trust_delta})")
        else:
            print_styled(
                f"  ! {char['name']}'s trust: {new_trust} ({trust_delta})", Theme.WARNING
            )

    # Set flags
    flag = scene.get("sets_flag")
    if flag:
        queries.set_flag(flag, True)

    press_enter()


def do_travel() -> bool:
    """Handle travel to the next node. Returns True if travel happened."""
    from engine.travel import travel_to_node
    from engine.bus_damage import check_bus_immobilized

    # Check if bus can move at all
    if check_bus_immobilized():
        narrator_text(
            "The bus isn't going anywhere. The engine or wheels are destroyed. "
            "You need to repair them before you can travel."
        )
        press_enter()
        return False

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

    # Filter hidden routes
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

    # Fuel cost uses component multiplier (engine + wheels condition)
    fuel_mult = queries.get_fuel_multiplier()

    options = []
    for n in visible_nodes:
        fuel_cost = max(1, int(n["fuel_cost"] * bus["fuel_efficiency"] * fuel_mult))
        desc = n.get("edge_description", f"Head to {n['name']}")
        node_type = n["node_type"].replace("_", " ").title()
        affordable = (
            "" if resources["fuel"] >= fuel_cost
            else styled(" [NOT ENOUGH FUEL]", Theme.DAMAGE)
        )
        penalty = ""
        if fuel_mult > 1.1:
            penalty = styled(f" (+{int((fuel_mult-1)*100)}% from damage)", Theme.WARNING)
        options.append(
            f"{desc}\n       [{node_type}] — Fuel cost: {fuel_cost}{penalty}{affordable}"
        )
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

    audio.play_music("travel")
    narrator_text(f"The bus rumbles forward. {result['fuel_cost']} fuel burned.")
    status_update(f"Arrived at {target['name']}")
    status_update(f"Fuel remaining: {result['fuel_remaining']}")

    press_enter()
    return True


def handle_recruitment_from_event(effects: dict):
    """Handle NPC recruitment triggered by events."""
    if not effects.get("recruit_random"):
        return

    new_npc = recruit_next_npc()
    if not new_npc:
        return

    print()
    narrator_text(f"A new survivor joins the bus: {new_npc['name']}.")

    chars_path = os.path.join(DATA_DIR, "characters.json")
    with open(chars_path) as f:
        templates = json.load(f).get("npc_templates", [])
    for t in templates:
        if t["name"] == new_npc["name"]:
            dialogue(new_npc["name"], t.get("intro_dialogue", "..."))
            break

    status_update(f"Crew size: {queries.crew_count()}")

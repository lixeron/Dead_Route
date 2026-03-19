"""
HUD and status display functions.
Shows resource bars, crew status, bus condition, phase info.
"""

from ui.style import (
    Color, Theme, styled, print_styled, print_blank,
    progress_bar, simple_table, panel, divider, get_terminal_width
)
from db import queries


PHASE_DISPLAY = {
    "morning":   ("MORNING",   Theme.MORNING,   "Low",     Theme.RISK_LOW),
    "afternoon": ("AFTERNOON", Theme.AFTERNOON,  "Medium",  Theme.RISK_MEDIUM),
    "evening":   ("EVENING",   Theme.EVENING,    "High",    Theme.RISK_HIGH),
    "midnight":  ("MIDNIGHT",  Theme.MIDNIGHT,   "Extreme", Theme.RISK_EXTREME),
}


def show_hud():
    """Display the main HUD with resources, bus status, and phase info."""
    state = queries.get_game_state()
    resources = queries.get_resources()
    bus = queries.get_bus()
    crew = queries.get_alive_crew()
    node = queries.get_current_node()

    phase_name, phase_color, risk_label, risk_color = PHASE_DISPLAY.get(
        state["current_phase"], ("UNKNOWN", Color.WHITE, "?", Color.WHITE)
    )

    width = min(get_terminal_width() - 2, 76)

    # Top bar: Day and Phase
    print()
    print_styled("=" * width, Color.GRAY)

    day_str = f"Day {state['current_day']}"
    phase_str = styled(phase_name, phase_color, Color.BOLD)
    risk_str = styled(f"Risk: {risk_label}", risk_color)
    threat_str = styled(f"Threat Lv.{state['threat_level']}", Theme.WARNING)

    location = "Unknown"
    if node:
        location = node["name"]

    print(f"  {styled(day_str, Color.BRIGHT_WHITE, Color.BOLD)}  |  {phase_str}  |  "
          f"{risk_str}  |  {threat_str}")
    print(f"  {styled('Location:', Color.GRAY)} {styled(location, Color.BRIGHT_WHITE)}")

    print_styled("-" * width, Color.GRAY)

    # Resources row
    fuel_color = Theme.FUEL if resources["fuel"] > 10 else Theme.DAMAGE
    food_color = Theme.FOOD if resources["food"] > 5 else Theme.DAMAGE
    ammo_color = Theme.AMMO if resources["ammo"] > 3 else Theme.DAMAGE

    res_line = (
        f"  {styled('Fuel:', fuel_color)} {resources['fuel']:>3}  "
        f"{styled('Food:', food_color)} {resources['food']:>3}  "
        f"{styled('Scrap:', Theme.SCRAP)} {resources['scrap']:>3}  "
        f"{styled('Ammo:', ammo_color)} {resources['ammo']:>3}  "
        f"{styled('Meds:', Theme.MEDICINE)} {resources['medicine']:>3}"
    )
    print(res_line)

    # Bus components status
    try:
        components = queries.get_all_components()
        state_styles = {
            "intact": (Theme.SUCCESS, "OK "),
            "worn": (Theme.WARNING, "WRN"),
            "damaged": (Theme.DAMAGE, "DMG"),
            "destroyed": (Theme.DAMAGE + Color.BOLD, "XXX"),
        }
        comp_parts = []
        for key in ["engine", "armor_plating", "windows", "wheels"]:
            comp = components.get(key, {})
            st = comp.get("state", "intact")
            color, label = state_styles.get(st, (Color.GRAY, "???"))
            name = comp.get("name", key)
            comp_parts.append(f"{styled(name + ':', Color.GRAY)}{styled(label, color)}")
        print(f"  {' '.join(comp_parts)}")
    except Exception:
        # Fallback if components not initialized yet
        armor_color = Theme.SUCCESS if bus["armor"] > bus["armor_max"] * 0.5 else (
            Theme.WARNING if bus["armor"] > bus["armor_max"] * 0.25 else Theme.DAMAGE
        )
        print(f"  {styled('Bus Armor:', armor_color)} {bus['armor']}/{bus['armor_max']}")

    print(f"  {styled('Crew:', Color.GRAY)} {len(crew)}/{bus['crew_capacity']}")

    print_styled("=" * width, Color.GRAY)
    print()


def show_crew_status():
    """Display detailed crew status with injuries, morale, and effective skills."""
    crew = queries.get_alive_crew()
    state = queries.get_game_state()

    print()
    print_styled("  -- CREW STATUS --", Color.BOLD + Color.BRIGHT_WHITE)
    print()

    for c in crew:
        if c["is_player"]:
            name_display = styled(f"{c['name']} (You)", Theme.PLAYER_NAME, Color.BOLD)
        else:
            name_display = styled(c["name"], Theme.NPC_NAME, Color.BOLD)

        # Injury display
        injury = c.get("injury", "none")
        injury_str = ""
        if injury != "none":
            injury_data = queries.INJURY_TYPES.get(injury, {})
            injury_label = injury_data.get("label", injury)
            injury_color = Theme.DAMAGE if injury in ("critical", "infected", "badly_hurt") else Theme.WARNING
            injury_str = f"  {styled(f'[{injury_label}]', injury_color)}"

        # Trust display for NPCs
        trust_str = ""
        if not c["is_player"]:
            trust = c["trust"]
            if trust <= 20:
                trust_color = Theme.TRUST_LOW
                trust_label = "Hostile"
            elif trust <= 40:
                trust_color = Theme.TRUST_LOW
                trust_label = "Wary"
            elif trust <= 60:
                trust_color = Theme.MUTED
                trust_label = "Neutral"
            elif trust <= 80:
                trust_color = Theme.TRUST_HIGH
                trust_label = "Loyal"
            else:
                trust_color = Theme.TRUST_HIGH
                trust_label = "Devoted"
            trust_str = f"  {styled(f'Trust: {trust_label} ({trust})', trust_color)}"

        # Morale display
        morale = c.get("morale", 60)
        if morale < 20:
            morale_str = styled(f"  Morale: Breaking ({morale})", Theme.DAMAGE)
        elif morale < 40:
            morale_str = styled(f"  Morale: Low ({morale})", Theme.WARNING)
        elif morale < 60:
            morale_str = styled(f"  Morale: Shaky ({morale})", Theme.MUTED)
        elif morale < 80:
            morale_str = styled(f"  Morale: Steady ({morale})", Color.GRAY)
        else:
            morale_str = styled(f"  Morale: Strong ({morale})", Theme.SUCCESS)

        hp_color = Theme.SUCCESS if c["hp"] > 60 else (Theme.WARNING if c["hp"] > 30 else Theme.DAMAGE)
        hp_bar = progress_bar(c["hp"], c["hp_max"], width=15, fill_color=hp_color, label="HP")

        # Effective skills (after penalties)
        eff_combat = queries.get_effective_skill(c, "combat")
        eff_medical = queries.get_effective_skill(c, "medical")
        eff_mech = queries.get_effective_skill(c, "mechanical")
        eff_scav = queries.get_effective_skill(c, "scavenging")

        # Show penalty in red if skill is reduced
        def skill_display(name, base, effective):
            if effective < base:
                return f"{styled(name, Color.GRAY)}{styled(str(effective), Theme.DAMAGE):>4}"
            return f"{styled(name, Color.GRAY)}{effective:>2}"

        print(f"  {name_display}{injury_str}{trust_str}")
        print(f"    {hp_bar}{morale_str}")
        print(f"    {skill_display('Combat:', c['combat'], eff_combat)}  "
              f"{skill_display('Medical:', c['medical'], eff_medical)}  "
              f"{skill_display('Mech:', c['mechanical'], eff_mech)}  "
              f"{skill_display('Scav:', c['scavenging'], eff_scav)}")
        print()


def show_location_description():
    """Display current location description."""
    node = queries.get_current_node()
    if not node:
        return

    node_colors = {
        "town": Color.YELLOW,
        "highway": Color.GRAY,
        "rural": Color.GREEN,
        "urban": Color.RED,
        "outpost": Color.CYAN,
        "dead_zone": Color.BRIGHT_RED,
    }

    color = node_colors.get(node["node_type"], Color.WHITE)
    type_display = node["node_type"].replace("_", " ").title()

    print(panel(
        node["description"],
        title=f"{node['name']} [{type_display}]",
        border_color=color,
        title_color=Color.BOLD + color,
    ))


def show_bus_status():
    """Display detailed bus component status with effects."""
    print()
    print_styled("  -- BUS STATUS --", Color.BOLD + Color.BRIGHT_WHITE)
    print()

    state_styles = {
        "intact":    (Theme.SUCCESS, "INTACT   "),
        "worn":      (Theme.WARNING, "WORN     "),
        "damaged":   (Theme.DAMAGE,  "DAMAGED  "),
        "destroyed": (Theme.DAMAGE + Color.BOLD, "DESTROYED"),
    }

    try:
        components = queries.get_all_components()
    except Exception:
        print("  Bus component data unavailable.")
        return

    for key in ["engine", "armor_plating", "windows", "wheels"]:
        comp = components.get(key, {})
        name = comp.get("name", key)
        state = comp.get("state", "intact")
        stats = comp.get("stats", {})
        desc = stats.get("desc", "")
        color, label = state_styles.get(state, (Color.GRAY, "???"))

        print(f"  {styled(f'{name:<16}', Color.BRIGHT_WHITE)}{styled(label, color)}  {Theme.MUTED}{desc}{Color.RESET}")

        # Show gameplay effects for non-intact states
        if state != "intact":
            effects = []
            if "fuel_mult" in stats and stats["fuel_mult"] > 1.0 and stats["fuel_mult"] < 999:
                effects.append(f"+{int((stats['fuel_mult']-1)*100)}% fuel cost")
            elif "fuel_mult" in stats and stats["fuel_mult"] >= 999:
                effects.append("CANNOT TRAVEL")
            if "rest_mult" in stats and stats["rest_mult"] < 1.0 and stats["rest_mult"] > 0:
                effects.append(f"-{int((1-stats['rest_mult'])*100)}% rest healing")
            elif "rest_mult" in stats and stats["rest_mult"] <= 0:
                effects.append("REST DISABLED")
            if "absorb" in stats:
                effects.append(f"{int(stats['absorb']*100)}% damage absorption")
            if "morale_drain" in stats and stats["morale_drain"] > 0:
                effects.append(f"-{stats['morale_drain']} trust/phase")
            if "travel_mult" in stats and stats["travel_mult"] > 1.0 and stats["travel_mult"] < 999:
                effects.append(f"+{int((stats['travel_mult']-1)*100)}% travel fuel")
            elif "travel_mult" in stats and stats["travel_mult"] >= 999:
                effects.append("CANNOT TRAVEL")
            if "can_flee" in stats and not stats["can_flee"]:
                effects.append("CANNOT FLEE COMBAT")
            if effects:
                print(f"  {'':16}  {Theme.WARNING}{', '.join(effects)}{Color.RESET}")
        print()

    # Show installed upgrades
    upgrades = queries.get_installed_upgrades()
    if upgrades:
        print_styled("  Installed upgrades:", Color.GRAY)
        for u in upgrades:
            print(f"    {styled(u.replace('_', ' ').title(), Theme.INFO)}")
        print()

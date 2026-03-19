"""
Passive systems: resource drains, decay, trust consequences.
Runs every phase automatically before player actions.
"""

import random
from db import queries

STARVATION_DAMAGE = 8
STAMINA_DRAIN_PER_PHASE = 5
FUEL_LEAK_PER_DAY = 2


def run_passive_systems() -> list[str]:
    """Run all passive drain/damage systems. Returns list of warning strings."""
    warnings = []
    state = queries.get_game_state()
    resources = queries.get_resources()
    crew = queries.get_alive_crew()
    crew_count = len(crew)

    # ── FOOD DRAIN (morning + evening) ──
    if state["current_phase"] in ("morning", "evening"):
        food_cost = max(1, crew_count // 2)
        if resources["food"] >= food_cost:
            queries.update_resources(food=-food_cost)
            warnings.append(f"-{food_cost} Food (crew meals)")
        else:
            queries.set_resources(food=0)
            warnings.append("NO FOOD — Crew is starving!")
            for c in crew:
                queries.damage_character(c["id"], STARVATION_DAMAGE)
                if not c["is_player"]:
                    queries.change_trust(c["id"], -3)
            warnings.append(f"All crew take {STARVATION_DAMAGE} starvation damage")

    # ── FUEL LEAK (morning only, until upgrade) ──
    if state["current_phase"] == "morning" and not queries.has_upgrade("fuel_efficiency_kit"):
        if resources["fuel"] > 0:
            leak = min(FUEL_LEAK_PER_DAY, resources["fuel"])
            queries.update_resources(fuel=-leak)
            warnings.append(f"-{leak} Fuel (engine leak — needs repair upgrade)")

    # ── STAMINA DRAIN ──
    for c in crew:
        base_drain = STAMINA_DRAIN_PER_PHASE
        # Paranoia scar adds extra stamina drain
        try:
            from engine.trauma import get_scar_stamina_drain
            base_drain += get_scar_stamina_drain(c["id"])
        except Exception:
            pass
        new_stam = max(0, c["stamina"] - base_drain)
        queries.update_character(c["id"], stamina=new_stam)

    # ── LOW TRUST CONSEQUENCES ──
    for c in crew:
        if c["is_player"]:
            continue
        if c["trust"] <= 15 and c["is_alive"]:
            if random.random() < 0.3:
                queries.update_character(c["id"], is_alive=0)
                warnings.append(f"!! {c['name']} has abandoned the bus in the night !!")
        elif c["trust"] <= 25 and random.random() < 0.15:
            stolen = random.choice(["food", "ammo", "scrap"])
            amount = random.randint(1, 2)
            queries.update_resources(**{stolen: -amount})
            warnings.append(f"{c['name']} stole {amount} {stolen} — trust is dangerously low")

    # ── WINDOW MORALE/TRUST DRAIN ──
    window_drain = queries.get_window_morale_drain()
    if window_drain > 0:
        for c in crew:
            if not c["is_player"]:
                queries.change_trust(c["id"], -window_drain)
        if window_drain >= 5:
            warnings.append("Destroyed windows are crushing crew morale")
        elif window_drain >= 2:
            warnings.append("Damaged windows making the crew uneasy")

    # ── CHECK BUS IMMOBILIZED ──
    if not queries.can_bus_travel():
        # Only game over if also out of scrap to repair
        resources_now = queries.get_resources()
        if resources_now["scrap"] < 5:
            queries.update_game_state(game_over=1, ending_type="bad")
            warnings.append("THE BUS IS IMMOBILIZED — Not enough scrap to repair")

    # ── CHECK PLAYER DEATH ──
    player = queries.get_player()
    if not player or not player["is_alive"]:
        queries.update_game_state(game_over=1, ending_type="bad")
        warnings.append("YOU ARE DEAD")

    return warnings

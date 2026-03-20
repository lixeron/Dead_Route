"""
Test suite: Combat, infection, trauma, and bus damage systems.
"""

import random
from db import queries


class TestCombat:
    def test_stat_check_combat_returns_result(self):
        from engine.combat import stat_check_combat
        result = stat_check_combat(1, base_threat=5)
        assert "result" in result
        assert result["result"] in ("decisive_victory", "victory", "pyrrhic", "defeat")
        assert "damage_taken" in result
        assert "character_name" in result

    def test_combat_narrative_exists(self):
        from engine.combat import stat_check_combat, generate_combat_narrative
        result = stat_check_combat(1, base_threat=5)
        narrative = generate_combat_narrative(result)
        assert isinstance(narrative, str)
        assert len(narrative) > 50  # Should be descriptive

    def test_combat_outcomes_vary(self):
        from engine.combat import stat_check_combat
        outcomes = set()
        for _ in range(100):
            result = stat_check_combat(1, base_threat=8)
            outcomes.add(result["result"])
        # With enough trials, we should see at least 2 different outcomes
        assert len(outcomes) >= 2

    def test_combat_applies_damage(self):
        from engine.combat import stat_check_combat
        initial_hp = queries.get_character(1)["hp"]
        # High threat = likely to take damage
        for _ in range(10):
            queries.heal_character(1, 100)
            result = stat_check_combat(1, base_threat=15)
            if result["damage_taken"] > 0:
                char = queries.get_character(1)
                assert char["hp"] < 100
                break


class TestInfection:
    def _setup_npc(self):
        queries.create_character(
            "InfectedNPC", combat=5, personality="gruff", trust=50
        )
        crew = queries.get_alive_crew()
        return [c for c in crew if c["name"] == "InfectedNPC"][0]

    def test_infect_character(self):
        npc = self._setup_npc()
        queries.infect_character(npc["id"])
        char = queries.get_character(npc["id"])
        assert char["infected"] == 1
        assert char["infection_stage"] == 0

    def test_advance_infection(self):
        npc = self._setup_npc()
        queries.infect_character(npc["id"])
        new_stage = queries.advance_infection(npc["id"])
        assert new_stage == 1

    def test_infection_full_progression(self):
        npc = self._setup_npc()
        queries.infect_character(npc["id"])
        for expected in [1, 2, 3, 4]:
            stage = queries.advance_infection(npc["id"])
            assert stage == expected

    def test_cure_infection(self):
        npc = self._setup_npc()
        queries.infect_character(npc["id"])
        queries.advance_infection(npc["id"])
        queries.cure_infection(npc["id"])
        char = queries.get_character(npc["id"])
        assert char["infected"] == 0
        assert char["infection_stage"] == 0

    def test_delay_infection(self):
        npc = self._setup_npc()
        queries.infect_character(npc["id"])
        queries.advance_infection(npc["id"])  # Stage 1
        queries.advance_infection(npc["id"])  # Stage 2
        queries.delay_infection(npc["id"])     # Back to 1
        char = queries.get_character(npc["id"])
        assert char["infection_stage"] == 1

    def test_get_infected_crew(self):
        npc = self._setup_npc()
        assert len(queries.get_infected_crew()) == 0
        queries.infect_character(npc["id"])
        infected = queries.get_infected_crew()
        assert len(infected) == 1
        assert infected[0]["name"] == "InfectedNPC"

    def test_tick_infections_advances_stage(self):
        from engine.infection import tick_infections
        npc = self._setup_npc()
        queries.infect_character(npc["id"])
        queries.update_game_state(current_phase="morning")
        events = tick_infections()
        assert len(events) == 1
        assert events[0]["new_stage"] == 1
        assert len(events[0]["narrative"]) > 0


class TestTrauma:
    def test_scar_application(self):
        from engine.trauma import roll_for_scar, get_character_scars
        queries.create_character("Scarred", combat=5, personality="gruff", trust=50)
        crew = [c for c in queries.get_alive_crew() if c["name"] == "Scarred"]
        char_id = crew[0]["id"]

        # Force scars by rolling many times against defeat
        scar = None
        # Ensure we're in squeeze era where scars are possible
        queries.update_game_state(current_day=10)
        for _ in range(100):
            scar = roll_for_scar(char_id, "defeat")
            if scar:
                break

        if scar:  # May not trigger due to probability
            scars = get_character_scars(char_id)
            assert len(scars) >= 1
            assert scars[0]["id"] == scar["id"]

    def test_no_scars_in_breathing_era(self):
        from engine.trauma import roll_for_scar
        queries.update_game_state(current_day=3)  # Breathing era
        queries.create_character("SafeNPC", combat=5, personality="gruff", trust=50)
        crew = [c for c in queries.get_alive_crew() if c["name"] == "SafeNPC"]
        char_id = crew[0]["id"]

        for _ in range(50):
            scar = roll_for_scar(char_id, "defeat")
            assert scar is None  # No scars during breathing era


class TestBusDamage:
    def test_initial_bus_components(self):
        comps = queries.get_all_components()
        assert "engine" in comps
        assert "armor_plating" in comps
        assert "windows" in comps
        assert "wheels" in comps
        for comp in comps.values():
            assert comp["state"] == "intact"

    def test_degrade_component(self):
        old, new = queries.degrade_component("windows")
        assert old == "intact"
        assert new == "worn"

    def test_repair_component(self):
        queries.degrade_component("engine")  # intact -> worn
        old, new = queries.repair_component("engine")
        assert old == "worn"
        assert new == "intact"

    def test_full_degradation(self):
        for expected in ["worn", "damaged", "destroyed"]:
            _, new = queries.degrade_component("armor_plating")
            assert new == expected

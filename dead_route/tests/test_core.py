"""
Test suite: Database, resources, characters, and game state management.
"""

from db import queries


class TestGameState:
    def test_game_state_exists(self):
        state = queries.get_game_state()
        assert state is not None
        assert state["player_name"] == "TestPlayer"
        assert state["current_day"] == 1
        assert state["current_phase"] == "morning"

    def test_advance_phase(self):
        new_day, new_phase = queries.advance_phase()
        assert new_phase == "afternoon"
        assert new_day == 1

    def test_advance_phase_full_cycle(self):
        for expected in ["afternoon", "evening", "midnight"]:
            _, phase = queries.advance_phase()
            assert phase == expected
        # Next advance should roll to new day
        day, phase = queries.advance_phase()
        assert phase == "morning"
        assert day == 2

    def test_game_over_flag(self):
        state = queries.get_game_state()
        assert state["game_over"] == 0
        queries.update_game_state(game_over=1)
        state = queries.get_game_state()
        assert state["game_over"] == 1


class TestResources:
    def test_initial_resources(self):
        res = queries.get_resources()
        assert res["fuel"] == 20
        assert res["food"] == 8
        assert res["scrap"] == 4
        assert res["ammo"] == 5
        assert res["medicine"] == 1

    def test_update_resources_add(self):
        queries.update_resources(fuel=5, food=3)
        res = queries.get_resources()
        assert res["fuel"] == 25
        assert res["food"] == 11

    def test_update_resources_subtract(self):
        queries.update_resources(fuel=-10)
        res = queries.get_resources()
        assert res["fuel"] == 10

    def test_resources_floor_at_zero(self):
        queries.update_resources(fuel=-999)
        res = queries.get_resources()
        assert res["fuel"] == 0


class TestCharacters:
    def test_player_exists(self):
        crew = queries.get_alive_crew()
        assert len(crew) >= 1
        player = [c for c in crew if c["is_player"]]
        assert len(player) == 1
        assert player[0]["name"] == "TestPlayer"

    def test_create_npc(self):
        queries.create_character(
            "Marcus Cole", combat=6, medical=2, mechanical=7,
            scavenging=4, personality="gruff", trust=55
        )
        crew = queries.get_alive_crew()
        marcus = [c for c in crew if c["name"] == "Marcus Cole"]
        assert len(marcus) == 1
        assert marcus[0]["combat"] == 6
        assert marcus[0]["personality"] == "gruff"

    def test_damage_character(self):
        char = queries.get_character(1)  # Player
        initial_hp = char["hp"]
        queries.damage_character(1, 25)
        char = queries.get_character(1)
        assert char["hp"] == initial_hp - 25

    def test_character_death(self):
        queries.damage_character(1, 999)
        char = queries.get_character(1)
        assert char["is_alive"] == 0

    def test_change_trust(self):
        queries.create_character("NPC", trust=50, personality="gruff")
        npc = [c for c in queries.get_alive_crew() if c["name"] == "NPC"][0]
        new_trust = queries.change_trust(npc["id"], 10)
        assert new_trust == 60


class TestFlags:
    def test_set_and_get_flag(self):
        assert queries.get_flag("test_flag") == False
        queries.set_flag("test_flag", True)
        assert queries.get_flag("test_flag") == True

    def test_multiple_flags(self):
        queries.set_flag("flag_a", True)
        queries.set_flag("flag_b", True)
        flags = queries.get_all_flags()
        assert "flag_a" in flags
        assert "flag_b" in flags

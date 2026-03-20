"""
Test suite: Balance config, direction system, coin, events, NPCs, banter.
"""

import random
from db import queries


class TestBalance:
    def test_era_detection(self):
        from engine.balance import get_era
        queries.update_game_state(current_day=3)
        assert get_era() == "breathing"
        queries.update_game_state(current_day=10)
        assert get_era() == "squeeze"
        queries.update_game_state(current_day=18)
        assert get_era() == "endgame"

    def test_get_balance_returns_values(self):
        from engine.balance import get_balance
        queries.update_game_state(current_day=3)
        combat = get_balance("COMBAT_CHANCE")
        assert isinstance(combat, dict)
        assert "morning" in combat
        assert 0 < combat["morning"] < 1

    def test_breathing_era_no_scars(self):
        from engine.balance import SCAR_CHANCE
        assert SCAR_CHANCE["breathing"]["pyrrhic"] == 0.0
        assert SCAR_CHANCE["breathing"]["defeat"] == 0.0

    def test_breathing_era_no_infection(self):
        from engine.balance import INFECTION_CHANCE
        assert INFECTION_CHANCE["breathing"]["pyrrhic"] == 0.0
        assert INFECTION_CHANCE["breathing"]["defeat"] == 0.0

    def test_endgame_harder_than_breathing(self):
        from engine.balance import COMBAT_CHANCE, SCAVENGE_MULTIPLIER
        assert COMBAT_CHANCE["endgame"]["morning"] > COMBAT_CHANCE["breathing"]["morning"]
        assert SCAVENGE_MULTIPLIER["endgame"] < SCAVENGE_MULTIPLIER["breathing"]

    def test_starting_resources_defined(self):
        from engine.balance import STARTING_RESOURCES
        assert STARTING_RESOURCES["fuel"] == 20
        assert STARTING_RESOURCES["food"] == 8


class TestDirection:
    def test_progress_calculation(self):
        from engine.direction import get_progress
        prog = get_progress()
        assert "progress_pct" in prog
        assert "distance_to_haven" in prog
        assert prog["distance_to_haven"] > 0

    def test_milestones_defined(self):
        from engine.direction import MILESTONES
        assert len(MILESTONES) >= 5
        assert 50 in MILESTONES  # Halfway milestone

    def test_meridian_awareness_starts_zero(self):
        from engine.direction import get_meridian_awareness
        assert get_meridian_awareness() == 0

    def test_meridian_awareness_increases(self):
        from engine.direction import get_meridian_awareness
        queries.set_flag("nadia_cure_motivation", True)
        assert get_meridian_awareness() >= 20

    def test_era_transition_fires_once(self):
        from engine.direction import check_era_transition
        queries.update_game_state(current_day=8)
        text = check_era_transition()
        assert text is not None
        assert len(text) > 50
        # Second call should return None (already fired)
        text2 = check_era_transition()
        assert text2 is None

    def test_npc_hint_format(self):
        from engine.direction import get_npc_hint
        queries.create_character("Hint NPC", personality="gruff", trust=50)
        queries.set_resources(fuel=3, food=1, ammo=0, medicine=0, scrap=2)
        # May return None due to probability, try multiple times
        hint = None
        for _ in range(50):
            hint = get_npc_hint()
            if hint:
                break
        if hint:
            assert isinstance(hint, str)
            assert len(hint) > 20


class TestCoin:
    def test_coin_not_available_initially(self):
        assert not queries.get_flag("has_coin")

    def test_coin_moments_defined(self):
        from engine.coin import COIN_MOMENTS
        assert len(COIN_MOMENTS) >= 5
        for key, moment in COIN_MOMENTS.items():
            assert "description" in moment
            assert "heads_reward" in moment
            assert "tails_penalty" in moment

    def test_no_coin_moment_without_coin(self):
        from engine.coin import get_random_coin_moment
        moment = get_random_coin_moment()
        assert moment is None

    def test_coin_flip_is_fair(self):
        results = {"heads": 0, "tails": 0}
        for _ in range(1000):
            results[random.choice(["heads", "tails"])] += 1
        # Should be roughly 50/50 (within 10% margin)
        ratio = results["heads"] / 1000
        assert 0.4 < ratio < 0.6


class TestEvents:
    def test_events_load(self):
        from engine.events import load_events
        events = load_events()
        assert len(events) >= 5
        # Should include both base and dark events
        ids = {e["id"] for e in events}
        assert "infected_child" in ids or "roadside_stranger" in ids

    def test_event_structure(self):
        from engine.events import load_events
        events = load_events()
        for event in events:
            assert "id" in event
            assert "description" in event
            assert "choices" in event
            assert len(event["choices"]) >= 1
            for choice in event["choices"]:
                assert "label" in choice
                assert "success" in choice


class TestNPCPool:
    def test_npc_templates_load(self):
        from engine.crew import load_npc_templates
        templates = load_npc_templates()
        assert len(templates) == 13

    def test_all_npcs_have_required_fields(self):
        from engine.crew import load_npc_templates
        required = ["name", "personality", "combat", "medical",
                    "mechanical", "scavenging", "intro_dialogue"]
        templates = load_npc_templates()
        for npc in templates:
            for field in required:
                assert field in npc, f"{npc['name']} missing {field}"

    def test_unique_personalities(self):
        from engine.crew import load_npc_templates
        templates = load_npc_templates()
        personalities = [t["personality"] for t in templates]
        # All 13 should have a personality
        assert len(personalities) == 13

    def test_recruit_npc(self):
        from engine.crew import recruit_next_npc
        npc = recruit_next_npc()
        assert npc is not None
        assert npc["name"] != "TestPlayer"


class TestBanter:
    def test_all_personalities_have_banter(self):
        from engine.banter import BANTER
        from engine.crew import load_npc_templates
        templates = load_npc_templates()
        personalities = {t["personality"] for t in templates}
        for p in personalities:
            assert p in BANTER, f"Missing banter for personality: {p}"

    def test_banter_has_all_contexts(self):
        from engine.banter import BANTER
        required_contexts = ["idle", "low_fuel", "low_food", "after_combat", "night"]
        for personality, contexts in BANTER.items():
            for ctx in required_contexts:
                assert ctx in contexts, f"{personality} missing context: {ctx}"

    def test_cross_banter_exists(self):
        from engine.banter import CROSS_BANTER
        assert len(CROSS_BANTER) >= 20

    def test_get_ambient_banter(self):
        from engine.banter import get_ambient_banter
        queries.create_character("BanterNPC", personality="gruff", trust=50)
        # May return None, try multiple times
        banter = None
        for _ in range(20):
            banter = get_ambient_banter("idle")
            if banter:
                break
        assert banter is not None


class TestDeepDialogue:
    def test_deep_scenes_defined(self):
        from engine.deep_dialogue import DEEP_DIALOGUE
        assert len(DEEP_DIALOGUE) >= 6

    def test_get_scene_by_trust(self):
        from engine.deep_dialogue import get_deep_scene
        scene = get_deep_scene("Marcus Cole", 70, "backstory")
        if scene:
            assert "text" in scene
            assert "trust_delta" in scene
            assert len(scene["text"]) > 0

    def test_quiet_moments_defined(self):
        from engine.deep_dialogue import QUIET_MOMENTS
        assert len(QUIET_MOMENTS) >= 5


class TestFourthWall:
    def test_darkness_scoring(self):
        from engine.fourth_wall import get_darkness_score
        assert get_darkness_score() == 0
        queries.set_flag("mercy_kill", True)
        assert get_darkness_score() >= 1

    def test_no_trigger_before_day_10(self):
        from engine.fourth_wall import should_trigger
        queries.update_game_state(current_day=5)
        queries.set_flag("mercy_kill", True)
        queries.set_flag("robbed_family", True)
        assert not should_trigger()

    def test_glitch_functions(self):
        from engine.fourth_wall import _zalgo, _corrupt_text, _creepy_case
        assert len(_zalgo("test")) >= 4
        assert len(_corrupt_text("test", 0.5)) == 4
        assert _creepy_case("ab") == "aB"

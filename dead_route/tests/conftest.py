"""
Pytest configuration and shared fixtures for Dead Route tests.
"""

import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def fresh_database():
    """Reset the database before each test."""
    from db.database import reset_db
    from db import queries
    from engine.travel import generate_map

    reset_db()
    queries.create_game("TestPlayer", "they/them", "they", "them", "their")
    queries.set_resources(fuel=20, food=8, scrap=4, ammo=5, medicine=1)
    queries.create_character("TestPlayer", is_player=True, combat=6)

    start_id = generate_map()
    queries.update_game_state(current_node_id=start_id)
    queries.mark_node_visited(start_id)
    queries.init_bus_components()

    yield

    # Cleanup
    db_path = os.path.join(os.path.dirname(__file__), "..", "dead_route.db")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass

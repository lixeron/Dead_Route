"""
Map generation and travel between nodes.
"""

import random
from db import queries

# Node name pools by type
NODE_NAMES = {
    "town": [
        "Ashwood Junction", "Cedar Falls", "Millbrook", "Ridgecrest",
        "Dusty Pines", "Hollow Creek", "Birchville", "Copperfield",
        "Irondale", "Shady Oaks", "Red Mesa", "Willowbank",
    ],
    "highway": [
        "Interstate 40 Stretch", "Route 66 Corridor", "Highway 9 Overpass",
        "The Long Mile", "Deadman's Straightaway", "Bridge District",
        "The Bypass", "Freeway Ruins",
    ],
    "rural": [
        "Henderson Farm", "Old Mill Road", "Wheatfield Crossing",
        "The Orchard", "Backwater Creek", "Pine Ridge Trail",
        "Sunflower Valley", "Quiet Meadows",
    ],
    "urban": [
        "Downtown Ruins", "The Financial District", "Westside Projects",
        "University Quarter", "Metro Center", "The Docks",
        "Industrial Park", "Chinatown Block",
    ],
    "outpost": [
        "The Barricade", "Fort Coleman", "Safe House 7",
        "The Trading Post", "Riverside Camp", "The Bunker",
    ],
    "dead_zone": [
        "The Swarm Corridor", "Blackout District", "Infected Mile",
        "The Hive", "Ground Zero Bypass", "Corpse Highway",
    ],
}

NODE_DESCRIPTIONS = {
    "town": "A small town, partially overrun. Buildings line the main street — some intact, most not. Worth searching if you can handle what's inside.",
    "highway": "Long open road. Fast travel, but you're exposed. Keep the windows up and the pedal down.",
    "rural": "Quiet farmland stretches to the horizon. Fewer infected out here, but also fewer supplies. The peace is almost unsettling.",
    "urban": "Dense city blocks. Every shadow could hide a dozen of them. But cities have supplies — if you're brave enough to look.",
    "outpost": "A survivor settlement. Walls made of cars and sheet metal. They're cautious, but willing to trade.",
    "dead_zone": "The infected own this stretch. No stopping. No exploring. Just pray you have enough fuel to make it through.",
}


def generate_map(num_nodes: int = 18) -> int:
    """
    Generate a semi-random route map.
    Returns the starting node ID.
    """
    used_names = set()
    nodes = []

    def pick_name(node_type: str) -> str:
        pool = NODE_NAMES.get(node_type, ["Unknown Location"])
        available = [n for n in pool if n not in used_names]
        if not available:
            available = pool
        name = random.choice(available)
        used_names.add(name)
        return name

    # Define the route structure
    # Start -> 4-5 nodes -> Fork -> Branch A (3-4) / Branch B (3-4) -> Merge -> 3-4 nodes -> Haven
    route_template = [
        # Opening stretch
        ("town", 1, False),
        ("rural", 1, False),
        ("highway", 1, False),
        ("town", 2, False),
        # First fork
        ("urban", 2, True),   # Fork point
    ]

    # Branch A (harder, more loot)
    branch_a = [
        ("urban", 2, False),
        ("dead_zone", 1, False),
        ("town", 1, False),
    ]

    # Branch B (safer, less loot)
    branch_b = [
        ("rural", 1, False),
        ("town", 1, False),
        ("rural", 2, False),
    ]

    # Post-merge stretch
    post_merge = [
        ("outpost", 2, False),
        ("highway", 1, False),
        ("urban", 2, True),  # Second fork (late game - Meridian branch possible)
    ]

    # Final stretch to Haven
    final_stretch = [
        ("dead_zone", 1, False),
        ("town", 1, False),
    ]

    # Haven (end node)
    haven = ("outpost", 1, False)

    # Create starting node
    order = 0
    start_id = queries.create_map_node(
        name="Greenfield Elementary",
        node_type="town",
        description="The abandoned school where you found the bus. The parking lot is littered with backpacks and tiny shoes. Time to leave.",
        fuel_cost=0, days_to_clear=1, node_order=order
    )
    order += 1

    # Create route nodes
    prev_id = start_id
    for ntype, days, is_fork in route_template:
        nid = queries.create_map_node(
            name=pick_name(ntype), node_type=ntype,
            description=NODE_DESCRIPTIONS[ntype],
            fuel_cost=random.randint(3, 7),
            days_to_clear=days, is_fork=is_fork, node_order=order
        )
        queries.create_map_edge(prev_id, nid, f"Continue along the route toward {pick_name(ntype) if False else 'the next stop'}.")
        prev_id = nid
        order += 1

    fork_node_id = prev_id

    # Branch A
    prev_a = fork_node_id
    for ntype, days, is_fork in branch_a:
        nid = queries.create_map_node(
            name=pick_name(ntype), node_type=ntype,
            description=NODE_DESCRIPTIONS[ntype],
            fuel_cost=random.randint(3, 6),
            days_to_clear=days, node_order=order
        )
        if prev_a == fork_node_id:
            queries.create_map_edge(prev_a, nid, "Take the highway through the city. Faster, but crawling with infected.")
        else:
            queries.create_map_edge(prev_a, nid)
        prev_a = nid
        order += 1

    # Branch B
    prev_b = fork_node_id
    for ntype, days, is_fork in branch_b:
        nid = queries.create_map_node(
            name=pick_name(ntype), node_type=ntype,
            description=NODE_DESCRIPTIONS[ntype],
            fuel_cost=random.randint(4, 8),
            days_to_clear=days, node_order=order
        )
        if prev_b == fork_node_id:
            queries.create_map_edge(prev_b, nid, "Detour through the back roads. Longer and burns more fuel, but quieter.")
        else:
            queries.create_map_edge(prev_b, nid)
        prev_b = nid
        order += 1

    # Merge point
    merge_id = queries.create_map_node(
        name=pick_name("outpost"), node_type="outpost",
        description=NODE_DESCRIPTIONS["outpost"],
        fuel_cost=random.randint(3, 6),
        days_to_clear=2, node_order=order
    )
    queries.create_map_edge(prev_a, merge_id, "The routes converge at a survivor camp.")
    queries.create_map_edge(prev_b, merge_id, "The routes converge at a survivor camp.")
    order += 1

    # Post-merge
    prev_id = merge_id
    for ntype, days, is_fork in post_merge:
        nid = queries.create_map_node(
            name=pick_name(ntype), node_type=ntype,
            description=NODE_DESCRIPTIONS[ntype],
            fuel_cost=random.randint(3, 7),
            days_to_clear=days, is_fork=is_fork, node_order=order
        )
        queries.create_map_edge(prev_id, nid)
        prev_id = nid
        order += 1

    late_fork_id = prev_id

    # Final stretch to Haven
    prev_haven = late_fork_id
    for ntype, days, is_fork in final_stretch:
        nid = queries.create_map_node(
            name=pick_name(ntype), node_type=ntype,
            description=NODE_DESCRIPTIONS[ntype],
            fuel_cost=random.randint(4, 7),
            days_to_clear=days, node_order=order
        )
        if prev_haven == late_fork_id:
            queries.create_map_edge(prev_haven, nid, "Continue toward Haven. The safe zone is close.")
        else:
            queries.create_map_edge(prev_haven, nid)
        prev_haven = nid
        order += 1

    # Haven
    haven_id = queries.create_map_node(
        name="Haven",
        node_type="outpost",
        description="The walled settlement. Lights glow behind concrete barriers. You can hear generators humming. The end of the road.",
        fuel_cost=random.randint(3, 5),
        days_to_clear=1, node_order=order
    )
    queries.create_map_edge(prev_haven, haven_id, "The final push to Haven.")
    order += 1

    # Meridian branch (secret - from late fork)
    meridian_nodes = [
        ("dead_zone", 1), ("urban", 2), ("dead_zone", 1),
    ]
    prev_m = late_fork_id
    for ntype, days in meridian_nodes:
        nid = queries.create_map_node(
            name=pick_name(ntype), node_type=ntype,
            description=NODE_DESCRIPTIONS[ntype],
            fuel_cost=random.randint(5, 8),
            days_to_clear=days, is_meridian=True, node_order=order
        )
        if prev_m == late_fork_id:
            queries.create_map_edge(prev_m, nid,
                "A faded road marked on the scientist's map. \"MERIDIAN - 120mi.\" This is it.",
                requires_fragment=True)
        else:
            queries.create_map_edge(prev_m, nid)
        prev_m = nid
        order += 1

    # Meridian facility
    meridian_id = queries.create_map_node(
        name="Meridian Research Facility",
        node_type="urban",
        description="A massive concrete complex behind razor wire and blast doors. This is where LAZARUS was born. And where it might die.",
        fuel_cost=5, days_to_clear=2, is_meridian=True, node_order=order
    )
    queries.create_map_edge(prev_m, meridian_id)

    return start_id


def travel_to_node(node_id: int) -> dict:
    """
    Travel to a node. Consumes fuel. Returns travel result.
    """
    node = queries.get_character(node_id)  # wrong function
    from db.database import get_connection
    conn = get_connection()
    row = conn.execute("SELECT * FROM map_nodes WHERE id = ?", (node_id,)).fetchone()
    conn.close()
    node = dict(row) if row else None

    if not node:
        return {"success": False, "reason": "invalid_node"}

    bus = queries.get_bus()
    resources = queries.get_resources()

    # Calculate fuel cost
    fuel_cost = int(node["fuel_cost"] * bus["fuel_efficiency"])
    fuel_cost = max(1, fuel_cost)

    if resources["fuel"] < fuel_cost:
        if node["node_type"] == "dead_zone":
            # Game over - stranded in dead zone
            queries.update_game_state(game_over=1, ending_type="bad")
            return {"success": False, "reason": "no_fuel_dead_zone", "fuel_cost": fuel_cost}
        else:
            return {"success": False, "reason": "no_fuel", "fuel_cost": fuel_cost}

    # Consume fuel and update position
    queries.update_resources(fuel=-fuel_cost)
    queries.update_game_state(current_node_id=node_id)
    queries.mark_node_visited(node_id)

    return {
        "success": True,
        "node": node,
        "fuel_cost": fuel_cost,
        "fuel_remaining": resources["fuel"] - fuel_cost,
    }

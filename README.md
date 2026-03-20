# 🧟 DEAD ROUTE

[![CI](https://github.com/YOUR_USERNAME/dead-route/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/dead-route/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**A zombie survival roguelite where every choice scars you — literally.**

Dead Route is a text-based survival game where you manage a crew of survivors on an armored school bus, traveling across a post-apocalyptic wasteland toward a place called Haven. Every day brings impossible choices: who eats, who fights, who you leave behind. Crew members get infected, develop PTSD, lose eyes and limbs. The bus breaks down. The dead don't stop. And sometimes, the game notices what you've done.

Heavily inspired by Undertale, Last of Us, Death Road to Canada, 60 Seconds!, Detroit Become Human, and more.
Idea stemmed from the AI slop ads that show gameplay that doesn't correlate with the actual game itself. 
Decided to use the interesting concept, add to it, and turn it into a playable game.

---

## Features

- **19 interconnected game systems** — combat, infection, trauma, bus damage, morale, trust, and more
- **13 unique NPCs** with full personality systems, progressive backstories, and 165+ lines of contextual banter
- **LAZARUS infection** — a 5-stage body horror system with graphic deterioration and euthanasia choices
- **Permanent scars** — 10 types of physical and psychological trauma that never heal
- **The Lucky Coin** — 50/50 coin flip gambles inspired by Fear & Hunger
- **4th wall breaking event** — the game watches your dark choices and responds
- **Three-era difficulty curve** — learn, struggle, survive (Days 1-7, 8-14, 15+)
- **Direction system** — progress bar, milestones, NPC hints, secret ending breadcrumbs
- **Audio system** — 14 phase-based music tracks, 5 SFX triggers, per-phase atmosphere [CURRENTLY DOESN'T WORK]
- **Interruptible text** — typewriter effect with skip support (press Enter) [CURRENTLY DOESN'T WORK]

## Quick Start

### Run locally (no dependencies beyond Python 3.11+)

```bash
git clone https://github.com/YOUR_USERNAME/dead-route.git
cd dead-route
make run
```

Or directly:

```bash
cd dead_route && python3 main.py
```

### Run with Docker

```bash
# One command
docker run -it $(docker build -q .)

# Or with Make
make docker-run

# Or with docker-compose (persists saves)
make compose-up
```

### Run tests

```bash
make test          # Full test suite with verbose output
make test-quick    # Quick pass/fail
make test-cov      # With coverage report
```

## Architecture

Dead Route uses a three-layer architecture designed for portability to Godot Engine:

```
┌─────────────────────────────────────────┐
│  PRESENTATION (ui/)                     │
│  Terminal output, typewriter, menus     │  ← Replaced by Godot UI
├─────────────────────────────────────────┤
│  LOGIC (engine/)                        │
│  Combat, infection, events, balance     │  ← Rewritten in GDScript
├─────────────────────────────────────────┤
│  DATA (db/ + data/)                     │
│  SQLite database, JSON config files     │  ← Carries over unchanged
└─────────────────────────────────────────┘
```

### Project Structure

```
dead_route/
├── main.py                 # Entry point (thin orchestrator)
├── db/
│   ├── database.py         # SQLite schema and connection management
│   └── queries.py          # All data access functions
├── engine/                 # Game logic (16 modules)
│   ├── game_loop.py        # Main phase cycle state machine
│   ├── actions.py          # Player action handlers
│   ├── combat.py           # Stat-check combat with graphic narratives
│   ├── infection.py        # LAZARUS 5-stage infection system
│   ├── trauma.py           # Permanent scars and PTSD
│   ├── bus_damage.py       # 4-component degradation system
│   ├── balance.py          # Central difficulty configuration
│   ├── direction.py        # Progress, milestones, Meridian hints
│   ├── coin.py             # Lucky coin 50/50 gamble mechanic
│   ├── fourth_wall.py      # Meta-awareness event
│   ├── deep_dialogue.py    # Trust-gated character conversations
│   ├── events.py           # JSON event loader and resolver
│   ├── phase_push.py       # Time-as-cost mechanic
│   ├── crew.py             # NPC recruitment and management
│   ├── banter.py           # Context-sensitive crew dialogue
│   ├── travel.py           # Map generation and navigation
│   ├── audio.py            # Music/SFX playback
│   ├── passive.py          # Per-phase automatic systems
│   ├── crisis.py           # Forced narrative events
│   ├── endings.py          # Haven, Meridian, and game over
│   └── intro.py            # Title and character creation
├── ui/                     # Presentation layer
│   ├── style.py            # ANSI colors, typewriter, formatting
│   ├── narration.py        # Cinematic text and pacing
│   ├── display.py          # HUD, crew status, bus status
│   └── input.py            # Player input with stdin flush
├── data/                   # JSON game data (moddable)
│   ├── events.json         # Base narrative events
│   ├── dark_events.json    # Mature-content events
│   ├── characters.json     # 13 NPC templates
│   └── upgrades.json       # Bus upgrade definitions
├── audio/                  # Audio files (user-provided)
│   ├── music/              # Phase music, title, combat, etc.
│   ├── sfx/                # Sound effects
│   └── README.txt          # File naming guide
├── tests/                  # Test suite
│   ├── conftest.py         # Shared fixtures
│   ├── test_core.py        # Database, resources, characters
│   ├── test_systems.py     # Combat, infection, trauma, bus
│   └── test_content.py     # Balance, events, NPCs, banter
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── .github/workflows/ci.yml
```

## Audio Setup (Optional)

The game runs silently by default. Drop audio files into `audio/music/` and `audio/sfx/` to enable the soundtrack. See [`audio/README.txt`](dead_route/audio/README.txt) for file naming.

Requires `mpv`, `ffplay`, or `paplay` on your system.

## Difficulty Eras

| Era | Days | Philosophy |
|-----|------|------------|
| **Breathing** | 1-7 | Learn the systems. Generous loot, no scars, no infection. |
| **The Squeeze** | 8-14 | Moral complexity. Scars trigger. Dark events appear. |
| **Endgame** | 15+ | Scarce everything. Every choice costs something. |

## The Godot Transition

This Python CLI version is the MVP and reference implementation. A Godot 4.x graphical version is in development, featuring:

- Pixel art bus interior as the main gameplay screen
- Character sprites with state-dependent animations
- Event scene illustrations
- Per-character dialogue beeps
- Audio crossfading between phases
- Screen shake, weather particles, and shader effects

Look at document to understand the transition plan and implementation.

## Contributing

This is a solo project in active development. Transitioning to Godot.

## License

MIT License. See [LICENSE](LICENSE) for details.

---

*"The dead don't mourn. They just keep walking."*

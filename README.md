# PROJECT DEAD ROUTE

[![CI](https://github.com/lixeron/Dead_Route/actions/workflows/ci.yml/badge.svg)](https://github.com/lixeron/Dead_Route/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**A zombie survival roguelite where every choice scars you — literally.**

Dead Route is a text-based survival game where you manage a crew of survivors on an armored school bus, traveling across a post-apocalyptic wasteland toward Haven. Every day brings impossible choices: who eats, who fights, who you leave behind. Crew members get infected, develop PTSD, lose eyes and limbs. The bus breaks down. The dead don't stop. And sometimes, the game notices what you've done.


Heavily inspired by Undertale, Last of Us, Death Road to Canada, 60 Seconds!, Detroit Become Human, and more.
Idea stemmed from the AI slop ads that show gameplay that doesn't correlate with the actual game itself. 
Decided to use the interesting concept, add to it, and turn it into a playable game.


---

## How to Play 

### Step 1: Install Python

**Windows:**
1. Open the **Microsoft Store** (search "Microsoft Store" in your Start menu)
2. Search for **"Python"**
3. Install **Python 3.12** (or the latest version available)
4. That's it — no settings to configure

**Mac:**
1. Open **Terminal** (search "Terminal" in Spotlight)
2. Type `python3 --version` and press Enter
3. If Python isn't installed, your Mac will prompt you to install it — follow the prompts

**Linux:**
Python is likely already installed. Open a terminal and type `python3 --version` to check.

### Step 2: Download the Game

**Option A — Download ZIP (easiest):**
1. Click the green **"Code"** button at the top of this page
2. Click **"Download ZIP"**
3. Extract the ZIP file anywhere on your computer

**Option B — Git clone:**
```bash
git clone https://github.com/lixeron/Dead_Route.git
```

### Step 3: Run the Game

**Windows:**
1. Open the extracted folder
2. Navigate into the `dead_route` folder
3. Double-click `main.py` — if Python is installed, the game will launch in a terminal window

**Or from any terminal/command prompt:**
```bash
cd Dead_Route/dead_route
python3 main.py
```

> **Note:** On Windows, you may need to use `python` instead of `python3`.

### Gameplay Tips
- **Press Enter** during text to skip ahead — the game has typewriter text that you can speed through
- **Numbers** are used to select choices (type 1, 2, 3, etc. and press Enter)
- The game **auto-saves** — your progress is stored in a database file
- **Audio is optional** — drop `.mp3` or `.ogg` files into `audio/music/` and `audio/sfx/` to enable the soundtrack (see `audio/README.txt` for file names)

**NOTE** Since this is being ran through a terminal, issues/bugs with this are likely. Concept is more for Godot

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
- **Medicine triage** — choose who gets healed when you don't have enough for everyone
- **Era-gated content** — the world gets darker and more gruesome as days pass
- **Audio system** — 14 phase-based music tracks, 5 SFX triggers, per-phase atmosphere
- **Interruptible text** — typewriter effect with skip support (press Enter)

## Content

- Extreme physical injury and gore
- Infection and bodily deterioration
- Mercy killing / euthanasia decisions
- Child endangerment (narrative events)
- Cannibalism (implied)
- Psychological trauma and PTSD


---

## Quick Start (For Developers)

### Run locally
```bash
git clone https://github.com/lixeron/Dead_Route.git
cd Dead_Route
make run
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
├── engine/                 # Game logic (18 modules)
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
├── tests/                  # Test suite (34 tests)
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

Requires `mpv`, `ffplay`, or `paplay` on your system for audio playback.

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
- Event scene illustrations and death cutscenes
- Per-character dialogue beeps (Undertale-style)
- Audio crossfading between phases
- Screen shake, weather particles, and shader effects
- Click-to-interact with character sprites on the bus

See the transition documentation for the complete transition plan.

## Contributing

Bug reports and feedback welcome via [Issues](https://github.com/lixeron/Dead_Route/issues). If you playtest and find something broken or have ideas, open an issue!

## License

MIT License. See [LICENSE](LICENSE) for details.

---



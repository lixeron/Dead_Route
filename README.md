# Dead_Route
> ⚠️ **Status: Work In Progress (MVP Phase)** > *This is currently a text-based/terminal MVP built to test and refine the core gameplay loop and survival mechanics before transitioning to a full graphical engine (Godot/Unity).*

## 💡 The Origin Story
This project stemmed from those dumb AI "slop" mobile game ads. You know the ones: the gameplay in the ad actually looks incredibly fun (anime characters surviving on a fortified school bus while zombies swarm outside), but the actual downloaded game is just another generic city-builder that has absolutely nothing to do with the ad. 

Since I couldn't find a game that actually plays like that, I decided to build it myself. 

**The Vibe:** If *Death Road to Canada*, *The Last of Us*, and *The Oregon Trail* had a very dark, traumatized baby. 

## 🎲 What is Dead Route?
*Dead Route* is a gritty, true-roguelite survival game where you manage a rusted-out school bus and a crew of flawed survivors crossing a post-apocalyptic wasteland. 

It is designed to be a **genuine survival horror experience**. The game doesn't just throw zombies at you; it throws starvation, paranoia, failing engine parts, and impossible moral choices. Death is permanent, and the world gets worse every single day.

## ⚙️ Core Mechanics (In Development)
* **The 4-Phase Day & "Phase Push":** Time is your most valuable currency. Actions are split into Morning, Afternoon, Evening, and Midnight. The later it gets, the deadlier the encounters. Certain narrative choices "push" the phase forward, forcing you to navigate back to your bus in the pitch black.
* **The Rolling Fortress:** The bus isn't just a vehicle; it's your only shelter. It takes localized damage (shattered windows negate rest, busted radiators guzzle fuel) and can be upgraded with welded armor, cow catchers, and roof turrets using scavenged scrap.
* **The Slow Rot (Hidden Infection):** Bitten crew members don't die instantly. They slowly succumb to the LAZARUS pathogen over several days, forcing you to use incredibly rare medicine, euthanize them, or risk them turning inside the bus while everyone is sleeping.
* **Permanent Trauma:** Surviving a brutal encounter might leave a character permanently maimed or psychologically scarred, heavily penalizing their stats for the rest of the run.
* **The Burden of Triage:** Resource scarcity forces horrific choices. When food runs out, starving crew members might steal rations, attempt mutiny, or slip away into the night.

## 🛠️ Tech Stack (MVP)
The current prototype is designed with a strict Model-View-Controller (MVC) architecture to make the eventual transition to a graphical engine seamless.
* **Logic/Engine:** Python 3.10+
* **Data Layer:** SQLite (Tracks dynamic run state, relationships, and bus integrity)
* **Content:** JSON-driven event architecture
* **UI:** Custom ANSI terminal styling

## 🚀 Development Roadmap
* **Phase 1 (Current):** Playable terminal-based MVP. Proving out the 4-phase day, SQLite database state, stat-check combat, and event injection.
* **Phase 2 (Depth):** Full map generation, expanded JSON narrative events, and deep crew relationship/trust mechanics.
* **Phase 3 (The Port):** Transitioning the validated game logic and database structure into a game engine (Unity or Godot) for the final graphical release.

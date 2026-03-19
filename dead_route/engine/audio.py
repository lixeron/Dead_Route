"""
Audio system for Dead Route.
Plays background music and sound effects using system audio players.
Fails silently if no audio files or players are found — game works fine without audio.

Tries players in order: mpv, ffplay, paplay, aplay.
Music loops in a background thread. SFX plays once.

Usage:
    from engine.audio import audio
    audio.play_music("morning")     # Loops audio/music/morning.mp3
    audio.play_sfx("gunshot")       # Plays audio/sfx/gunshot.mp3 once
    audio.stop_music()              # Stops current music
    audio.set_volume(0.5)           # 0.0 to 1.0 (mpv/ffplay only)
"""

import os
import subprocess
import threading
import signal
import time

# ── Path Configuration ─────────────────────────────────────

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC_DIR = os.path.join(PROJECT_ROOT, "audio", "music")
SFX_DIR = os.path.join(PROJECT_ROOT, "audio", "sfx")

# Map logical names to filenames (user can change these)
MUSIC_FILES = {
    "title":     "title",
    "intro":     "intro",
    "morning":   "morning",
    "afternoon": "afternoon",
    "evening":   "evening",
    "midnight":  "midnight",
    "combat":    "combat",
    "event":     "event",
    "haven":     "haven",
    "gameover":  "gameover",
    "travel":    "travel",
}

SFX_FILES = {
    "engine_start": "engine_start",
    "gunshot":      "gunshot",
    "bite":         "bite",
    "upgrade":      "upgrade",
    "loot":         "loot",
}

SUPPORTED_EXTENSIONS = [".mp3", ".ogg", ".wav", ".flac", ".m4a"]


def _find_file(directory: str, name: str) -> str | None:
    """Find an audio file by name, trying all supported extensions."""
    for ext in SUPPORTED_EXTENSIONS:
        path = os.path.join(directory, name + ext)
        if os.path.isfile(path):
            return path
    return None


def _find_player() -> tuple[str, list[str]] | None:
    """
    Find a working audio player on the system.
    Returns (player_name, base_command) or None.
    """
    players = [
        ("mpv", ["mpv", "--no-video", "--really-quiet"]),
        ("ffplay", ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]),
        ("paplay", ["paplay"]),
        ("aplay", ["aplay", "-q"]),
    ]
    for name, cmd in players:
        try:
            subprocess.run(
                ["which", cmd[0]],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2
            )
            return name, cmd
        except Exception:
            continue
    return None


class AudioManager:
    """Manages background music and sound effects."""

    def __init__(self):
        self._music_process: subprocess.Popen | None = None
        self._music_thread: threading.Thread | None = None
        self._current_music: str | None = None
        self._stop_flag = threading.Event()
        self._volume: float = 0.7
        self._enabled: bool = True
        self._player = _find_player()

    @property
    def available(self) -> bool:
        """Check if audio playback is possible."""
        return self._player is not None and self._enabled

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False
        self.stop_music()

    def toggle(self) -> bool:
        """Toggle audio on/off. Returns new state."""
        if self._enabled:
            self.disable()
        else:
            self.enable()
        return self._enabled

    def set_volume(self, vol: float):
        """Set volume (0.0 to 1.0). Only works with mpv/ffplay."""
        self._volume = max(0.0, min(1.0, vol))

    def play_music(self, track_name: str):
        """
        Play a music track in a loop. Stops current music first.
        If the same track is already playing, does nothing.
        """
        if not self.available:
            return

        if self._current_music == track_name and self._music_process:
            return  # Already playing this track

        logical_name = MUSIC_FILES.get(track_name, track_name)
        filepath = _find_file(MUSIC_DIR, logical_name)
        if not filepath:
            return  # File not found — silent fail

        self.stop_music()
        self._current_music = track_name
        self._stop_flag.clear()

        # Start looping in a background thread
        self._music_thread = threading.Thread(
            target=self._music_loop,
            args=(filepath,),
            daemon=True
        )
        self._music_thread.start()

    def stop_music(self):
        """Stop currently playing music."""
        self._stop_flag.set()
        self._kill_music_process()
        self._current_music = None

    def play_sfx(self, sfx_name: str):
        """Play a one-shot sound effect (non-blocking)."""
        if not self.available:
            return

        logical_name = SFX_FILES.get(sfx_name, sfx_name)
        filepath = _find_file(SFX_DIR, logical_name)
        if not filepath:
            return

        # Fire and forget in a daemon thread
        threading.Thread(
            target=self._play_once,
            args=(filepath,),
            daemon=True
        ).start()

    def crossfade_to(self, track_name: str, fade_time: float = 1.0):
        """
        Transition to a new track. Simple stop-start for now.
        (True crossfading would require mixing — future enhancement.)
        """
        self.play_music(track_name)

    def _music_loop(self, filepath: str):
        """Background loop: play the track, restart when it ends."""
        while not self._stop_flag.is_set():
            self._play_once(filepath, is_music=True)
            # Small gap between loops
            if not self._stop_flag.is_set():
                self._stop_flag.wait(timeout=0.5)

    def _play_once(self, filepath: str, is_music: bool = False):
        """Play a file once using the system player."""
        if not self._player:
            return

        player_name, base_cmd = self._player
        cmd = list(base_cmd)

        # Add volume control for supported players
        if player_name == "mpv":
            vol_pct = int(self._volume * 100)
            cmd.extend([f"--volume={vol_pct}"])
        elif player_name == "ffplay":
            cmd.extend(["-volume", str(int(self._volume * 100))])

        cmd.append(filepath)

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid if os.name != "nt" else None
            )

            if is_music:
                self._music_process = proc

            # Wait for it to finish (or be killed)
            proc.wait()

        except Exception:
            pass

    def _kill_music_process(self):
        """Kill the current music subprocess."""
        proc = self._music_process
        if proc and proc.poll() is None:
            try:
                # Kill the process group to catch any child processes
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                try:
                    proc.kill()
                except Exception:
                    pass
        self._music_process = None


# ── Singleton ──────────────────────────────────────────────

audio = AudioManager()


# ── Convenience: Phase music mapping ──────────────────────

PHASE_MUSIC = {
    "morning": "morning",
    "afternoon": "afternoon",
    "evening": "evening",
    "midnight": "midnight",
}


def play_phase_music(phase: str):
    """Play the appropriate music for the current game phase."""
    track = PHASE_MUSIC.get(phase)
    if track:
        audio.play_music(track)

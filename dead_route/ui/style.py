"""
ANSI terminal styling utilities.
Zero-dependency replacement for the Rich library.
Provides colored text, bold/dim/italic, panels, and tables.
"""

import os
import sys
import time
import shutil


# ── ANSI Escape Codes ──────────────────────────────────────

class Color:
    """ANSI color codes."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    STRIKETHROUGH = "\033[9m"

    # Foreground
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # Bright foreground
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_DARKGRAY = "\033[100m"


# ── Game-specific color themes ─────────────────────────────

class Theme:
    """Semantic color mappings for game elements."""
    # Phase colors
    MORNING = Color.BRIGHT_YELLOW
    AFTERNOON = Color.YELLOW
    EVENING = Color.RED
    MIDNIGHT = Color.MAGENTA

    # Risk levels
    RISK_LOW = Color.GREEN
    RISK_MEDIUM = Color.YELLOW
    RISK_HIGH = Color.RED
    RISK_EXTREME = Color.BRIGHT_RED

    # Resources
    FUEL = Color.YELLOW
    FOOD = Color.GREEN
    SCRAP = Color.GRAY
    AMMO = Color.RED
    MEDICINE = Color.CYAN

    # UI elements
    TITLE = Color.BRIGHT_RED
    SUBTITLE = Color.GRAY
    DIALOGUE = Color.BRIGHT_WHITE
    NARRATOR = Color.DIM
    CHOICE = Color.BRIGHT_CYAN
    SUCCESS = Color.BRIGHT_GREEN
    FAILURE = Color.BRIGHT_RED
    WARNING = Color.BRIGHT_YELLOW
    INFO = Color.BRIGHT_BLUE
    MUTED = Color.GRAY

    # Combat
    DAMAGE = Color.RED
    HEAL = Color.GREEN
    COMBAT_ACTION = Color.YELLOW

    # Characters
    NPC_NAME = Color.BRIGHT_CYAN
    PLAYER_NAME = Color.BRIGHT_GREEN
    TRUST_HIGH = Color.GREEN
    TRUST_MID = Color.YELLOW
    TRUST_LOW = Color.RED


# ── Utility Functions ──────────────────────────────────────

def get_terminal_width() -> int:
    """Get current terminal width, default 80."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def styled(text: str, *styles: str) -> str:
    """Apply ANSI styles to text."""
    prefix = "".join(styles)
    return f"{prefix}{text}{Color.RESET}"


def clear_screen():
    """Clear terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def flush_input():
    """Flush any buffered stdin so stale keypresses don't skip prompts."""
    try:
        import select
        while select.select([sys.stdin], [], [], 0)[0]:
            sys.stdin.read(1)
    except Exception:
        pass


def _check_skip() -> bool:
    """Check if user pressed a key (non-blocking). Returns True if input waiting."""
    try:
        import select
        return bool(select.select([sys.stdin], [], [], 0)[0])
    except Exception:
        return False


def typewriter(text: str, delay: float = 0.03, style: str = ""):
    """
    Print text with a typewriter effect.
    Press Enter during animation to instantly finish the current text.
    """
    skipping = False
    for char in text:
        sys.stdout.write(f"{style}{char}{Color.RESET}")
        sys.stdout.flush()
        if not skipping:
            if _check_skip():
                # User pressed a key — dump the rest instantly
                skipping = True
                # Consume the keypress so it doesn't bleed into the next prompt
                try:
                    sys.stdin.readline()
                except Exception:
                    pass
                continue
            if char in ".!?":
                time.sleep(delay * 4)
            elif char == ",":
                time.sleep(delay * 2)
            elif char == "\n":
                time.sleep(delay * 3)
            else:
                time.sleep(delay)
    print()


def slow_print(text: str, delay: float = 0.02, style: str = ""):
    """
    Print text word by word for dramatic pacing.
    Press Enter to instantly finish the current text.
    """
    words = text.split(" ")
    skipping = False
    for i, word in enumerate(words):
        sys.stdout.write(f"{style}{word}{Color.RESET}")
        if i < len(words) - 1:
            sys.stdout.write(" ")
        sys.stdout.flush()
        if not skipping:
            if _check_skip():
                skipping = True
                try:
                    sys.stdin.readline()
                except Exception:
                    pass
                continue
            time.sleep(delay)
    print()


def print_styled(text: str, *styles: str):
    """Print a line with ANSI styling."""
    print(styled(text, *styles))


def print_blank(count: int = 1):
    """Print blank lines."""
    for _ in range(count):
        print()


# ── Box Drawing / Panels ──────────────────────────────────

# Box-drawing characters
BOX_TL = "╔"
BOX_TR = "╗"
BOX_BL = "╚"
BOX_BR = "╝"
BOX_H = "═"
BOX_V = "║"
BOX_LT = "╠"
BOX_RT = "╣"

THIN_TL = "┌"
THIN_TR = "┐"
THIN_BL = "└"
THIN_BR = "┘"
THIN_H = "─"
THIN_V = "│"
THIN_LT = "├"
THIN_RT = "┤"


def panel(text: str, title: str = "", width: int = 0,
          border_color: str = Color.GRAY, title_color: str = Color.BRIGHT_WHITE,
          text_color: str = "", padding: int = 1) -> str:
    """
    Create a bordered panel with optional title.
    Returns the panel as a string.
    """
    if width == 0:
        width = min(get_terminal_width() - 2, 76)

    inner_width = width - 2  # subtract border chars
    lines = []

    # Word-wrap the text
    wrapped = _word_wrap(text, inner_width - (padding * 2))

    # Top border
    if title:
        title_display = f" {title} "
        remaining = inner_width - len(title_display)
        left_bar = BOX_H * 2
        right_bar = BOX_H * (remaining - 2)
        lines.append(f"{border_color}{BOX_TL}{left_bar}{title_color}{title_display}{border_color}{right_bar}{BOX_TR}{Color.RESET}")
    else:
        lines.append(f"{border_color}{BOX_TL}{BOX_H * inner_width}{BOX_TR}{Color.RESET}")

    # Content lines
    pad = " " * padding
    for line in wrapped:
        content = f"{pad}{line}"
        visible_len = len(line) + padding
        right_pad = inner_width - visible_len - padding
        if right_pad < 0:
            right_pad = 0
        lines.append(f"{border_color}{BOX_V}{Color.RESET}{text_color}{content}{' ' * (right_pad + padding)}{Color.RESET}{border_color}{BOX_V}{Color.RESET}")

    # Bottom border
    lines.append(f"{border_color}{BOX_BL}{BOX_H * inner_width}{BOX_BR}{Color.RESET}")

    return "\n".join(lines)


def divider(char: str = "─", width: int = 0, color: str = Color.GRAY) -> str:
    """Create a horizontal divider."""
    if width == 0:
        width = min(get_terminal_width() - 2, 76)
    return f"{color}{char * width}{Color.RESET}"


def progress_bar(current: int, maximum: int, width: int = 20,
                 fill_color: str = Color.GREEN, empty_color: str = Color.GRAY,
                 label: str = "") -> str:
    """Create a text-based progress bar."""
    if maximum <= 0:
        ratio = 0
    else:
        ratio = max(0, min(1, current / maximum))
    filled = int(width * ratio)
    empty = width - filled

    bar = f"{fill_color}{'█' * filled}{empty_color}{'░' * empty}{Color.RESET}"

    if label:
        return f"{label} {bar} {current}/{maximum}"
    return f"{bar} {current}/{maximum}"


# ── Tables ─────────────────────────────────────────────────

def simple_table(headers: list[str], rows: list[list[str]],
                 header_color: str = Color.BOLD + Color.BRIGHT_WHITE,
                 border_color: str = Color.GRAY,
                 col_widths: list[int] | None = None) -> str:
    """Create a simple bordered table."""
    if not col_widths:
        # Auto-calculate widths
        col_widths = []
        for i, h in enumerate(headers):
            max_w = len(h)
            for row in rows:
                if i < len(row):
                    max_w = max(max_w, len(row[i]))
            col_widths.append(max_w + 2)

    lines = []
    total_width = sum(col_widths) + len(col_widths) + 1

    # Top border
    top = THIN_TL
    for i, w in enumerate(col_widths):
        top += THIN_H * w
        top += THIN_TR if i == len(col_widths) - 1 else "┬"
    lines.append(f"{border_color}{top}{Color.RESET}")

    # Header row
    hdr = THIN_V
    for i, h in enumerate(headers):
        hdr += f"{Color.RESET}{header_color} {h:<{col_widths[i]-1}}{Color.RESET}{border_color}{THIN_V}"
    lines.append(f"{border_color}{hdr}{Color.RESET}")

    # Header separator
    sep = THIN_LT
    for i, w in enumerate(col_widths):
        sep += THIN_H * w
        sep += THIN_RT if i == len(col_widths) - 1 else "┼"
    lines.append(f"{border_color}{sep}{Color.RESET}")

    # Data rows
    for row in rows:
        r = THIN_V
        for i, w in enumerate(col_widths):
            val = row[i] if i < len(row) else ""
            r += f"{Color.RESET} {val:<{w-1}}{border_color}{THIN_V}"
        lines.append(f"{border_color}{r}{Color.RESET}")

    # Bottom border
    bot = THIN_BL
    for i, w in enumerate(col_widths):
        bot += THIN_H * w
        bot += THIN_BR if i == len(col_widths) - 1 else "┴"
    lines.append(f"{border_color}{bot}{Color.RESET}")

    return "\n".join(lines)


# ── Internal helpers ───────────────────────────────────────

def _word_wrap(text: str, width: int) -> list[str]:
    """Simple word-wrap that respects newlines."""
    result = []
    for paragraph in text.split("\n"):
        if not paragraph:
            result.append("")
            continue
        words = paragraph.split(" ")
        current_line = ""
        for word in words:
            if current_line and len(current_line) + 1 + len(word) > width:
                result.append(current_line)
                current_line = word
            else:
                current_line = f"{current_line} {word}" if current_line else word
        if current_line:
            result.append(current_line)
    return result if result else [""]

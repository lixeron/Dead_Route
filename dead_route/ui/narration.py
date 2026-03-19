"""
Narration system: cinematic text crawls, dramatic text, atmospheric writing.
"""

import time
import sys
from ui.style import (
    Color, Theme, styled, typewriter, slow_print,
    print_styled, print_blank, clear_screen, panel, divider,
    get_terminal_width
)


def dramatic_pause(seconds: float = 1.5):
    time.sleep(seconds)


def crawl_text(lines: list[str], delay_per_line: float = 0.04,
               pause_between: float = 0.8, style: str = ""):
    for line in lines:
        if line == "":
            print()
            time.sleep(pause_between * 0.5)
            continue
        typewriter(line, delay=delay_per_line, style=style)
        time.sleep(pause_between)


def narrator_text(text: str, pause_after: float = 0.5):
    width = min(get_terminal_width() - 4, 72)
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        lines.append(current)

    for line in lines:
        slow_print(line, delay=0.02, style=Theme.NARRATOR)
    if pause_after:
        time.sleep(pause_after)


def dialogue(speaker: str, text: str, speaker_color: str = Theme.NPC_NAME):
    print()
    print(f"  {speaker_color}{speaker}:{Color.RESET}")
    width = min(get_terminal_width() - 8, 68)
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        lines.append(current)

    for i, line in enumerate(lines):
        prefix = '    "' if i == 0 else "     "
        suffix = '"' if i == len(lines) - 1 else ""
        typewriter(f"{prefix}{line}{suffix}", delay=0.025, style=Theme.DIALOGUE)
    time.sleep(0.3)


def scene_break(label: str = "", style: str = Theme.MUTED):
    print()
    width = min(get_terminal_width() - 4, 72)
    if label:
        padding = (width - len(label) - 2) // 2
        line = f"{'─' * padding} {label} {'─' * padding}"
        print_styled(line, style)
    else:
        print(divider(width=width))
    print()
    time.sleep(0.5)


def title_card(title: str, subtitle: str = ""):
    clear_screen()
    print_blank(3)
    width = min(get_terminal_width() - 4, 72)
    padding = (width - len(title)) // 2
    print(f"{' ' * padding}{Theme.TITLE}{Color.BOLD}{title}{Color.RESET}")
    if subtitle:
        sub_padding = (width - len(subtitle)) // 2
        print_blank(1)
        print(f"{' ' * sub_padding}{Theme.SUBTITLE}{Color.ITALIC}{subtitle}{Color.RESET}")
    print_blank(1)
    print(f"{Theme.MUTED}{'═' * width}{Color.RESET}")
    print_blank(2)
    time.sleep(1.0)


def reveal_text(text: str, style: str = Color.BRIGHT_WHITE, final_pause: float = 1.0):
    print()
    width = min(get_terminal_width() - 4, 72)
    padding = max(0, (width - len(text)) // 2)
    sys.stdout.write(f"{' ' * padding}")
    typewriter(text, delay=0.05, style=style)
    time.sleep(final_pause)


def status_update(text: str, style: str = Theme.INFO):
    print(f"\n  {style}» {text}{Color.RESET}")
    time.sleep(0.3)


def loot_display(items: dict):
    if not items:
        return
    resource_styles = {
        "fuel": (Theme.FUEL, "Fuel"),
        "food": (Theme.FOOD, "Food"),
        "scrap": (Theme.SCRAP, "Scrap"),
        "ammo": (Theme.AMMO, "Ammo"),
        "medicine": (Theme.MEDICINE, "Medicine"),
    }
    print()
    print_styled("  +-- Found -----------------+", Theme.SUCCESS)
    for key, amount in items.items():
        if amount > 0 and key in resource_styles:
            style, label = resource_styles[key]
            print(f"  {Theme.SUCCESS}|{Color.RESET}  {style}+{amount} {label}{Color.RESET}")
    print_styled("  +-------------------------+", Theme.SUCCESS)
    print()


def damage_display(entity: str, amount: int):
    print(f"\n  {Theme.DAMAGE}x {entity} takes {amount} damage{Color.RESET}")
    time.sleep(0.3)

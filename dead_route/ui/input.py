"""
Player input handling: choice menus, text prompts, confirmations.
All user input flows through this module.
"""

import sys
from ui.style import (
    Color, Theme, styled, print_styled, print_blank,
    divider, panel
)


def get_text_input(prompt: str, style: str = Theme.CHOICE) -> str:
    """Get free-text input from the player."""
    print()
    sys.stdout.write(f"{style}{prompt}{Color.RESET} ")
    sys.stdout.flush()
    try:
        result = input().strip()
    except (EOFError, KeyboardInterrupt):
        print()
        result = ""
    return result


def get_choice(options: list[str], prompt: str = "What do you do?",
               prompt_style: str = Theme.CHOICE,
               option_style: str = "",
               show_numbers: bool = True) -> int:
    """
    Present numbered choices and get player selection.
    Returns 0-based index of the chosen option.
    """
    print()
    print_styled(prompt, prompt_style)
    print()

    for i, option in enumerate(options):
        num_display = styled(f"  [{i + 1}]", Theme.CHOICE)
        print(f"{num_display} {option_style}{option}{Color.RESET}")

    print()
    while True:
        sys.stdout.write(f"{Theme.MUTED}> {Color.RESET}")
        sys.stdout.flush()
        try:
            raw = input().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            continue

        try:
            choice = int(raw)
            if 1 <= choice <= len(options):
                return choice - 1
        except ValueError:
            pass

        print_styled(f"  Enter a number between 1 and {len(options)}.", Theme.WARNING)


def get_choice_with_details(options: list[dict], prompt: str = "What do you do?") -> int:
    """
    Present choices with descriptions.
    Each option: {"label": str, "description": str (optional)}
    Returns 0-based index.
    """
    print()
    print_styled(prompt, Theme.CHOICE)
    print()

    for i, opt in enumerate(options):
        num_display = styled(f"  [{i + 1}]", Theme.CHOICE)
        label = styled(opt["label"], Color.BRIGHT_WHITE)
        print(f"{num_display} {label}")
        if opt.get("description"):
            print(f"       {Theme.MUTED}{opt['description']}{Color.RESET}")

    print()
    while True:
        sys.stdout.write(f"{Theme.MUTED}> {Color.RESET}")
        sys.stdout.flush()
        try:
            raw = input().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            continue

        try:
            choice = int(raw)
            if 1 <= choice <= len(options):
                return choice - 1
        except ValueError:
            pass

        print_styled(f"  Enter a number between 1 and {len(options)}.", Theme.WARNING)


def confirm(prompt: str = "Continue?", default_yes: bool = True) -> bool:
    """Yes/No confirmation prompt."""
    hint = "(Y/n)" if default_yes else "(y/N)"
    sys.stdout.write(f"\n{Theme.MUTED}{prompt} {hint} {Color.RESET}")
    sys.stdout.flush()
    try:
        raw = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return default_yes

    if not raw:
        return default_yes
    return raw in ("y", "yes")


def press_enter(prompt: str = "Press Enter to continue..."):
    """Wait for the player to press Enter."""
    print()
    sys.stdout.write(f"{Theme.MUTED}{prompt}{Color.RESET}")
    sys.stdout.flush()
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        print()

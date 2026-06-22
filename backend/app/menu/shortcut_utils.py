"""shortcut_utils — Pure-Python macOS global shortcut helpers.

Provides shortcut string parsing and display formatting for the
snackbar menu global hotkey registration. Kept as a separate module
so the logic is testable without AppKit or PyObjC.

Shortcut string format: modifier tokens joined by '+', e.g.
  "ctrl+cmd+v"     -> ⌃⌘V
  "cmd+shift+v"    -> ⌘⇧V
  "ctrl+opt+c"     -> ⌃⌥C

Supported modifier tokens: cmd/command, ctrl/control,
  shift, opt/alt/option.
Key tokens: any single letter a-z, or digits/symbols
  matching the macOS US keyboard layout key codes below.
"""
from __future__ import annotations

# macOS virtual key codes (US QWERTY layout)
SHORTCUT_KEY_CODES: dict[str, int] = {
    "a": 0,  "s": 1,  "d": 2,  "f": 3,  "h": 4,  "g": 5,
    "z": 6,  "x": 7,  "c": 8,  "v": 9,  "b": 11, "q": 12,
    "w": 13, "e": 14, "r": 15, "y": 16, "t": 17,
    "1": 18, "2": 19, "3": 20, "4": 21, "6": 22, "5": 23,
    "=": 24, "9": 25, "7": 26, "-": 27, "8": 28, "0": 29,
    "]": 30, "o": 31, "u": 32, "[": 33, "i": 34, "p": 35,
    "l": 37, "j": 38, "'": 39, "k": 40, ";": 41,
    "\\": 42, ",": 43, "/": 44, "n": 45, "m": 46, ".": 47,
}

# macOS NSEventModifierFlag values (avoids importing AppKit in tests)
MOD_COMMAND: int = 1 << 20   # NSEventModifierFlagCommand
MOD_SHIFT: int = 1 << 17     # NSEventModifierFlagShift
MOD_CONTROL: int = 1 << 18   # NSEventModifierFlagControl
MOD_OPTION: int = 1 << 19    # NSEventModifierFlagOption

# Combined mask for comparing against NSEvent.modifierFlags()
MOD_ALL: int = MOD_COMMAND | MOD_SHIFT | MOD_CONTROL | MOD_OPTION

_MODIFIER_MAP: dict[str, int] = {
    "cmd": MOD_COMMAND,
    "command": MOD_COMMAND,
    "shift": MOD_SHIFT,
    "ctrl": MOD_CONTROL,
    "control": MOD_CONTROL,
    "opt": MOD_OPTION,
    "alt": MOD_OPTION,
    "option": MOD_OPTION,
}

_MODIFIER_SYMBOLS: dict[str, str] = {
    "ctrl": "⌃", "control": "⌃",
    "opt": "⌥", "alt": "⌥", "option": "⌥",
    "shift": "⇧",
    "cmd": "⌘", "command": "⌘",
}

# Canonical display order for modifier symbols
_SYMBOL_ORDER = ("⌃", "⌥", "⇧", "⌘")


def parse_shortcut(
    shortcut: str,
) -> tuple[int, int] | None:
    """Parse a shortcut string into (modifier_mask, key_code).

    Returns None if the string is invalid or missing a key or modifier.
    """
    parts = [p.strip() for p in shortcut.lower().split("+")]
    mods = 0
    key: int | None = None
    for part in parts:
        if part in _MODIFIER_MAP:
            mods |= _MODIFIER_MAP[part]
        elif part in SHORTCUT_KEY_CODES:
            key = SHORTCUT_KEY_CODES[part]
        else:
            return None
    if key is None or mods == 0:
        return None
    return mods, key


def shortcut_display(shortcut: str) -> str:
    """Convert a shortcut string to a human-readable symbol form.

    Example: "ctrl+cmd+v" -> "⌃⌘V"
    Returns the original string as-is if it cannot be parsed.
    """
    parts = [p.strip() for p in shortcut.lower().split("+")]
    symbols: list[str] = []
    key_char = ""
    for part in parts:
        if part in _MODIFIER_SYMBOLS:
            symbols.append(_MODIFIER_SYMBOLS[part])
        elif part in SHORTCUT_KEY_CODES:
            key_char = part.upper()
        else:
            return shortcut
    if not key_char:
        return shortcut
    ordered = [s for s in _SYMBOL_ORDER if s in symbols]
    return "".join(ordered) + key_char

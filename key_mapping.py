"""Direction-to-key mappings used when executing stratagem sequences."""

DEFAULT_DIRECTION_KEY_LAYOUT = "arrow_keys"

DIRECTION_KEY_LAYOUTS = {
    "arrow_keys": {
        "UP": "KEY_UP",
        "DOWN": "KEY_DOWN",
        "LEFT": "KEY_LEFT",
        "RIGHT": "KEY_RIGHT",
    },
    "wasd": {
        "UP": "KEY_W",
        "DOWN": "KEY_S",
        "LEFT": "KEY_A",
        "RIGHT": "KEY_D",
    },
}


def normalize_direction_key_layout(layout: str) -> str:
    """Return a supported layout, falling back for missing or stale settings."""
    if layout in DIRECTION_KEY_LAYOUTS:
        return layout
    return DEFAULT_DIRECTION_KEY_LAYOUT


def get_direction_key(direction: str, layout: str) -> str:
    """Return the evdev key name for a direction in the selected layout."""
    normalized_layout = normalize_direction_key_layout(layout)
    try:
        return DIRECTION_KEY_LAYOUTS[normalized_layout][direction]
    except KeyError as error:
        raise ValueError(f"Unsupported stratagem direction: {direction!r}") from error

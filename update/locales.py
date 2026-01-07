"""
Locale file generation for the Helldivers 2 StreamController plugin.

Generates en_US.json with stratagem names and smart label strings.
"""

import json
from pathlib import Path

from .config import DISPLAY_NAMES, LOCALE_EN_US
from .scraper import load_stratagems


def split_into_labels(name: str, max_label_length: int = 12) -> dict[str, str]:
    """
    Split a stratagem name into top, center, and bottom labels.
    
    Strategy:
    - Single word: bottom only
    - Two words: center + bottom
    - Three+ words: top + center + bottom
    
    Args:
        name: The full display name of the stratagem
        max_label_length: Maximum characters per label
        
    Returns:
        Dict with 'top', 'center', 'bottom' keys
    """
    # Handle quoted names (like "Guard Dog")
    # Keep quotes together with the following word
    words = name.split()
    
    # Merge quoted words
    merged_words = []
    i = 0
    while i < len(words):
        word = words[i]
        if word.startswith('"') and not word.endswith('"'):
            # Find the closing quote
            quoted = [word]
            i += 1
            while i < len(words) and not words[i].endswith('"'):
                quoted.append(words[i])
                i += 1
            if i < len(words):
                quoted.append(words[i])
            merged_words.append(' '.join(quoted))
        else:
            merged_words.append(word)
        i += 1
    
    words = merged_words
    
    if len(words) == 1:
        # Single word: just bottom
        return {"top": "", "center": "", "bottom": words[0]}
    
    elif len(words) == 2:
        # Two words: center + bottom
        return {"top": "", "center": words[0], "bottom": words[1]}
    
    elif len(words) == 3:
        # Three words: top + center + bottom
        return {"top": words[0], "center": words[1], "bottom": words[2]}
    
    else:
        # 4+ words: need to combine some
        # Try: first word | middle words | last word
        # Or: first two | middle | last
        
        # Common patterns:
        # "Orbital 120MM HE Barrage" -> "Orbital" | "120MM" | "HE Barrage"
        # "Eagle Napalm Airstrike" -> "Eagle" | "Napalm" | "Airstrike"
        
        top = words[0]
        bottom = words[-1]
        center = ' '.join(words[1:-1])
        
        # If center is too long, try alternative splits
        if len(center) > max_label_length:
            # Try: first word | second word | rest
            center = words[1]
            bottom = ' '.join(words[2:])
            
            if len(bottom) > max_label_length:
                # Last resort: abbreviate or truncate
                bottom = bottom[:max_label_length]
        
        return {"top": top, "center": center, "bottom": bottom}


def generate_locale_entries(keys: list[str] = None) -> dict:
    """
    Generate locale entries for all stratagems.
    
    Args:
        keys: Optional list of stratagem keys. If None, uses all from stratagems.json.
        
    Returns:
        Dict ready to be serialized as JSON
    """
    if keys is None:
        stratagems = load_stratagems()
        keys = list(stratagems.keys())
    
    locale = {
        "plugin.name": "HELLDIVERS 2",
        "actions.StratagemHeroToggle.name": "Stratagem Hero Toggle",
        "actions.StratagemHeroToggle.labels.top": "",
        "actions.StratagemHeroToggle.labels.center": "Stratagem",
        "actions.StratagemHeroToggle.labels.bottom": "Hero",
    }
    
    for key in sorted(keys):
        display_name = DISPLAY_NAMES.get(key, key)
        labels = split_into_labels(display_name)
        
        locale[f"actions.{key}.name"] = display_name
        locale[f"actions.{key}.labels.top"] = labels["top"]
        locale[f"actions.{key}.labels.center"] = labels["center"]
        locale[f"actions.{key}.labels.bottom"] = labels["bottom"]
    
    return locale


def write_locale_file(
    output_path: Path = LOCALE_EN_US,
    keys: list[str] = None,
    dry_run: bool = False,
) -> bool:
    """
    Generate and write the locale file.
    
    Args:
        output_path: Path to write the locale file
        keys: Optional list of stratagem keys
        dry_run: If True, print but don't write
        
    Returns:
        True if successful
    """
    locale = generate_locale_entries(keys)
    
    if dry_run:
        print(f"Would write {len(locale)} entries to {output_path}")
        print("\nSample entries:")
        for i, (k, v) in enumerate(locale.items()):
            if i >= 20:
                print("  ...")
                break
            print(f"  {k}: {v}")
        return True
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(locale, f, indent=2, ensure_ascii=False)
        f.write('\n')
    
    print(f"Wrote {len(locale)} locale entries to {output_path}")
    return True


def merge_with_existing(
    existing_path: Path = LOCALE_EN_US,
    output_path: Path = None,
    dry_run: bool = False,
) -> bool:
    """
    Merge generated locale entries with an existing locale file.
    
    Preserves custom entries that are not auto-generated.
    
    Args:
        existing_path: Path to existing locale file
        output_path: Path to write merged file (defaults to existing_path)
        dry_run: If True, print but don't write
        
    Returns:
        True if successful
    """
    if output_path is None:
        output_path = existing_path
    
    # Load existing
    existing = {}
    if existing_path.exists():
        with open(existing_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    
    # Generate new entries
    generated = generate_locale_entries()
    
    # Merge: generated entries take precedence, but preserve custom entries
    merged = {}
    
    # First add all generated entries
    merged.update(generated)
    
    # Then add any existing entries that aren't in generated
    for key, value in existing.items():
        if key not in merged:
            merged[key] = value
    
    if dry_run:
        new_keys = set(generated.keys()) - set(existing.keys())
        removed_keys = set(existing.keys()) - set(merged.keys())
        print(f"Merge summary:")
        print(f"  New entries: {len(new_keys)}")
        print(f"  Preserved custom entries: {len(set(existing.keys()) - set(generated.keys()))}")
        if new_keys:
            print(f"\nNew entries:")
            for k in sorted(list(new_keys))[:10]:
                print(f"  {k}")
            if len(new_keys) > 10:
                print(f"  ... and {len(new_keys) - 10} more")
        return True
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
        f.write('\n')
    
    print(f"Wrote {len(merged)} locale entries to {output_path}")
    return True


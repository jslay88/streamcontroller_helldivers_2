"""
Stratagem data management for the Helldivers 2 StreamController plugin.

Stratagems are scraped from the wiki and stored in stratagems.json.
"""

import json
from pathlib import Path

from .config import STRATAGEMS_JSON
from .scraper import load_stratagems, scrape_and_save


def generate_stratagems_json(
    output_path: Path = STRATAGEMS_JSON,
    from_wiki: bool = True,
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """
    Generate the stratagems.json file by scraping the wiki.
    
    Args:
        output_path: Path to write the stratagems file
        from_wiki: If True, scrape from wiki. If False, just validate existing.
        dry_run: If True, print but don't write
        verbose: If True, print detailed output
        
    Returns:
        True if successful
    """
    if from_wiki:
        stratagems = scrape_and_save(
            output_path=output_path,
            merge=True,
            dry_run=dry_run,
            verbose=verbose,
        )
        return len(stratagems) > 0
    else:
        # Just load and display existing
        stratagems = load_stratagems(output_path)
        if dry_run:
            print(f"Existing stratagems in {output_path}: {len(stratagems)}")
            for i, (key, seq) in enumerate(sorted(stratagems.items())):
                if i >= 10:
                    print("  ...")
                    break
                print(f"  {key}: {seq}")
        return len(stratagems) > 0


def validate_sequences(path: Path = STRATAGEMS_JSON) -> list[str]:
    """
    Validate that all stratagem sequences use valid directions.
    
    Returns:
        List of validation error messages (empty if all valid)
    """
    valid_directions = {"UP", "DOWN", "LEFT", "RIGHT"}
    errors = []
    
    stratagems = load_stratagems(path)
    
    for key, sequence in stratagems.items():
        if not sequence:
            errors.append(f"{key}: Empty sequence")
            continue
        
        for i, direction in enumerate(sequence):
            if direction not in valid_directions:
                errors.append(f"{key}[{i}]: Invalid direction '{direction}'")
    
    return errors


def get_sequence(key: str, path: Path = STRATAGEMS_JSON) -> list[str] | None:
    """
    Get the key sequence for a stratagem.
    
    Args:
        key: The stratagem internal key
        path: Path to the stratagems JSON file
        
    Returns:
        List of direction strings, or None if not found
    """
    stratagems = load_stratagems(path)
    return stratagems.get(key)


def list_stratagems(path: Path = STRATAGEMS_JSON) -> list[str]:
    """
    Get a list of all available stratagem keys.
    
    Returns:
        Sorted list of stratagem keys
    """
    stratagems = load_stratagems(path)
    return sorted(stratagems.keys())


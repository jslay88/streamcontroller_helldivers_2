#!/usr/bin/env python3
"""
Test page generator for Helldivers 2 StreamController plugin.

Generates StreamController pages containing all stratagems for testing.
Each page has navigation buttons to switch between pages.
"""

import json
import math
from pathlib import Path
from typing import Any

from .config import PLUGIN_DIR, STRATAGEM_MAPPINGS


# Stream Deck layout configuration
# Standard Stream Deck has 5 columns x 3 rows = 15 keys
DECK_COLUMNS = 5
DECK_ROWS = 3
TOTAL_KEYS = DECK_COLUMNS * DECK_ROWS

# Reserve positions for navigation (bottom row, left and right corners)
NAV_PREV_POS = (0, DECK_ROWS - 1)  # 0x2 - bottom left
NAV_NEXT_POS = (DECK_COLUMNS - 1, DECK_ROWS - 1)  # 4x2 - bottom right

# Keys available for stratagems per page (total minus navigation)
KEYS_PER_PAGE = TOTAL_KEYS - 2  # 13 stratagems per page

# Default pages output directory
PAGES_DIR = Path(PLUGIN_DIR).parent.parent / "pages"

# Page name prefix
PAGE_PREFIX = "HD2 Test"


def create_key_action(action_id: str, settings: dict = None) -> dict:
    """Create a key action configuration."""
    return {
        "states": {
            "0": {
                "actions": [
                    {
                        "id": action_id,
                        "settings": settings or {}
                    }
                ],
                "image-control-action": 0,
                "label-control-actions": [0, 0, 0],
                "background-control-action": 0
            }
        }
    }


def create_page_switch_action(page_path: str) -> dict:
    """Create a page switch action configuration."""
    return {
        "states": {
            "0": {
                "actions": [
                    {
                        "id": "com_core447_DeckPlugin::ChangePage",
                        "settings": {
                            "selected_page": page_path
                        }
                    }
                ],
                "image-control-action": 0,
                "label-control-actions": [0, 0, 0],
                "background-control-action": 0
            }
        }
    }


def create_empty_key() -> dict:
    """Create an empty key configuration."""
    return {
        "states": {
            "0": {
                "actions": [],
                "image-control-action": 0,
                "label-control-actions": [0, 0, 0],
                "background-control-action": 0
            }
        }
    }


def pos_to_key(col: int, row: int) -> str:
    """Convert column, row position to key string."""
    return f"{col}x{row}"


def get_available_positions() -> list[tuple[int, int]]:
    """Get list of positions available for stratagems (excluding nav buttons)."""
    positions = []
    for row in range(DECK_ROWS):
        for col in range(DECK_COLUMNS):
            pos = (col, row)
            # Skip navigation positions
            if pos not in (NAV_PREV_POS, NAV_NEXT_POS):
                positions.append(pos)
    return positions


def generate_page(
    page_name: str,
    stratagems: list[str],
    prev_page: str | None,
    next_page: str | None,
    include_hero_toggle: bool = False,
) -> dict:
    """
    Generate a single page configuration.
    
    Args:
        page_name: Name of this page
        stratagems: List of stratagem keys to include
        prev_page: Path to previous page (None if first page)
        next_page: Path to next page (None if last page)
        include_hero_toggle: Include the Hero mode toggle button
    
    Returns:
        Page configuration dictionary
    """
    page = {
        "brightness": {"value": 75},
        "keys": {}
    }
    
    available_positions = get_available_positions()
    
    # Add stratagems
    for i, stratagem_key in enumerate(stratagems):
        if i >= len(available_positions):
            break
        
        col, row = available_positions[i]
        key_pos = pos_to_key(col, row)
        action_id = f"net_jslay_helldivers_2::{stratagem_key}"
        page["keys"][key_pos] = create_key_action(action_id)
    
    # Add navigation buttons
    if prev_page:
        key_pos = pos_to_key(*NAV_PREV_POS)
        page["keys"][key_pos] = create_page_switch_action(prev_page)
    
    if next_page:
        key_pos = pos_to_key(*NAV_NEXT_POS)
        page["keys"][key_pos] = create_page_switch_action(next_page)
    
    return page


def generate_test_pages(
    output_dir: Path = None,
    page_prefix: str = PAGE_PREFIX,
    dry_run: bool = False,
    verbose: bool = False,
) -> list[Path]:
    """
    Generate test pages containing all stratagems.
    
    Args:
        output_dir: Directory to write pages to
        page_prefix: Prefix for page file names
        dry_run: If True, don't write files
        verbose: Print detailed progress
    
    Returns:
        List of generated page paths
    """
    output_dir = output_dir or PAGES_DIR
    output_dir = Path(output_dir)
    
    # Get all stratagem keys sorted alphabetically
    stratagem_keys = sorted(STRATAGEM_MAPPINGS.keys())
    total_stratagems = len(stratagem_keys)
    
    # Calculate number of pages needed
    # First page has hero toggle, so one less stratagem
    first_page_stratagems = KEYS_PER_PAGE - 1
    other_page_stratagems = KEYS_PER_PAGE
    
    if total_stratagems <= first_page_stratagems:
        num_pages = 1
    else:
        remaining = total_stratagems - first_page_stratagems
        num_pages = 1 + math.ceil(remaining / other_page_stratagems)
    
    print(f"Generating {num_pages} test pages for {total_stratagems} stratagems...")
    
    # Generate page file names and relative paths for navigation
    page_files = []  # Actual file paths for writing
    page_refs = []   # Relative paths for page navigation (./data/pages/...)
    for i in range(num_pages):
        page_name = f"{page_prefix} {i + 1}"
        page_files.append(output_dir / f"{page_name}.json")
        # Use relative path format for StreamController
        page_refs.append(f"./data/pages/{page_name}.json")
    
    # Split stratagems across pages
    pages_data = []
    offset = 0
    
    for page_idx in range(num_pages):
        if page_idx == 0:
            # First page: include hero toggle, fewer stratagems
            count = first_page_stratagems
        else:
            count = other_page_stratagems
        
        page_stratagems = stratagem_keys[offset:offset + count]
        offset += count
        
        # Determine navigation using relative paths
        prev_page = page_refs[page_idx - 1] if page_idx > 0 else None
        next_page = page_refs[page_idx + 1] if page_idx < num_pages - 1 else None
        
        # For circular navigation, connect last to first
        if page_idx == 0 and num_pages > 1:
            prev_page = page_refs[-1]
        if page_idx == num_pages - 1 and num_pages > 1:
            next_page = page_refs[0]
        
        page_name = f"{page_prefix} {page_idx + 1}"
        page_data = generate_page(
            page_name=page_name,
            stratagems=page_stratagems,
            prev_page=prev_page,
            next_page=next_page,
            include_hero_toggle=(page_idx == 0),
        )
        
        # Add hero toggle on first page
        if page_idx == 0:
            # Put it in the first available position after nav buttons
            # Use position 1x2 (middle bottom, next to prev nav)
            hero_pos = pos_to_key(1, DECK_ROWS - 1)
            page_data["keys"][hero_pos] = create_key_action(
                "net_jslay_helldivers_2::StratagemHeroToggle"
            )
        
        pages_data.append((page_files[page_idx], page_data, page_stratagems))
    
    # Write pages
    generated = []
    for page_path, page_data, stratagems in pages_data:
        if verbose:
            print(f"  {page_path.name}: {len(stratagems)} stratagems")
        
        if not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(page_path, "w") as f:
                json.dump(page_data, f, indent=4)
        
        generated.append(page_path)
    
    action = "Would generate" if dry_run else "Generated"
    print(f"{action} {len(generated)} pages in {output_dir}")
    
    return generated


def list_generated_pages(output_dir: Path = None, page_prefix: str = PAGE_PREFIX) -> list[Path]:
    """List existing test pages."""
    output_dir = output_dir or PAGES_DIR
    output_dir = Path(output_dir)
    
    if not output_dir.exists():
        return []
    
    return sorted(output_dir.glob(f"{page_prefix}*.json"))


def clean_test_pages(
    output_dir: Path = None,
    page_prefix: str = PAGE_PREFIX,
    dry_run: bool = False,
) -> int:
    """
    Remove generated test pages.
    
    Returns:
        Number of pages removed
    """
    pages = list_generated_pages(output_dir, page_prefix)
    
    if not pages:
        print("No test pages found to remove.")
        return 0
    
    for page_path in pages:
        if not dry_run:
            page_path.unlink()
        print(f"  {'Would remove' if dry_run else 'Removed'}: {page_path.name}")
    
    return len(pages)


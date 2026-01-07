"""
Scrape stratagem data from the Helldivers 2 wiki.

Fetches stratagem names and arrow codes from wiki.gg.
"""

import json
import re
import subprocess
from pathlib import Path

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

from .config import WIKI_TO_KEY_MAPPINGS, LEGACY_KEYS, STRATAGEMS_JSON


# Wiki URL
STRATAGEMS_PAGE = "https://helldivers.wiki.gg/wiki/Stratagems"


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    if not HAS_BS4:
        print("Required packages not found. Install them with:")
        print("  pip install beautifulsoup4")
        return False
    return True


def fetch_page(url: str) -> str:
    """Fetch a page using curl to avoid bot detection."""
    result = subprocess.run(
        ['curl', '-s', '--compressed', 
         '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
         '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
         '-H', 'Accept-Language: en-US,en;q=0.5',
         url],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed: {result.stderr}")
    return result.stdout


def normalize_wiki_name(name: str) -> str:
    """
    Normalize a wiki stratagem name for matching.
    
    E.g., "MG-43 Machine Gun" -> "Machine Gun"
    """
    # Remove model numbers at the start like "MG-43", "APW-1", "EAT-17", etc.
    name = re.sub(r'^([A-Z]{1,3}/)?[A-Z]{1,4}-?\d+[A-Z]?\s+', '', name, flags=re.IGNORECASE)
    return name.strip()


def wiki_name_to_key(wiki_name: str) -> str:
    """
    Convert a wiki stratagem name to an internal key.
    
    Uses WIKI_TO_KEY_MAPPINGS first, then generates a key from the name.
    """
    # First, try direct lookup in wiki mappings
    if wiki_name in WIKI_TO_KEY_MAPPINGS:
        return WIKI_TO_KEY_MAPPINGS[wiki_name]
    
    # Try with normalized name (model numbers removed)
    normalized = normalize_wiki_name(wiki_name)
    if normalized in WIKI_TO_KEY_MAPPINGS:
        return WIKI_TO_KEY_MAPPINGS[normalized]
    
    # Generate key from name: remove model numbers, special chars, make PascalCase
    # Remove quoted nicknames like "Guard Dog"
    clean_name = re.sub(r'"([^"]+)"', r'\1', normalized)
    
    # Remove special characters
    clean_name = clean_name.replace("-", "").replace("'", "").replace(".", "").replace("/", "")
    
    # Convert to PascalCase
    words = clean_name.split()
    return "".join(word.capitalize() for word in words)


def scrape_stratagems_raw(verbose: bool = False) -> dict[str, list[str]]:
    """
    Scrape all stratagem codes from the wiki, keeping original wiki names.
    
    Returns:
        Dict mapping original wiki name to arrow code list
    """
    if not check_dependencies():
        return {}
    
    print(f"Fetching stratagems from: {STRATAGEMS_PAGE}")
    html = fetch_page(STRATAGEMS_PAGE)
    
    soup = BeautifulSoup(html, 'html.parser')
    
    stratagems = {}
    
    # Find all tables with class 'wikitable'
    tables = soup.find_all('table', class_='wikitable')
    print(f"Found {len(tables)} stratagem tables")
    
    for table in tables:
        rows = table.find_all('tr')
        
        for row in rows[1:]:  # Skip header row
            cells = row.find_all(['td', 'th'])
            
            # Get stratagem name (usually in first cell with a link)
            wiki_name = ''
            for cell in cells:
                link = cell.find('a')
                if link:
                    text = link.get_text(strip=True)
                    # Skip very short names or navigation links
                    if text and len(text) > 2 and not text.startswith('['):
                        wiki_name = text
                        break
            
            if not wiki_name:
                continue
            
            # Skip non-stratagem entries
            skip_names = ['warbonds', 'helldivers', 'category', 'ship module', 'dlc']
            if any(skip in wiki_name.lower() for skip in skip_names):
                continue
            
            # Get arrows from all cells
            arrows = []
            for cell in cells:
                for img in cell.find_all('img'):
                    alt = img.get('alt', '')
                    if 'Arrow' in alt:
                        if 'Down' in alt:
                            arrows.append('DOWN')
                        elif 'Up' in alt:
                            arrows.append('UP')
                        elif 'Left' in alt:
                            arrows.append('LEFT')
                        elif 'Right' in alt:
                            arrows.append('RIGHT')
            
            # Valid stratagems have at least 3 arrows
            if arrows and len(arrows) >= 3:
                stratagems[wiki_name] = arrows
                if verbose:
                    print(f"  {wiki_name}: {' '.join(arrows)}")
    
    return stratagems


def scrape_stratagems(verbose: bool = False) -> dict[str, list[str]]:
    """
    Scrape all stratagem codes from the wiki.
    
    Returns:
        Dict mapping internal key to arrow code list
    """
    raw = scrape_stratagems_raw(verbose=verbose)
    
    stratagems = {}
    for wiki_name, arrows in raw.items():
        key = wiki_name_to_key(wiki_name)
        stratagems[key] = arrows
        if verbose:
            print(f"  {wiki_name} -> {key}")
    
    return stratagems


def scrape_and_save(
    output_path: Path = STRATAGEMS_JSON,
    merge: bool = True,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict[str, list[str]]:
    """
    Scrape stratagems from the wiki and save to JSON.
    
    Args:
        output_path: Path to save the JSON file
        merge: If True, merge with existing file
        dry_run: If True, don't write file
        verbose: If True, print detailed output
        
    Returns:
        Dict of scraped stratagems
    """
    stratagems = scrape_stratagems(verbose=verbose)
    
    print(f"\nScraped {len(stratagems)} stratagems from wiki")
    
    if not stratagems:
        print("No stratagems found! The wiki structure may have changed.")
        return {}
    
    # Merge with existing if requested
    if merge and output_path.exists():
        print(f"Merging with existing {output_path}")
        with open(output_path, 'r') as f:
            existing = json.load(f)
        # New data takes precedence
        existing.update(stratagems)
        stratagems = existing
    
    # Sort by name
    stratagems = dict(sorted(stratagems.items()))
    
    if dry_run:
        print(f"Dry run - would save {len(stratagems)} stratagems to {output_path}")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(stratagems, f, indent=2)
            f.write('\n')
        print(f"Saved {len(stratagems)} stratagems to {output_path}")
    
    return stratagems


def load_stratagems(path: Path = STRATAGEMS_JSON) -> dict[str, list[str]]:
    """
    Load stratagems from the JSON file.
    
    Args:
        path: Path to the stratagems JSON file
        
    Returns:
        Dict mapping key to arrow sequence, or empty dict if file doesn't exist
    """
    if not path.exists():
        return {}
    
    with open(path, 'r') as f:
        return json.load(f)


def get_all_keys(path: Path = STRATAGEMS_JSON) -> list[str]:
    """
    Get all stratagem keys from the JSON file.
    
    Returns:
        Sorted list of stratagem keys
    """
    stratagems = load_stratagems(path)
    return sorted(stratagems.keys())


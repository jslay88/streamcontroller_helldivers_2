"""
Scrape stratagem data from the Helldivers 2 wiki.

Fetches stratagem names and arrow codes from wiki.gg.
Uses the MediaWiki API (reliable) with HTML scraping as fallback when the
wiki HTML is behind Cloudflare and often returns a challenge page.
"""

import json
import re
import subprocess
import time
from pathlib import Path

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from .config import STRATAGEM_MAPPINGS, WIKI_TO_KEY_MAPPINGS, LEGACY_KEYS, STRATAGEMS_JSON


# Wiki URL (HTML – may be behind Cloudflare)
STRATAGEMS_PAGE = "https://helldivers.wiki.gg/wiki/Stratagems"
# MediaWiki API (same host but often not behind the same challenge)
WIKI_API_URL = "https://helldivers.wiki.gg/api.php"

# Retry config for HTML fallback
HTML_FETCH_RETRIES = 2
HTML_FETCH_RETRY_DELAY_SEC = 1.5


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


def fetch_parsed_html_via_api(title: str = "Stratagems") -> str | None:
    """
    Fetch rendered HTML via the MediaWiki parse API. This expands all
    templates (e.g. {{Stratagem Table}}) so we get the full page content
    even when the wiki restructures into transclusions. Also bypasses the
    Cloudflare challenge that blocks direct HTML fetches.
    """
    if not HAS_REQUESTS:
        return None
    params = {
        "action": "parse",
        "page": title,
        "prop": "text",
        "format": "json",
    }
    try:
        r = requests.get(
            WIKI_API_URL,
            params=params,
            headers={"User-Agent": "Helldivers2StreamController/1.0 (https://github.com/StreamController)"},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        return data.get("parse", {}).get("text", {}).get("*")
    except Exception:
        return None



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


def _extract_arrows_from_cells(cells) -> list[str]:
    """Extract arrow directions from table cells' <img> alt text.

    Handles both old format ("Arrow Down") and new format
    ("Stratagem Arrow Down.svg").
    """
    arrows = []
    for cell in cells:
        for img in cell.find_all('img'):
            alt = img.get('alt', '').lower()
            if 'arrow' not in alt:
                continue
            if 'down' in alt:
                arrows.append('DOWN')
            elif 'up' in alt:
                arrows.append('UP')
            elif 'left' in alt:
                arrows.append('LEFT')
            elif 'right' in alt:
                arrows.append('RIGHT')
    return arrows


def _scrape_stratagems_from_html(html: str, verbose: bool = False) -> dict[str, list[str]]:
    """Parse stratagems from full wiki HTML (used as fallback)."""
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table', class_='wikitable')
    stratagems = {}
    for table in tables:
        rows = table.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            wiki_name = ''
            for cell in cells:
                link = cell.find('a')
                if link:
                    text = link.get_text(strip=True)
                    if text and len(text) > 2 and not text.startswith('['):
                        wiki_name = text
                        break
            if not wiki_name:
                continue
            skip_names = ['warbonds', 'helldivers', 'category', 'ship module', 'dlc']
            if any(skip in wiki_name.lower() for skip in skip_names):
                continue
            arrows = _extract_arrows_from_cells(cells)
            if arrows and len(arrows) >= 3:
                stratagems[wiki_name] = arrows
                if verbose:
                    print(f"  {wiki_name}: {' '.join(arrows)}")
    return stratagems


def scrape_stratagems_raw(verbose: bool = False) -> dict[str, list[str]]:
    """
    Scrape all stratagem codes from the wiki, keeping original wiki names.

    Uses the MediaWiki parse API first (reliable, expands templates, not
    blocked by Cloudflare). Falls back to direct HTML fetch with retries.
    """
    if not check_dependencies():
        return {}

    # 1) Prefer MediaWiki parse API – returns rendered HTML with templates
    #    expanded (e.g. {{Stratagem Table}}) and avoids Cloudflare.
    api_html = fetch_parsed_html_via_api("Stratagems")
    if api_html:
        stratagems = _scrape_stratagems_from_html(api_html, verbose=verbose)
        if len(stratagems) >= 10:
            print(f"Fetching stratagems from: {WIKI_API_URL} (MediaWiki parse API)")
            print(f"Found {len(stratagems)} stratagems from wiki")
            return stratagems

    # 2) Fallback: fetch HTML directly (may hit Cloudflare challenge)
    print(f"Fetching stratagems from: {STRATAGEMS_PAGE}")
    for attempt in range(HTML_FETCH_RETRIES):
        if attempt > 0:
            time.sleep(HTML_FETCH_RETRY_DELAY_SEC)
            print(f"Retry {attempt + 1}/{HTML_FETCH_RETRIES}...")
        try:
            html = fetch_page(STRATAGEMS_PAGE)
        except RuntimeError:
            continue
        tables = BeautifulSoup(html, 'html.parser').find_all('table', class_='wikitable')
        print(f"Found {len(tables)} stratagem tables")
        if len(tables) >= 2:
            stratagems = _scrape_stratagems_from_html(html, verbose=verbose)
            if stratagems:
                return stratagems
    return {}


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
    
    # Keep only keys that are in STRATAGEM_MAPPINGS (config). This drops stale
    # keys like BmdC4Pack when the config uses C4Pack with wiki "B/MD C4 Pack".
    stratagems = {k: v for k, v in stratagems.items() if k in STRATAGEM_MAPPINGS}
    
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


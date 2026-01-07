"""
Helldivers 2 StreamController Plugin - Asset Generation Scripts

This package provides tools for generating plugin assets:
- Scraping stratagem data from the wiki
- Generating icons from SVG files
- Creating locale files
- Managing stratagem key sequences

Usage:
    python -m scripts.cli [command] [options]
    
Commands:
    generate-all    Generate all assets (scrape, icons, locales)
    scrape          Scrape stratagems from wiki.gg
    icons           Generate PNG icons from SVG files
    locales         Generate locale files
    stratagems      Generate/display stratagems.json
    list            List available stratagems
    validate        Validate configuration
"""

from .config import (
    ASSETS_DIR,
    DATA_DIR,
    ICONS_DIR,
    LEGACY_KEYS,
    LOCALE_EN_US,
    LOCALES_DIR,
    PLUGIN_DIR,
    SCRIPTS_DIR,
    STRATAGEM_MAPPINGS,
    STRATAGEMS_JSON,
    SVG_TO_KEY_MAPPINGS,
    WIKI_TO_KEY_MAPPINGS,
    get_stratagem_info,
)
from .scraper import load_stratagems, scrape_and_save

__all__ = [
    "ASSETS_DIR",
    "DATA_DIR",
    "ICONS_DIR",
    "LEGACY_KEYS",
    "LOCALE_EN_US",
    "LOCALES_DIR",
    "PLUGIN_DIR",
    "SCRIPTS_DIR",
    "STRATAGEM_MAPPINGS",
    "STRATAGEMS_JSON",
    "SVG_TO_KEY_MAPPINGS",
    "WIKI_TO_KEY_MAPPINGS",
    "get_stratagem_info",
    "load_stratagems",
    "scrape_and_save",
]


#!/usr/bin/env python3
"""
CLI for the Helldivers 2 StreamController plugin asset generation.

Usage:
    python -m scripts [command] [options]
    
Commands:
    discover        Discover new stratagems from wiki/SVGs (run this first!)
    generate-all    Generate all assets (icons, locales, stratagems, pages)
    icons           Generate PNG icons from SVG files
    locales         Generate locale files
    stratagems      Generate stratagems.json
    pages           Generate test pages with all stratagems
    scrape          Scrape stratagems from wiki.gg
    list            List available stratagems
    validate        Validate configuration
    
Workflow:
    1. Run `discover` to find new stratagems
    2. Add suggested mappings to scripts/config.py
    3. Run `generate-all` to create all assets
"""

import argparse
import sys
from pathlib import Path

from .config import (
    DEFAULT_ICON_SCALE,
    DEFAULT_ICON_SIZE,
    ICONS_DIR,
    LOCALE_EN_US,
    STRATAGEMS_JSON,
    STRATAGEM_MAPPINGS,
    WIKI_TO_KEY_MAPPINGS,
    SVG_TO_KEY_MAPPINGS,
)


def cmd_generate_all(args):
    """Generate all assets."""
    from .download import SVGDownloadContext
    from .icons import generate_icons
    from .locales import write_locale_file
    from .stratagems import generate_stratagems_json
    from .pages import generate_test_pages
    
    print("=" * 60)
    print("Helldivers 2 StreamController Plugin - Asset Generator")
    print("=" * 60)
    
    errors = 0
    
    # Generate stratagems.json
    print("\n[1/4] Generating stratagems.json...")
    if not generate_stratagems_json(dry_run=args.dry_run):
        errors += 1
    
    # Generate locale file
    print("\n[2/4] Generating locale file...")
    if not write_locale_file(dry_run=args.dry_run):
        errors += 1
    
    # Generate icons
    print("\n[3/4] Generating icons...")
    with SVGDownloadContext() as svg_dir:
        if svg_dir is None:
            print("Failed to download SVG icons!")
            errors += 1
        else:
            converted, icon_errors = generate_icons(
                svg_dir,
                output_dir=args.output_dir or ICONS_DIR,
                size=args.size,
                icon_scale=args.icon_scale,
                dry_run=args.dry_run,
                verbose=args.verbose,
            )
            errors += icon_errors
    
    # Generate test pages
    if not args.skip_pages:
        print("\n[4/4] Generating test pages...")
        try:
            generate_test_pages(
                output_dir=args.pages_dir,
                dry_run=args.dry_run,
                verbose=args.verbose,
            )
        except Exception as e:
            print(f"Failed to generate test pages: {e}")
            errors += 1
    else:
        print("\n[4/4] Skipping test pages (--skip-pages)")
    
    print("\n" + "=" * 60)
    if args.dry_run:
        print("Dry run complete!")
    elif errors == 0:
        print("All assets generated successfully!")
    else:
        print(f"Completed with {errors} error(s)")
    
    return 0 if errors == 0 else 1


def cmd_icons(args):
    """Generate PNG icons."""
    from .download import SVGDownloadContext
    from .icons import generate_icons
    
    with SVGDownloadContext() as svg_dir:
        if svg_dir is None:
            print("Failed to download SVG icons!")
            return 1
        
        converted, errors = generate_icons(
            svg_dir,
            output_dir=args.output_dir or ICONS_DIR,
            size=args.size,
            icon_scale=args.icon_scale,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
    
    return 0 if errors == 0 else 1


def cmd_locales(args):
    """Generate locale files."""
    from .locales import merge_with_existing, write_locale_file
    
    if args.merge:
        success = merge_with_existing(
            output_path=args.output or LOCALE_EN_US,
            dry_run=args.dry_run,
        )
    else:
        success = write_locale_file(
            output_path=args.output or LOCALE_EN_US,
            dry_run=args.dry_run,
        )
    
    return 0 if success else 1


def cmd_stratagems(args):
    """Generate stratagems.json by scraping the wiki."""
    from .stratagems import generate_stratagems_json
    
    success = generate_stratagems_json(
        output_path=args.output or STRATAGEMS_JSON,
        from_wiki=not args.no_scrape,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )
    
    return 0 if success else 1


def cmd_scrape(args):
    """Scrape stratagems from the wiki."""
    from .scraper import scrape_and_save
    
    stratagems = scrape_and_save(
        output_path=args.output or STRATAGEMS_JSON,
        merge=args.merge,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )
    
    return 0 if stratagems else 1


def cmd_pages(args):
    """Generate test pages for stratagems."""
    from .pages import generate_test_pages, clean_test_pages, list_generated_pages
    
    if args.clean:
        removed = clean_test_pages(
            output_dir=args.output_dir,
            dry_run=args.dry_run,
        )
        print(f"{'Would remove' if args.dry_run else 'Removed'} {removed} test pages")
        return 0
    
    if args.list:
        pages = list_generated_pages(output_dir=args.output_dir)
        if pages:
            print(f"Found {len(pages)} test pages:")
            for p in pages:
                print(f"  - {p.name}")
        else:
            print("No test pages found.")
        return 0
    
    pages = generate_test_pages(
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )
    
    return 0 if pages else 1


def cmd_list(args):
    """List available stratagems."""
    from .config import DISPLAY_NAMES, LEGACY_KEYS
    from .scraper import load_stratagems
    
    stratagems = load_stratagems()
    
    if not stratagems:
        print("No stratagems found. Run 'scrape' command first.")
        return 1
    
    if args.format == "keys":
        for key in sorted(stratagems.keys()):
            legacy = " (legacy)" if key in LEGACY_KEYS else ""
            print(f"{key}{legacy}")
    elif args.format == "names":
        for key in sorted(stratagems.keys()):
            name = DISPLAY_NAMES.get(key, key)
            print(f"{key}: {name}")
    elif args.format == "sequences":
        for key in sorted(stratagems.keys()):
            seq = stratagems[key]
            print(f"{key}: {' '.join(seq)}")
    elif args.format == "json":
        import json
        data = {
            key: {
                "name": DISPLAY_NAMES.get(key, key),
                "sequence": stratagems[key],
                "legacy": key in LEGACY_KEYS,
            }
            for key in sorted(stratagems.keys())
        }
        print(json.dumps(data, indent=2))
    
    print(f"\nTotal: {len(stratagems)} stratagems")
    print(f"Legacy (backward compatible): {len([k for k in stratagems if k in LEGACY_KEYS])}")
    
    return 0


def cmd_validate(args):
    """Validate configuration."""
    from .config import (
        DISPLAY_NAMES,
        ICONS_DIR,
        LEGACY_KEYS,
        SVG_TO_KEY_MAPPINGS,
    )
    from .scraper import load_stratagems
    from .stratagems import validate_sequences
    
    stratagems = load_stratagems()
    
    errors = []
    warnings = []
    
    if not stratagems:
        errors.append("No stratagems found! Run 'scrape' command first.")
    else:
        # Validate sequences
        seq_errors = validate_sequences()
        errors.extend(seq_errors)
        
        # Check for missing display names
        for key in stratagems:
            if key not in DISPLAY_NAMES:
                warnings.append(f"Missing display name for: {key}")
        
        # Check for legacy keys that have sequences
        legacy_with_seq = set(LEGACY_KEYS) & set(stratagems.keys())
        legacy_missing_seq = set(LEGACY_KEYS) - set(stratagems.keys())
        
        for key in legacy_missing_seq:
            warnings.append(f"Legacy key missing sequence: {key}")
        
        # Check for SVG mappings that don't have sequences
        for svg_name, key in SVG_TO_KEY_MAPPINGS.items():
            if key not in stratagems:
                warnings.append(f"SVG '{svg_name}' maps to key '{key}' which has no sequence")
        
        # Check for existing icons
        if ICONS_DIR.exists():
            existing_icons = {p.stem for p in ICONS_DIR.glob("*.png")}
            missing_icons = set(stratagems.keys()) - existing_icons
            extra_icons = existing_icons - set(stratagems.keys()) - {"hero_on", "hero_off", "helldivers2_logo", "_stepforward", "_stepbakcward"}
            
            for key in missing_icons:
                warnings.append(f"Missing icon: {key}.png")
            
            for key in extra_icons:
                warnings.append(f"Extra icon (no stratagem): {key}.png")
    
    # Print results
    print("Validation Results")
    print("=" * 40)
    
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(f"  ❌ {e}")
    
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠️  {w}")
    
    if not errors and not warnings:
        print("✅ All checks passed!")
    
    print(f"\nSummary:")
    print(f"  Stratagems defined: {len(stratagems)}")
    print(f"  Legacy keys: {len(LEGACY_KEYS)}")
    print(f"  SVG mappings: {len(SVG_TO_KEY_MAPPINGS)}")
    print(f"  Display names: {len(DISPLAY_NAMES)}")
    
    return 0 if not errors else 1


def cmd_discover(args):
    """
    Discover new stratagems from wiki and SVG sources.
    
    Compares what's in STRATAGEM_MAPPINGS against:
    - Wiki: stratagems scraped from wiki.gg
    - SVGs: stratagem icons from the GitHub repository
    
    Shows what needs to be added to the mappings.
    """
    from .download import SVGDownloadContext, find_all_svgs
    from .scraper import scrape_stratagems_raw
    import re
    
    print("=" * 60)
    print("Discover New Stratagems")
    print("=" * 60)
    
    # Current mappings - get the wiki and svg names we've defined
    mapped_wiki_names = set(WIKI_TO_KEY_MAPPINGS.keys())
    mapped_svg_names = set(SVG_TO_KEY_MAPPINGS.keys())
    mapped_keys = set(STRATAGEM_MAPPINGS.keys())
    
    # Scrape wiki - get raw names
    print("\n📡 Scraping wiki.gg for stratagems...")
    wiki_data = scrape_stratagems_raw()  # Returns {wiki_name: arrows}
    wiki_names = set(wiki_data.keys())
    
    # Download and scan SVGs
    print("\n📥 Downloading SVG repository...")
    svg_names = set()
    try:
        with SVGDownloadContext() as svg_dir:
            svgs_by_category = find_all_svgs(svg_dir)
            for category, svg_list in svgs_by_category.items():
                for svg_path, svg_name in svg_list:  # It's a tuple (Path, str)
                    svg_names.add(svg_name)
    except Exception as e:
        print(f"  ⚠️  Could not download SVGs: {e}")
    
    # Find differences - compare wiki names to our mapped wiki names
    new_on_wiki = wiki_names - mapped_wiki_names
    new_svgs = svg_names - mapped_svg_names
    
    # Check for mappings with no wiki entry
    wiki_missing = mapped_wiki_names - wiki_names
    
    # Check for mappings with no SVG
    svg_missing = mapped_svg_names - svg_names
    
    # Generate suggested keys for new entries
    def suggest_key(name: str) -> str:
        """Generate a PascalCase key from a name."""
        clean = re.sub(r'"([^"]+)"', r'\1', name)  # Remove quotes
        clean = clean.replace("-", " ").replace(".", " ").replace("'", "")
        words = clean.split()
        return "".join(word.capitalize() for word in words)
    
    # Print results
    print("\n" + "=" * 60)
    print("DISCOVERY RESULTS")
    print("=" * 60)
    
    if new_on_wiki:
        print(f"\n🆕 NEW ON WIKI ({len(new_on_wiki)}):")
        print("   Add these to STRATAGEM_MAPPINGS in config.py:\n")
        for name in sorted(new_on_wiki):
            key = suggest_key(name)
            sequence = wiki_data.get(name, [])
            seq_str = ", ".join(f'"{d}"' for d in sequence)
            print(f'    "{key}": {{"wiki": "{name}", "svg": "{name}", "name": "{name}"}},')
            if args.verbose:
                print(f'        # Sequence: [{seq_str}]')
    else:
        print("\n✅ No new stratagems on wiki")
    
    if new_svgs:
        print(f"\n🎨 NEW SVG ICONS ({len(new_svgs)}):")
        print("   These SVGs don't have mappings:\n")
        for name in sorted(new_svgs):
            key = suggest_key(name)
            print(f'    "{key}": {{"wiki": "{name}", "svg": "{name}", "name": "{name}"}},')
    else:
        print("\n✅ No unmapped SVG icons")
    
    if args.verbose:
        if wiki_missing:
            print(f"\n⚠️  WIKI ENTRIES NOT FOUND ({len(wiki_missing)}):")
            print("   These mappings have wiki names that weren't found on wiki:")
            for name in sorted(wiki_missing):
                key = WIKI_TO_KEY_MAPPINGS.get(name, "?")
                print(f"    - {name} (key: {key})")
        
        if svg_missing:
            print(f"\n⚠️  SVG FILES NOT FOUND ({len(svg_missing)}):")
            print("   These mappings have SVG names that weren't found:")
            for name in sorted(svg_missing):
                key = SVG_TO_KEY_MAPPINGS.get(name, "?")
                print(f"    - {name} (key: {key})")
    
    # Summary
    print("\n" + "-" * 60)
    print("SUMMARY")
    print("-" * 60)
    print(f"  Mapped stratagems: {len(mapped_keys)}")
    print(f"  Wiki stratagems:   {len(wiki_names)} ({len(new_on_wiki)} new)")
    print(f"  SVG icons:         {len(svg_names)} ({len(new_svgs)} unmapped)")
    
    if new_on_wiki or new_svgs:
        print("\n💡 TIP: Copy the suggested mappings above to scripts/config.py")
        print("   then run `python -m scripts generate-all` to generate assets.")
        return 1
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Helldivers 2 StreamController Plugin - Asset Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # generate-all command
    gen_all = subparsers.add_parser("generate-all", help="Generate all assets")
    gen_all.add_argument("-n", "--dry-run", action="store_true", help="Show what would be done")
    gen_all.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    gen_all.add_argument("-o", "--output-dir", type=Path, help="Output directory for icons")
    gen_all.add_argument("-s", "--size", type=int, default=DEFAULT_ICON_SIZE, help="Icon size")
    gen_all.add_argument("--icon-scale", type=float, default=DEFAULT_ICON_SCALE, help="Icon scale factor")
    gen_all.add_argument("--skip-pages", action="store_true", help="Skip generating test pages")
    gen_all.add_argument("--pages-dir", type=Path, help="Output directory for test pages")
    gen_all.set_defaults(func=cmd_generate_all)
    
    # icons command
    icons = subparsers.add_parser("icons", help="Generate PNG icons")
    icons.add_argument("-n", "--dry-run", action="store_true", help="Show what would be done")
    icons.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    icons.add_argument("-o", "--output-dir", type=Path, help="Output directory")
    icons.add_argument("-s", "--size", type=int, default=DEFAULT_ICON_SIZE, help="Icon size")
    icons.add_argument("--icon-scale", type=float, default=DEFAULT_ICON_SCALE, help="Icon scale factor")
    icons.set_defaults(func=cmd_icons)
    
    # locales command
    locales = subparsers.add_parser("locales", help="Generate locale files")
    locales.add_argument("-n", "--dry-run", action="store_true", help="Show what would be done")
    locales.add_argument("-o", "--output", type=Path, help="Output file path")
    locales.add_argument("--merge", action="store_true", help="Merge with existing file")
    locales.set_defaults(func=cmd_locales)
    
    # stratagems command
    strat = subparsers.add_parser("stratagems", help="Generate stratagems.json from wiki")
    strat.add_argument("-n", "--dry-run", action="store_true", help="Show what would be done")
    strat.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    strat.add_argument("-o", "--output", type=Path, help="Output file path")
    strat.add_argument("--no-scrape", action="store_true", help="Don't scrape, just show existing")
    strat.set_defaults(func=cmd_stratagems)
    
    # scrape command
    scrape = subparsers.add_parser("scrape", help="Scrape stratagems from wiki.gg")
    scrape.add_argument("-n", "--dry-run", action="store_true", help="Show what would be done")
    scrape.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    scrape.add_argument("-o", "--output", type=Path, help="Output file path")
    scrape.add_argument("--merge", action="store_true", help="Merge with existing file")
    scrape.set_defaults(func=cmd_scrape)
    
    # pages command
    pages = subparsers.add_parser("pages", help="Generate test pages with all stratagems")
    pages.add_argument("-n", "--dry-run", action="store_true", help="Show what would be done")
    pages.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    pages.add_argument("-o", "--output-dir", type=Path, help="Output directory for pages")
    pages.add_argument("--clean", action="store_true", help="Remove generated test pages")
    pages.add_argument("--list", action="store_true", help="List existing test pages")
    pages.set_defaults(func=cmd_pages)
    
    # list command
    list_cmd = subparsers.add_parser("list", help="List stratagems")
    list_cmd.add_argument(
        "-f", "--format",
        choices=["keys", "names", "sequences", "json"],
        default="keys",
        help="Output format",
    )
    list_cmd.set_defaults(func=cmd_list)
    
    # validate command
    validate = subparsers.add_parser("validate", help="Validate configuration")
    validate.set_defaults(func=cmd_validate)
    
    # discover command
    discover = subparsers.add_parser(
        "discover",
        help="Discover new stratagems from wiki/SVGs not yet in mappings",
    )
    discover.add_argument("-v", "--verbose", action="store_true", help="Show additional details")
    discover.set_defaults(func=cmd_discover)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())


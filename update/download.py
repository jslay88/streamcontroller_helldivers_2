"""
Download SVG icons from GitHub repository.
"""

import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from .config import SVG_REPO_ZIP_URL, SVG_REPO_EXTRACTED_NAME


def download_svg_icons(dest_dir: Path) -> Path | None:
    """
    Download and extract SVG icons from GitHub to a directory.
    
    Args:
        dest_dir: The directory to extract into
        
    Returns:
        Path to the extracted SVG directory, or None on error
    """
    print(f"Downloading SVG icons from GitHub...")
    print(f"  URL: {SVG_REPO_ZIP_URL}")
    
    try:
        zip_path = dest_dir / "icons.zip"
        
        # Download the zip file
        print("  Downloading...")
        urllib.request.urlretrieve(SVG_REPO_ZIP_URL, zip_path)
        
        # Extract the zip file
        print("  Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)
        
        # The extracted folder has a specific name
        extracted_dir = dest_dir / SVG_REPO_EXTRACTED_NAME
        
        if not extracted_dir.exists():
            print(f"  ERROR: Expected folder '{SVG_REPO_EXTRACTED_NAME}' not found in zip")
            return None
        
        # Clean up zip file
        zip_path.unlink()
        
        print("  Download complete!")
        return extracted_dir
        
    except urllib.error.URLError as e:
        print(f"  ERROR: Failed to download: {e}")
        return None
    except zipfile.BadZipFile as e:
        print(f"  ERROR: Invalid zip file: {e}")
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def find_all_svgs(svg_dir: Path) -> dict[str, list[tuple[Path, str]]]:
    """
    Find all SVG files in the SVG directory, organized by category.
    
    Args:
        svg_dir: Path to the directory containing SVG category folders
    
    Returns:
        Dict mapping category name to list of (svg_path, svg_name) tuples
    """
    result = {}
    
    if not svg_dir.exists():
        print(f"SVG directory not found: {svg_dir}")
        return result
    
    for category_dir in svg_dir.iterdir():
        if category_dir.is_dir() and not category_dir.name.startswith('.'):
            category_name = category_dir.name
            svgs = []
            
            for svg_file in category_dir.glob("*.svg"):
                svg_name = svg_file.stem  # Name without extension
                svgs.append((svg_file, svg_name))
            
            if svgs:
                result[category_name] = svgs
    
    return result


class SVGDownloadContext:
    """
    Context manager for downloading SVGs to a temporary directory.
    
    Usage:
        with SVGDownloadContext() as svg_dir:
            # svg_dir is the path to extracted SVGs
            # automatically cleaned up when context exits
    """
    
    def __init__(self):
        self._temp_dir = None
        self._svg_dir = None
    
    def __enter__(self) -> Path | None:
        self._temp_dir = tempfile.TemporaryDirectory()
        temp_path = Path(self._temp_dir.name)
        self._svg_dir = download_svg_icons(temp_path)
        return self._svg_dir
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._temp_dir:
            self._temp_dir.cleanup()
        return False


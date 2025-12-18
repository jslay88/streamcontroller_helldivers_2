"""
Icon generation: Convert SVG stratagem icons to PNG with corner borders.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image as PILImage

try:
    import cairosvg
    from PIL import Image, ImageDraw
except ImportError:
    cairosvg = None
    Image = None
    ImageDraw = None

from .config import (
    COLOR_MAPPINGS,
    DEFAULT_ICON_COLOR,
    DEFAULT_ICON_SCALE,
    DEFAULT_ICON_SIZE,
    ICONS_DIR,
    SVG_TO_KEY_MAPPINGS,
)


def check_dependencies():
    """Check if required dependencies are installed."""
    if cairosvg is None or Image is None:
        print("Required packages not found. Install them with:")
        print("  pip install cairosvg pillow")
        return False
    return True


def normalize_hex_color(color: str) -> str:
    """Normalize a hex color to lowercase 6-character format."""
    color = color.strip().lower()
    if color.startswith('#'):
        hex_part = color[1:]
        if len(hex_part) == 3:
            hex_part = ''.join(c * 2 for c in hex_part)
        return f"#{hex_part}"
    return color


def apply_color_mapping(color: str) -> tuple[str, bool]:
    """
    Apply color mapping to convert SVG colors to PNG colors.
    
    Returns:
        Tuple of (mapped_color, was_mapped)
    """
    normalized = normalize_hex_color(color)
    if normalized in COLOR_MAPPINGS:
        return normalize_hex_color(COLOR_MAPPINGS[normalized]), True
    return normalized, False


def replace_colors_in_svg(svg_content: str, color_map: dict) -> str:
    """Replace colors in SVG content based on a color mapping."""
    result = svg_content
    
    for old_color, new_color in color_map.items():
        old_normalized = normalize_hex_color(old_color)
        new_normalized = normalize_hex_color(new_color)
        
        if old_normalized == new_normalized:
            continue
        
        old_hex = old_normalized[1:]
        new_hex = new_normalized[1:]
        
        result = result.replace(f"#{old_hex}", f"#{new_hex}")
        result = result.replace(f"#{old_hex.upper()}", f"#{new_hex}")
        result = re.sub(
            rf'#({old_hex})',
            f'#{new_hex}',
            result,
            flags=re.IGNORECASE
        )
    
    return result


# Colors to ignore when extracting accent color
IGNORE_COLORS = {
    "#fff", "#ffffff", "#FFF", "#FFFFFF",
    "white", "WHITE", "White",
    "#fefefe", "#FEFEFE",
}


def is_white_color(color: str) -> bool:
    """Check if a color is white or near-white."""
    normalized = normalize_hex_color(color)
    if normalized in IGNORE_COLORS or color in IGNORE_COLORS:
        return True
    
    if normalized.startswith('#') and len(normalized) == 7:
        try:
            r = int(normalized[1:3], 16)
            g = int(normalized[3:5], 16)
            b = int(normalized[5:7], 16)
            if r > 240 and g > 240 and b > 240:
                return True
        except ValueError:
            pass
    
    return False


def extract_accent_color(svg_content: str) -> str:
    """Extract the accent color from an SVG file."""
    colors = []
    
    fill_attr_pattern = re.compile(r'fill\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
    colors.extend(fill_attr_pattern.findall(svg_content))
    
    style_fill_pattern = re.compile(r'style\s*=\s*["\'][^"\']*fill\s*:\s*([^;"\'\s]+)', re.IGNORECASE)
    colors.extend(style_fill_pattern.findall(svg_content))
    
    for color in colors:
        color = color.strip()
        if not is_white_color(color):
            return normalize_hex_color(color)
    
    return DEFAULT_ICON_COLOR


def has_corner_borders(svg_content: str) -> bool:
    """Detect if an SVG has built-in corner border triangles."""
    d_pattern = re.compile(r'd\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
    sep = r'[\s,]*'
    
    for d_match in d_pattern.finditer(svg_content):
        d_content = d_match.group(1)
        
        starts_at_corner = bool(re.match(
            rf'M{sep}[0-9]{{1,2}}{sep}(1[12][0-9]|[0-9]{{1,2}}){sep}[Vv]',
            d_content, re.IGNORECASE
        ))
        
        if not starts_at_corner:
            continue
        
        z_count = len(re.findall(r'[Zz]', d_content))
        if z_count != 4:
            continue
        
        m_count = len(re.findall(r'[Mm]', d_content))
        if m_count < 3 or m_count > 5:
            continue
        
        if len(d_content) > 200:
            continue
        
        triangle_pattern = rf'[Vv]{sep}-?\d+{sep}[Ll]{sep}-?\d+{sep}-?\d+{sep}[Hh]{sep}-?\d+{sep}[Zz]'
        triangle_count = len(re.findall(triangle_pattern, d_content, re.IGNORECASE))
        if triangle_count >= 2:
            return True
    
    return False


def remove_corner_borders(svg_content: str) -> str:
    """Remove built-in corner border paths from an SVG."""
    path_pattern = re.compile(
        r'<path\s+[^>]*?d\s*=\s*["\']([^"\']+)["\'][^>]*/?\s*>',
        re.IGNORECASE | re.DOTALL
    )
    
    sep = r'[\s,]*'
    
    def is_corner_border_path(d_attr: str) -> bool:
        d = d_attr
        
        starts_at_corner = bool(re.match(
            rf'M{sep}[0-9]{{1,2}}{sep}(1[12][0-9]|[0-9]{{1,2}}){sep}[Vv]',
            d, re.IGNORECASE
        ))
        
        if not starts_at_corner:
            return False
        
        z_count = len(re.findall(r'[Zz]', d))
        if z_count != 4:
            return False
        
        m_count = len(re.findall(r'[Mm]', d))
        if m_count < 3 or m_count > 5:
            return False
        
        if len(d) > 200:
            return False
        
        triangle_pattern = rf'[Vv]{sep}-?\d+{sep}[Ll]{sep}-?\d+{sep}-?\d+{sep}[Hh]{sep}-?\d+{sep}[Zz]'
        triangle_count = len(re.findall(triangle_pattern, d, re.IGNORECASE))
        if triangle_count < 2:
            return False
        
        return True
    
    def replace_corner_path(match):
        d_attr = match.group(1)
        if is_corner_border_path(d_attr):
            return ''
        return match.group(0)
    
    result = path_pattern.sub(replace_corner_path, svg_content)
    result = re.sub(r'\n\s*\n', '\n', result)
    
    return result


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def draw_corner_borders(image: Image.Image, color: str) -> Image.Image:
    """Draw L-shaped gradient corner borders on the image."""
    rgb_color = hex_to_rgb(color)
    
    w, h = image.size
    
    padding = max(int(w * 0.07), 5)
    line_length = max(int(w * 0.50), 35)
    line_width = max(int(w * 0.014), 2)
    corner_radius = max(int(w * 0.06), 6)
    
    result = image.copy().convert("RGBA")
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Top-left L-shape
    tl_x = padding
    tl_y = padding
    
    for i in range(line_length):
        alpha = int(255 * (1 - (i / line_length) ** 0.7))
        y = tl_y + corner_radius + i
        if y < h - padding:
            draw.line([(tl_x, y), (tl_x + line_width - 1, y)], fill=(*rgb_color, alpha))
    
    for i in range(line_length):
        alpha = int(255 * (1 - (i / line_length) ** 0.7))
        x = tl_x + corner_radius + i
        if x < w - padding:
            draw.line([(x, tl_y), (x, tl_y + line_width - 1)], fill=(*rgb_color, alpha))
    
    draw.arc([tl_x, tl_y, tl_x + corner_radius * 2, tl_y + corner_radius * 2],
             start=180, end=270, fill=(*rgb_color, 255), width=line_width)
    
    # Bottom-right L-shape
    br_x = w - padding - line_width
    br_y = h - padding - line_width
    
    for i in range(line_length):
        alpha = int(255 * (1 - (i / line_length) ** 0.7))
        y = br_y - corner_radius - i
        if y > padding:
            for lw in range(line_width):
                draw.point((br_x + lw, y), fill=(*rgb_color, alpha))
    
    for i in range(line_length):
        alpha = int(255 * (1 - (i / line_length) ** 0.7))
        x = br_x - corner_radius - i
        if x > padding:
            for lw in range(line_width):
                draw.point((x, br_y + lw), fill=(*rgb_color, alpha))
    
    draw.arc([br_x - corner_radius * 2 + line_width - 1, br_y - corner_radius * 2 + line_width - 1,
              br_x + line_width - 1, br_y + line_width - 1],
             start=0, end=90, fill=(*rgb_color, 255), width=line_width)
    
    result = Image.alpha_composite(result, overlay)
    return result


def svg_to_png_with_borders(
    svg_path: Path,
    output_path: Path,
    size: int = DEFAULT_ICON_SIZE,
    icon_scale: float = DEFAULT_ICON_SCALE,
) -> tuple[str, str, bool, bool]:
    """
    Convert an SVG to PNG with colored corner borders.
    
    Returns:
        Tuple of (original_color, final_color, was_mapped, had_corners)
    """
    svg_content = svg_path.read_text(encoding='utf-8')
    
    original_color = extract_accent_color(svg_content)
    color, was_mapped = apply_color_mapping(original_color)
    
    had_corners = has_corner_borders(svg_content)
    if had_corners:
        svg_content = remove_corner_borders(svg_content)
    
    if was_mapped:
        svg_content = replace_colors_in_svg(svg_content, {original_color: color})
    
    svg_bytes = svg_content.encode('utf-8')
    icon_size = int(size * icon_scale)
    
    png_data = cairosvg.svg2png(
        bytestring=svg_bytes,
        output_width=icon_size,
        output_height=icon_size,
    )
    
    icon = Image.open(io.BytesIO(png_data)).convert("RGBA")
    final_image = Image.new("RGBA", (size, size), (26, 26, 26, 255))
    
    offset = (size - icon_size) // 2
    final_image.paste(icon, (offset, offset), icon)
    
    image_with_borders = draw_corner_borders(final_image, color)
    image_with_borders.save(output_path, "PNG")
    
    return original_color, color, was_mapped, had_corners


def get_output_key(svg_name: str) -> str:
    """Get the internal key for an SVG name."""
    return SVG_TO_KEY_MAPPINGS.get(svg_name, svg_name.replace(" ", "").replace("-", ""))


def generate_icons(
    svg_dir: Path,
    output_dir: Path = ICONS_DIR,
    size: int = DEFAULT_ICON_SIZE,
    icon_scale: float = DEFAULT_ICON_SCALE,
    dry_run: bool = False,
    verbose: bool = False,
) -> tuple[int, int]:
    """
    Generate PNG icons from SVG files.
    
    Args:
        svg_dir: Directory containing SVG category folders
        output_dir: Output directory for PNG files
        size: Icon size in pixels
        icon_scale: Scale factor for the icon within the image
        dry_run: If True, don't actually generate files
        verbose: If True, print detailed output
        
    Returns:
        Tuple of (converted_count, error_count)
    """
    if not check_dependencies():
        return 0, 1
    
    from .download import find_all_svgs
    
    svgs_by_category = find_all_svgs(svg_dir)
    
    if not svgs_by_category:
        print("No SVG files found!")
        return 0, 1
    
    total_svgs = sum(len(svgs) for svgs in svgs_by_category.values())
    print(f"Found {total_svgs} SVG files in {len(svgs_by_category)} categories")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    converted = 0
    errors = 0
    
    for category, svgs in sorted(svgs_by_category.items()):
        print(f"\n{category}:")
        
        for svg_path, svg_name in sorted(svgs, key=lambda x: x[1]):
            key = get_output_key(svg_name)
            output_path = output_dir / f"{key}.png"
            
            if dry_run:
                svg_content = svg_path.read_text(encoding='utf-8')
                original_color = extract_accent_color(svg_content)
                final_color, was_mapped = apply_color_mapping(original_color)
                had_corners = has_corner_borders(svg_content)
                corner_note = " (will remove corners)" if had_corners else ""
                if was_mapped:
                    color_info = f"{original_color} -> {final_color}"
                else:
                    color_info = final_color
                print(f"  {svg_name} -> {key}.png ({color_info}){corner_note}")
            else:
                try:
                    original_color, final_color, was_mapped, had_corners = svg_to_png_with_borders(
                        svg_path, output_path, size, icon_scale
                    )
                    converted += 1
                    if verbose:
                        corner_note = " (removed corners)" if had_corners else ""
                        if was_mapped:
                            color_info = f"{original_color} -> {final_color}"
                        else:
                            color_info = final_color
                        print(f"  {svg_name} -> {key}.png ({color_info}){corner_note}")
                except Exception as e:
                    print(f"  ERROR: {svg_name}: {e}")
                    errors += 1
    
    if dry_run:
        print(f"\nDry run complete. Would convert {total_svgs} files.")
    else:
        print(f"\nConversion complete!")
        print(f"  Converted: {converted}")
        print(f"  Errors: {errors}")
    
    return converted, errors


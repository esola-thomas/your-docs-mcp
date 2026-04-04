"""Color utilities and CSS variable generation for white-label theming."""

import re


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a hex color string to RGB tuple.

    Args:
        hex_color: Hex color string (e.g., '#3b82f6')

    Returns:
        Tuple of (red, green, blue) values 0-255
    """
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to hex color string.

    Args:
        r: Red value 0-255
        g: Green value 0-255
        b: Blue value 0-255

    Returns:
        Hex color string (e.g., '#3b82f6')
    """
    return f"#{min(255, max(0, r)):02x}{min(255, max(0, g)):02x}{min(255, max(0, b)):02x}"


def darken(hex_color: str, amount: float = 0.15) -> str:
    """Darken a hex color by a percentage.

    Args:
        hex_color: Hex color string
        amount: Amount to darken (0.0 to 1.0)

    Returns:
        Darkened hex color string
    """
    r, g, b = hex_to_rgb(hex_color)
    factor = 1.0 - amount
    return rgb_to_hex(int(r * factor), int(g * factor), int(b * factor))


def lighten(hex_color: str, amount: float = 0.15) -> str:
    """Lighten a hex color by a percentage.

    Args:
        hex_color: Hex color string
        amount: Amount to lighten (0.0 to 1.0)

    Returns:
        Lightened hex color string
    """
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex(
        int(r + (255 - r) * amount),
        int(g + (255 - g) * amount),
        int(b + (255 - b) * amount),
    )


def rgba(hex_color: str, alpha: float) -> str:
    """Convert hex color to rgba() CSS value.

    Args:
        hex_color: Hex color string
        alpha: Alpha value (0.0 to 1.0)

    Returns:
        CSS rgba() string
    """
    r, g, b = hex_to_rgb(hex_color)
    return f"rgba({r}, {g}, {b}, {alpha})"


def is_valid_hex_color(value: str) -> bool:
    """Check if a string is a valid 6-digit hex color."""
    return bool(re.match(r"^#[0-9a-fA-F]{6}$", value))


def generate_css_overrides(
    primary_color: str,
    font_family: str | None = None,
    font_family_code: str | None = None,
) -> dict[str, str]:
    """Generate CSS custom property overrides from branding config.

    Args:
        primary_color: Primary accent color (hex)
        font_family: Override for --font-sans
        font_family_code: Override for --font-mono

    Returns:
        Dict of CSS variable name -> value
    """
    default_primary = "#3b82f6"
    overrides: dict[str, str] = {}

    if primary_color != default_primary:
        overrides["--accent-primary"] = primary_color
        overrides["--accent-hover"] = darken(primary_color, 0.15)
        overrides["--accent-light"] = lighten(primary_color, 0.85)
        overrides["--info"] = primary_color

    if font_family:
        overrides["--font-sans"] = font_family

    if font_family_code:
        overrides["--font-mono"] = font_family_code

    return overrides

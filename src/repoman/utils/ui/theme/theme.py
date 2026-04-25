"""Theme configuration for the repoman CLI application."""

import math
from typing import TYPE_CHECKING, Any

from catppuccin import PALETTE
from rich.theme import Theme

if TYPE_CHECKING:
    from rich.style import Style

_RAMP_FIRST_STOP = 0.33
_RAMP_SECOND_STOP = 0.66
_RAMP_FINAL_SPAN = 0.34


def color_rgb(color: Any) -> tuple[int, int, int]:
    """Return an RGB tuple for Catppuccin color objects."""
    if hasattr(color, "rgb"):
        return (color.rgb.r, color.rgb.g, color.rgb.b)
    return _hex_to_rgb(color.hex)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.removeprefix("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _lerp_rgb(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def _create_theme(colors: Any) -> Theme:
    styles: dict[str, Style | str] = {
        # Base Catppuccin palette aliases
        "rosewater": colors.rosewater.hex,
        "flamingo": colors.flamingo.hex,
        "pink": colors.pink.hex,
        "mauve": colors.mauve.hex,
        "red": colors.red.hex,
        "maroon": colors.maroon.hex,
        "peach": colors.peach.hex,
        "yellow": colors.yellow.hex,
        "green": colors.green.hex,
        "teal": colors.teal.hex,
        "sky": colors.sky.hex,
        "sapphire": colors.sapphire.hex,
        "blue": colors.blue.hex,
        "lavender": colors.lavender.hex,
        "text": colors.text.hex,
        "subtext1": colors.subtext1.hex,
        "subtext0": colors.subtext0.hex,
        "overlay2": colors.overlay2.hex,
        "overlay1": colors.overlay1.hex,
        "overlay0": colors.overlay0.hex,
        "surface2": colors.surface2.hex,
        "surface1": colors.surface1.hex,
        "surface0": colors.surface0.hex,
        "base": colors.base.hex,
        "mantle": colors.mantle.hex,
        "crust": colors.crust.hex,
        # UI roles
        "ui.border": colors.overlay1.hex,
        "ui.header": colors.overlay2.hex,
        # Semantic roles
        "tool.name": f"bold {colors.yellow.hex}",
        "tool.args": f"{colors.subtext0.hex}",
        "tool.ok": f"{colors.green.hex}",
        "tool.fail": f"{colors.red.hex}",
        "info": f"{colors.subtext0.hex}",
        "muted": f"{colors.overlay0.hex}",
        # Markdown roles
        "markdown.strong": f"bold {colors.yellow.hex}",
        "markdown.emphasis": f"italic {colors.peach.hex}",
        "markdown.code": colors.sky.hex,
        "markdown.code_block": colors.sky.hex,
        "markdown.link": f"underline {colors.blue.hex}",
        "markdown.h1": f"bold {colors.yellow.hex}",
        "markdown.h2": f"bold {colors.peach.hex}",
        "markdown.h3": f"bold {colors.maroon.hex}",
    }
    return Theme(styles=styles, inherit=True)


def set_theme(theme_name: str = "dark") -> Theme:
    """Set the theme for the application."""
    if theme_name == "light":
        theme = _create_theme(PALETTE.frappe.colors)
    elif theme_name == "dark":
        theme = _create_theme(PALETTE.mocha.colors)
    else:
        raise ValueError(f"Unknown theme: {theme_name}")
    return theme


def cool_ramp(progress: float, colors: Any = PALETTE.mocha.colors) -> tuple[int, int, int]:
    """Blend through cool Catppuccin colors for logo animation progress."""
    p = max(0.0, min(1.0, progress))
    text = color_rgb(colors.text)
    sky = color_rgb(colors.sky)
    blue = color_rgb(colors.blue)
    lavender = color_rgb(colors.lavender)
    if p < _RAMP_FIRST_STOP:
        return _lerp_rgb(text, sky, p / _RAMP_FIRST_STOP)

    if p < _RAMP_SECOND_STOP:
        return _lerp_rgb(
            sky,
            blue,
            (p - _RAMP_FIRST_STOP) / _RAMP_FIRST_STOP,
        )

    return _lerp_rgb(blue, lavender, (p - _RAMP_SECOND_STOP) / _RAMP_FINAL_SPAN)


def catppuccin_hold_shimmer(t: float, settle_t: float, colors: Any) -> tuple[int, int, int]:
    """Return a subtle blue-to-lavender shimmer color for settled animations."""
    blue = color_rgb(colors.blue)
    lavender = color_rgb(colors.lavender)
    shimmer = (1.0 - max(0.0, min(1.0, settle_t))) * (0.5 + 0.5 * math.sin(t * 4.0))
    shimmer *= 0.18

    return _lerp_rgb(blue, lavender, shimmer)

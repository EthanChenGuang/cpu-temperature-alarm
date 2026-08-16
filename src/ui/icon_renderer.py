"""Render peak temperature digits on Pillow tray icons."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

__all__ = ["peak_display_text", "render_peak_icon"]

VALID_SIZES = (16, 32)


def peak_display_text(peak_temp: float | None) -> str:
    """Return display text for tray icon — integer peak or placeholder."""
    if peak_temp is None:
        return "--"
    return str(int(round(peak_temp)))


def render_peak_icon(
    peak_temp: float | None,
    *,
    size: int = 16,
    alerting: bool = False,
) -> Image.Image:
    """Draw peak temperature digits on a square RGBA icon."""
    if size not in VALID_SIZES:
        raise ValueError(f"icon size must be one of {VALID_SIZES}, got {size}")

    from PIL import Image, ImageDraw, ImageFont

    background = (180, 40, 40, 255) if alerting else (45, 45, 48, 255)
    image = Image.new("RGBA", (size, size), background)
    draw = ImageDraw.Draw(image)

    text = peak_display_text(peak_temp)
    font_size = 10 if size == 16 else 18
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = max(0, (size - text_width) // 2 - bbox[0])
    y = max(0, (size - text_height) // 2 - bbox[1])
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    return image

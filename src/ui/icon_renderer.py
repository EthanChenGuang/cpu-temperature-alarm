"""Render tray icons (peak digits) and desktop app icons (thermometer badge)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

__all__ = [
    "TRAY_ICON_SIZE",
    "generate_app_icon_file",
    "peak_display_text",
    "render_app_icon",
    "render_peak_icon",
    "render_tray_icon",
]

TRAY_SIZES = (16, 32)
APP_SIZES = (16, 32, 64)
TRAY_ICON_SIZE = 64
_APP_ICON_SOURCE = Path(__file__).resolve().parents[2] / "assets" / "app-icon.png"

_TRAY_FONTS = (
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/DejaVuSans.ttf",
)
_APP_FONTS = (
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/DejaVuSans.ttf",
)


def _load_font(font_size: int, *, paths: tuple[str, ...]):
    from PIL import ImageFont

    for path in paths:
        try:
            return ImageFont.truetype(path, font_size)
        except OSError:
            continue
    return ImageFont.load_default()


def _load_tray_font(font_size: int):
    return _load_font(font_size, paths=_TRAY_FONTS)


def _fit_font(
    draw,
    text: str,
    max_width: int,
    max_height: int,
    *,
    start_size: int,
    font_paths: tuple[str, ...] = _TRAY_FONTS,
):
    for font_size in range(start_size, 6, -1):
        font = _load_font(font_size, paths=font_paths)
        bbox = draw.textbbox((0, 0), text, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        if width <= max_width and height <= max_height:
            return font, bbox
    font = _load_font(6, paths=font_paths)
    return font, draw.textbbox((0, 0), text, font=font)


def peak_display_text(peak_temp: float | None, *, decimals: int = 0) -> str:
    """Return display text for tray icon — rounded peak or placeholder."""
    if peak_temp is None:
        return "--"
    if decimals <= 0:
        return str(int(round(peak_temp)))
    return f"{peak_temp:.{decimals}f}"


def _draw_text_with_outline(
    draw,
    xy: tuple[int, int],
    text: str,
    *,
    font,
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int],
    width: int = 1,
    anchor: str = "lt",
) -> None:
    x, y = xy
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, fill=outline, font=font, anchor=anchor)
    draw.text((x, y), text, fill=fill, font=font, anchor=anchor)


def _tray_text_anchor_point(size: int) -> tuple[int, int]:
    """Return canvas point for optically centered tray digits."""
    # Slight upward nudge — pure bbox center reads low after Windows tray downscale.
    return size // 2, size // 2 - max(1, size // 32)


def render_tray_icon(
    peak_temp: float | None,
    *,
    size: int = 16,
    alerting: bool = False,
) -> Image.Image:
    """Draw peak temperature digits on a transparent tray icon."""
    if size not in TRAY_SIZES and size != TRAY_ICON_SIZE:
        raise ValueError(f"tray icon size must be one of {TRAY_SIZES} or {TRAY_ICON_SIZE}, got {size}")

    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    text = peak_display_text(peak_temp)
    anchor_x, anchor_y = _tray_text_anchor_point(size)
    start_size = max(10, int(size * 0.84))
    font, _bbox = _fit_font(
        draw,
        text,
        size - max(2, size // 14),
        size - max(4, size // 8),
        start_size=start_size,
    )
    fill = (255, 72, 56, 255) if alerting else (255, 255, 255, 255)
    outline = (20, 20, 24, 220) if alerting else (20, 20, 24, 200)
    stroke = max(1, size // 24)
    _draw_text_with_outline(
        draw,
        (anchor_x, anchor_y),
        text,
        font=font,
        fill=fill,
        outline=outline,
        width=stroke,
        anchor="mm",
    )
    return image


def render_peak_icon(
    peak_temp: float | None,
    *,
    size: int = 16,
    alerting: bool = False,
) -> Image.Image:
    """Alias for tray icon rendering."""
    return render_tray_icon(peak_temp, size=size, alerting=alerting)


def _palette(alerting: bool) -> dict[str, tuple[int, int, int, int]]:
    if alerting:
        return {
            "bg": (176, 38, 24, 255),
            "bg_inner": (220, 72, 42, 255),
            "ring": (255, 196, 72, 255),
            "tube": (255, 255, 255, 230),
            "mercury": (255, 220, 64, 255),
            "text": (255, 255, 255, 255),
            "accent": (255, 120, 40, 255),
        }
    return {
        "bg": (34, 48, 68, 255),
        "bg_inner": (52, 72, 98, 255),
        "ring": (120, 168, 220, 255),
        "tube": (255, 255, 255, 210),
        "mercury": (255, 120, 48, 255),
        "text": (255, 255, 255, 255),
        "accent": (255, 150, 64, 255),
    }


def _fill_level(peak_temp: float | None, alerting: bool) -> float:
    if peak_temp is None:
        return 0.35
    level = max(0.15, min(1.0, peak_temp / 100.0))
    if alerting:
        return max(level, 0.72)
    return level


def _draw_circle_background(draw, size: int, colors: dict[str, tuple[int, int, int, int]], alerting: bool) -> None:
    margin = max(1, size // 16)
    outer = (margin, margin, size - margin - 1, size - margin - 1)
    draw.ellipse(outer, fill=colors["bg"])
    inset = margin + max(1, size // 14)
    inner = (inset, inset, size - inset - 1, size - inset - 1)
    draw.ellipse(inner, fill=colors["bg_inner"])
    if alerting and size >= 24:
        ring_inset = max(0, margin - 1)
        ring_box = (ring_inset, ring_inset, size - ring_inset - 1, size - ring_inset - 1)
        draw.ellipse(ring_box, outline=colors["ring"], width=max(1, size // 18))


def _draw_thermometer(
    draw,
    *,
    size: int,
    colors: dict[str, tuple[int, int, int, int]],
    fill_level: float,
) -> None:
    if size < 24:
        return

    cx = int(size * 0.30)
    tube_w = max(2, size // 10)
    tube_top = int(size * 0.18)
    tube_bottom = int(size * 0.62)
    bulb_r = max(3, size // 8)
    bulb_cy = tube_bottom + bulb_r - max(1, size // 20)

    tube_left = cx - tube_w // 2
    tube_right = cx + tube_w // 2
    draw.rounded_rectangle(
        (tube_left, tube_top, tube_right, tube_bottom),
        radius=max(1, tube_w // 2),
        fill=colors["tube"],
    )
    draw.ellipse(
        (cx - bulb_r, bulb_cy - bulb_r, cx + bulb_r, bulb_cy + bulb_r),
        fill=colors["tube"],
    )

    mercury_top = tube_bottom - int((tube_bottom - tube_top - 2) * fill_level)
    draw.rounded_rectangle(
        (tube_left + 1, mercury_top, tube_right - 1, tube_bottom - 1),
        radius=max(1, tube_w // 3),
        fill=colors["mercury"],
    )
    draw.ellipse(
        (cx - bulb_r + 1, bulb_cy - bulb_r + 1, cx + bulb_r - 1, bulb_cy + bulb_r - 1),
        fill=colors["mercury"],
    )


def _draw_alert_flame(draw, size: int, colors: dict[str, tuple[int, int, int, int]]) -> None:
    if size < 32:
        return
    x = int(size * 0.68)
    y = int(size * 0.16)
    w = max(3, size // 10)
    h = max(5, size // 6)
    draw.polygon(
        [
            (x, y + h),
            (x + w, y + h),
            (x + w // 2, y),
            (x - w // 3, y + h // 2),
        ],
        fill=colors["accent"],
    )
    draw.polygon(
        [
            (x + w // 2, y + h),
            (x + w, y + h // 2),
            (x + w // 2, y + h // 3),
        ],
        fill=colors["ring"],
    )


def render_app_icon(
    peak_temp: float | None,
    *,
    size: int = 64,
    alerting: bool = False,
) -> Image.Image:
    """Draw a thermometer badge with temperature for desktop / exe icons."""
    if size not in APP_SIZES:
        raise ValueError(f"app icon size must be one of {APP_SIZES}, got {size}")

    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    colors = _palette(alerting)
    fill_level = _fill_level(peak_temp, alerting)

    _draw_circle_background(draw, size, colors, alerting)
    _draw_thermometer(draw, size=size, colors=colors, fill_level=fill_level)
    if alerting:
        _draw_alert_flame(draw, size, colors)

    text = peak_display_text(peak_temp)
    text_x0 = int(size * 0.46)
    max_w = size - text_x0 - 2
    font, bbox = _fit_font(
        draw, text, max_w, int(size * 0.42), start_size=max(8, size // 3), font_paths=_APP_FONTS
    )
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = text_x0 + max(0, (size - text_x0 - text_w) // 2) - bbox[0]
    y = (size - text_h) // 2 - bbox[1]
    draw.text((x, y), text, fill=colors["text"], font=font)
    return image


def _load_app_icon_source() -> Image.Image:
    """Load the static app icon artwork used for exe / shortcut icons."""
    from PIL import Image

    if not _APP_ICON_SOURCE.is_file():
        raise FileNotFoundError(f"app icon source not found: {_APP_ICON_SOURCE}")
    return Image.open(_APP_ICON_SOURCE).convert("RGBA")


def generate_app_icon_file(path: str | Path, *, alerting: bool = True) -> Path:
    """Write a multi-size .ico file for PyInstaller / shortcuts."""
    from PIL import Image

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    base = _load_app_icon_source()
    sizes = [16, 32, 48, 64, 128, 256]
    largest = max(sizes)
    image = base.resize((largest, largest), Image.Resampling.LANCZOS)
    image.save(output, format="ICO", sizes=[(size, size) for size in sizes])
    return output

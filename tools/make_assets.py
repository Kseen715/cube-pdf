"""Draw assets/icon.png: a page under a magnifier.

The build makes every other icon from it (Tauri's "icon" command), and the
web page uses it as is. Run it after changing the drawing; the result is
committed, so building does not need Pillow.
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'assets'

CANVAS = 1024

BLUE = '#1e66c8'
PALE_BLUE = '#b9cdea'
TEXT_GREY = '#7a8ba3'
AMBER = '#ffb300'

PAGE = (230, 150, 730, 830)  # left, top, right, bottom
FOLD = 140
TEXT_LINE_WIDTHS = (330, 380, 300, 380, 250)
LENS_CENTER = (650, 640)
LENS_RADIUS = 165


def draw_page(draw: ImageDraw.ImageDraw) -> None:
    left, top, right, bottom = PAGE
    outline = [
        (left, top),
        (right - FOLD, top),
        (right, top + FOLD),
        (right, bottom),
        (left, bottom),
    ]
    corner = [
        (right - FOLD, top),
        (right - FOLD, top + FOLD),
        (right, top + FOLD),
    ]
    draw.polygon(outline, fill='white')
    draw.polygon(corner, fill=PALE_BLUE)

    for i, width in enumerate(TEXT_LINE_WIDTHS):
        y = 330 + i * 85
        line = (300, y, 300 + width, y + 36)
        draw.rounded_rectangle(line, radius=18, fill=TEXT_GREY)


def draw_magnifier(draw: ImageDraw.ImageDraw) -> None:
    cx, cy = LENS_CENTER
    r = LENS_RADIUS
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=AMBER, width=58)
    handle = (cx + 115, cy + 115, cx + 270, cy + 270)
    draw.line(handle, fill=AMBER, width=95)


def draw_icon() -> Image.Image:
    image = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    background = (40, 40, CANVAS - 40, CANVAS - 40)
    draw.rounded_rectangle(background, radius=180, fill=BLUE)
    draw_page(draw)
    draw_magnifier(draw)
    return image


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    draw_icon().save(ASSETS / 'icon.png')
    print(f'Wrote {ASSETS / "icon.png"}')


if __name__ == '__main__':
    main()

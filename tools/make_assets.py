"""Draw assets/app.ico (a page under a magnifier) and assets/splash.png."""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'assets'

# The splash shows the same name as the window title
sys.path.insert(0, str(ROOT / 'src'))
from ocr_app import APP_NAME  # noqa: E402

FONTS = Path(r'C:\Windows\Fonts')

# Drawn large, then downscaled by Pillow for each icon size
CANVAS = 1024
ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)

BLUE = '#1e66c8'
PALE_BLUE = '#b9cdea'
TEXT_GREY = '#7a8ba3'
AMBER = '#ffb300'
SPLASH_HINT = '#dbe7f7'

PAGE = (230, 150, 730, 830)  # left, top, right, bottom
FOLD = 140
TEXT_LINE_WIDTHS = (330, 380, 300, 380, 250)
LENS_CENTER = (650, 640)
LENS_RADIUS = 165

SPLASH_SIZE = (560, 200)
SPLASH_ICON_SIZE = 140


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


def draw_splash(icon: Image.Image) -> Image.Image:
    image = Image.new('RGB', SPLASH_SIZE, BLUE)
    size = (SPLASH_ICON_SIZE, SPLASH_ICON_SIZE)
    small_icon = icon.resize(size, Image.LANCZOS)
    image.paste(small_icon, (30, 30), small_icon)

    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(str(FONTS / 'segoeuib.ttf'), 34)
    hint_font = ImageFont.truetype(str(FONTS / 'segoeui.ttf'), 19)
    draw.text((195, 52), APP_NAME, font=title_font, fill='white')
    draw.text(
        (197, 108),
        'Программа запускается, подождите…',
        font=hint_font,
        fill=SPLASH_HINT,
    )
    return image


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    icon = draw_icon()
    icon.save(ASSETS / 'app.ico', sizes=[(s, s) for s in ICON_SIZES])
    draw_splash(icon).save(ASSETS / 'splash.png')
    print(f'Wrote assets to {ASSETS}')


if __name__ == '__main__':
    main()

"""Draw assets/icon.png: a cube whose side is a page of text.

The build makes every other icon from it (Tauri's "icon" command), and the
web page uses it as is. The cube in the page's top bar (web/index.html) is
the same drawing; change both together. Run it after changing the drawing;
the result is committed, so building does not need Pillow.
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'assets'

CANVAS = 1024

PAPER = '#f3f3f1'
INK = '#141414'
BLUE = '#1d5fbf'
PALE_BLUE = '#b9cdea'

# An isometric cube: the corners of its outline and its centre
TOP = (512, 92)
UPPER_LEFT = (148, 302)
UPPER_RIGHT = (876, 302)
CENTRE = (512, 512)
LOWER_LEFT = (148, 722)
LOWER_RIGHT = (876, 722)
BOTTOM = (512, 932)

# The text lines on the left side run along its edges, at 30 degrees
SLOPE = 0.577
LINE_START_X = 210
LINE_WIDTHS = (240, 270, 200)
LINE_PITCH = 100
LINE_HEIGHT = 34


def draw_text_lines(draw: ImageDraw.ImageDraw) -> None:
    x0 = LINE_START_X
    top = UPPER_LEFT[1] + (x0 - UPPER_LEFT[0]) * SLOPE + 100
    for i, width in enumerate(LINE_WIDTHS):
        y0 = top + i * LINE_PITCH
        x1, y1 = x0 + width, y0 + width * SLOPE
        line = [
            (x0, y0),
            (x1, y1),
            (x1, y1 + LINE_HEIGHT),
            (x0, y0 + LINE_HEIGHT),
        ]
        draw.polygon(line, fill=PALE_BLUE)


def draw_icon() -> Image.Image:
    image = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.polygon([TOP, UPPER_RIGHT, CENTRE, UPPER_LEFT], fill=PAPER)
    draw.polygon([UPPER_LEFT, CENTRE, BOTTOM, LOWER_LEFT], fill=BLUE)
    draw.polygon([CENTRE, UPPER_RIGHT, LOWER_RIGHT, BOTTOM], fill=INK)
    draw_text_lines(draw)
    return image


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    draw_icon().save(ASSETS / 'icon.png')
    print(f'Wrote {ASSETS / "icon.png"}')


if __name__ == '__main__':
    main()

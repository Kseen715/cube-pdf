"""Draw assets/app.ico (a page under a magnifying glass) and assets/splash.png."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parent.parent / 'assets'
S = 1024  # drawn large, downscaled by Pillow for each icon size
FONTS = Path(r'C:\Windows\Fonts')


def draw_icon() -> Image.Image:
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((40, 40, S - 40, S - 40), radius=180, fill='#1e66c8')
    page = (230, 150, 730, 830)
    fold = 140
    d.polygon(
        [(page[0], page[1]), (page[2] - fold, page[1]), (page[2], page[1] + fold),
         (page[2], page[3]), (page[0], page[3])],
        fill='white',
    )
    d.polygon(
        [(page[2] - fold, page[1]), (page[2] - fold, page[1] + fold), (page[2], page[1] + fold)],
        fill='#b9cdea',
    )
    for i, width in enumerate((330, 380, 300, 380, 250)):
        y = 330 + i * 85
        d.rounded_rectangle((300, y, 300 + width, y + 36), radius=18, fill='#7a8ba3')
    cx, cy, r = 650, 640, 165
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline='#ffb300', width=58)
    d.line((cx + 115, cy + 115, cx + 270, cy + 270), fill='#ffb300', width=95)
    return im


def draw_splash(icon: Image.Image) -> Image.Image:
    im = Image.new('RGB', (560, 200), '#1e66c8')
    im.paste(icon.resize((140, 140), Image.LANCZOS), (30, 30), icon.resize((140, 140), Image.LANCZOS))
    d = ImageDraw.Draw(im)
    d.text((195, 52), 'Распознавание PDF', font=ImageFont.truetype(str(FONTS / 'segoeuib.ttf'), 34), fill='white')
    d.text((197, 108), 'Программа запускается, подождите…', font=ImageFont.truetype(str(FONTS / 'segoeui.ttf'), 19), fill='#dbe7f7')
    return im


if __name__ == '__main__':
    ASSETS.mkdir(exist_ok=True)
    icon = draw_icon()
    icon.save(ASSETS / 'app.ico', sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    draw_splash(icon).save(ASSETS / 'splash.png')
    print(f'Wrote assets to {ASSETS}')

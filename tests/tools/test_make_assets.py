"""tools/make_assets.py draws the icons committed in assets/."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from PIL import Image
from support import ROOT, make_assets


class DrawIcon(unittest.TestCase):
    def assert_committed(self, drawn: Image.Image, name: str):
        with Image.open(ROOT / 'assets' / name) as committed:
            self.assertEqual(drawn.size, committed.size)
            self.assertEqual(drawn.mode, 'RGBA')
            self.assertEqual(
                drawn.tobytes(), committed.convert('RGBA').tobytes()
            )

    def test_matches_the_committed_icon(self):
        self.assert_committed(make_assets.draw_icon(), 'icon.png')

    def test_matches_the_committed_android_foreground(self):
        self.assert_committed(
            make_assets.draw_android_foreground(), 'icon-android.png'
        )

    def test_android_cube_stays_in_the_safe_zone(self):
        image = make_assets.draw_android_foreground()
        centre = make_assets.CANVAS / 2
        safe_radius = make_assets.CANVAS * 33 / 108
        left, top, right, bottom = image.getbbox()
        self.assertLessEqual(centre - top, safe_radius)
        self.assertLessEqual(bottom - centre, safe_radius)


class Main(unittest.TestCase):
    def test_writes_both_icons(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets = Path(tmp) / 'assets'
            with (
                mock.patch.object(make_assets, 'ASSETS', assets),
                redirect_stdout(io.StringIO()),
            ):
                make_assets.main()
            for name in ('icon.png', 'icon-android.png'):
                with Image.open(assets / name) as written:
                    self.assertEqual(written.size, (make_assets.CANVAS,) * 2)


if __name__ == '__main__':
    unittest.main()

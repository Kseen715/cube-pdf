"""tools/make_assets.py draws the icon the committed assets/icon.png is."""

import unittest

from PIL import Image
from support import ROOT, make_assets


class DrawIcon(unittest.TestCase):
    def test_matches_the_committed_icon(self):
        drawn = make_assets.draw_icon()
        with Image.open(ROOT / 'assets' / 'icon.png') as committed:
            self.assertEqual(drawn.size, committed.size)
            self.assertEqual(drawn.mode, 'RGBA')
            self.assertEqual(
                drawn.tobytes(), committed.convert('RGBA').tobytes()
            )


if __name__ == '__main__':
    unittest.main()

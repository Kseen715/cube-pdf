"""tools/coverage_badge.py sums the lcov reports of the suites into one
badge."""

import json
import tempfile
import unittest
from pathlib import Path

from support import coverage_badge as cb


def lcov(*files: tuple[int, int]) -> str:
    return ''.join(
        f'SF:file{i}\nDA:1,1\nLH:{hit}\nLF:{found}\nend_of_record\n'
        for i, (hit, found) in enumerate(files)
    )


class Badge(unittest.TestCase):
    def test_sums_the_files_of_a_report(self):
        self.assertEqual(cb.lcov_lines(lcov((3, 4), (1, 6))), (4, 10))

    def test_rounds_down(self):
        self.assertEqual(cb.badge(999, 1000)['message'], '99%')

    def test_colors_by_percentage(self):
        self.assertEqual(cb.badge(90, 100)['color'], 'brightgreen')
        self.assertEqual(cb.badge(89, 100)['color'], 'green')
        self.assertEqual(cb.badge(0, 100)['color'], 'red')

    def test_no_lines_is_unknown(self):
        self.assertEqual(cb.badge(0, 0)['message'], 'unknown')


class Update(unittest.TestCase):
    def test_counts_every_suite_with_its_last_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            badges = Path(tmp)
            cb.update(badges, 'core', lcov((1, 10)))
            cb.update(badges, 'web', lcov((5, 10)))
            cb.update(badges, 'web', lcov((9, 10)))

            written = json.loads((badges / 'coverage.json').read_text())
            self.assertEqual(written['message'], '50%')
            self.assertEqual(written['schemaVersion'], 1)


if __name__ == '__main__':
    unittest.main()

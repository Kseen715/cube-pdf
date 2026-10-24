"""Update the coverage badge of the README with one suite's test coverage.

Usage: python3 tools/coverage_badge.py BADGES_DIR SUITE LCOV_FILE

CI runs it after each suite of tests (tools, web, core) in a checkout of
the badges branch. It keeps the suite's covered and coverable lines in
BADGES_DIR/suites/SUITE.json and writes BADGES_DIR/coverage.json, the
shields.io endpoint the README badge reads, from the sum of all suites
there. A suite that did not run, like core.yml when the core is unchanged,
counts with its last numbers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# The lowest percentage for each color, from the top; shields.io's names
COLORS = (
    (90, 'brightgreen'),
    (75, 'green'),
    (60, 'yellowgreen'),
    (40, 'yellow'),
    (20, 'orange'),
    (0, 'red'),
)


def lcov_lines(text: str) -> tuple[int, int]:
    """The covered and coverable lines of every file in an lcov report."""
    hit = found = 0
    for line in text.splitlines():
        if line.startswith('LH:'):
            hit += int(line[3:])
        elif line.startswith('LF:'):
            found += int(line[3:])
    return hit, found


def badge(hit: int, found: int) -> dict:
    if not found:
        return badge_json('unknown', 'lightgrey')
    # Rounded down, so the badge never shows 100% with lines left uncovered
    percent = hit * 100 // found
    color = next(name for least, name in COLORS if percent >= least)
    return badge_json(f'{percent}%', color)


def badge_json(message: str, color: str) -> dict:
    return {
        'schemaVersion': 1,
        'label': 'coverage',
        'message': message,
        'color': color,
    }


def update(badges_dir: Path, suite: str, lcov: str) -> dict:
    suites = badges_dir / 'suites'
    suites.mkdir(parents=True, exist_ok=True)
    hit, found = lcov_lines(lcov)
    (suites / f'{suite}.json').write_text(
        json.dumps({'hit': hit, 'found': found}) + '\n'
    )

    totals = [json.loads(path.read_text()) for path in suites.glob('*.json')]
    result = badge(
        sum(total['hit'] for total in totals),
        sum(total['found'] for total in totals),
    )
    (badges_dir / 'coverage.json').write_text(json.dumps(result) + '\n')
    return result


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    badges_dir, suite, lcov_file = Path(sys.argv[1]), *sys.argv[2:]

    lcov = Path(lcov_file).read_text(encoding='utf-8')
    result = update(badges_dir, suite, lcov)
    print(f'Coverage with {suite}: {result["message"]}')


if __name__ == '__main__':
    main()

"""Entry point: the same exe is the window and, with --worker, the OCR process."""

from __future__ import annotations

import sys


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == '--worker':
        from ocr_app import worker

        return worker.main(sys.argv[2])

    from ocr_app import gui

    # Files dropped onto the exe icon arrive as arguments
    return gui.main(sys.argv[1:])

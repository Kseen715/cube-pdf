"""Locate bundled resources and point the environment at the bundled programs."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def resource_root() -> Path:
    """Folder holding vendor/ and assets/: the unpacked exe, or the repo checkout."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2]


def asset(name: str) -> Path:
    return resource_root() / 'assets' / name


def legal_file(name: str) -> Path:
    """LICENSE or THIRD-PARTY-NOTICES.txt (generated into build/ in a checkout)."""
    if getattr(sys, 'frozen', False) or name == 'LICENSE':
        return resource_root() / name
    return resource_root() / 'build' / name


def activate_vendor_programs() -> None:
    """Make OCRmyPDF use the bundled Tesseract and Ghostscript.

    OCRmyPDF searches PATH before the registry and Program Files, so prepending
    the bundled folders wins over any system-wide installation.
    """
    vendor = resource_root() / 'vendor'
    tesseract = vendor / 'tesseract'
    ghostscript = vendor / 'ghostscript' / 'bin'
    os.environ['PATH'] = os.pathsep.join(
        [str(tesseract), str(ghostscript), os.environ.get('PATH', '')]
    )
    os.environ['TESSDATA_PREFIX'] = str(tesseract / 'tessdata')

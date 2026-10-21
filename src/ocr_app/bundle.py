"""Locate bundled resources and point the environment at bundled programs."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return getattr(sys, 'frozen', False)


def resource_root() -> Path:
    """The unpacked exe, or the repository checkout during development."""
    if is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2]


def asset(name: str) -> Path:
    return resource_root() / 'assets' / name


def legal_file(name: str) -> Path:
    # In a checkout, the notices are generated into build/, not committed
    if is_frozen() or name == 'LICENSE':
        return resource_root() / name
    return resource_root() / 'build' / name


def activate_vendor_programs() -> None:
    """Make OCRmyPDF use the bundled Tesseract and Ghostscript.

    OCRmyPDF searches PATH before the registry and Program Files, so
    prepending the bundled folders wins over any system-wide installation.
    """
    vendor = resource_root() / 'vendor'
    tesseract = vendor / 'tesseract'
    ghostscript = vendor / 'ghostscript' / 'bin'

    os.environ['PATH'] = os.pathsep.join(
        [str(tesseract), str(ghostscript), os.environ.get('PATH', '')]
    )
    os.environ['TESSDATA_PREFIX'] = str(tesseract / 'tessdata')

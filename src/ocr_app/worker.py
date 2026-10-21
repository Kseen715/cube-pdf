"""Worker process: runs OCRmyPDF on one file and reports through ocr_app.ipc.

The GUI starts this as a separate process (the same exe with --worker) so the
window never freezes and a job can be cancelled by killing the process.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import traceback
from pathlib import Path

from ocr_app import IMAGE_EXTENSIONS
from ocr_app.bundle import activate_vendor_programs
from ocr_app.ipc import emit

# Images without a believable resolution are assumed to be scans at this DPI
FALLBACK_IMAGE_DPI = 300


class _IpcLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            emit('log', level=record.levelname, msg=record.getMessage())
        except Exception:  # noqa: BLE001 - logging must never crash the job
            pass


def _hide_child_consoles() -> None:
    """Stop Tesseract/Ghostscript from flashing console windows.

    This process has no console (the exe is a GUI app), so Windows would give
    every console program it starts a new visible window.
    """
    original_init = subprocess.Popen.__init__

    def init(self, *args, **kwargs):
        kwargs['creationflags'] = kwargs.get('creationflags', 0) | subprocess.CREATE_NO_WINDOW
        original_init(self, *args, **kwargs)

    subprocess.Popen.__init__ = init


def _image_needs_dpi(path: Path) -> bool:
    if path.suffix.lower() not in IMAGE_EXTENSIONS:
        return False
    from PIL import Image

    try:
        with Image.open(path) as im:
            dpi = im.info.get('dpi')
    except OSError:
        return False  # let OCRmyPDF report the unreadable file
    return not dpi or min(float(d) for d in dpi) < 72


def _error_kind(exc: BaseException) -> str:
    from PIL import Image
    from ocrmypdf import exceptions as ex

    checks = [
        (ex.EncryptedPdfError, 'encrypted'),
        ((ex.PriorOcrFoundError, ex.TaggedPDFError), 'has_text'),
        (ex.OutputFileAccessError, 'output_access'),
        ((ex.InputFileError, ex.UnsupportedImageFormatError, ex.DpiError), 'bad_input'),
        (ex.MissingDependencyError, 'missing_dependency'),
        ((MemoryError, Image.DecompressionBombError), 'too_big'),
        (PermissionError, 'output_access'),
    ]
    for types, kind in checks:
        if isinstance(exc, types):
            return kind
    return 'other'


def run(job: dict) -> int:
    activate_vendor_programs()
    _hide_child_consoles()

    import ocrmypdf

    log = logging.getLogger('ocrmypdf')
    log.setLevel(logging.INFO)
    log.addHandler(_IpcLogHandler())

    input_file = Path(job['input'])
    output_file = Path(job['output'])
    options = dict(
        language=job['languages'],
        # Pages that already have text are copied as is, unless forced
        mode='force' if job.get('force') else 'skip',
        tagged_pdf_mode='ignore',
        # The original keeps its signature; only the new copy loses it
        invalidate_digital_signatures=True,
        rotate_pages=True,
        deskew=bool(job.get('deskew')),
        jobs=os.cpu_count() or 1,
        progress_bar=True,
        plugins=['ocr_app.progress_plugin'],
    )
    if _image_needs_dpi(input_file):
        options['image_dpi'] = FALLBACK_IMAGE_DPI

    try:
        ocrmypdf.ocr(input_file, output_file, **options)
    except Exception as exc:  # noqa: BLE001 - every failure goes to the GUI
        emit(
            'error',
            kind=_error_kind(exc),
            detail=f'{type(exc).__name__}: {exc}',
            trace=traceback.format_exc(),
        )
        return 1
    emit('done', output=str(output_file))
    return 0


def main(payload: str) -> int:
    return run(json.loads(payload))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))

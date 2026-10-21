"""OCRmyPDF plugin that reports progress to the GUI instead of drawing a console bar."""

from __future__ import annotations

from ocrmypdf import hookimpl

from ocr_app.ipc import emit


class IpcProgressBar:
    """Implements ocrmypdf.pluginspec.ProgressBar."""

    def __init__(self, *, total=None, desc=None, unit=None, disable=False, **kwargs):
        self.total = total
        self.desc = desc
        self.disable = disable
        self.done = 0

    def __enter__(self):
        if not self.disable:
            emit('progress', desc=self.desc, done=0, total=self.total)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def update(self, n=1, *, completed=None):
        self.done = completed if completed is not None else self.done + n
        if not self.disable:
            emit('progress', desc=self.desc, done=self.done, total=self.total)


@hookimpl
def get_progressbar_class():
    return IpcProgressBar

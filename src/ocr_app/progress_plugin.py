"""OCRmyPDF plugin that reports progress to the GUI, not to a console bar."""

from __future__ import annotations

from ocrmypdf import hookimpl

from ocr_app import ipc


class IpcProgressBar:
    """Implements ocrmypdf.pluginspec.ProgressBar."""

    def __init__(
        self, *, total=None, desc=None, unit=None, disable=False, **kwargs
    ):
        self.total = total
        self.desc = desc
        self.disable = disable
        self.done = 0

    def __enter__(self):
        self._report()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def update(self, n=1, *, completed=None):
        self.done = completed if completed is not None else self.done + n
        self._report()

    def _report(self) -> None:
        if not self.disable:
            ipc.emit(
                'progress', desc=self.desc, done=self.done, total=self.total
            )


@hookimpl
def get_progressbar_class():
    return IpcProgressBar

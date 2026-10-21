"""Start one worker process and deliver its messages to the GUI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from ocr_app import ipc
from ocr_app.bundle import is_frozen
from ocr_app.winjob import KillOnCloseJob

SRC_DIR = Path(__file__).resolve().parents[1]


def _command(payload: str) -> list[str]:
    if is_frozen():
        return [sys.executable, '--worker', payload]
    return [sys.executable, '-m', 'ocr_app', '--worker', payload]


def _environment(tmp: str) -> dict[str, str]:
    env = os.environ.copy()
    # Leftovers of a killed job stay in our own folder, deleted afterwards
    env.update(
        TMP=tmp,
        TEMP=tmp,
        PYINSTALLER_SUPPRESS_SPLASH_SCREEN='1',
    )
    if not is_frozen():
        env['PYTHONPATH'] = str(SRC_DIR)
    return env


def _to_message(line: str) -> dict | None:
    message = ipc.parse(line)
    if message is None and line.strip():
        return {'event': 'log', 'level': 'OUTPUT', 'msg': line.rstrip()}
    return message


class WorkerProcess(QObject):
    """One OCR job in its own process.

    The signals are emitted from a reader thread; Qt queues them, so the
    connected slots run in the GUI thread.
    """

    message = Signal(dict)
    finished = Signal(int)

    def __init__(self, job: dict) -> None:
        super().__init__()
        self._tmp = tempfile.mkdtemp(prefix='ocr_app_')
        self._proc = subprocess.Popen(
            _command(json.dumps(job)),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=_environment(self._tmp),
            creationflags=subprocess.CREATE_NO_WINDOW,
            encoding='utf-8',
            errors='replace',
        )
        self._job: KillOnCloseJob | None = KillOnCloseJob()
        self._job.assign(int(self._proc._handle))  # type: ignore[attr-defined]
        threading.Thread(target=self._pump, daemon=True).start()

    def cancel(self) -> None:
        if self._job:
            self._job.terminate()

    def _pump(self) -> None:
        for line in self._proc.stdout:  # type: ignore[union-attr]
            message = _to_message(line)
            if message:
                self.message.emit(message)
        code = self._proc.wait()

        # Detached first, so a late cancel() cannot use a closed handle
        job, self._job = self._job, None
        if job:
            job.close()
        shutil.rmtree(self._tmp, ignore_errors=True)

        self.finished.emit(code)

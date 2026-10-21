"""Worker-to-GUI messages: one JSON object per line on the worker's stdout."""

from __future__ import annotations

import json
import sys
import threading
from typing import Any

_lock = threading.Lock()


def emit(event: str, **fields: Any) -> None:
    # Pure ASCII, so the pipe's code page (often cp1251) cannot break a message
    line = json.dumps({'event': event, **fields}, ensure_ascii=True)
    with _lock:
        if sys.stdout is None:
            return
        sys.stdout.write(line + '\n')
        sys.stdout.flush()


def parse(line: str) -> dict[str, Any] | None:
    """Return the message in *line*, or None if it is stray text, not a message."""
    line = line.strip()
    if not line.startswith('{'):
        return None
    try:
        message = json.loads(line)
    except ValueError:
        return None
    return message if isinstance(message, dict) and 'event' in message else None

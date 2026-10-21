"""PyInstaller entry script (also runnable directly for development)."""

import sys
from pathlib import Path

if not getattr(sys, 'frozen', False):
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))

from ocr_app.main import main  # noqa: E402

sys.exit(main())

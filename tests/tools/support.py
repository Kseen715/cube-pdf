"""What the tests of tools/ share: the repository root and the tools.

The tools are scripts, not a package, so they are loaded from their files.
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_tool(name: str):
    path = ROOT / 'tools' / f'{name}.py'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


collect_licenses = load_tool('collect_licenses')
make_assets = load_tool('make_assets')

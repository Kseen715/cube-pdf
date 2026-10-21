"""Download and unpack the third-party programs that get bundled into the exe.

Result (git-ignored):
    vendor/tesseract/    tesseract.exe, its DLLs, tessdata/ with eng, rus, deu, osd
    vendor/ghostscript/  bin/gswin64c.exe, bin/gsdll64.dll, lib/

Installers are cached in vendor/_downloads and checked against pinned SHA-256
hashes. The NSIS installers are unpacked with 7-Zip, so nothing is installed
system-wide and no admin rights are needed.

Usage: python tools/fetch_vendor.py [--force]
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / 'vendor'
DOWNLOADS = VENDOR / '_downloads'

TESSERACT = (
    'https://github.com/tesseract-ocr/tesseract/releases/download/5.5.3/'
    'tesseract-ocr-w64-setup-5.5.3.20260724.exe',
    'bee9e3434bd94fd65387d9be28cd467a41f61b1275383b55b0f59a1331270ae4',
)
GHOSTSCRIPT = (
    'https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/'
    'gs10080/gs10080w64.exe',
    '52a91b8bf09298788d7a57b9206127026c23eacd75405f0a131e26dc381dce50',
)
# "tessdata" (not _fast/_best): the models Tesseract's own docs recommend.
TESSDATA_BASE = 'https://github.com/tesseract-ocr/tessdata/raw/4.1.0/'
TESSDATA = {
    'eng': 'daa0c97d651c19fba3b25e81317cd697e9908c8208090c94c3905381c23fc047',
    'rus': '681be2c2bead1bc7bd235df88c44e8e60ae73ae866840c0ad4e3b4c247bd37c2',
    'deu': '896b3b4956503ab9daa10285db330881b2d74b70d889b79262cc534b9ec699a4',
    'osd': 'e19f2ae860792fdf372cf48d8ce70ae5da3c4052962fe22e9de1f680c374bb0e',
}


def find_7z() -> str:
    for candidate in (
        shutil.which('7z'),
        r'C:\Program Files\7-Zip\7z.exe',
        r'C:\Program Files (x86)\7-Zip\7z.exe',
    ):
        if candidate and Path(candidate).is_file():
            return candidate
    sys.exit('7-Zip (7z.exe) is required to unpack the installers. Install it first.')


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, expected_sha256: str, name: str | None = None) -> Path:
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    target = DOWNLOADS / (name or url.rsplit('/', 1)[-1])
    if not target.exists() or sha256(target) != expected_sha256:
        print(f'Downloading {url}')
        partial = target.with_suffix(target.suffix + '.part')
        with urllib.request.urlopen(url) as resp, partial.open('wb') as out:
            shutil.copyfileobj(resp, out)
        partial.replace(target)
    actual = sha256(target)
    if actual != expected_sha256:
        sys.exit(f'SHA-256 mismatch for {target.name}: got {actual}')
    return target


def unpack_nsis(installer: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    subprocess.run(
        [find_7z(), 'x', '-y', f'-o{dest}', str(installer)],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    # NSIS bookkeeping, not part of the program
    shutil.rmtree(dest / '$PLUGINSDIR', ignore_errors=True)
    for uninstaller in dest.rglob('uninstall*.exe'):
        uninstaller.unlink()


def remove(paths) -> None:
    for path in paths:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def fetch_tesseract() -> None:
    dest = VENDOR / 'tesseract'
    unpack_nsis(download(*TESSERACT), dest)
    # Training tools, man pages and the Java debug viewer are not needed for OCR
    remove(p for p in dest.glob('*.exe') if p.name != 'tesseract.exe')
    remove(dest.glob('*.html'))
    remove([dest / 'doc'])
    tessdata = dest / 'tessdata'
    remove(tessdata.glob('*.jar'))
    # Replace whatever languages the installer ships with exactly our set
    remove(tessdata.glob('*.traineddata'))
    for lang, digest in TESSDATA.items():
        src = download(TESSDATA_BASE + f'{lang}.traineddata', digest)
        shutil.copy2(src, tessdata / src.name)


def fetch_ghostscript() -> None:
    dest = VENDOR / 'ghostscript'
    unpack_nsis(download(*GHOSTSCRIPT), dest)
    bin_dir = dest / 'bin'
    remove([dest / 'doc', dest / 'examples', bin_dir / 'gswin64.exe', bin_dir / 'gsdll64.lib'])
    remove(dest.glob('uninst*'))
    remove(dest.glob('vcredist*.exe'))
    # Ghostscript is built with MSVC; ship its runtime instead of the redist installer
    system32 = Path(r'C:\Windows\System32')
    for dll in ('msvcp140.dll', 'vcruntime140.dll', 'vcruntime140_1.dll'):
        if not (system32 / dll).exists():
            sys.exit(f'{dll} not found; install the Microsoft Visual C++ 2015+ x64 runtime')
        shutil.copy2(system32 / dll, bin_dir / dll)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--force', action='store_true', help='unpack again')
    args = parser.parse_args()

    if args.force or not (VENDOR / 'tesseract' / 'tesseract.exe').exists():
        fetch_tesseract()
    if args.force or not (VENDOR / 'ghostscript' / 'bin' / 'gswin64c.exe').exists():
        fetch_ghostscript()
    print(f'Vendor programs ready in {VENDOR}')


if __name__ == '__main__':
    main()

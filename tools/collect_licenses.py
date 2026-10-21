"""Write build/THIRD-PARTY-NOTICES.txt: every third-party component inside the exe.

Sources of the license texts:
    Python packages   their *.dist-info in the running environment, found by
                      walking the dependencies of the packages in REQUIREMENTS
    Python, PyInstaller bootloader
                      the interpreter's LICENSE.txt and PyInstaller's COPYING.txt
    Tesseract, Ghostscript
                      vendor/licenses/, copied from the installers by fetch_vendor.py
    Tesseract's DLLs  licenses/ in this repository (upstream license files)

Run it with the build venv's Python after fetch_vendor.py.
"""

from __future__ import annotations

import sys
from importlib import metadata
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parent.parent
LICENSES = ROOT / 'licenses'
VENDOR_LICENSES = ROOT / 'vendor' / 'licenses'
OUTPUT = ROOT / 'build' / 'THIRD-PARTY-NOTICES.txt'
SOURCE_URL = 'https://github.com/Kseen715/ocrmypdf-app'

# Top-level runtime packages; PyInstaller itself is a build tool, not shipped
REQUIREMENTS = ['ocrmypdf', 'PySide6-Essentials']

# (component, version, SPDX license, license files, source)
# Files are relative to licenses/ unless they start with 'vendor:'.
NATIVE = [
    ('Tesseract OCR (tesseract.exe, libtesseract-5.dll)', '5.5.3', 'Apache-2.0',
     ['vendor:tesseract.txt'], 'https://github.com/tesseract-ocr/tesseract'),
    ('Tesseract language data (eng, rus, deu, osd)', '4.1.0', 'Apache-2.0',
     ['vendor:tesseract.txt'], 'https://github.com/tesseract-ocr/tessdata'),
    ('Ghostscript (gswin64c.exe, gsdll64.dll, lib/, Resource/, iccprofiles/)', '10.08.0',
     'AGPL-3.0-or-later', ['vendor:ghostscript.txt'],
     'ghostscript-10.08.0.tar.xz, attached to every release of this program'),
    ('Leptonica (libleptonica-6.dll)', '1.87.0', 'BSD-2-Clause',
     ['leptonica.txt'], 'https://github.com/DanBloomberg/leptonica'),
    ('libarchive (libarchive-13.dll)', '3.8.8', 'BSD-2-Clause',
     ['libarchive.txt'], 'https://github.com/libarchive/libarchive'),
    ('libb2 / BLAKE2 (libb2-1.dll)', '', 'CC0-1.0',
     ['libb2.txt'], 'https://github.com/BLAKE2/libb2'),
    ('Brotli (libbrotlicommon.dll, libbrotlidec.dll)', '1.2.0', 'MIT',
     ['brotli.txt'], 'https://github.com/google/brotli'),
    ('bzip2 (libbz2-1.dll)', '1.0.8', 'bzip2-1.0.6',
     ['bzip2.txt'], 'https://gitlab.com/bzip2/bzip2'),
    ('curl (libcurl-4.dll)', '8.21.0', 'curl',
     ['curl.txt'], 'https://github.com/curl/curl'),
    ('libdeflate (libdeflate.dll)', '', 'MIT',
     ['libdeflate.txt'], 'https://github.com/ebiggers/libdeflate'),
    ('Expat (libexpat-1.dll)', '2.8.2', 'MIT',
     ['expat.txt'], 'https://github.com/libexpat/libexpat'),
    ('GCC runtime libraries (libgcc_s_seh-1.dll, libstdc++-6.dll)', '',
     'GPL-3.0-or-later WITH GCC-exception-3.1',
     ['GPL-3.0.txt', 'gcc-runtime-exception.txt'], 'https://gcc.gnu.org'),
    ('GIFLIB (libgif-7.dll)', '5.2.2', 'MIT',
     ['giflib.txt'], 'https://sourceforge.net/projects/giflib/'),
    ('GNU libiconv (libiconv-2.dll)', '1.19', 'LGPL-2.1-or-later',
     ['LGPL-2.1.txt'], 'libiconv-1.19.tar.gz, attached to every release of this program'),
    ('libidn2 (libidn2-0.dll)', '2.3.8', 'LGPL-3.0-or-later OR GPL-2.0-or-later',
     ['LGPL-3.0.txt', 'GPL-3.0.txt', 'GPL-2.0.txt'],
     'libidn2-2.3.8.tar.gz, attached to every release of this program'),
    ('GNU gettext runtime (libintl-8.dll)', '1.0', 'LGPL-2.1-or-later',
     ['LGPL-2.1.txt'], 'gettext-1.0.tar.gz, attached to every release of this program'),
    ('JBIG-KIT (libjbig-0.dll)', '2.1', 'GPL-2.0-or-later',
     ['GPL-2.0.txt'], 'jbigkit-2.1.tar.gz, attached to every release of this program'),
    ('libjpeg-turbo (libjpeg-8.dll)', '3.1.3', 'IJG AND BSD-3-Clause AND Zlib',
     ['libjpeg-turbo.md', 'libjpeg-turbo-ijg.txt'],
     'https://github.com/libjpeg-turbo/libjpeg-turbo'),
    ('LERC (libLerc.dll)', '', 'Apache-2.0',
     ['lerc.txt'], 'https://github.com/Esri/lerc'),
    ('LZ4 (liblz4.dll)', '1.10.0', 'BSD-2-Clause',
     ['lz4.txt'], 'https://github.com/lz4/lz4'),
    ('XZ Utils (liblzma-5.dll)', '5.8.3', '0BSD',
     ['xz.txt', 'xz-0BSD.txt'], 'https://github.com/tukaani-project/xz'),
    ('OpenJPEG (libopenjp2-7.dll)', '2.5.4', 'BSD-2-Clause',
     ['openjpeg.txt'], 'https://github.com/uclouvain/openjpeg'),
    ('libpng (libpng16-16.dll)', '1.6.58', 'libpng-2.0',
     ['libpng.txt'], 'https://github.com/pnggroup/libpng'),
    ('libpsl (libpsl-5.dll)', '0.21.5', 'MIT',
     ['libpsl.txt'], 'https://github.com/rockdaboot/libpsl'),
    ('libssh2 (libssh2-1.dll)', '1.11.1', 'BSD-3-Clause',
     ['libssh2.txt'], 'https://github.com/libssh2/libssh2'),
    ('LibTIFF (libtiff-6.dll)', '4.7.2', 'libtiff',
     ['libtiff.md'], 'https://gitlab.com/libtiff/libtiff'),
    ('GNU libunistring (libunistring-5.dll)', '1.4.2', 'LGPL-3.0-or-later OR GPL-2.0-or-later',
     ['LGPL-3.0.txt', 'GPL-3.0.txt', 'GPL-2.0.txt'],
     'libunistring-1.4.2.tar.gz, attached to every release of this program'),
    ('libwebp (libwebp-7.dll, libwebpmux-3.dll, libsharpyuv-0.dll)', '1.6.0', 'BSD-3-Clause',
     ['libwebp.txt', 'libwebp-patents.txt'], 'https://github.com/webmproject/libwebp'),
    ('mingw-w64 winpthreads (libwinpthread-1.dll)', '', 'MIT AND BSD-3-Clause',
     ['winpthreads.txt'], 'https://github.com/mingw-w64/mingw-w64'),
    ('Zstandard (libzstd.dll)', '1.5.7', 'BSD-3-Clause',
     ['zstd.txt'], 'https://github.com/facebook/zstd'),
    ('zlib (zlib1.dll)', '1.3.2', 'Zlib',
     ['zlib.txt'], 'https://github.com/madler/zlib'),
]

HEADER = f"""\
OCR-PDF: third-party notices
============================

OCR-PDF is free software under the GNU Affero General Public License v3 or
later (see LICENSE). Its source code, the build scripts and this file are at
{SOURCE_URL}

OCR-PDF.exe contains the third-party components listed below, each under its
own license. The full license texts follow the list. The (A)GPL and LGPL
components are unmodified; the exact source code of each of them is attached
to every GitHub release of OCR-PDF, next to the exe.

The Microsoft Visual C++ runtime DLLs next to Ghostscript (msvcp140.dll,
vcruntime140.dll, vcruntime140_1.dll) are redistributed under the Microsoft
Visual Studio license terms for Distributable Code.
"""

RULE = '=' * 78


def runtime_distributions() -> list[metadata.Distribution]:
    """The installed distributions REQUIREMENTS need at run time, sorted by name."""
    found: dict[str, metadata.Distribution] = {}
    todo = [Requirement(r) for r in REQUIREMENTS]
    while todo:
        req = todo.pop()
        key = canonicalize_name(req.name)
        if key in found:
            continue
        dist = metadata.distribution(req.name)
        found[key] = dist
        for spec in dist.requires or []:
            dep = Requirement(spec)
            # Extras are never requested here, so 'extra == ...' markers are false
            if dep.marker is None or dep.marker.evaluate({'extra': ''}):
                todo.append(dep)
    return sorted(found.values(), key=lambda d: canonicalize_name(d.metadata['Name']))


def dist_license(dist: metadata.Distribution) -> str:
    meta = dist.metadata
    if meta.get('License-Expression'):
        return meta['License-Expression']
    # Old-style 'License' is free text, sometimes the whole license
    lines = (meta.get('License') or '').strip().splitlines()
    if lines and len(lines[0]) <= 80:
        return lines[0]
    classifiers = [c.rsplit(' :: ', 1)[-1] for c in meta.get_all('Classifier') or []
                   if c.startswith('License ::')]
    return ', '.join(classifiers) or 'see license text'


def dist_license_files(dist: metadata.Distribution) -> list[tuple[str, str]]:
    """(relative name, text) of the license files in the dist-info folder."""
    result = []
    for file in dist.files or []:
        parts = file.parts
        if not parts[0].endswith('.dist-info'):
            continue
        inner = parts[1:]
        if (inner and inner[0] == 'licenses') or (
            len(inner) == 1 and inner[0].upper().startswith(('LICENSE', 'COPYING', 'NOTICE'))
        ):
            result.append(('/'.join(inner), file.locate().read_text(encoding='utf-8', errors='replace')))
    return result


def license_text(name: str) -> str:
    if name.startswith('vendor:'):
        path = VENDOR_LICENSES / name.removeprefix('vendor:')
        if not path.exists():
            sys.exit(f'{path} is missing: run tools/fetch_vendor.py --force first')
    else:
        path = LICENSES / name
    return path.read_text(encoding='utf-8', errors='replace')


def section(title: str, body: str) -> str:
    return f'\n\n{RULE}\n{title}\n{RULE}\n\n{body.strip()}\n'


def main() -> None:
    dists = runtime_distributions()
    pyinstaller = metadata.distribution('pyinstaller')
    python_license = Path(sys.base_prefix) / 'LICENSE.txt'
    python_version = '.'.join(map(str, sys.version_info[:3]))
    lines = [HEADER, '\nComponents\n----------\n']

    def row(name: str, version: str, spdx: str, source: str) -> None:
        lines.append(f'* {name} {version}'.rstrip() + f'\n    License: {spdx}\n    Source: {source}\n')

    row('Python', python_version, 'PSF-2.0 (and the licenses in its LICENSE.txt)',
        'https://www.python.org/downloads/source/')
    row('PyInstaller bootloader', pyinstaller.version,
        'GPL-2.0-or-later WITH Bootloader-exception', 'https://github.com/pyinstaller/pyinstaller')
    for dist in dists:
        name = dist.metadata['Name']
        row(name, dist.version, dist_license(dist), f'https://pypi.org/project/{name}/{dist.version}/')
    lines.append(
        '  The PySide6 wheels contain Qt 6, licensed under LGPL-3.0-only. Qt in turn\n'
        '  includes third-party code listed at https://doc.qt.io/qt-6/licenses-used-in-qt.html\n'
    )
    for name, version, spdx, _, source in NATIVE:
        row(name, version, spdx, source)

    lines.append(section(f'Python {python_version}', python_license.read_text(encoding='utf-8')))
    for rel, text in dist_license_files(pyinstaller):
        lines.append(section(f'PyInstaller {pyinstaller.version}: {rel}', text))
    for dist in dists:
        title = f"{dist.metadata['Name']} {dist.version}"
        for rel, text in dist_license_files(dist):
            if rel.endswith('LicenseRef-Qt-Commercial.txt'):
                continue  # the commercial option does not apply to this build
            lines.append(section(f'{title}: {rel}', text))
        if canonicalize_name(dist.metadata['Name']) in {'pyside6-essentials', 'shiboken6'}:
            lines.append(section(f'{title}: LGPL-3.0', license_text('LGPL-3.0.txt')))
    shown: set[str] = set()
    for name, version, _, files, _ in NATIVE:
        for file in files:
            title = f'{name} {version}'.rstrip()
            if file in shown:
                lines.append(section(title, f'Licensed under the text of {file} above.'))
            else:
                shown.add(file)
                lines.append(section(f'{title}: {file.removeprefix("vendor:")}', license_text(file)))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(''.join(lines), encoding='utf-8', newline='\r\n')
    print(f'Wrote {OUTPUT} ({OUTPUT.stat().st_size // 1024} KB, {len(dists)} Python packages)')


if __name__ == '__main__':
    main()

"""Write build/THIRD-PARTY-NOTICES.txt: every third-party component in the exe.

Sources of the license texts:
    Python packages   their *.dist-info in the running environment, found by
                      walking the dependencies of the packages in REQUIREMENTS
    Python, PyInstaller bootloader
                      the interpreter's LICENSE.txt and PyInstaller's
                      COPYING.txt
    Tesseract, Ghostscript
                      vendor/licenses/, copied from the installers by
                      fetch_vendor.py
    Tesseract's DLLs  licenses/ in this repository (upstream license files)

Run it with the build venv's Python after fetch_vendor.py.
"""

from __future__ import annotations

import sys
from importlib import metadata
from pathlib import Path
from typing import NamedTuple

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parent.parent
LICENSES = ROOT / 'licenses'
VENDOR_LICENSES = ROOT / 'vendor' / 'licenses'
OUTPUT = ROOT / 'build' / 'THIRD-PARTY-NOTICES.txt'

# One source of truth for the repository URL: the app shows the same one
sys.path.insert(0, str(ROOT / 'src'))
from ocr_app import SOURCE_URL  # noqa: E402

# Top-level runtime packages; PyInstaller itself is a build tool, not shipped
REQUIREMENTS = ['ocrmypdf', 'PySide6-Essentials']

# Qt ships its LGPL text only in the Qt sources, not in these wheels
QT_DISTRIBUTIONS = {'pyside6-essentials', 'shiboken6'}
# The commercial license option does not apply to this build
SKIPPED_LICENSE_FILES = ('LicenseRef-Qt-Commercial.txt',)
LICENSE_FILE_PREFIXES = ('LICENSE', 'COPYING', 'NOTICE')
MAX_LICENSE_NAME_LENGTH = 80

VENDOR_PREFIX = 'vendor:'
RULE = '=' * 78


class Native(NamedTuple):
    name: str
    version: str
    spdx: str
    # Relative to licenses/, or to vendor/licenses/ with the 'vendor:' prefix
    files: list[str]
    source: str


def attached(tarball: str) -> str:
    return f'{tarball}, attached to every release of this program'


def github(project: str) -> str:
    return f'https://github.com/{project}'


LGPL3_OR_GPL2 = 'LGPL-3.0-or-later OR GPL-2.0-or-later'
LGPL3_OR_GPL2_FILES = ['LGPL-3.0.txt', 'GPL-3.0.txt', 'GPL-2.0.txt']

NATIVE = [
    Native(
        'Tesseract OCR (tesseract.exe, libtesseract-5.dll)',
        '5.5.3',
        'Apache-2.0',
        ['vendor:tesseract.txt'],
        github('tesseract-ocr/tesseract'),
    ),
    Native(
        'Tesseract language data (eng, rus, deu, osd)',
        '4.1.0',
        'Apache-2.0',
        ['vendor:tesseract.txt'],
        github('tesseract-ocr/tessdata'),
    ),
    Native(
        'Ghostscript (gswin64c.exe, gsdll64.dll, lib/, Resource/, '
        'iccprofiles/)',
        '10.08.0',
        'AGPL-3.0-or-later',
        ['vendor:ghostscript.txt'],
        attached('ghostscript-10.08.0.tar.xz'),
    ),
    Native(
        'Leptonica (libleptonica-6.dll)',
        '1.87.0',
        'BSD-2-Clause',
        ['leptonica.txt'],
        github('DanBloomberg/leptonica'),
    ),
    Native(
        'libarchive (libarchive-13.dll)',
        '3.8.8',
        'BSD-2-Clause',
        ['libarchive.txt'],
        github('libarchive/libarchive'),
    ),
    Native(
        'libb2 / BLAKE2 (libb2-1.dll)',
        '',
        'CC0-1.0',
        ['libb2.txt'],
        github('BLAKE2/libb2'),
    ),
    Native(
        'Brotli (libbrotlicommon.dll, libbrotlidec.dll)',
        '1.2.0',
        'MIT',
        ['brotli.txt'],
        github('google/brotli'),
    ),
    Native(
        'bzip2 (libbz2-1.dll)',
        '1.0.8',
        'bzip2-1.0.6',
        ['bzip2.txt'],
        'https://gitlab.com/bzip2/bzip2',
    ),
    Native(
        'curl (libcurl-4.dll)',
        '8.21.0',
        'curl',
        ['curl.txt'],
        github('curl/curl'),
    ),
    Native(
        'libdeflate (libdeflate.dll)',
        '',
        'MIT',
        ['libdeflate.txt'],
        github('ebiggers/libdeflate'),
    ),
    Native(
        'Expat (libexpat-1.dll)',
        '2.8.2',
        'MIT',
        ['expat.txt'],
        github('libexpat/libexpat'),
    ),
    Native(
        'GCC runtime libraries (libgcc_s_seh-1.dll, libstdc++-6.dll)',
        '',
        'GPL-3.0-or-later WITH GCC-exception-3.1',
        ['GPL-3.0.txt', 'gcc-runtime-exception.txt'],
        'https://gcc.gnu.org',
    ),
    Native(
        'GIFLIB (libgif-7.dll)',
        '5.2.2',
        'MIT',
        ['giflib.txt'],
        'https://sourceforge.net/projects/giflib/',
    ),
    Native(
        'GNU libiconv (libiconv-2.dll)',
        '1.19',
        'LGPL-2.1-or-later',
        ['LGPL-2.1.txt'],
        attached('libiconv-1.19.tar.gz'),
    ),
    Native(
        'libidn2 (libidn2-0.dll)',
        '2.3.8',
        LGPL3_OR_GPL2,
        LGPL3_OR_GPL2_FILES,
        attached('libidn2-2.3.8.tar.gz'),
    ),
    Native(
        'GNU gettext runtime (libintl-8.dll)',
        '1.0',
        'LGPL-2.1-or-later',
        ['LGPL-2.1.txt'],
        attached('gettext-1.0.tar.gz'),
    ),
    Native(
        'JBIG-KIT (libjbig-0.dll)',
        '2.1',
        'GPL-2.0-or-later',
        ['GPL-2.0.txt'],
        attached('jbigkit-2.1.tar.gz'),
    ),
    Native(
        'libjpeg-turbo (libjpeg-8.dll)',
        '3.1.3',
        'IJG AND BSD-3-Clause AND Zlib',
        ['libjpeg-turbo.md', 'libjpeg-turbo-ijg.txt'],
        github('libjpeg-turbo/libjpeg-turbo'),
    ),
    Native(
        'LERC (libLerc.dll)',
        '',
        'Apache-2.0',
        ['lerc.txt'],
        github('Esri/lerc'),
    ),
    Native(
        'LZ4 (liblz4.dll)',
        '1.10.0',
        'BSD-2-Clause',
        ['lz4.txt'],
        github('lz4/lz4'),
    ),
    Native(
        'XZ Utils (liblzma-5.dll)',
        '5.8.3',
        '0BSD',
        ['xz.txt', 'xz-0BSD.txt'],
        github('tukaani-project/xz'),
    ),
    Native(
        'OpenJPEG (libopenjp2-7.dll)',
        '2.5.4',
        'BSD-2-Clause',
        ['openjpeg.txt'],
        github('uclouvain/openjpeg'),
    ),
    Native(
        'libpng (libpng16-16.dll)',
        '1.6.58',
        'libpng-2.0',
        ['libpng.txt'],
        github('pnggroup/libpng'),
    ),
    Native(
        'libpsl (libpsl-5.dll)',
        '0.21.5',
        'MIT',
        ['libpsl.txt'],
        github('rockdaboot/libpsl'),
    ),
    Native(
        'libssh2 (libssh2-1.dll)',
        '1.11.1',
        'BSD-3-Clause',
        ['libssh2.txt'],
        github('libssh2/libssh2'),
    ),
    Native(
        'LibTIFF (libtiff-6.dll)',
        '4.7.2',
        'libtiff',
        ['libtiff.md'],
        'https://gitlab.com/libtiff/libtiff',
    ),
    Native(
        'GNU libunistring (libunistring-5.dll)',
        '1.4.2',
        LGPL3_OR_GPL2,
        LGPL3_OR_GPL2_FILES,
        attached('libunistring-1.4.2.tar.gz'),
    ),
    Native(
        'libwebp (libwebp-7.dll, libwebpmux-3.dll, libsharpyuv-0.dll)',
        '1.6.0',
        'BSD-3-Clause',
        ['libwebp.txt', 'libwebp-patents.txt'],
        github('webmproject/libwebp'),
    ),
    Native(
        'mingw-w64 winpthreads (libwinpthread-1.dll)',
        '',
        'MIT AND BSD-3-Clause',
        ['winpthreads.txt'],
        github('mingw-w64/mingw-w64'),
    ),
    Native(
        'Zstandard (libzstd.dll)',
        '1.5.7',
        'BSD-3-Clause',
        ['zstd.txt'],
        github('facebook/zstd'),
    ),
    Native(
        'zlib (zlib1.dll)',
        '1.3.2',
        'Zlib',
        ['zlib.txt'],
        github('madler/zlib'),
    ),
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

QT_NOTE = (
    '  The PySide6 wheels contain Qt 6, licensed under LGPL-3.0-only. Qt in '
    'turn\n  includes third-party code listed at '
    'https://doc.qt.io/qt-6/licenses-used-in-qt.html\n'
)


def runtime_distributions() -> list[metadata.Distribution]:
    """The distributions REQUIREMENTS need at run time, sorted by name."""
    found: dict[str, metadata.Distribution] = {}
    todo = [Requirement(r) for r in REQUIREMENTS]
    while todo:
        requirement = todo.pop()
        key = canonicalize_name(requirement.name)
        if key in found:
            continue
        dist = metadata.distribution(requirement.name)
        found[key] = dist
        for spec in dist.requires or []:
            dependency = Requirement(spec)
            # Extras are never requested, so 'extra == ...' markers are false
            marker = dependency.marker
            if marker is None or marker.evaluate({'extra': ''}):
                todo.append(dependency)
    return sorted(found.values(), key=dist_key)


def dist_key(dist: metadata.Distribution) -> str:
    return canonicalize_name(dist.metadata['Name'])


def dist_title(dist: metadata.Distribution) -> str:
    return f'{dist.metadata["Name"]} {dist.version}'


def dist_license(dist: metadata.Distribution) -> str:
    meta = dist.metadata
    if meta.get('License-Expression'):
        return meta['License-Expression']

    # Old-style 'License' is free text, sometimes the whole license
    lines = (meta.get('License') or '').strip().splitlines()
    if lines and len(lines[0]) <= MAX_LICENSE_NAME_LENGTH:
        return lines[0]

    classifiers = [
        c.rsplit(' :: ', 1)[-1]
        for c in meta.get_all('Classifier') or []
        if c.startswith('License ::')
    ]
    return ', '.join(classifiers) or 'see license text'


def is_license_file(inner: tuple[str, ...]) -> bool:
    """Whether a path inside a .dist-info folder is a license file."""
    if inner and inner[0] == 'licenses':
        return True
    if len(inner) != 1:
        return False
    return inner[0].upper().startswith(LICENSE_FILE_PREFIXES)


def dist_license_files(dist: metadata.Distribution) -> list[tuple[str, str]]:
    """(name inside .dist-info, text) of every license file of dist."""
    result = []
    for file in dist.files or []:
        folder, *inner = file.parts
        if folder.endswith('.dist-info') and is_license_file(tuple(inner)):
            text = file.locate().read_text(encoding='utf-8', errors='replace')
            result.append(('/'.join(inner), text))
    return result


def license_text(name: str) -> str:
    if name.startswith(VENDOR_PREFIX):
        path = VENDOR_LICENSES / name.removeprefix(VENDOR_PREFIX)
        if not path.exists():
            sys.exit(f'{path} is missing: run tools/fetch_vendor.py --force')
    else:
        path = LICENSES / name
    return path.read_text(encoding='utf-8', errors='replace')


def row(name: str, version: str, spdx: str, source: str) -> str:
    title = f'* {name} {version}'.rstrip()
    return f'{title}\n    License: {spdx}\n    Source: {source}\n'


def section(title: str, body: str) -> str:
    return f'\n\n{RULE}\n{title}\n{RULE}\n\n{body.strip()}\n'


def python_version() -> str:
    return '.'.join(map(str, sys.version_info[:3]))


def component_list(
    dists: list[metadata.Distribution], pyinstaller: metadata.Distribution
) -> list[str]:
    rows = [
        row(
            'Python',
            python_version(),
            'PSF-2.0 (and the licenses in its LICENSE.txt)',
            'https://www.python.org/downloads/source/',
        ),
        row(
            'PyInstaller bootloader',
            pyinstaller.version,
            'GPL-2.0-or-later WITH Bootloader-exception',
            github('pyinstaller/pyinstaller'),
        ),
    ]
    for dist in dists:
        name = dist.metadata['Name']
        pypi = f'https://pypi.org/project/{name}/{dist.version}/'
        rows.append(row(name, dist.version, dist_license(dist), pypi))
    rows.append(QT_NOTE)
    for native in NATIVE:
        rows.append(
            row(native.name, native.version, native.spdx, native.source)
        )
    return rows


def python_license_sections(
    dists: list[metadata.Distribution], pyinstaller: metadata.Distribution
) -> list[str]:
    python_license = Path(sys.base_prefix) / 'LICENSE.txt'
    sections = [
        section(
            f'Python {python_version()}',
            python_license.read_text(encoding='utf-8'),
        )
    ]
    for name, text in dist_license_files(pyinstaller):
        sections.append(
            section(f'PyInstaller {pyinstaller.version}: {name}', text)
        )

    for dist in dists:
        title = dist_title(dist)
        for name, text in dist_license_files(dist):
            if not name.endswith(SKIPPED_LICENSE_FILES):
                sections.append(section(f'{title}: {name}', text))
        if dist_key(dist) in QT_DISTRIBUTIONS:
            lgpl = license_text('LGPL-3.0.txt')
            sections.append(section(f'{title}: LGPL-3.0', lgpl))
    return sections


def native_license_sections() -> list[str]:
    # Shared texts such as the GPL are printed once and referenced after that
    sections = []
    shown: set[str] = set()
    for native in NATIVE:
        title = f'{native.name} {native.version}'.rstrip()
        for file in native.files:
            if file in shown:
                body = f'Licensed under the text of {file} above.'
                sections.append(section(title, body))
            else:
                shown.add(file)
                name = file.removeprefix(VENDOR_PREFIX)
                sections.append(section(f'{title}: {name}', license_text(file)))
    return sections


def main() -> None:
    dists = runtime_distributions()
    pyinstaller = metadata.distribution('pyinstaller')
    parts = [
        HEADER,
        '\nComponents\n----------\n',
        *component_list(dists, pyinstaller),
        *python_license_sections(dists, pyinstaller),
        *native_license_sections(),
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(''.join(parts), encoding='utf-8', newline='\r\n')

    size_kb = OUTPUT.stat().st_size // 1024
    print(f'Wrote {OUTPUT} ({size_kb} KB, {len(dists)} Python packages)')


if __name__ == '__main__':
    main()

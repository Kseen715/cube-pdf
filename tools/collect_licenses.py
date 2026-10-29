"""Write THIRD-PARTY-NOTICES.txt: every third-party component of one build.

Usage: python3 tools/collect_licenses.py linux|windows|wasm|android \
           BUILD_DIR OUTPUT

The Makefile runs it inside the build container once the libraries are
built, because every license text is read from where it comes from:

    src:<package>/<path>   the unpacked upstream source, BUILD_DIR/src
    toolchain:<path>       the target's toolchain: Emscripten ($EMSDK) or
                           the Android NDK ($NDK_HOME)
    <name>                 licenses/ in this repository, for what has no
                           source tree in the build: the compiler runtimes
                           and the Android libraries
    Rust crates            their own license files, listed by
                           `cargo metadata` for the app
    Android libraries      listed in the Gradle lockfile of the Android
                           project
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent
LICENSES = ROOT / 'licenses'
VERSIONS_MK = ROOT / 'deps' / 'versions.mk'
CONFIG_JS = ROOT / 'web' / 'js' / 'config.js'
DESKTOP = ROOT / 'desktop'
GRADLE_LOCKFILE = DESKTOP / 'gen' / 'android' / 'app' / 'gradle.lockfile'

# The Rust target whose crates each app has; every Android ABI has the same
APP_TARGETS = {
    'linux': 'x86_64-unknown-linux-gnu',
    'windows': 'x86_64-pc-windows-msvc',
    'android': 'aarch64-linux-android',
}
ALL_TARGETS = ('linux', 'windows', 'wasm', 'android')

# Licenses a Rust crate may use: all of them allow combining with the AGPL
ALLOWED_LICENSES = {
    '0BSD',
    'Apache-2.0',
    'BSD-2-Clause',
    'BSD-3-Clause',
    'BSL-1.0',
    'CC0-1.0',
    'CDLA-Permissive-2.0',
    'ISC',
    'MIT',
    'MIT-0',
    'MPL-2.0',
    'Unicode-3.0',
    'Unicode-DFS-2016',
    'Unlicense',
    'Zlib',
}
LICENSE_FILE = re.compile(r'^(licen[cs]e|copying|notice|unlicense)', re.I)

# The Maven groups the APK may take libraries from, with their license and
# its text in licenses/. Only add a group after checking the license of
# every library in it, as for ALLOWED_LICENSES.
# A group ending in "." also stands for the groups under it.
APACHE = ('Apache-2.0', 'Apache-2.0.txt')
ANDROID_GROUPS = {
    'androidx.': APACHE,
    'com.fasterxml.jackson': APACHE,
    'com.fasterxml.jackson.': APACHE,
    'com.google.android.material': APACHE,
    'com.google.errorprone': APACHE,
    'com.google.guava': APACHE,
    'org.jetbrains': APACHE,
    'org.jetbrains.kotlin': APACHE,
    'org.jetbrains.kotlinx': APACHE,
    'org.jspecify': APACHE,
}
# The Gradle configuration of what goes into the release APK
ANDROID_RUNTIME = 'universalReleaseRuntimeClasspath'
RULE = '=' * 78


class Component(NamedTuple):
    name: str
    version: str
    spdx: str
    files: list[str]
    source: str
    targets: tuple[str, ...] = ALL_TARGETS


def read_versions() -> dict[str, str]:
    """The NAME := value lines of deps/versions.mk, with $(NAME) expanded."""
    text = VERSIONS_MK.read_text(encoding='utf-8').replace('\\\n', ' ')
    values: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r'^(\w+)\s*:=\s*(.*)$', line)
        if match:
            name, value = match.groups()
            values[name] = re.sub(
                r'\$\((\w+)\)', lambda m: values[m.group(1)], value.strip()
            )
    return values


def source_url() -> str:
    match = re.search(
        r"SOURCE_URL = '([^']+)'", CONFIG_JS.read_text(encoding='utf-8')
    )
    if not match:
        sys.exit(f'SOURCE_URL not found in {CONFIG_JS}')
    return match.group(1)


def compiler_version(command: str) -> str:
    """Empty when the compiler belongs to another target's container."""
    try:
        result = subprocess.run(
            [command, '-dumpfullversion'], capture_output=True, text=True
        )
    except FileNotFoundError:
        return ''
    return result.stdout.strip()


def ndk_version() -> str:
    """Empty outside the Android container."""
    properties = Path(os.environ.get('NDK_HOME', '/')) / 'source.properties'
    if not properties.exists():
        return ''
    match = re.search(r'Pkg\.ReleaseName = (\S+)', properties.read_text())
    return match.group(1) if match else ''


def components(v: dict[str, str]) -> list[Component]:
    def attached(package: str) -> str:
        return f'{v[package + "_FILE"]}, attached to every release'

    def font(name: str, package: str, use: str) -> Component:
        folder = package.lower().replace('_', '-')
        return Component(
            f'{name}, the typeface of {use}',
            f'{v[package + "_VERSION"]} (Fontsource)',
            'OFL-1.1',
            [f'src:{folder}/LICENSE'],
            v[package + '_HOME'],
        )

    both = 'compiled into MuPDF and Ghostscript'
    return [
        Component(
            'Tesseract OCR',
            v['TESSERACT_VERSION'],
            'Apache-2.0',
            ['src:tesseract/LICENSE'],
            v['TESSERACT_HOME'],
        ),
        Component(
            'Tesseract language data (eng, rus, deu, ita, osd)',
            v['TESSDATA_VERSION'],
            'Apache-2.0',
            ['src:tesseract/LICENSE'],
            v['TESSDATA_HOME'],
        ),
        Component(
            'Leptonica',
            v['LEPTONICA_VERSION'],
            'BSD-2-Clause',
            ['src:leptonica/leptonica-license.txt'],
            v['LEPTONICA_HOME'],
        ),
        Component(
            'zlib',
            v['ZLIB_VERSION'],
            'Zlib',
            ['src:zlib/LICENSE'],
            v['ZLIB_HOME'],
        ),
        Component(
            'MuPDF',
            v['MUPDF_VERSION'],
            'AGPL-3.0-or-later',
            ['src:mupdf/COPYING'],
            attached('MUPDF'),
        ),
        Component(
            'Ghostscript (ocr-pdf-gs)',
            v['GHOSTSCRIPT_VERSION'],
            'AGPL-3.0-or-later',
            ['src:ghostscript/LICENSE', 'src:mupdf/COPYING'],
            attached('GHOSTSCRIPT'),
        ),
        Component(
            f'FreeType, {both}',
            '2.14.3',
            'FTL',
            ['src:mupdf/thirdparty/freetype/docs/FTL.TXT'],
            'https://freetype.org',
        ),
        Component(
            f'IJG libjpeg, {both}',
            '10',
            'IJG',
            ['src:mupdf/thirdparty/libjpeg/README'],
            'https://ijg.org',
        ),
        Component(
            f'OpenJPEG, {both}',
            '2.5.4',
            'BSD-2-Clause',
            ['src:mupdf/thirdparty/openjpeg/LICENSE'],
            'https://github.com/uclouvain/openjpeg',
        ),
        Component(
            f'jbig2dec, {both}',
            '0.20',
            'AGPL-3.0-or-later',
            ['src:mupdf/thirdparty/jbig2dec/LICENSE', 'src:mupdf/COPYING'],
            'part of the MuPDF and Ghostscript sources',
        ),
        Component(
            f'Little CMS (lcms2mt), {both}',
            '2.19',
            'MIT',
            ['src:mupdf/thirdparty/lcms2/LICENSE'],
            'part of the MuPDF and Ghostscript sources',
        ),
        Component(
            'libpng, compiled into Ghostscript',
            '1.6.58',
            'libpng-2.0',
            ['src:ghostscript/libpng/LICENSE'],
            'part of the Ghostscript sources',
        ),
        Component(
            'Brotli, compiled into Ghostscript',
            '1.2.0',
            'MIT',
            ['src:ghostscript/brotli/LICENSE'],
            'part of the Ghostscript sources',
        ),
        Component(
            'extract, compiled into Ghostscript',
            '',
            'AGPL-3.0-or-later',
            ['src:ghostscript/extract/COPYING'],
            'part of the Ghostscript sources',
        ),
        font('Oswald', 'OSWALD', 'the headings'),
        font('Manrope', 'MANROPE', 'the window'),
        font('JetBrains Mono', 'JETBRAINS_MONO', 'labels and logs'),
        Component(
            'GCC runtime libraries (libstdc++, libgcc), linked statically',
            compiler_version(os.environ.get('CXX', 'g++')),
            'GPL-3.0-or-later WITH GCC-exception-3.1',
            ['GPL-3.0.txt', 'gcc-runtime-exception.txt'],
            'https://gcc.gnu.org',
            ('linux', 'windows'),
        ),
        Component(
            'MinGW-w64 runtime, linked statically',
            '12.0.0',
            'ZPL-2.1 AND MIT AND BSD-3-Clause AND public domain',
            ['mingw-w64-runtime.txt'],
            'https://github.com/mingw-w64/mingw-w64',
            ('windows',),
        ),
        Component(
            'MinGW-w64 winpthreads, linked statically',
            '12.0.0',
            'MIT AND BSD-3-Clause',
            ['winpthreads.txt'],
            'https://github.com/mingw-w64/mingw-w64',
            ('windows',),
        ),
        Component(
            'Emscripten runtime',
            compiler_version('emcc'),
            'MIT OR NCSA',
            ['toolchain:LICENSE'],
            'https://github.com/emscripten-core/emscripten',
            ('wasm',),
        ),
        Component(
            'musl libc (in the Emscripten runtime)',
            '',
            'MIT',
            ['toolchain:system/lib/libc/musl/COPYRIGHT'],
            'https://musl.libc.org',
            ('wasm',),
        ),
        Component(
            'LLVM libc++, libc++abi, compiler-rt (in the Emscripten runtime)',
            '',
            'Apache-2.0 WITH LLVM-exception',
            ['toolchain:system/lib/libcxx/LICENSE.TXT'],
            'https://github.com/llvm/llvm-project',
            ('wasm',),
        ),
        Component(
            'LLVM libc++, libc++abi, compiler-rt, libunwind (in the Android '
            'NDK), linked statically',
            ndk_version(),
            'Apache-2.0 WITH LLVM-exception',
            ['toolchain:toolchains/llvm/prebuilt/linux-x86_64/NOTICE'],
            'https://github.com/llvm/llvm-project',
            ('android',),
        ),
    ]


def toolchain_dir(target: str) -> Path:
    if target == 'android':
        return Path(os.environ['NDK_HOME'])
    return Path(os.environ['EMSDK']) / 'upstream' / 'emscripten'


def license_text(name: str, target: str, build_dir: Path) -> str:
    if name.startswith('src:'):
        path = build_dir / 'src' / name.removeprefix('src:')
    elif name.startswith('toolchain:'):
        path = toolchain_dir(target) / name.removeprefix('toolchain:')
    else:
        path = LICENSES / name
    return read_license(path)


def read_license(path: Path) -> str:
    if not path.exists():
        sys.exit(f'license file missing: {path}')
    return path.read_text(encoding='utf-8', errors='replace')


# --- Rust crates of the desktop app ------------------------------------------


class Crate(NamedTuple):
    name: str
    version: str
    spdx: str
    folder: Path


def cargo_metadata(triple: str) -> dict:
    command = [
        'cargo',
        'metadata',
        '--format-version',
        '1',
        '--manifest-path',
        str(DESKTOP / 'Cargo.toml'),
        '--filter-platform',
        triple,
    ]
    if (DESKTOP / 'Cargo.lock').exists():
        command.append('--locked')
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        sys.exit(f'cargo metadata failed:\n{result.stderr}')
    return json.loads(result.stdout)


def shipped_crates(triple: str) -> list[Crate]:
    """The crates compiled into the app: its normal dependencies, without
    the ones only build scripts and tests use."""
    meta = cargo_metadata(triple)
    nodes = {node['id']: node for node in meta['resolve']['nodes']}
    root = meta['resolve']['root']
    seen: set[str] = set()
    todo = [root]
    while todo:
        package = todo.pop()
        if package not in seen:
            seen.add(package)
            todo += [
                dep['pkg']
                for dep in nodes[package]['deps']
                if any(kind['kind'] is None for kind in dep['dep_kinds'])
            ]
    crates = [
        Crate(
            p['name'],
            p['version'],
            p['license'] or '',
            Path(p['manifest_path']).parent,
        )
        for p in meta['packages']
        if p['id'] in seen and p['id'] != root
    ]
    return sorted(crates, key=lambda crate: (crate.name, crate.version))


def license_allowed(expression: str) -> bool:
    """Whether an SPDX expression can be satisfied with ALLOWED_LICENSES.
    An exception (WITH) only adds permissions, so it is left out."""
    text = re.sub(r'\s+WITH\s+[\w.-]+', '', expression.replace('/', ' OR '))
    words = []
    for token in re.findall(r'[()]|[\w.+-]+', text):
        if token in ('(', ')'):
            words.append(token)
        elif token in ('AND', 'OR'):
            words.append(token.lower())
        else:
            words.append(str(token.rstrip('+') in ALLOWED_LICENSES))
    # Only True, False, and, or and brackets reach eval
    return bool(words) and eval(' '.join(words))


def crate_license_files(crate: Crate) -> list[tuple[str, str]]:
    return [
        (path.name, path.read_text(encoding='utf-8', errors='replace'))
        for path in sorted(crate.folder.iterdir())
        if path.is_file() and LICENSE_FILE.match(path.name)
    ]


def check_crates(crates: list[Crate]) -> None:
    refused = [c for c in crates if not license_allowed(c.spdx)]
    if refused:
        names = ', '.join(f'{c.name} {c.version} ({c.spdx})' for c in refused)
        sys.exit(f'Crates under licenses not cleared for CUBE-PDF: {names}')


# --- Android libraries of the APK --------------------------------------------


class Library(NamedTuple):
    name: str  # group:artifact
    version: str
    spdx: str
    text: str  # the license text, in licenses/


def library_license(name: str) -> tuple[str, str] | None:
    group = name.split(':')[0]
    for prefix, license in ANDROID_GROUPS.items():
        if group == prefix or prefix.endswith('.') and group.startswith(prefix):
            return license
    return None


def android_libraries() -> list[Library]:
    """The libraries Gradle puts into the release APK, as its lockfile
    pins them. Gradle fails the build when they differ from the lockfile."""
    if not GRADLE_LOCKFILE.exists():
        sys.exit(f'missing {GRADLE_LOCKFILE}')
    libraries, refused = [], []
    for line in GRADLE_LOCKFILE.read_text(encoding='utf-8').splitlines():
        coordinate, _, configurations = line.partition('=')
        if ANDROID_RUNTIME not in configurations.split(','):
            continue
        group, artifact, version = coordinate.split(':')
        name = f'{group}:{artifact}'
        license = library_license(name)
        if license:
            libraries.append(Library(name, version, *license))
        else:
            refused.append(coordinate)
    if refused:
        names = ', '.join(refused)
        sys.exit(f'Android libraries not cleared for CUBE-PDF: {names}')
    return sorted(libraries)


# --- the notices file --------------------------------------------------------

PROGRAMS = {
    'linux': 'The Linux packages of CUBE-PDF (CUBE-PDF, ocr-pdf-core and\n'
    'ocr-pdf-gs)',
    'windows': 'The Windows build of CUBE-PDF (CUBE-PDF.exe, ocr-pdf-core.exe\n'
    'and ocr-pdf-gs.exe)',
    'wasm': 'The web version of CUBE-PDF (ocr-core.wasm, gs.wasm and the\n'
    'JavaScript that loads them)',
    'android': 'The Android app of CUBE-PDF (the APK; ocr-pdf-core and\n'
    'ocr-pdf-gs are in it as lib*.so)',
}

HEADER = """\
CUBE-PDF: third-party notices
=============================

CUBE-PDF is free software under the GNU Affero General Public License v3 or
later (see LICENSE). Its source code, the build scripts and this file are at
{url}

{programs} contain the third-party components listed below,
each under its own license. The full license texts follow the list. Every
component is built from the source tarball named in deps/versions.mk, or,
for the fonts, taken from the Fontsource package named there. Their exact
source code, of the (A)GPL ones in particular, is attached to every GitHub
release of CUBE-PDF. Small patches (deps/patches) only make the sources
build for some targets, without changing what the programs do: Tesseract's
SIMD detection for WebAssembly and its CPU feature library for Android,
and a header of Ghostscript for Android's C library.

Portions of this software are copyright (C) The FreeType Project
(https://freetype.org). All rights reserved.

This software is based in part on the work of the Independent JPEG Group.
"""

PLATFORM_NOTES = {
    'windows': """
CUBE-PDF.exe links the Microsoft Visual C++ runtime (vcruntime) statically,
under the Microsoft Visual Studio license terms for Distributable Code. The
Universal C Runtime and Microsoft Edge WebView2, which show its window, are
part of Windows and not shipped here.
""",
    'linux': """
The window uses GTK and WebKitGTK from the Linux distribution; they are not
part of these packages.
""",
    'android': """
The window uses the Android System WebView, which is part of Android and
not shipped here.
""",
}


def row(name: str, version: str, spdx: str, source: str) -> str:
    title = f'* {name} {version}'.rstrip()
    return f'{title}\n    License: {spdx}\n    Source: {source}\n'


def section(title: str, body: str) -> str:
    return f'\n\n{RULE}\n{title}\n{RULE}\n\n{body.strip()}\n'


def text_sections(
    title: str, texts: list[tuple[str, str]], shown: dict[str, str]
) -> list[str]:
    """Each distinct text is printed once; later uses point back to it."""
    sections = []
    for name, text in texts:
        heading = f'{title}: {name}'
        if text in shown:
            body = f'Licensed under the text shown above for {shown[text]}.'
            sections.append(section(heading, body))
        else:
            shown[text] = heading
            sections.append(section(heading, text))
    return sections


def crate_sections(crates: list[Crate], shown: dict[str, str]) -> list[str]:
    sections = []
    for crate in crates:
        title = f'Crate {crate.name} {crate.version} ({crate.spdx})'
        texts = crate_license_files(crate) or [
            ('license', f'{crate.spdx}; the crate ships no license file.')
        ]
        sections += text_sections(title, texts, shown)
    return sections


def library_sections(
    libraries: list[Library], shown: dict[str, str]
) -> list[str]:
    """One list of the libraries, then each of their license texts once."""
    if not libraries:
        return []
    listing = ''.join(
        f'{lib.name} {lib.version} ({lib.spdx})\n' for lib in libraries
    )
    sections = [section('Android libraries (from Google Maven)', listing)]
    for text in sorted({lib.text for lib in libraries}):
        texts = [(text, read_license(LICENSES / text))]
        sections += text_sections('Android libraries', texts, shown)
    return sections


def summary_rows(crates: list[Crate], libraries: list[Library]) -> list[str]:
    rows = []
    if crates:
        rows.append(
            row(
                'Tauri and the other Rust crates of the window',
                f'({len(crates)} crates)',
                'see each crate below',
                'https://crates.io',
            )
        )
    if libraries:
        rows.append(
            row(
                'AndroidX, Kotlin and the other Android libraries',
                f'({len(libraries)} libraries)',
                'see the list below',
                'https://maven.google.com, https://central.sonatype.com',
            )
        )
    return rows


def notices(target: str, build_dir: Path) -> str:
    native = [c for c in components(read_versions()) if target in c.targets]
    crates = []
    if target in APP_TARGETS:
        crates = shipped_crates(APP_TARGETS[target])
        check_crates(crates)
    libraries = android_libraries() if target == 'android' else []

    parts = [
        HEADER.format(url=source_url(), programs=PROGRAMS[target]),
        PLATFORM_NOTES.get(target, ''),
        '\nComponents\n----------\n',
        *(row(c.name, c.version, c.spdx, c.source) for c in native),
        *summary_rows(crates, libraries),
    ]

    shown: dict[str, str] = {}
    for c in native:
        texts = [
            (name.rsplit('/', 1)[-1], license_text(name, target, build_dir))
            for name in c.files
        ]
        parts += text_sections(f'{c.name} {c.version}'.rstrip(), texts, shown)
    parts += crate_sections(crates, shown)
    parts += library_sections(libraries, shown)
    return ''.join(parts)


def main() -> None:
    if len(sys.argv) != 4 or sys.argv[1] not in ALL_TARGETS:
        sys.exit(__doc__)
    target, build_dir, output = sys.argv[1], Path(sys.argv[2]), sys.argv[3]

    Path(output).write_text(notices(target, build_dir), encoding='utf-8')
    size_kb = Path(output).stat().st_size // 1024
    print(f'Wrote {output} ({size_kb} KB)')


if __name__ == '__main__':
    main()

"""tools/collect_licenses.py: the parts that need no built libraries."""

import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from support import collect_licenses as cl

VERSIONS = """\
HOME := https://example.org
FOO_VERSION := 1.2
FOO_URL := \\
    $(HOME)/foo-$(FOO_VERSION).tar.gz
"""
RUNTIME = cl.ANDROID_RUNTIME
LOCKFILE = f"""\
# This is a Gradle generated file
androidx.core:core:1.13.1={RUNTIME},otherClasspath
org.jetbrains.kotlin:kotlin-stdlib:2.2.10={RUNTIME}
com.example:build-only:1.0=lintClasspath
empty=
"""


MIT_TEXT = 'Permission is hereby granted, free of charge...'
TRIPLE = cl.APP_TARGETS['linux']


def temp_dir(test: unittest.TestCase) -> Path:
    folder = tempfile.TemporaryDirectory()
    test.addCleanup(folder.cleanup)
    return Path(folder.name)


def temp_file(test: unittest.TestCase, text: str) -> Path:
    path = temp_dir(test) / 'file'
    path.write_text(text, encoding='utf-8')
    return path


def write_files(folder: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        (folder / name).parent.mkdir(parents=True, exist_ok=True)
        (folder / name).write_text(text, encoding='utf-8')
    return folder


def package(name: str, license: str | None = 'MIT') -> dict:
    return {
        'id': name,
        'name': name,
        'version': '1.0.0',
        'license': license,
        'manifest_path': f'/crates/{name}/Cargo.toml',
    }


def dep(name: str, *kinds: str | None) -> dict:
    return {
        'pkg': name,
        'dep_kinds': [{'kind': kind, 'target': None} for kind in kinds],
    }


# The app needs serde, which needs itoa, which needs serde again; zip is
# both a dev and a normal dependency; cc only builds, tempfile only tests
METADATA = {
    'packages': [
        package(name)
        for name in ('app', 'serde', 'itoa', 'zip', 'cc', 'tempfile')
    ]
    + [package('rand', None)],
    'resolve': {
        'root': 'app',
        'nodes': [
            {
                'id': 'app',
                'deps': [
                    dep('serde', None),
                    dep('zip', 'dev', None),
                    dep('cc', 'build'),
                    dep('tempfile', 'dev'),
                ],
            },
            {'id': 'serde', 'deps': [dep('itoa', None), dep('cc', 'build')]},
            {'id': 'itoa', 'deps': [dep('serde', None)]},
            {'id': 'zip', 'deps': [dep('rand', None)]},
            {'id': 'cc', 'deps': []},
            {'id': 'tempfile', 'deps': [dep('cc', None)]},
            {'id': 'rand', 'deps': []},
        ],
    },
}


class ReadVersions(unittest.TestCase):
    def test_expands_names_and_joins_continued_lines(self):
        with mock.patch.object(cl, 'VERSIONS_MK', temp_file(self, VERSIONS)):
            values = cl.read_versions()
        self.assertEqual(
            values['FOO_URL'], 'https://example.org/foo-1.2.tar.gz'
        )

    def test_every_source_package_is_complete(self):
        values = cl.read_versions()
        for package in values['SOURCE_PACKAGES'].split():
            for field in ('URL', 'FILE', 'SHA256'):
                self.assertIn(f'{package}_{field}', values)
            self.assertRegex(values[f'{package}_SHA256'], r'^[0-9a-f]{64}$')


class LicenseAllowed(unittest.TestCase):
    def test_allowed(self):
        for expression in (
            'MIT',
            'MIT OR Apache-2.0',
            'MIT/Apache-2.0',
            'Apache-2.0 WITH LLVM-exception',
            '(MIT OR GPL-2.0-only) AND ISC',
            'MPL-2.0+',
        ):
            with self.subTest(expression):
                self.assertTrue(cl.license_allowed(expression))

    def test_refused(self):
        for expression in ('', 'GPL-2.0-only', 'MIT AND GPL-3.0', 'BUSL-1.1'):
            with self.subTest(expression):
                self.assertFalse(cl.license_allowed(expression))

    def test_check_crates_stops_on_a_refused_crate(self):
        crates = [
            cl.Crate('fine', '1.0.0', 'MIT', Path()),
            cl.Crate('bad', '2.0.0', 'GPL-2.0-only', Path()),
        ]
        with self.assertRaises(SystemExit) as stop:
            cl.check_crates(crates)
        self.assertIn('bad 2.0.0', str(stop.exception))


class AndroidLibraries(unittest.TestCase):
    def test_group_prefixes(self):
        self.assertEqual(cl.library_license('androidx.core:core'), cl.APACHE)
        self.assertEqual(
            cl.library_license('org.jetbrains.kotlin:kotlin-stdlib'),
            cl.APACHE,
        )
        self.assertIsNone(cl.library_license('androidxfake:lib'))
        self.assertIsNone(cl.library_license('com.example:lib'))

    def test_reads_only_the_release_runtime(self):
        with mock.patch.object(
            cl, 'GRADLE_LOCKFILE', temp_file(self, LOCKFILE)
        ):
            libraries = cl.android_libraries()
        self.assertEqual(
            [(lib.name, lib.version) for lib in libraries],
            [
                ('androidx.core:core', '1.13.1'),
                ('org.jetbrains.kotlin:kotlin-stdlib', '2.2.10'),
            ],
        )

    def test_stops_on_an_unknown_group(self):
        lockfile = LOCKFILE + f'com.example:lib:1.0={RUNTIME}\n'
        with mock.patch.object(
            cl, 'GRADLE_LOCKFILE', temp_file(self, lockfile)
        ):
            with self.assertRaises(SystemExit):
                cl.android_libraries()

    def test_the_committed_lockfile_is_cleared(self):
        self.assertTrue(cl.android_libraries())


class Notices(unittest.TestCase):
    def test_a_text_is_printed_once(self):
        shown = {}
        first = cl.text_sections('A 1', [('LICENSE', 'text')], shown)
        second = cl.text_sections('B 2', [('COPYING', 'text')], shown)
        self.assertIn('text', first[0])
        self.assertIn('shown above for A 1: LICENSE', second[0])

    def test_components(self):
        for component in cl.components(cl.read_versions()):
            with self.subTest(component.name):
                self.assertTrue(component.spdx)
                self.assertTrue(component.files)
                self.assertLessEqual(
                    set(component.targets), set(cl.ALL_TARGETS)
                )

    def test_license_files_kept_in_the_repository_exist(self):
        for component in cl.components(cl.read_versions()):
            for name in component.files:
                if not name.startswith(('src:', 'toolchain:')):
                    self.assertTrue((cl.LICENSES / name).is_file(), name)

    def test_source_url(self):
        self.assertRegex(cl.source_url(), r'^https://github\.com/[\w.-]+/')


class ShippedCrates(unittest.TestCase):
    def test_only_what_the_app_runs(self):
        with mock.patch.object(cl, 'cargo_metadata', return_value=METADATA):
            crates = cl.shipped_crates(TRIPLE)
        self.assertEqual(
            [(crate.name, crate.spdx) for crate in crates],
            [('itoa', 'MIT'), ('rand', ''), ('serde', 'MIT'), ('zip', 'MIT')],
        )
        self.assertEqual(crates[0].folder, Path('/crates/itoa'))

    def test_a_crate_without_a_license_is_refused(self):
        with mock.patch.object(cl, 'cargo_metadata', return_value=METADATA):
            crates = cl.shipped_crates(TRIPLE)
        with self.assertRaises(SystemExit) as stop:
            cl.check_crates(crates)
        self.assertIn('rand 1.0.0 ()', str(stop.exception))


class CargoMetadata(unittest.TestCase):
    def cargo(self, files: dict[str, str], returncode: int = 0):
        desktop = write_files(temp_dir(self), files)
        answer = subprocess.CompletedProcess(
            [], returncode, stdout='{"packages": []}', stderr='no network'
        )
        with (
            mock.patch.object(cl, 'DESKTOP', desktop),
            mock.patch.object(cl.subprocess, 'run', return_value=answer) as run,
        ):
            return cl.cargo_metadata(TRIPLE), run.call_args.args[0]

    def test_keeps_to_the_committed_lockfile(self):
        meta, command = self.cargo({'Cargo.lock': ''})
        self.assertEqual(meta, {'packages': []})
        self.assertIn('--locked', command)
        self.assertEqual(
            command[command.index('--filter-platform') + 1], TRIPLE
        )
        self.assertNotIn('--locked', self.cargo({})[1])

    def test_stops_when_cargo_fails(self):
        with self.assertRaises(SystemExit) as stop:
            self.cargo({}, returncode=101)
        self.assertIn('no network', str(stop.exception))


class LicenseTexts(unittest.TestCase):
    def test_read_from_where_each_comes_from(self):
        folder = write_files(
            temp_dir(self),
            {
                'build/src/foo/COPYING': 'foo',
                'ndk/NOTICE': 'ndk',
                'emsdk/upstream/emscripten/LICENSE': 'emscripten',
            },
        )
        build = folder / 'build'
        environment = {
            'NDK_HOME': str(folder / 'ndk'),
            'EMSDK': str(folder / 'emsdk'),
        }
        with mock.patch.dict(os.environ, environment):
            texts = [
                cl.license_text('src:foo/COPYING', 'linux', build),
                cl.license_text('toolchain:NOTICE', 'android', build),
                cl.license_text('toolchain:LICENSE', 'wasm', build),
                cl.license_text('Apache-2.0.txt', 'android', build),
            ]
        self.assertEqual(texts[:3], ['foo', 'ndk', 'emscripten'])
        self.assertIn('Apache License', texts[3])

    def test_a_missing_file_stops_the_build(self):
        with self.assertRaises(SystemExit) as stop:
            cl.license_text('src:gone/LICENSE', 'linux', temp_dir(self))
        self.assertIn('gone/LICENSE', str(stop.exception))

    def test_the_license_files_of_a_crate(self):
        folder = write_files(
            temp_dir(self),
            {
                name: name
                for name in (
                    'LICENSE-MIT',
                    'LICENSE-APACHE',
                    'COPYING',
                    'NOTICE.md',
                    'UNLICENSE',
                    'license.txt',
                    'LICENSES/MIT.txt',
                    'Cargo.toml',
                    'README.md',
                    'src/license.rs',
                )
            },
        )
        crate = cl.Crate('foo', '1.0.0', 'MIT', folder)
        self.assertEqual(
            [name for name, _ in cl.crate_license_files(crate)],
            [
                'COPYING',
                'LICENSE-APACHE',
                'LICENSE-MIT',
                'NOTICE.md',
                'UNLICENSE',
                'license.txt',
            ],
        )

    def test_a_crate_without_a_license_file_says_so(self):
        crate = cl.Crate('bare', '0.1.0', 'MIT', temp_dir(self))
        [text] = cl.crate_sections([crate], {})
        self.assertIn('Crate bare 0.1.0 (MIT): license', text)
        self.assertIn('MIT; the crate ships no license file.', text)


class Toolchain(unittest.TestCase):
    def test_compiler_version(self):
        answer = subprocess.CompletedProcess([], 0, stdout='13.2.0\n')
        with mock.patch.object(cl.subprocess, 'run', return_value=answer):
            self.assertEqual(cl.compiler_version('gcc'), '13.2.0')
        with mock.patch.object(
            cl.subprocess, 'run', side_effect=FileNotFoundError
        ):
            self.assertEqual(cl.compiler_version('x86_64-w64-mingw32-gcc'), '')

    def test_ndk_version(self):
        ndk = write_files(
            temp_dir(self),
            {'source.properties': 'Pkg.Desc = NDK\nPkg.ReleaseName = r27c\n'},
        )
        with mock.patch.dict(os.environ, {'NDK_HOME': str(ndk)}):
            self.assertEqual(cl.ndk_version(), 'r27c')
        with mock.patch.dict(os.environ, {'NDK_HOME': str(ndk / 'none')}):
            self.assertEqual(cl.ndk_version(), '')


class NoticesFile(unittest.TestCase):
    """notices() for a few made-up components, crates and libraries."""

    def setUp(self):
        folder = write_files(
            temp_dir(self),
            {
                'build/src/foo/COPYING': MIT_TEXT,
                'build/src/web/LICENSE': 'web only',
                'crates/serde/LICENSE-MIT': MIT_TEXT,
            },
        )
        self.build = folder / 'build'
        self.components = [
            cl.Component(
                'Foo', '1.0', 'MIT', ['src:foo/COPYING'], 'https://foo'
            ),
            cl.Component(
                'Web', '', 'ISC', ['src:web/LICENSE'], 'https://web', ('wasm',)
            ),
        ]
        self.crates = [
            cl.Crate('serde', '1.0.0', 'MIT', folder / 'crates' / 'serde')
        ]
        self.libraries = [
            cl.Library('androidx.core:core', '1.13.1', *cl.APACHE),
            cl.Library('androidx.webkit:webkit', '1.12.0', *cl.APACHE),
        ]

    def notices(self, target: str) -> tuple[str, mock.Mock]:
        with (
            mock.patch.object(cl, 'components', return_value=self.components),
            mock.patch.object(
                cl, 'shipped_crates', return_value=self.crates
            ) as crates,
            mock.patch.object(
                cl, 'android_libraries', return_value=self.libraries
            ),
        ):
            return cl.notices(target, self.build), crates

    def test_lists_what_the_target_has(self):
        text, crates = self.notices('linux')
        crates.assert_called_once_with(cl.APP_TARGETS['linux'])
        self.assertTrue(text.startswith('CUBE-PDF: third-party notices'))
        self.assertIn(cl.source_url(), text)
        self.assertIn(cl.PROGRAMS['linux'], text)
        self.assertIn(cl.PLATFORM_NOTES['linux'], text)
        self.assertIn(cl.row('Foo', '1.0', 'MIT', 'https://foo'), text)
        self.assertNotIn('* Web', text)
        self.assertIn('Rust crates of the window (1 crates)', text)
        self.assertNotIn('Android libraries', text)

    def test_each_license_text_once(self):
        text, _ = self.notices('linux')
        self.assertEqual(text.count(MIT_TEXT), 1)
        self.assertIn('Foo 1.0: COPYING\n', text)
        self.assertIn(
            'Crate serde 1.0.0 (MIT): LICENSE-MIT\n'
            f'{cl.RULE}\n\n'
            'Licensed under the text shown above for Foo 1.0: COPYING.',
            text,
        )

    def test_the_web_has_no_crates(self):
        text, crates = self.notices('wasm')
        crates.assert_not_called()
        self.assertIn(cl.row('Web', '', 'ISC', 'https://web'), text)
        self.assertIn(f'{cl.RULE}\nWeb: LICENSE\n', text)
        self.assertNotIn('crates', text)

    def test_the_apk_lists_its_libraries(self):
        text, _ = self.notices('android')
        self.assertIn('Android libraries (2 libraries)', text)
        self.assertIn(
            'androidx.core:core 1.13.1 (Apache-2.0)\n'
            'androidx.webkit:webkit 1.12.0 (Apache-2.0)\n',
            text,
        )
        self.assertEqual(text.count('Android libraries: Apache-2.0.txt'), 1)
        apache = (cl.LICENSES / 'Apache-2.0.txt').read_text(encoding='utf-8')
        self.assertIn(apache.strip(), text)

    def test_a_refused_crate_stops_it(self):
        self.crates.append(cl.Crate('gpl', '1.0.0', 'GPL-2.0-only', Path()))
        with self.assertRaises(SystemExit):
            self.notices('windows')


class Main(unittest.TestCase):
    def test_writes_the_notices_of_a_target(self):
        output = temp_dir(self) / 'THIRD-PARTY-NOTICES.txt'
        argv = ['collect_licenses.py', 'wasm', 'build', str(output)]
        with (
            mock.patch.object(cl.sys, 'argv', argv),
            mock.patch.object(cl, 'notices', return_value='notices') as make,
            redirect_stdout(io.StringIO()) as printed,
        ):
            cl.main()
        make.assert_called_once_with('wasm', Path('build'))
        self.assertEqual(output.read_text(encoding='utf-8'), 'notices')
        self.assertIn(str(output), printed.getvalue())

    def test_refuses_an_unknown_target(self):
        argv = ['collect_licenses.py', 'macos', 'build', 'out.txt']
        with mock.patch.object(cl.sys, 'argv', argv):
            with self.assertRaises(SystemExit) as stop:
                cl.main()
        self.assertEqual(stop.exception.code, cl.__doc__)


if __name__ == '__main__':
    unittest.main()

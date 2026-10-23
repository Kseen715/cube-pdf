"""tools/collect_licenses.py: the parts that need no built libraries."""

import tempfile
import unittest
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


def temp_file(test: unittest.TestCase, text: str) -> Path:
    folder = tempfile.TemporaryDirectory()
    test.addCleanup(folder.cleanup)
    path = Path(folder.name) / 'file'
    path.write_text(text, encoding='utf-8')
    return path


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


if __name__ == '__main__':
    unittest.main()

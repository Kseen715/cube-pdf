"""The legal statements that AGENTS.md asks to keep consistent."""

import json
import re
import unittest

from support import ROOT

COPYRIGHT = re.compile(r'Copyright © (\d{4}) ([^<"\n]+)')
LICENSE_NAME = 'AGPL-3.0-or-later'
PROJECTS = ('OCRmyPDF', 'Tesseract', 'MuPDF', 'Ghostscript')


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def readme_section(title: str) -> str:
    match = re.search(
        rf'^## {title}\n(.*?)(?=^## )', read('README.md'), re.M | re.S
    )
    return match.group(1) if match else ''


class Legal(unittest.TestCase):
    def test_copyright_agrees(self):
        about = COPYRIGHT.search(read('web/js/dialogs.js'))
        tauri = json.loads(read('desktop/tauri.conf.json'))
        bundle = COPYRIGHT.search(tauri['bundle']['copyright'])
        self.assertIsNotNone(about)
        self.assertIsNotNone(bundle)
        self.assertEqual(about.groups(), bundle.groups())
        self.assertEqual(tauri['bundle']['publisher'], about.group(2))

    def test_the_license_is_the_agpl(self):
        self.assertIn('GNU AFFERO GENERAL PUBLIC LICENSE', read('LICENSE'))
        tauri = json.loads(read('desktop/tauri.conf.json'))
        self.assertEqual(tauri['bundle']['license'], LICENSE_NAME)
        self.assertIn(f'license = "{LICENSE_NAME}"', read('desktop/Cargo.toml'))
        self.assertIn(
            'GNU Affero General Public License v3.0 or later',
            readme_section('License'),
        )

    def test_about_keeps_the_notices(self):
        dialogs = read('web/js/dialogs.js')
        self.assertIn('GNU Affero General Public License', dialogs)
        self.assertIn('без каких-либо гарантий', dialogs)
        self.assertIn('SOURCE_URL', dialogs)
        self.assertIn('THIRD-PARTY-NOTICES.txt', dialogs)

    def test_readme_says_it_is_not_affiliated(self):
        section = ' '.join(readme_section('License').split())
        match = re.search(r'not affiliated with[^.]*\.', section)
        self.assertIsNotNone(match)
        for project in PROJECTS:
            self.assertIn(project, match.group(0))


if __name__ == '__main__':
    unittest.main()

// web/js/i18n.js and locales/: every language has every text

import assert from 'node:assert/strict';
import { afterEach, test } from 'node:test';

import { LANGUAGES } from '../../web/js/config.js';
import { LOCALES, has, setLocale, t } from '../../web/js/i18n.js';

const PLACEHOLDER = /\{(\w+)\}/g;
const COUNTS = 1000;

function placeholders(text) {
    const forms = typeof text === 'object' ? Object.values(text) : [text];
    return new Set(forms.flatMap(
        (form) => [...form.matchAll(PLACEHOLDER)].map(([, name]) => name)));
}

afterEach(() => setLocale('en'));

test('every locale has the same texts as English', () => {
    const keys = Object.keys(LOCALES.en.texts).sort();
    for (const [code, { texts }] of Object.entries(LOCALES))
        assert.deepEqual(Object.keys(texts).sort(), keys, code);
});

test('every translation fills in the same values', () => {
    for (const [key, english] of Object.entries(LOCALES.en.texts)) {
        for (const [code, { texts }] of Object.entries(LOCALES)) {
            assert.deepEqual(placeholders(texts[key]),
                placeholders(english), `${code} ${key}`);
        }
    }
});

// The counts are of files and pages: a few hundred at most
test('a text with a form per count has the forms its language needs', () => {
    for (const [code, { texts }] of Object.entries(LOCALES)) {
        const rules = new Intl.PluralRules(code);
        const forms = new Set(Array.from({ length: COUNTS },
            (_, count) => rules.select(count)));
        for (const [key, text] of Object.entries(texts)) {
            if (typeof text !== 'object') continue;
            for (const form of forms)
                assert.ok(form in text, `${code} ${key} ${form}`);
        }
    }
});

test('every language of the text is named, in every locale', () => {
    for (const code of LANGUAGES) assert.ok(has(`language.${code}`), code);
    for (const { ocr } of Object.values(LOCALES))
        assert.ok(LANGUAGES.includes(ocr), ocr);
});

test('fills in values and picks the form for the count', () => {
    setLocale('ru');
    assert.equal(t('files.count', { count: 1 }), '1 файл');
    assert.equal(t('files.count', { count: 3 }), '3 файла');
    assert.equal(t('files.count', { count: 11 }), '11 файлов');
    setLocale('en');
    assert.equal(t('files.count', { count: 2 }), '2 files');
    assert.equal(t('task.willBe', { output: 'a.pdf' }), 'Will become a.pdf');
});

test('an unknown key is shown as it is', () => {
    assert.equal(t('no.such.key'), 'no.such.key');
    assert.ok(!has('no.such.key'));
});

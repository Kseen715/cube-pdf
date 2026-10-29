// web/js/i18n.js and locales/: every language has every text

import assert from 'node:assert/strict';
import { afterEach, describe, test } from 'node:test';

import { LANGUAGES } from '../../web/js/config.js';
import {
    LOCALES, currentLocale, has, initialLocale, localizePage, onLocaleChange,
    setLocale, t,
} from '../../web/js/i18n.js';
import { installDocument } from './dom.js';

const PLACEHOLDER = /\{(\w+)\}/g;
const COUNTS = 1000;
const STORAGE_KEY = 'cube-pdf-locale';
const BROWSER = ['localStorage', 'navigator'];

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

test('the page is shown in the chosen language', () => {
    const document = installDocument();
    const button = document.createElement('button');
    button.dataset.i18n = 'start';
    button.dataset.i18nLabel = 'about.link';
    button.dataset.i18nTitle = 'stop';
    document.body.append(button);

    setLocale('de');
    localizePage();
    assert.equal(document.documentElement.lang, 'de');
    assert.equal(button.textContent, t('start'));
    assert.equal(button.getAttribute('aria-label'), t('about.link'));
    assert.equal(button.title, t('stop'));
    assert.notEqual(button.textContent, LOCALES.en.texts.start);
});

// In a browser with the given storage and languages
describe('the first language', () => {
    const real = Object.fromEntries(BROWSER.map((name) =>
        [name, Object.getOwnPropertyDescriptor(globalThis, name)]));

    afterEach(() => {
        for (const name of BROWSER)
            Object.defineProperty(globalThis, name, real[name]);
    });

    function browser(storage, languages) {
        Object.defineProperty(globalThis, 'localStorage',
            { value: storage, configurable: true });
        Object.defineProperty(globalThis, 'navigator',
            { value: { languages }, configurable: true });
    }

    function storageWith(saved) {
        const items = new Map(saved ? [[STORAGE_KEY, saved]] : []);
        return {
            items,
            getItem: (key) => items.get(key) ?? null,
            setItem: (key, value) => items.set(key, value),
        };
    }

    const brokenStorage = {
        getItem() {
            throw new Error('denied');
        },
        setItem() {
            throw new Error('denied');
        },
    };

    test('is the one chosen before', () => {
        browser(storageWith('it'), ['de-DE']);
        assert.equal(initialLocale(), 'it');
    });

    test('is the first of the browser\'s the page has', () => {
        browser(storageWith(null), ['fr-FR', 'DE-at', 'ru']);
        assert.equal(initialLocale(), 'de');
        browser(storageWith('fr'), ['ru-RU']);
        assert.equal(initialLocale(), 'ru');
    });

    test('is the browser\'s when storage is refused', () => {
        browser(brokenStorage, ['it']);
        assert.equal(initialLocale(), 'it');
    });

    test('is English otherwise', () => {
        browser(storageWith(null), ['fr', 'ja']);
        assert.equal(initialLocale(), 'en');
        browser(undefined, undefined);
        assert.equal(initialLocale(), 'en');
    });

    test('a new choice is kept and announced', () => {
        const storage = storageWith(null);
        browser(storage, []);
        const heard = [];
        onLocaleChange(() => heard.push(currentLocale()));
        setLocale('ru');
        assert.equal(storage.items.get(STORAGE_KEY), 'ru');
        assert.deepEqual(heard, ['ru']);
        assert.equal(initialLocale(), 'ru');
    });

    test('a choice holds without storage', () => {
        browser(brokenStorage, []);
        setLocale('de');
        assert.equal(currentLocale(), 'de');
        assert.equal(t('start'), LOCALES.de.texts.start);
    });
});

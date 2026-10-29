// The languages of the interface. Every text the page shows has a key;
// locales/<code>.js holds the texts of one language. The choice is
// remembered in this browser, like the theme; the first time, the
// browser's own language is taken when the page has it.

import de from './locales/de.js';
import en from './locales/en.js';
import it from './locales/it.js';
import ru from './locales/ru.js';

// Interface language -> its name in itself, the Tesseract model of the
// same language and its texts, in the order of the switch
export const LOCALES = {
    ru: { name: 'Русский', ocr: 'rus', texts: ru },
    en: { name: 'English', ocr: 'eng', texts: en },
    de: { name: 'Deutsch', ocr: 'deu', texts: de },
    it: { name: 'Italiano', ocr: 'ita', texts: it },
};
const FALLBACK = 'en';
const STORAGE_KEY = 'cube-pdf-locale';

const listeners = [];
let locale = initialLocale();

// The saved choice, else the browser's first language the page has
export function initialLocale() {
    try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved in LOCALES) return saved;
    } catch {
        // without storage the browser's language decides
    }
    for (const tag of globalThis.navigator?.languages ?? []) {
        const code = tag.slice(0, 2).toLowerCase();
        if (code in LOCALES) return code;
    }
    return FALLBACK;
}

export function currentLocale() {
    return locale;
}

export function setLocale(code) {
    locale = code;
    try {
        localStorage.setItem(STORAGE_KEY, code);
    } catch {
        // the choice still holds until the page is closed
    }
    for (const listener of listeners) listener();
}

export function onLocaleChange(listener) {
    listeners.push(listener);
}

export function has(key) {
    return key in LOCALES[FALLBACK].texts;
}

// The text of key with each {name} replaced by params.name. A text with a
// form per count (an object of Intl.PluralRules categories) takes
// params.count.
export function t(key, params = {}) {
    let text = LOCALES[locale].texts[key] ?? LOCALES[FALLBACK].texts[key];
    if (text === undefined) return key;
    if (typeof text === 'object') {
        const form = new Intl.PluralRules(locale).select(params.count);
        text = text[form] ?? text.other;
    }
    return text.replace(/\{(\w+)\}/g,
        (match, name) => `${params[name] ?? match}`);
}

// The page's fixed texts: data-i18n names the key of an element's text,
// data-i18n-label of its aria-label, data-i18n-title of its tooltip
export function localizePage() {
    document.documentElement.lang = locale;
    for (const node of document.querySelectorAll('[data-i18n]'))
        node.textContent = t(node.dataset.i18n);
    for (const node of document.querySelectorAll('[data-i18n-label]'))
        node.setAttribute('aria-label', t(node.dataset.i18nLabel));
    for (const node of document.querySelectorAll('[data-i18n-title]'))
        node.title = t(node.dataset.i18nTitle);
}

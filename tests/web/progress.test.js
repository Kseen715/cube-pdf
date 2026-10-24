// web/js/progress.js: the engine's messages as a percentage and a label

import assert from 'node:assert/strict';
import { test } from 'node:test';

import { setLocale } from '../../web/js/i18n.js';
import { FileProgress } from '../../web/js/progress.js';

setLocale('ru');

test('each stage fills its share of the bar', () => {
    const progress = new FileProgress();
    progress.update('scan', 0, 1);
    assert.equal(progress.percent, 0);
    progress.update('ocr', 2, 4);
    assert.equal(progress.percent, 45);
    progress.update('save', 0, 1);
    assert.equal(progress.percent, 85);
    progress.update('pdfa', 1, 1);
    assert.equal(progress.percent, 100);
});

test('counts pages and names the next one', () => {
    const progress = new FileProgress();
    const label = progress.update('ocr', 1, 3);
    assert.equal(label, 'Распознаю текст: страница 2 из 3');
    assert.equal(progress.pages, 3);
    assert.equal(progress.pagesDone, 1);

    assert.equal(progress.update('ocr', 3, 3),
        'Распознаю текст: страница 3 из 3');
    assert.equal(progress.pagesDone, 3);
});

test('a late message from a parallel page does not go back', () => {
    const progress = new FileProgress();
    progress.update('ocr', 3, 4);
    const percent = progress.percent;
    progress.update('ocr', 2, 4);
    assert.equal(progress.percent, percent);
    assert.equal(progress.pagesDone, 3);
});

test('an unknown stage keeps the bar where it is', () => {
    const progress = new FileProgress();
    progress.update('ocr', 4, 4);
    assert.equal(progress.update('mystery', 1, 2), 'Обрабатываю');
    assert.equal(progress.percent, 85);
});

test('a stage without a total starts at its beginning', () => {
    const progress = new FileProgress();
    progress.update('save', 0, 0);
    assert.equal(progress.percent, 85);
    assert.equal(progress.pages, 0);
});

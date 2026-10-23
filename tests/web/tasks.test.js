// web/js/tasks.js: one file in the list, and what the user is told when
// it fails

import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { test } from 'node:test';

import { State, Task } from '../../web/js/tasks.js';

const ROOT = new URL('../../', import.meta.url);
// Where an error kind is named: the core's ocr::Error and kind_of(), its
// catch blocks, and the Android shell's failures
const KIND_PATTERNS = [
    /Error\("(\w+)"/g,
    /return "(\w+)";/g,
    /kind = "(\w+)"/g,
    /failure\("(\w+)"\)/g,
];
// The engines' own kind for a run that ended without saying why
const ENGINE_KINDS = ['crash'];

function sourceFiles(folder, extension) {
    return readdirSync(new URL(folder, ROOT))
        .filter((name) => name.endsWith(extension))
        .map((name) => readFileSync(new URL(`${folder}${name}`, ROOT), 'utf8'));
}

function errorKinds() {
    const sources = [...sourceFiles('core/src/', '.cpp'),
        ...sourceFiles('desktop/src/', '.rs')];
    const kinds = new Set(ENGINE_KINDS);
    for (const text of sources)
        for (const pattern of KIND_PATTERNS)
            for (const [, kind] of text.matchAll(pattern)) kinds.add(kind);
    return kinds;
}

function failedWith(kind, details = '') {
    const task = new Task({ name: 'scan.pdf', key: 'scan.pdf' });
    task.setError(kind, details);
    return task;
}

test('a new task waits for its turn', () => {
    const task = new Task({ name: 'scan.jpg', key: 'scan.jpg' });
    assert.equal(task.output, 'scan_ocr.pdf');
    assert.equal(task.state, State.WAITING);
    assert.equal(task.note(), 'Получится scan_ocr.pdf');
});

test('the note follows the state', () => {
    const task = new Task({ name: 'scan.pdf', key: 'scan.pdf' });
    task.state = State.RUNNING;
    assert.equal(task.note(), 'Запускаю…');
    task.progress.update('scan', 0, 1);
    assert.equal(task.note(), 'Изучаю файл…');
    task.state = State.DONE;
    assert.equal(task.note(), 'Сохранён как scan_ocr.pdf');
});

test('reset forgets the last run', () => {
    const task = failedWith('encrypted', 'details');
    task.state = State.FAILED;
    task.progress.update('ocr', 1, 2);
    task.reset();
    assert.equal(task.state, State.WAITING);
    assert.equal(task.error, '');
    assert.equal(task.details, '');
    assert.equal(task.progress.percent, 0);
});

test('an error names the output file and keeps the details', () => {
    const task = failedWith('output_access', 'EACCES');
    assert.match(task.error, /«scan_ocr\.pdf»/);
    assert.equal(task.details, 'EACCES');
    task.state = State.FAILED;
    assert.equal(task.note(), task.error);
});

test('an unknown kind gets the general message', () => {
    assert.equal(failedWith('no_such_kind').error, failedWith('other').error);
});

test('every kind the programs report has its own message', () => {
    const general = failedWith('other').error;
    const kinds = errorKinds();
    assert.ok(kinds.has('encrypted') && kinds.has('has_text'));
    for (const kind of kinds) {
        if (kind !== 'other')
            assert.notEqual(failedWith(kind).error, general, kind);
    }
});

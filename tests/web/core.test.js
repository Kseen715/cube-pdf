// web/js/core.js: the arguments of ocr-pdf-core and the lines it writes

import assert from 'node:assert/strict';
import { test } from 'node:test';

import { coreMessage, runOptions } from '../../web/js/core.js';

test('options become arguments', () => {
    assert.deepEqual(
        runOptions({ languages: ['rus', 'eng'], force: false, deskew: false }),
        ['--languages', 'rus+eng']);
    assert.deepEqual(
        runOptions({ languages: ['deu'], force: true, deskew: true }),
        ['--languages', 'deu', '--force', '--deskew']);
});

test('a JSON line on stdout is a message', () => {
    const line = '{"event":"progress","stage":"ocr","done":1,"total":2}';
    assert.deepEqual(coreMessage(line, 'stdout'),
        { event: 'progress', stage: 'ocr', done: 1, total: 2 });
});

test('anything else is logged', () => {
    assert.deepEqual(coreMessage('Warning: odd font', 'stdout'),
        { event: 'log', level: 'stdout', msg: 'Warning: odd font' });
    assert.deepEqual(coreMessage('{"event":"done"}', 'stderr'),
        { event: 'log', level: 'stderr', msg: '{"event":"done"}' });
});

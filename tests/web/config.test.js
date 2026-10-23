// web/js/config.js: output names, accepted files, pages run at once

import assert from 'node:assert/strict';
import { afterEach, describe, test } from 'node:test';

import {
    hasInputExtension, outputName, parallelPages,
} from '../../web/js/config.js';

const realNavigator = Object.getOwnPropertyDescriptor(globalThis,
    'navigator');

function fakeNavigator(fields) {
    Object.defineProperty(globalThis, 'navigator', {
        value: fields, configurable: true,
    });
}

describe('outputName', () => {
    test('replaces the extension', () => {
        assert.equal(outputName('scan.pdf'), 'scan_ocr.pdf');
        assert.equal(outputName('a.b.PNG'), 'a.b_ocr.pdf');
    });

    test('keeps a name without an extension whole', () => {
        assert.equal(outputName('scan'), 'scan_ocr.pdf');
        assert.equal(outputName('.hidden'), '.hidden_ocr.pdf');
    });
});

describe('hasInputExtension', () => {
    test('accepts PDF and images in any case', () => {
        for (const name of ['a.pdf', 'b.JPG', 'c.jpeg', 'd.Png', 'e.tif',
            'f.TIFF'])
            assert.ok(hasInputExtension(name), name);
    });

    test('refuses other files', () => {
        for (const name of ['a.docx', 'pdf', 'b.pdf.txt', 'c.gif'])
            assert.ok(!hasInputExtension(name), name);
    });
});

describe('parallelPages', () => {
    afterEach(() => {
        if (realNavigator)
            Object.defineProperty(globalThis, 'navigator', realNavigator);
        else delete globalThis.navigator;
    });

    test('one page per core when memory is unknown', () => {
        fakeNavigator({ hardwareConcurrency: 6 });
        assert.equal(parallelPages(), 6);
    });

    test('limited by memory', () => {
        fakeNavigator({ hardwareConcurrency: 8, deviceMemory: 2 });
        assert.equal(parallelPages(), 4);
    });

    test('at least one page', () => {
        fakeNavigator({ hardwareConcurrency: 4, deviceMemory: 0.25 });
        assert.equal(parallelPages(), 1);
    });

    test('two cores when the browser does not say', () => {
        fakeNavigator({});
        assert.equal(parallelPages(), 2);
    });
});

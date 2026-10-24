// web/js/update.js: which release is newer and which of its files to get

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { afterEach, describe, test } from 'node:test';

import { LATEST_RELEASE_API, UPDATE_FILES } from '../../web/js/config.js';
import {
    checkForUpdate, findUpdate, isNewer, parseVersion,
} from '../../web/js/update.js';

const WORKFLOW = new URL('../../.github/workflows/build.yml',
    import.meta.url);
const PAGE = 'https://github.com/Kseen715/cube-pdf/releases/tag/v2.3.0';

function release(tag, names) {
    return {
        tag_name: tag,
        html_url: PAGE,
        assets: names.map((name, i) => ({ name, size: 100 + i })),
    };
}

const LATEST = release('v2.3.0', [
    'CUBE-PDF-2.3.0-windows-x86_64.exe',
    'CUBE-PDF-2.3.0-windows-x86_64.zip',
    'CUBE-PDF-2.3.0-linux-glibc-x86_64.deb',
    'CUBE-PDF-2.3.0-linux-glibc-x86_64.rpm',
    'CUBE-PDF-2.3.0-android-universal.apk',
    'LICENSE',
]);

describe('parseVersion', () => {
    test('reads tags and app versions', () => {
        assert.deepEqual(parseVersion('v2.3.0'), [2, 3, 0]);
        assert.deepEqual(parseVersion('v2.2.1+b4c2406+dirty'), [2, 2, 1]);
        assert.deepEqual(parseVersion('v10.0.12'), [10, 0, 12]);
    });

    test('refuses what is not a version', () => {
        for (const text of ['', undefined, '2.3.0', 'v2.3', 'latest'])
            assert.equal(parseVersion(text), null, text);
    });
});

describe('isNewer', () => {
    test('compares part by part, as numbers', () => {
        assert.ok(isNewer([2, 10, 0], [2, 9, 9]));
        assert.ok(isNewer([3, 0, 0], [2, 99, 99]));
        assert.ok(isNewer([2, 2, 2], [2, 2, 1]));
    });

    test('the same or an older version is not newer', () => {
        assert.ok(!isNewer([2, 2, 1], [2, 2, 1]));
        assert.ok(!isNewer([2, 1, 9], [2, 2, 0]));
    });
});

describe('findUpdate', () => {
    test('picks the file of each kind of package', () => {
        for (const [kind, suffix] of Object.entries(UPDATE_FILES)) {
            const update = findUpdate(LATEST, 'v2.2.1+b4c2406', kind);
            assert.ok(update.file.name.endsWith(suffix), kind);
        }
        const update = findUpdate(LATEST, 'v2.2.1', 'deb');
        assert.deepEqual(update, {
            from: 'v2.2.1',
            to: 'v2.3.0',
            page: PAGE,
            file: { name: 'CUBE-PDF-2.3.0-linux-glibc-x86_64.deb', size: 102 },
        });
    });

    test('shows the version without the commit', () => {
        assert.equal(findUpdate(LATEST, 'v2.2.1+b4c2406', 'rpm').from,
            'v2.2.1');
    });

    test('no file when the app cannot install or the release lacks it', () => {
        assert.equal(findUpdate(LATEST, 'v2.2.1', null).file, null);
        const bare = release('v2.3.0', ['LICENSE']);
        assert.equal(findUpdate(bare, 'v2.2.1', 'windows').file, null);
        assert.equal(findUpdate({ tag_name: 'v2.3.0' }, 'v2.2.1', 'deb').file,
            null);
    });

    test('nothing when the app is as new or newer', () => {
        assert.equal(findUpdate(LATEST, 'v2.3.0+abc1234', 'deb'), null);
        assert.equal(findUpdate(LATEST, 'v2.4.0', 'deb'), null);
    });

    test('nothing without versions to compare', () => {
        assert.equal(findUpdate(LATEST, '', 'deb'), null);
        assert.equal(findUpdate(release('nightly', []), 'v1.0.0', 'deb'),
            null);
        assert.equal(findUpdate(null, 'v1.0.0', 'deb'), null);
    });
});

describe('checkForUpdate', () => {
    const realFetch = globalThis.fetch;
    afterEach(() => {
        globalThis.fetch = realFetch;
    });

    function fakeFetch(answer) {
        const asked = [];
        globalThis.fetch = async (url) => {
            asked.push(url);
            return answer;
        };
        return asked;
    }

    test('asks GitHub for the latest release', async () => {
        const asked = fakeFetch({ ok: true, json: async () => LATEST });
        const update = await checkForUpdate('v2.2.1', 'windows');
        assert.deepEqual(asked, [LATEST_RELEASE_API]);
        assert.equal(update.to, 'v2.3.0');
    });

    test('nothing when GitHub refuses', async () => {
        fakeFetch({ ok: false, json: async () => ({}) });
        assert.equal(await checkForUpdate('v2.2.1', 'windows'), null);
    });

    test('does not ask without a version of its own', async () => {
        const asked = fakeFetch({ ok: true, json: async () => LATEST });
        assert.equal(await checkForUpdate('', 'windows'), null);
        assert.deepEqual(asked, []);
    });
});

describe('the release files', () => {
    test('the API is that of the source repository', () => {
        assert.equal(LATEST_RELEASE_API,
            'https://api.github.com/repos/Kseen715/cube-pdf/releases/latest');
    });

    test('the release job makes every file the apps update from', () => {
        const workflow = readFileSync(WORKFLOW, 'utf8');
        for (const suffix of Object.values(UPDATE_FILES))
            assert.ok(workflow.includes(`"$app${suffix}"`), suffix);
    });
});

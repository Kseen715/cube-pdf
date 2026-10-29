// web/js/tasks.js: one file in the list, what the user is told when it
// fails, and the list's rows

import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { describe, test } from 'node:test';

import { setLocale, t } from '../../web/js/i18n.js';
import { State, Task, TaskList } from '../../web/js/tasks.js';
import { installDocument } from './dom.js';

setLocale('ru');
installDocument();

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
// What a long document shows at most (MAX_CELLS)
const MAX_CELLS = 16;

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

// A list of the named files; activated collects the rows opened
function listOf(...names) {
    const element = document.createElement('ul');
    const activated = [];
    const list = new TaskList(element, 'action.open',
        (task) => activated.push(task));
    list.add(names.map((name) => ({ name, key: name })));
    return { list, element, activated };
}

function selectedNames(list) {
    return list.selected().map((task) => task.source.name);
}

// The row's cells: name, pages, state, action
function cells(task) {
    const [name, pages, state, action] = task.item.children;
    return { name, pages, state, action };
}

function readCells(task) {
    const [squares] = cells(task).pages.children;
    return squares.children.map((cell) => cell.className === 'read');
}

describe('TaskList', () => {
    test('a file already in the list is not added again', () => {
        const { list, element } = listOf('a.pdf', 'b.pdf', 'a.pdf');
        const added = list.add([{ name: 'b.pdf', key: 'b.pdf' },
            { name: 'c.pdf', key: 'c.pdf' }]);
        assert.deepEqual(added.map((task) => task.source.name), ['c.pdf']);
        assert.deepEqual(element.children, list.tasks.map((t) => t.item));
        assert.equal(list.tasks.length, 3);
    });

    test('a click selects one row; with Ctrl, Cmd or Shift one more', () => {
        const { list } = listOf('a.pdf', 'b.pdf', 'c.pdf');
        const [a, b, c] = list.tasks;
        a.item.dispatch('click');
        b.item.dispatch('click');
        assert.deepEqual(selectedNames(list), ['b.pdf']);
        c.item.dispatch('click', { ctrlKey: true });
        a.item.dispatch('click', { metaKey: true });
        assert.deepEqual(selectedNames(list), ['a.pdf', 'b.pdf', 'c.pdf']);
        c.item.dispatch('click', { shiftKey: true });
        assert.deepEqual(selectedNames(list), ['a.pdf', 'b.pdf']);
        assert.ok(a.item.classList.contains('selected'));
        assert.ok(!c.item.classList.contains('selected'));
    });

    test('a second click on the only selected row clears it', () => {
        const { list } = listOf('a.pdf');
        list.tasks[0].item.dispatch('click');
        list.tasks[0].item.dispatch('click');
        assert.deepEqual(list.selected(), []);
    });

    test('the button of a row opens it without selecting it', () => {
        const { list, activated } = listOf('a.pdf');
        const [task] = list.tasks;
        task.state = State.DONE;
        list.paint(task);
        const [button] = cells(task).action.children;
        assert.equal(button.textContent, t('action.open'));
        button.dispatch('click');
        assert.deepEqual(activated, [task]);
        assert.ok(!task.selected);
        task.item.dispatch('dblclick');
        assert.deepEqual(activated, [task, task]);
    });

    test('removing leaves the running file in the list', () => {
        const { list, element } = listOf('a.pdf', 'b.pdf', 'c.pdf');
        const [a, b, c] = list.tasks;
        b.state = State.RUNNING;
        assert.deepEqual(list.removeIdle([...list.tasks]), [a, c]);
        assert.deepEqual(list.tasks, [b]);
        assert.deepEqual(element.children, [b.item]);
    });

    test('pending files are all but the finished ones', () => {
        const { list } = listOf('a.pdf', 'b.pdf', 'c.pdf');
        const [a, b, c] = list.tasks;
        a.state = State.DONE;
        b.state = State.FAILED;
        assert.deepEqual(list.pending(), [b, c]);
        assert.equal(list.count(State.DONE), 1);
        assert.equal(list.count(State.RUNNING), 0);
    });

    test('a row shows its state, and an action where there is one', () => {
        const { list } = listOf('a.pdf');
        const [task] = list.tasks;
        const shown = () => {
            list.paint(task);
            const { state, action } = cells(task);
            return [task.item.className, state.textContent,
                action.textContent];
        };
        assert.deepEqual(shown(), ['waiting', t('task.waiting'), '']);
        task.state = State.RUNNING;
        task.progress.update('ocr', 1, 4);
        assert.deepEqual(shown(), ['running', '25 %', '']);
        task.state = State.DONE;
        assert.deepEqual(shown(),
            ['done', t('task.done'), t('action.open')]);
        task.state = State.CANCELLED;
        assert.deepEqual(shown(), ['cancelled', t('task.cancelled'), '']);
        task.state = State.FAILED;
        assert.deepEqual(shown(),
            ['failed', t('task.failed'), t('task.reason')]);
    });

    test('the tooltip names the file and why it failed', () => {
        const { list } = listOf();
        const [task] = list.add(
            [{ name: 'a.pdf', key: 'k', path: '/s/a.pdf' }]);
        assert.equal(task.item.title, '/s/a.pdf');
        task.state = State.FAILED;
        task.setError('encrypted', '');
        list.paint(task);
        assert.equal(task.item.title, `/s/a.pdf\n\n${task.error}`);
        assert.equal(cells(task).name.textContent, `a.pdf${task.error}`);
    });

    test('a file without a page count shows a dash', () => {
        const { list } = listOf('a.pdf');
        assert.equal(cells(list.tasks[0]).pages.textContent, '—');
    });

    test('the pages fit into at most 16 cells, filled in order', () => {
        const { list } = listOf('a.pdf');
        const [task] = list.tasks;
        for (let pages = 1; pages <= 200; pages++) {
            let filled = 0;
            for (let done = 0; done <= pages; done++) {
                task.progress.pages = pages;
                task.progress.pagesDone = done;
                list.paint(task);
                const read = readCells(task);
                const count = read.filter(Boolean).length;
                assert.ok(read.length <= MAX_CELLS, `${pages}`);
                assert.ok(count >= filled, `${done} of ${pages}`);
                assert.deepEqual(read,
                    read.map((_, i) => i < count), `${done} of ${pages}`);
                filled = count;
            }
            assert.equal(filled, readCells(task).length, `${pages}`);
            assert.match(cells(task).pages.textContent,
                new RegExp(`^${pages} / ${pages}`));
        }
        task.progress.pagesDone = 0;
        list.paint(task);
        assert.ok(readCells(task).every((read) => !read));
    });
});

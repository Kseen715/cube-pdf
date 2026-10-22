// One input file in the list, and the list itself

import { outputName } from './config.js';
import { FileProgress } from './progress.js';

// Engine error kind -> what we tell the user
const ERROR_MESSAGES = {
    encrypted: 'Файл защищён паролем. Снимите пароль и попробуйте ещё раз.',
    has_text:
        'В файле уже есть текст. Чтобы распознать его заново, отметьте ' +
        '«Распознать заново» в разделе «Обработка».',
    output_access:
        'Не получилось сохранить результат. Наверное, файл «{output}» ' +
        'открыт в другой программе. Закройте его и попробуйте ещё раз.',
    bad_input: 'Файл повреждён, или это не PDF и не картинка.',
    missing_dependency:
        'Программа собрана неправильно: не найден её компонент.',
    too_big: 'Файл слишком большой: не хватило памяти компьютера.',
    other: 'Что-то пошло не так.',
    crash: 'Распознавание неожиданно прервалось.',
};

// A long document shows this many cells; each then stands for several pages
const MAX_CELLS = 16;

export const State = {
    WAITING: 'waiting',
    RUNNING: 'running',
    DONE: 'done',
    FAILED: 'failed',
    CANCELLED: 'cancelled',
};

// State -> [the word in the state column, the row's action]; a finished
// file's action is named by the engine
const STATE_VIEW = {
    [State.WAITING]: ['Ждёт', ''],
    [State.RUNNING]: ['', ''],
    [State.DONE]: ['Готово', ''],
    [State.FAILED]: ['Ошибка', 'Причина'],
    [State.CANCELLED]: ['Остановлено', ''],
};

export class Task {
    // source: {name, key, path} on the desktop, {name, key, file} on the web
    constructor(source) {
        this.source = source;
        this.output = outputName(source.name);
        this.result = null; // the engine's handle on the finished file
        this.selected = false;
        this.reset();
    }

    reset() {
        this.state = State.WAITING;
        this.error = '';
        this.details = '';
        this.progress = new FileProgress();
    }

    setError(kind, details) {
        const message = ERROR_MESSAGES[kind] ?? ERROR_MESSAGES.other;
        this.error = message.replace('{output}', this.output);
        this.details = details;
    }

    // The second line under the file name
    note() {
        switch (this.state) {
            case State.RUNNING:
                return `${this.progress.label || 'Запускаю'}…`;
            case State.DONE:
                return `Сохранён как ${this.output}`;
            case State.FAILED:
                return this.error;
            default:
                return `Получится ${this.output}`;
        }
    }
}

function element(tag, className = '', text = '') {
    const node = document.createElement(tag);
    node.className = className;
    node.textContent = text;
    return node;
}

function pagesCell({ pages, pagesDone }) {
    const cell = element('div', 'task-pages');
    if (!pages) {
        cell.append(element('span', 'none', '—'));
        return cell;
    }
    const perCell = Math.ceil(pages / MAX_CELLS);
    const cells = element('span', 'cells');
    for (let i = 0; i < Math.ceil(pages / perCell); i++) {
        const read = (i + 1) * perCell <= pagesDone || pagesDone === pages;
        cells.append(element('i', read ? 'read' : ''));
    }
    const count = element('span', '', `${pagesDone} / ${pages}`);
    count.append(element('span', 'unit', ' стр.'));
    cell.append(cells, count);
    return cell;
}

export class TaskList {
    // doneLabel: the action of a finished file;
    // onActivate(task): open a finished file or explain a failed one
    constructor(list, doneLabel, onActivate) {
        this.element = list;
        this.doneLabel = doneLabel;
        this.onActivate = onActivate;
        this.tasks = [];
    }

    // Returns the new tasks; files already in the list are not added again
    add(sources) {
        const known = new Set(this.tasks.map((task) => task.source.key));
        const added = [];
        for (const source of sources) {
            if (!known.has(source.key)) {
                known.add(source.key);
                added.push(this.append(new Task(source)));
            }
        }
        return added;
    }

    // Removes every given task that is not running; returns the removed ones
    removeIdle(tasks) {
        const removed = tasks.filter((t) => t.state !== State.RUNNING);
        for (const task of removed) {
            this.tasks.splice(this.tasks.indexOf(task), 1);
            task.item.remove();
        }
        return removed;
    }

    selected() {
        return this.tasks.filter((task) => task.selected);
    }

    pending() {
        return this.tasks.filter((task) => task.state !== State.DONE);
    }

    count(state) {
        return this.tasks.filter((task) => task.state === state).length;
    }

    paint(task) {
        const [word, view] = STATE_VIEW[task.state];
        const action = task.state === State.DONE ? this.doneLabel : view;
        const name = element('div', 'task-name');
        name.append(element('span', 'file', task.source.name),
            element('span', 'sub', task.note()));

        const state = element('div', 'task-state');
        if (task.state === State.RUNNING)
            state.textContent = `${Math.floor(task.progress.percent)} %`;
        else if (task.state === State.DONE || task.state === State.FAILED)
            state.append(element('span', 'pill', word));
        else state.textContent = word;

        const actionCell = element('div', 'task-action');
        if (action) {
            const button = element('button', 'text-button', action);
            button.type = 'button';
            button.addEventListener('click', () => this.onActivate(task));
            actionCell.append(button);
        }

        task.item.className = task.state;
        task.item.classList.toggle('selected', task.selected);
        task.item.title = [task.source.path ?? task.source.name, task.error]
            .filter(Boolean)
            .join('\n\n');
        task.item.replaceChildren(name, pagesCell(task.progress), state,
            actionCell);
    }

    append(task) {
        task.item = document.createElement('li');
        task.item.addEventListener('click', (event) => {
            if (event.target.closest('button')) return;
            const only = !event.ctrlKey && !event.metaKey && !event.shiftKey;
            for (const other of this.tasks) {
                if (other === task) other.selected = !other.selected;
                else if (only) other.selected = false;
                other.item.classList.toggle('selected', other.selected);
            }
        });
        task.item.addEventListener('dblclick', () => this.onActivate(task));
        this.tasks.push(task);
        this.element.append(task.item);
        this.paint(task);
        return task;
    }
}

// One input file in the list, and the list itself

import { outputName } from './config.js';

// Engine error kind -> what we tell the user
const ERROR_MESSAGES = {
    encrypted: 'Файл защищён паролем. Снимите пароль и попробуйте ещё раз.',
    has_text:
        'В файле уже есть текст. Чтобы распознать его заново, нажмите ' +
        '«Дополнительные настройки» и отметьте «Распознать заново».',
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

export const State = {
    WAITING: 'waiting',
    RUNNING: 'running',
    DONE: 'done',
    FAILED: 'failed',
    CANCELLED: 'cancelled',
};

export class Task {
    // source: {name, key, path} on the desktop, {name, key, file} on the web
    constructor(source) {
        this.source = source;
        this.output = outputName(source.name);
        this.state = State.WAITING;
        this.error = '';
        this.details = '';
        this.result = null; // the engine's handle on the finished file
    }

    reset() {
        this.state = State.WAITING;
        this.error = '';
        this.details = '';
    }

    setError(kind, details) {
        const message = ERROR_MESSAGES[kind] ?? ERROR_MESSAGES.other;
        this.error = message.replace('{output}', this.output);
        this.details = details;
    }

    stateText(percent) {
        switch (this.state) {
            case State.WAITING:
                return 'ждёт';
            case State.RUNNING:
                return `в работе… ${percent ?? 0}%`;
            case State.DONE:
                return `✔ готово → ${this.output}`;
            case State.FAILED:
                return '✖ не получилось (двойной щелчок — подробности)';
            default:
                return 'остановлено';
        }
    }
}

export class TaskList {
    constructor(element) {
        this.element = element;
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
        return this.tasks.filter((t) => t.item.classList.contains('selected'));
    }

    pending() {
        return this.tasks.filter((task) => task.state !== State.DONE);
    }

    paint(task, percent) {
        task.item.textContent =
            `${task.source.name}   —   ${task.stateText(percent)}`;
        task.item.title = [task.source.path ?? task.source.name, task.error]
            .filter(Boolean)
            .join('\n\n');
        task.item.dataset.state = task.state;
    }

    append(task) {
        task.item = document.createElement('li');
        task.item.addEventListener('click', (event) => {
            if (!event.ctrlKey && !event.metaKey && !event.shiftKey) {
                for (const other of this.tasks)
                    other.item.classList.remove('selected');
            }
            task.item.classList.toggle('selected');
        });
        this.tasks.push(task);
        this.element.append(task.item);
        this.paint(task);
        return task;
    }
}

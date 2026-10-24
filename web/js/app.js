// The window. Deliberately simple: pick files, tick languages, press start.
// The same page runs in the browser (engine-web.js) and inside the desktop
// and Android apps (engine-desktop.js, engine-android.js); the engine is the
// only difference.

import {
    APP_NAME, DEFAULT_LANGUAGES, LANGUAGES, RELEASES_URL, hasInputExtension,
} from './config.js';
import * as dialogs from './dialogs.js';
import { State, TaskList } from './tasks.js';
import { checkForUpdate } from './update.js';
import { APP_VERSION } from './version.js';

const START_TEXT = 'Начать распознавание';
const STOP_TEXT = 'Остановить';
const FILE_WORDS = ['файл', 'файла', 'файлов'];
const REJECTED_PREFIX = 'Пропущены (это не PDF и не картинки): ';
const LOG_LINES_IN_DETAILS = 200;
const SETTINGS_KEY = 'ocr-pdf-settings';

const $ = (id) => document.getElementById(id);

// The Russian noun form for a count: 1 файл, 2 файла, 5 файлов
function plural(count, [one, few, many]) {
    const tens = count % 100;
    const units = count % 10;
    if (tens >= 11 && tens <= 14) return many;
    if (units === 1) return one;
    if (units >= 2 && units <= 4) return few;
    return many;
}

function loadSettings() {
    try {
        return JSON.parse(localStorage.getItem(SETTINGS_KEY)) ?? {};
    } catch {
        return {};
    }
}

class App {
    constructor(engine) {
        this.engine = engine;
        this.list = new TaskList($('tasks'), engine.actions.rowLabel,
            (task) => this.taskActivated(task));
        this.settings = loadSettings();
        this.running = false;
        this.run = null;
        this.current = null;
        this.batch = [];
        this.cancelling = false;
        this.log = [];
        this.update = null;
        this.updating = false;

        document.title = APP_NAME;
        $('intro').textContent = engine.intro;
        $('native').hidden = engine.kind !== 'web';
        $('releases').href = RELEASES_URL;
        $('version').textContent = APP_VERSION;
        this.buildLanguages();
        this.connect();
        this.applySettings();
        this.refresh();
        engine.startupSources().then((sources) => this.addSources(sources));
        this.checkUpdate();
    }

    buildLanguages() {
        this.languageBoxes = {};
        for (const [code, name] of Object.entries(LANGUAGES)) {
            const label = document.createElement('label');
            const box = document.createElement('input');
            box.type = 'checkbox';
            box.addEventListener('change', () => this.languageToggled(box));
            label.className = 'choice';
            label.append(box, name);
            $('languages').append(label);
            this.languageBoxes[code] = box;
        }
    }

    connect() {
        $('drop').addEventListener('click', () => this.pickFiles());
        $('clear').addEventListener('click', () => this.clearList());
        $('start').addEventListener('click', () => this.startOrStop());
        $('about').addEventListener('click', () => dialogs.showAbout());
        $('update').addEventListener('click', () => this.offerUpdate());
        document.addEventListener('keydown', (event) => {
            if (event.key === 'F1') {
                event.preventDefault();
                dialogs.showAbout();
            } else if (event.key === 'Delete' && !$('dialog').open) {
                this.removeSelected();
            }
        });
        this.engine.onDrop((sources) => this.addSources(sources));
        this.engine.onClose({
            running: () => this.running,
            confirmStop: () => this.confirmClose(),
        });
    }

    // --- settings --------------------------------------------------------

    applySettings() {
        let codes = this.settings.languages ?? DEFAULT_LANGUAGES;
        if (!codes.some((code) => code in LANGUAGES)) codes = DEFAULT_LANGUAGES;
        for (const [code, box] of Object.entries(this.languageBoxes))
            box.checked = codes.includes(code);
        $('deskew').checked = Boolean(this.settings.deskew);
        $('force').checked = Boolean(this.settings.force);
    }

    saveSettings() {
        Object.assign(this.settings, {
            languages: this.languages(),
            deskew: $('deskew').checked,
            force: $('force').checked,
        });
        try {
            localStorage.setItem(SETTINGS_KEY, JSON.stringify(this.settings));
        } catch {
            // settings are a convenience; the run goes on without them
        }
    }

    languages() {
        return Object.entries(this.languageBoxes)
            .filter(([, box]) => box.checked)
            .map(([code]) => code);
    }

    languageToggled(box) {
        if (!box.checked && !this.languages().length) {
            box.checked = true;
            $('status').textContent = 'Нужно оставить хотя бы один язык.';
        }
    }

    options() {
        return {
            languages: this.languages(),
            deskew: $('deskew').checked,
            force: $('force').checked,
        };
    }

    // --- file list -------------------------------------------------------

    async pickFiles() {
        const sources = await this.engine.pickFiles(this.settings.lastDir);
        if (sources.length && sources[0].path) {
            this.settings.lastDir = this.engine.folderOf(sources[0]);
            this.saveSettings();
        }
        this.addSources(sources);
        return sources.length > 0;
    }

    addSources(sources) {
        const rejected = sources.filter((s) => !hasInputExtension(s.name));
        const added = this.list.add(
            sources.filter((s) => hasInputExtension(s.name)));
        if (this.running) this.batch.push(...added);

        if (rejected.length) {
            $('status').textContent =
                REJECTED_PREFIX + rejected.map((s) => s.name).join(', ');
        } else if (!this.running) {
            $('status').textContent = '';
        }
        this.refresh();
    }

    removeSelected() {
        this.forget(this.list.removeIdle(this.list.selected()));
        this.refresh();
    }

    clearList() {
        this.forget(this.list.removeIdle([...this.list.tasks]));
        $('status').textContent = '';
        $('progress').value = 0;
        this.refresh();
    }

    forget(removed) {
        this.batch = this.batch.filter((task) => !removed.includes(task));
    }

    taskActivated(task) {
        if (task.state === State.DONE) this.engine.actions.open(task);
        else if (task.state === State.FAILED) dialogs.showError(task);
    }

    // --- updates ---------------------------------------------------------

    // The web version is always the latest, so its engine has no updates
    async checkUpdate() {
        const updates = this.engine.updates;
        if (!updates) return;
        try {
            const update = await checkForUpdate(APP_VERSION,
                await updates.kind());
            if (update && (update.file || updates.openPage)) {
                this.update = update;
                $('update').hidden = false;
            }
        } catch {
            // offline, or GitHub did not answer: the app works as it is
        }
    }

    async offerUpdate() {
        const update = this.update;
        if (this.running) {
            await dialogs.showMessage(
                'Обновить программу можно, когда распознавание закончится.');
            return;
        }
        if (!(await dialogs.confirmUpdate(update))) return;
        if (!update.file) {
            this.engine.updates.openPage(update.page);
            return;
        }

        this.updating = true;
        this.refresh();
        $('status').textContent = 'Скачиваю обновление…';
        try {
            await this.engine.updates.install(update, (percent) => {
                $('status').textContent = `Скачиваю обновление… ${percent} %`;
            });
            $('status').textContent = '';
        } catch (error) {
            $('status').textContent = '';
            await dialogs.showUpdateFailed(`${error}`);
        }
        this.updating = false;
        this.refresh();
    }

    // --- running ---------------------------------------------------------

    async startOrStop() {
        if (this.running) {
            this.stop();
            return;
        }
        let pending = this.list.pending();
        if (!pending.length && (await this.pickFiles()))
            pending = this.list.pending();
        if (pending.length) this.start(pending);
    }

    stop() {
        this.cancelling = true;
        this.batch = this.current ? [this.current] : [];
        $('status').textContent = 'Останавливаю…';
        this.run?.cancel();
    }

    start(pending) {
        this.saveSettings();
        this.batch = pending;
        this.batchStarted = Date.now();
        this.cancelling = false;
        this.running = true;
        for (const task of pending) {
            task.reset();
            this.list.paint(task);
        }
        this.refresh();
        this.next();
    }

    async next() {
        const task = this.batch.find((t) => t.state === State.WAITING);
        if (!task || this.cancelling) {
            this.batchFinished();
            return;
        }

        this.current = task;
        this.log = [];
        task.state = State.RUNNING;
        this.list.paint(task);
        task.item.scrollIntoView({ block: 'nearest' });
        this.setStatus('Запускаю');
        try {
            this.run = await this.engine.start(task, this.options(),
                (message) => this.onMessage(message));
        } catch (error) {
            this.taskFailed(task, 'crash', `${error}`);
            this.next();
            return;
        }
        this.finished(await this.run.finished);
    }

    onMessage(message) {
        const task = this.current;
        if (!task) return;

        if (message.event === 'log') {
            this.log.push(`${message.level}: ${message.msg}`);
        } else if (message.event === 'progress') {
            this.setStatus(task.progress.update(
                message.stage, message.done, message.total));
            this.list.paint(task);
        } else if (message.event === 'error') {
            task.setError(message.kind, message.detail ?? '');
        }
    }

    finished(code) {
        const task = this.current;
        this.current = null;
        this.run = null;
        if (this.cancelling) task.state = State.CANCELLED;
        else if (code === 0) task.state = State.DONE;
        else this.taskFailed(task, task.error ? null : 'crash');
        if (task.state === State.DONE)
            task.progress.pagesDone = task.progress.pages;
        this.list.paint(task);
        this.refresh();
        this.next();
    }

    // kind is null when the engine already said what went wrong
    taskFailed(task, kind, details = '') {
        task.state = State.FAILED;
        if (kind) task.setError(kind, details);
        const log = this.log.slice(-LOG_LINES_IN_DETAILS).join('\n');
        task.details += `\n\nЖурнал:\n${log}`;
        this.list.paint(task);
    }

    setStatus(text) {
        const task = this.current;
        if (!task) return;
        const count = this.batch.length;
        const index = Math.max(this.batch.indexOf(task), 0);

        const prefix = count > 1 ? `Файл ${index + 1} из ${count}: ` : '';
        $('status').textContent = `${prefix}${task.source.name}\n${text}…`;
        const fileFraction = task.progress.percent / 100;
        $('progress').value = ((index + fileFraction) / count) * 100;
    }

    batchFinished() {
        const batch = this.batch;
        this.batch = [];
        this.running = false;
        this.refresh();
        if (this.cancelling) {
            this.cancelling = false;
            $('status').textContent = 'Остановлено.';
            $('progress').value = 0;
            return;
        }

        const done = batch.filter((task) => task.state === State.DONE);
        const failed = batch.filter((task) => task.state === State.FAILED);
        $('progress').value = done.length && !failed.length ? 100 : 0;
        $('status').textContent = this.summary(done.length, failed.length);

        this.engine.attention();
        if (batch.length === 1 && failed.length) dialogs.showError(failed[0]);
        else if (done.length && this.engine.actions.doneDialog)
            dialogs.showDone(done, failed, this.engine.actions);
        else if (failed.length) dialogs.showAllFailed();
    }

    summary(done, failed) {
        const elapsed = Math.floor((Date.now() - this.batchStarted) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        const took = minutes ? `${minutes} мин ${seconds} с` : `${seconds} с`;
        let summary = `Готово за ${took}. Получилось: ${done}`;
        if (failed) summary += `, не получилось: ${failed}`;
        return `${summary}.`;
    }

    refresh() {
        const start = $('start');
        start.textContent = this.running ? STOP_TEXT : START_TEXT;
        start.classList.toggle('running', this.running);
        start.disabled = this.updating;
        $('update').disabled = this.updating;
        for (const box of [...Object.values(this.languageBoxes),
            $('deskew'), $('force')])
            box.disabled = this.running;
        $('clear').disabled = !this.list.tasks.length;
        if (!this.running && !this.list.tasks.length) $('progress').value = 0;
        $('files').classList.toggle('has-files', this.list.tasks.length > 0);
        $('count').textContent = this.countText();
    }

    countText() {
        const total = this.list.tasks.length;
        if (!total) return '';
        const parts = [`${total} ${plural(total, FILE_WORDS)}`];
        const done = this.list.count(State.DONE);
        const failed = this.list.count(State.FAILED);
        if (done) parts.push(`готово ${done}`);
        if (failed) parts.push(`с ошибкой ${failed}`);
        return parts.join(' · ');
    }

    async confirmClose() {
        const answer = await dialogs.showMessage(
            'Распознавание ещё идёт. Остановить его и закрыть программу?',
            ['Да', 'Нет']);
        if (answer !== 'Да') return false;
        this.stop();
        this.saveSettings();
        return true;
    }
}

async function loadEngine() {
    if (!window.__TAURI__)
        return new (await import('./engine-web.js')).WebEngine();
    if (navigator.userAgent.includes('Android'))
        return new (await import('./engine-android.js')).AndroidEngine();
    return new (await import('./engine-desktop.js')).DesktopEngine();
}

async function main() {
    const engine = await loadEngine();
    await engine.init();
    new App(engine);
}

main();

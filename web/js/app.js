// The window. Deliberately simple: pick files, tick languages, press start.
// The same page runs in the browser (engine-web.js) and inside the desktop
// and Android apps (engine-desktop.js, engine-android.js); the engine is the
// only difference.

import {
    APP_NAME, DEFAULT_LANGUAGES, LANGUAGES, OUTPUT_SUFFIX, RELEASES_URL,
    hasInputExtension,
} from './config.js';
import * as dialogs from './dialogs.js';
import {
    LOCALES, currentLocale, localizePage, onLocaleChange, setLocale, t,
} from './i18n.js';
import { State, TaskList } from './tasks.js';
import { checkForUpdate } from './update.js';
import { APP_VERSION } from './version.js';

const LOG_LINES_IN_DETAILS = 200;
const SETTINGS_KEY = 'ocr-pdf-settings';

const $ = (id) => document.getElementById(id);

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
        this.statusText = null;

        document.title = APP_NAME;
        $('native').hidden = engine.kind !== 'web';
        $('releases').href = RELEASES_URL;
        $('version').textContent = APP_VERSION;
        this.buildLocales();
        this.buildLanguages();
        this.connect();
        this.applySettings();
        this.localize();
        engine.startupSources().then((sources) => this.addSources(sources));
        this.checkUpdate();
    }

    buildLocales() {
        for (const [code, { name }] of Object.entries(LOCALES)) {
            const option = new Option(name, code);
            option.lang = code;
            $('locale').append(option);
        }
        $('locale').value = currentLocale();
        $('locale').addEventListener('change',
            () => setLocale($('locale').value));
        onLocaleChange(() => this.localize());
    }

    buildLanguages() {
        this.languageBoxes = {};
        for (const code of LANGUAGES) {
            const label = document.createElement('label');
            const box = document.createElement('input');
            box.type = 'checkbox';
            box.addEventListener('change', () => this.languageToggled(box));
            label.className = 'choice';
            label.append(box, document.createElement('span'));
            $('languages').append(label);
            this.languageBoxes[code] = box;
        }
    }

    // Every text in the window, again in the interface language
    localize() {
        localizePage();
        $('locale-code').textContent = currentLocale().toUpperCase();
        $('intro').textContent = t(this.engine.intro,
            { suffix: OUTPUT_SUFFIX });
        for (const [code, box] of Object.entries(this.languageBoxes))
            box.nextSibling.textContent = t(`language.${code}`);
        for (const task of this.list.tasks) this.list.paint(task);
        this.showStatus(this.statusText);
        this.refresh();
    }

    // text: a function that builds the line, so that it can be built
    // again in another language; null clears it
    showStatus(text) {
        this.statusText = text;
        $('status').textContent = text ? text() : '';
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

    // Without saved settings, the language of the interface is ticked too
    applySettings() {
        const defaults = [LOCALES[currentLocale()].ocr, ...DEFAULT_LANGUAGES];
        let codes = this.settings.languages ?? defaults;
        if (!codes.some((code) => LANGUAGES.includes(code))) codes = defaults;
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
            this.showStatus(() => t('languages.keepOne'));
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
            const names = rejected.map((s) => s.name).join(', ');
            this.showStatus(() => t('files.rejected', { names }));
        } else if (!this.running) {
            this.showStatus(null);
        }
        this.refresh();
    }

    removeSelected() {
        this.forget(this.list.removeIdle(this.list.selected()));
        this.refresh();
    }

    clearList() {
        this.forget(this.list.removeIdle([...this.list.tasks]));
        this.showStatus(null);
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
            await dialogs.showMessage(t('update.whenDone'));
            return;
        }
        if (!(await dialogs.confirmUpdate(update))) return;
        if (!update.file) {
            this.engine.updates.openPage(update.page);
            return;
        }

        this.updating = true;
        this.refresh();
        this.showStatus(() => t('update.downloading'));
        try {
            await this.engine.updates.install(update, (percent) => {
                this.showStatus(
                    () => t('update.downloadingPercent', { percent }));
            });
            this.showStatus(null);
        } catch (error) {
            this.showStatus(null);
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
        this.showStatus(() => t('status.stopping'));
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
        this.setStatus();
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
            task.progress.update(message.stage, message.done, message.total);
            this.setStatus();
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
        task.details += `\n\n${t('task.log')}\n${log}`;
        this.list.paint(task);
    }

    setStatus() {
        const task = this.current;
        if (!task) return;
        const count = this.batch.length;
        const index = Math.max(this.batch.indexOf(task), 0);

        this.showStatus(() => {
            const prefix = count > 1
                ? t('status.file', { index: index + 1, count })
                : '';
            return `${prefix}${task.source.name}\n${task.note()}`;
        });
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
            this.showStatus(() => t('status.stopped'));
            $('progress').value = 0;
            return;
        }

        const done = batch.filter((task) => task.state === State.DONE);
        const failed = batch.filter((task) => task.state === State.FAILED);
        $('progress').value = done.length && !failed.length ? 100 : 0;
        const elapsed = Math.floor((Date.now() - this.batchStarted) / 1000);
        this.showStatus(
            () => this.summary(elapsed, done.length, failed.length));

        this.engine.attention();
        if (batch.length === 1 && failed.length) dialogs.showError(failed[0]);
        else if (done.length && this.engine.actions.doneDialog)
            dialogs.showDone(done, failed, this.engine.actions);
        else if (failed.length) dialogs.showAllFailed();
    }

    summary(elapsed, done, failed) {
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        const took = t(minutes ? 'time.minutes' : 'time.seconds',
            { minutes, seconds });
        return t(failed ? 'status.summaryFailed' : 'status.summary',
            { took, done, failed });
    }

    refresh() {
        const start = $('start');
        start.textContent = t(this.running ? 'stop' : 'start');
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
        const parts = [t('files.count', { count: total })];
        const done = this.list.count(State.DONE);
        const failed = this.list.count(State.FAILED);
        if (done) parts.push(t('files.done', { count: done }));
        if (failed) parts.push(t('files.failed', { count: failed }));
        return parts.join(' · ');
    }

    async confirmClose() {
        const yes = t('dialog.yes');
        const answer = await dialogs.showMessage(t('close.running'),
            [yes, t('dialog.no')]);
        if (answer !== yes) return false;
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
    localizePage();
    const engine = await loadEngine();
    await engine.init();
    new App(engine);
}

main();

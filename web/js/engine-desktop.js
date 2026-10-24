// The desktop engine: the native ocr-pdf-core, which the Tauri shell starts
// once per file. The result goes next to the original file.

import { INPUT_EXTENSIONS, OUTPUT_SUFFIX } from './config.js';
import { coreMessage, runOptions } from './core.js';
import { t } from './i18n.js';
import { appUpdates } from './update.js';

const tauri = window.__TAURI__;
const CORE = 'binaries/ocr-pdf-core';
const FILTER_EXTENSIONS = INPUT_EXTENSIONS.map((ext) => ext.slice(1));

function splitPath(path) {
    const cut = Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'));
    return [path.slice(0, cut + 1), path.slice(cut + 1)];
}

function source(path) {
    // Windows and macOS file systems ignore case
    return { name: splitPath(path)[1], path, key: path.toLowerCase() };
}

export class DesktopEngine {
    constructor() {
        this.kind = 'desktop';
        // The texts are keys of i18n.js
        this.intro = 'intro.desktop';
        this.actions = {
            whereSingle: 'where.besideOne',
            whereMany: 'where.besideMany',
            rowLabel: 'action.open',
            open: (task) => tauri.opener.openPath(task.result),
            reveal: (task) => tauri.opener.revealItemInDir(task.result),
            doneDialog: true,
        };
        // The portable zip and other copies not installed from a package
        // send the user to the release's page instead
        this.updates = {
            ...appUpdates,
            openPage: (url) => tauri.opener.openUrl(url),
        };
    }

    async init() {
        this.tessdata = await tauri.path.resolveResource('tessdata');
    }

    // Paths -> sources; ocr-pdf-core expands folders
    async expand(paths) {
        const args = ['expand', '--extensions', INPUT_EXTENSIONS.join(','),
            '--skip-suffix', OUTPUT_SUFFIX, ...paths];
        const result = await tauri.shell.Command.sidecar(CORE, args).execute();
        return JSON.parse(result.stdout).map(source);
    }

    // Files the app was started with, such as ones dropped onto its icon
    async startupSources() {
        const paths = await tauri.core.invoke('startup_paths');
        return paths.length ? this.expand(paths) : [];
    }

    async pickFiles(startDir) {
        const paths = await tauri.dialog.open({
            multiple: true,
            defaultPath: startDir || undefined,
            filters: [
                { name: t('filter.supported'),
                    extensions: FILTER_EXTENSIONS },
                { name: t('filter.all'), extensions: ['*'] },
            ],
        });
        return paths ? this.expand(paths) : [];
    }

    folderOf(source) {
        return splitPath(source.path)[0];
    }

    onDrop(callback) {
        tauri.webview.getCurrentWebview().onDragDropEvent(async (event) => {
            if (event.payload.type === 'drop')
                callback(await this.expand(event.payload.paths));
        });
    }

    // guard: {running(), confirmStop()}, see App.connect
    onClose(guard) {
        const window = tauri.window.getCurrentWindow();
        window.onCloseRequested(async (event) => {
            if (guard.running() && !(await guard.confirmStop()))
                event.preventDefault();
        });
    }

    attention() {
        const window = tauri.window.getCurrentWindow();
        const { UserAttentionType } = tauri.window;
        window.requestUserAttention(UserAttentionType.Informational);
    }

    // Runs one file; onMessage gets the core's JSON messages. Resolves when
    // the process ends; cancel() kills it, and its Ghostscript with it.
    async start(task, options, onMessage) {
        const output = this.folderOf(task.source) + task.output;
        const args = ['run', '--input', task.source.path, '--output', output,
            '--tessdata', this.tessdata, ...runOptions(options)];

        const command = tauri.shell.Command.sidecar(CORE, args);
        command.stdout.on('data', (line) =>
            onMessage(coreMessage(line, 'stdout')));
        command.stderr.on('data', (line) =>
            onMessage(coreMessage(line, 'stderr')));
        const finished = new Promise((resolve) => {
            command.on('close', ({ code }) => resolve(code));
            command.on('error', (error) => {
                onMessage({ event: 'error', kind: 'crash',
                    detail: `${error}` });
                resolve(-1);
            });
        });
        const child = await command.spawn();
        task.result = output;
        return { finished, cancel: () => child.kill() };
    }
}

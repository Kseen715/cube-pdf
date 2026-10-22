// The desktop engine: the native ocr-pdf-core, which the Tauri shell starts
// once per file. The result goes next to the original file.

import { INPUT_EXTENSIONS, OUTPUT_SUFFIX } from './config.js';

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
        this.intro = 'Программа читает текст на сканах и фотографиях ' +
            'документов. Исходный файл не меняется: рядом с ним появится ' +
            `новый, с «${OUTPUT_SUFFIX}» в конце названия.`;
        this.actions = {
            whereSingle: 'Он лежит рядом с исходным.',
            whereMany: 'Новые файлы лежат рядом с исходными.',
            rowLabel: 'Открыть',
            openLabel: 'Открыть файл',
            open: (task) => tauri.opener.openPath(task.result),
            reveal: (task) => tauri.opener.revealItemInDir(task.result),
            doneDialog: true,
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
                { name: 'PDF и картинки', extensions: FILTER_EXTENSIONS },
                { name: 'Все файлы', extensions: ['*'] },
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
            '--languages', options.languages.join('+'),
            '--tessdata', this.tessdata];
        if (options.force) args.push('--force');
        if (options.deskew) args.push('--deskew');

        const command = tauri.shell.Command.sidecar(CORE, args);
        command.stdout.on('data', (line) => {
            try {
                onMessage(JSON.parse(line));
            } catch {
                onMessage({ event: 'log', level: 'stdout', msg: line });
            }
        });
        command.stderr.on('data', (line) =>
            onMessage({ event: 'log', level: 'stderr', msg: line }));
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

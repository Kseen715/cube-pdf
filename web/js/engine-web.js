// The web engine: the same OCR core, compiled to WebAssembly, runs in Web
// Workers on this computer's processor. Files never leave the browser; each
// result waits in memory until its row's button downloads it.

import {
    OUTPUT_SUFFIX, hasInputExtension, parallelPages,
} from './config.js';

const MAX_WORKERS = 8;
// Matches ocr_action in core/src/pdf.h
const SKIP = 0;

class WorkerClient {
    constructor() {
        this.worker = new Worker(new URL('./worker.js', import.meta.url),
            { type: 'module' });
        this.calls = new Map();
        this.nextId = 0;
        this.worker.onmessage = ({ data }) => {
            const call = this.calls.get(data.id);
            this.calls.delete(data.id);
            if (data.error) call.reject(data.error);
            else call.resolve(data.result);
        };
        this.worker.onerror = (event) =>
            this.failAll({ kind: 'crash', detail: event.message });
    }

    call(type, args = {}, transfer = []) {
        const id = this.nextId++;
        return new Promise((resolve, reject) => {
            this.calls.set(id, { resolve, reject });
            this.worker.postMessage({ id, type, ...args }, transfer);
        });
    }

    failAll(error) {
        for (const call of this.calls.values()) call.reject(error);
        this.calls.clear();
    }

    terminate() {
        this.worker.terminate();
        this.failAll({ kind: 'cancelled', detail: '' });
    }
}

function workerCount(pages) {
    return Math.max(1, Math.min(pages, parallelPages(), MAX_WORKERS));
}

function source(file) {
    return { name: file.name, file,
        key: `${file.name}|${file.size}|${file.lastModified}` };
}

// Inside folders our own results are skipped, as on the desktop
function wantedInFolder(name) {
    const stem = name.slice(0, name.lastIndexOf('.'));
    return hasInputExtension(name) && !stem.endsWith(OUTPUT_SUFFIX);
}

async function folderFiles(entry) {
    const reader = entry.createReader();
    const entries = [];
    for (;;) {
        const batch = await new Promise((resolve, reject) =>
            reader.readEntries(resolve, reject));
        if (!batch.length) break;
        entries.push(...batch);
    }
    entries.sort((a, b) => a.name.localeCompare(b.name));

    const files = [];
    for (const child of entries) {
        if (child.isDirectory) files.push(...(await folderFiles(child)));
        else if (wantedInFolder(child.name))
            files.push(await new Promise((ok, fail) => child.file(ok, fail)));
    }
    return files;
}

async function droppedFiles(dataTransfer) {
    const entries = [...dataTransfer.items]
        .map((item) => item.webkitGetAsEntry?.())
        .filter(Boolean);
    if (!entries.length) return [...dataTransfer.files];

    const files = [];
    for (const entry of entries) {
        if (entry.isDirectory) files.push(...(await folderFiles(entry)));
        else files.push(await new Promise((ok, fail) => entry.file(ok, fail)));
    }
    return files;
}

function download(blob, name) {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = name;
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 60_000);
}

export class WebEngine {
    constructor() {
        this.kind = 'web';
        this.intro = 'CUBE-PDF распознаёт текст на сканах и фотографиях ' +
            'документов (OCR) с помощью Tesseract. Распознавание идёт ' +
            'прямо на вашем устройстве: файлы никуда не отправляются и не ' +
            'покидают его. Готовый PDF, в котором можно искать и копировать ' +
            'текст, скачивается кнопкой «Скачать» рядом с названием файла.';
        // The row's button is the download, so no dialog after a batch
        this.actions = {
            rowLabel: 'Скачать',
            open: (task) => download(task.result, task.output),
            doneDialog: false,
        };
        this.pool = [];
        this.input = document.getElementById('file-input');
        this.input.accept = '.pdf,.jpg,.jpeg,.png,.tif,.tiff';
    }

    async init() {}

    async startupSources() {
        return [];
    }

    pickFiles() {
        return new Promise((resolve) => {
            this.input.value = '';
            this.input.onchange = () =>
                resolve([...this.input.files].map(source));
            this.input.oncancel = () => resolve([]);
            this.input.click();
        });
    }

    onDrop(callback) {
        document.addEventListener('dragover', (e) => e.preventDefault());
        document.addEventListener('drop', async (event) => {
            event.preventDefault();
            callback((await droppedFiles(event.dataTransfer)).map(source));
        });
    }

    // guard: {running()}; the browser asks the question itself
    onClose(guard) {
        window.addEventListener('beforeunload', (event) => {
            if (guard.running()) event.preventDefault();
        });
    }

    attention() {}

    // Runs one file; onMessage gets the same messages as from ocr-pdf-core.
    // cancel() stops every worker.
    async start(task, options, onMessage) {
        let cancelled = false;
        const finished = this.process(task, options, onMessage).then(
            (blob) => {
                task.result = blob;
                onMessage({ event: 'done', output: task.output });
                return 0;
            },
            (error) => {
                if (!cancelled) {
                    onMessage({ event: 'error', kind: error.kind ?? 'other',
                        detail: error.detail ?? `${error}` });
                }
                return 1;
            });
        return {
            finished,
            cancel: () => {
                cancelled = true;
                this.stop();
            },
        };
    }

    stop() {
        for (const client of this.pool) client.terminate();
        this.pool = [];
    }

    workers(count) {
        while (this.pool.length < count) this.pool.push(new WorkerClient());
        return this.pool.slice(0, count);
    }

    async process(task, options, onMessage) {
        const progress = (stage, done, total) =>
            onMessage({ event: 'progress', stage, done, total });
        progress('scan', 0, 1);
        const bytes = new Uint8Array(await task.source.file.arrayBuffer());
        const [main] = this.workers(1);
        const { pdf, pages } = await main.call('prepare',
            { name: task.source.name, bytes }, [bytes.buffer]);

        const results = await this.ocrPages(pdf, pages, options, progress);
        if (results.every((page) => page.action === SKIP))
            throw { kind: 'has_text', detail: 'every page already has text' };

        progress('save', 0, 1);
        const ocr = await main.call('assemble', { pdf, pages: results });
        progress('pdfa', 0, 1);
        const pdfa = await main.call('pdfa', { pdf: ocr.pdf });
        if (!pdfa.pdf) {
            const log = pdfa.log.join('\n');
            onMessage({ event: 'log', level: 'warning',
                msg: `Ghostscript could not make PDF/A:\n${log}` });
        }
        progress('pdfa', 1, 1);
        return new Blob([pdfa.pdf ?? ocr.pdf], { type: 'application/pdf' });
    }

    async ocrPages(pdf, pages, options, progress) {
        const workers = this.workers(workerCount(pages));
        await Promise.all(workers.map((w) => w.call('load', { pdf, options })));

        const results = new Array(pages);
        let next = 0;
        let done = 0;
        await Promise.all(workers.map(async (worker) => {
            for (let page; (page = next++) < pages;) {
                results[page] = await worker.call('page', { page });
                progress('ocr', ++done, pages);
            }
        }));
        return results;
    }
}

// The Android engine: the native ocr-pdf-core, which the app starts once
// per file (desktop/src/android.rs). Files come from the system's file
// picker; each result is saved to Downloads.

import { parallelPages } from './config.js';
import { coreMessage, runOptions } from './core.js';
import { appUpdates } from './update.js';

const { invoke, Channel } = window.__TAURI__.core;

function source({ name, uri }) {
    return { name, uri, key: uri };
}

export class AndroidEngine {
    constructor() {
        this.kind = 'android';
        // The texts are keys of i18n.js
        this.intro = 'intro.android';
        this.actions = {
            whereSingle: 'where.downloadsOne',
            whereMany: 'where.downloadsMany',
            rowLabel: 'action.open',
            open: (task) => invoke('open_result', { uri: task.result }),
            doneDialog: true,
        };
        this.updates = appUpdates;
    }

    async init() {}

    async startupSources() {
        return [];
    }

    async pickFiles() {
        return (await invoke('pick_files')).map(source);
    }

    folderOf() {
        return '';
    }

    // Files arrive only through the picker, and the window is not closed
    // the desktop way
    onDrop() {}

    onClose() {}

    attention() {}

    // Runs one file; onMessage gets the core's JSON messages. Resolves when
    // the core ends; cancel() kills it, and its Ghostscript with it.
    async start(task, options, onMessage) {
        const onEvent = new Channel();
        const finished = new Promise((resolve) => {
            onEvent.onmessage = (event) => {
                if (event.kind === 'line') {
                    const stream = event.stderr ? 'stderr' : 'stdout';
                    onMessage(coreMessage(event.text, stream));
                } else if (event.kind === 'finished') {
                    if (event.saved) {
                        task.result = event.saved.uri;
                        task.output = event.saved.name;
                    }
                    resolve(event.code);
                }
            };
            invoke('run_core', {
                input: task.source.uri,
                output: task.output,
                options: [...runOptions(options),
                    '--jobs', `${parallelPages()}`],
                onEvent,
            }).catch((error) => {
                onMessage({ event: 'error', kind: error.kind ?? 'crash',
                    detail: error.detail ?? `${error}` });
                resolve(-1);
            });
        });
        return { finished, cancel: () => invoke('cancel_core') };
    }
}

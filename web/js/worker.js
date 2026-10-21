// A Web Worker with its own instance of the OCR core (WebAssembly). The web
// engine (engine-web.js) sends it one request at a time:
//
//   prepare   the input as a PDF; an image is converted first
//   load      a PDF and the options for the pages that follow
//   page      OCR one page of the loaded PDF
//   assemble  the PDF with the pages' text layers
//   pdfa      PDF/A through Ghostscript, or null if that fails
//
// A failed request answers {error: {kind, detail}} with the core's kinds.

import OcrCore from '../wasm/ocr-core.js';
import { TESSDATA_PATH } from './build-info.js';

const WORK = '/work';
const TESSDATA = '/tessdata';
const TESSDATA_CACHE = 'ocr-tessdata';
// Matches ocr_action in core/src/pdf.h
const SKIP = 0;

const ready = OcrCore().then((core) => {
    core.FS.mkdir(WORK);
    core.FS.mkdir(TESSDATA);
    return core;
});
const loadedLanguages = new Set();

// Language models are large, so they are kept in the Cache Storage
async function fetchModel(lang) {
    const url = new URL(`../${TESSDATA_PATH}${lang}.traineddata`,
        import.meta.url);
    const cache = await caches.open(TESSDATA_CACHE).catch(() => null);
    let response = await cache?.match(url);
    if (!response) {
        response = await fetch(url);
        if (!response.ok) {
            throw { error: 'missing_dependency', detail: `${url}: ` +
                `${response.status}` };
        }
        await cache?.put(url, response.clone());
    }
    return new Uint8Array(await response.arrayBuffer());
}

async function loadLanguages(core, languages) {
    for (const lang of [...languages, 'osd']) {
        if (!loadedLanguages.has(lang)) {
            const model = await fetchModel(lang);
            core.FS.writeFile(`${TESSDATA}/${lang}.traineddata`, model);
            loadedLanguages.add(lang);
        }
    }
}

function check(result) {
    if (result.error) throw result;
    return result;
}

function clearWork(core) {
    for (const name of core.FS.readdir(WORK)) {
        if (name !== '.' && name !== '..') core.FS.unlink(`${WORK}/${name}`);
    }
}

function extension(name) {
    const dot = name.lastIndexOf('.');
    return dot > 0 ? name.slice(dot).toLowerCase() : '';
}

const handlers = {
    prepare(core, { name, bytes }) {
        clearWork(core);
        const input = `${WORK}/input${extension(name)}`;
        core.FS.writeFile(input, bytes);
        const { pdf, pages } = check(core.prepare(input, WORK));
        return { pdf: core.FS.readFile(pdf), pages };
    },

    async load(core, { pdf, options }) {
        await loadLanguages(core, options.languages);
        clearWork(core);
        core.FS.writeFile(`${WORK}/input.pdf`, pdf);
        check(core.startPages(`${WORK}/input.pdf`, TESSDATA, {
            languages: options.languages.join('+'),
            force: options.force,
            deskew: options.deskew,
        }));
        return {};
    },

    page(core, { page }) {
        const result = check(core.ocrPage(page, WORK));
        if (result.action === SKIP) return result;
        const layer = core.FS.readFile(result.layer);
        for (const name of core.FS.readdir(WORK)) {
            if (name.startsWith(`page-${page}.`) ||
                name.startsWith(`page-${page}-`))
                core.FS.unlink(`${WORK}/${name}`);
        }
        return { ...result, layer };
    },

    assemble(core, { pdf, pages }) {
        clearWork(core);
        core.FS.writeFile(`${WORK}/input.pdf`, pdf);
        const results = pages.map((page, i) => {
            if (page.action === SKIP) return { ...page, layer: '' };
            const layer = `${WORK}/layer-${i}.pdf`;
            core.FS.writeFile(layer, page.layer);
            return { ...page, layer };
        });
        check(core.assemble(`${WORK}/input.pdf`, results, `${WORK}/ocr.pdf`));
        return { pdf: core.FS.readFile(`${WORK}/ocr.pdf`) };
    },

    // A fresh Ghostscript each time: it is a program that ends with exit()
    async pdfa(core, { pdf }) {
        const { default: Ghostscript } = await import('../wasm/gs.js');
        const log = [];
        const gs = await Ghostscript({
            print: (line) => log.push(line),
            printErr: (line) => log.push(line),
        });
        gs.FS.writeFile('/in.pdf', pdf);
        gs.FS.writeFile('/pdfa.ps', core.pdfaDefinitions());
        let code;
        try {
            const args = core.pdfaArgs('/pdfa.ps', '/in.pdf', '/out.pdf');
            code = gs.callMain(args);
        } catch (exit) {
            code = exit.status ?? -1;
        }
        const ok = code === 0 && gs.FS.analyzePath('/out.pdf').exists;
        return { pdf: ok ? gs.FS.readFile('/out.pdf') : null, log };
    },
};

function transferables(result) {
    return [result.pdf, result.layer]
        .filter((bytes) => bytes instanceof Uint8Array)
        .map((bytes) => bytes.buffer);
}

self.onmessage = async ({ data: { id, type, ...args } }) => {
    try {
        const result = await handlers[type](await ready, args);
        self.postMessage({ id, result }, transferables(result));
    } catch (failure) {
        self.postMessage({
            id,
            error: {
                kind: failure.error ?? 'other',
                detail: failure.detail ?? `${failure}`,
            },
        });
    }
};

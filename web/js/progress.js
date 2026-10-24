// Turn the engine's progress messages into a percentage, a label and the
// count of recognised pages

import { t } from './i18n.js';

// Engine stage -> [the key of what we tell the user, start %, end %] of a
// file
const STAGES = {
    scan: ['stage.scan', 0, 5],
    ocr: ['stage.ocr', 5, 85],
    save: ['stage.save', 85, 90],
    pdfa: ['stage.save', 90, 100],
};
const PAGE_STAGES = new Set(['ocr']);

export class FileProgress {
    constructor() {
        this.percent = 0;
        this.stage = null; // null until the engine's first message
        this.pages = 0; // 0 until the engine says how many there are
        this.pagesDone = 0;
        this.page = 0;
    }

    // Built when shown, so it follows the interface language
    get label() {
        if (!this.stage) return '';
        const label = t(STAGES[this.stage]?.[0] ?? 'stage.other');
        if (!this.page) return label;
        return t('stage.page',
            { stage: label, page: this.page, total: this.pages });
    }

    // Record one progress message; return the label to show
    update(stage, done, total) {
        const [, start, end] = STAGES[stage] ?? [
            '', this.percent, this.percent,
        ];
        const fraction = total ? Math.min(done / total, 1) : 0;

        // A message from a parallel page must not move the bar back
        this.percent = Math.max(this.percent, start + (end - start) * fraction);

        this.stage = stage;
        this.page = 0;
        if (PAGE_STAGES.has(stage) && total) {
            this.pages = total;
            this.pagesDone = Math.max(this.pagesDone, Math.min(done, total));
            this.page = Math.min(done + 1, total);
        }
        return this.label;
    }
}

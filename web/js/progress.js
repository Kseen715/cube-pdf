// Turn the engine's progress messages into a percentage, a label and the
// count of recognised pages

// Engine stage -> [what we tell the user, start %, end %] of a file
const STAGES = {
    scan: ['Изучаю файл', 0, 5],
    ocr: ['Распознаю текст', 5, 85],
    save: ['Сохраняю документ', 85, 90],
    pdfa: ['Сохраняю документ', 90, 100],
};
const PAGE_STAGES = new Set(['ocr']);
const UNKNOWN_STAGE_LABEL = 'Обрабатываю';

export class FileProgress {
    constructor() {
        this.percent = 0;
        this.label = '';
        this.pages = 0; // 0 until the engine says how many there are
        this.pagesDone = 0;
    }

    // Record one progress message; return the label to show
    update(stage, done, total) {
        const [label, start, end] = STAGES[stage] ?? [
            UNKNOWN_STAGE_LABEL, this.percent, this.percent,
        ];
        const fraction = total ? Math.min(done / total, 1) : 0;

        // A message from a parallel page must not move the bar back
        this.percent = Math.max(this.percent, start + (end - start) * fraction);

        this.label = label;
        if (PAGE_STAGES.has(stage) && total) {
            this.pages = total;
            this.pagesDone = Math.max(this.pagesDone, Math.min(done, total));
            const page = Math.min(done + 1, total);
            this.label = `${label}: страница ${page} из ${total}`;
        }
        return this.label;
    }
}

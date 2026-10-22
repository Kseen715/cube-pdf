// Facts about the program that more than one place needs.
// tools/collect_licenses.py reads SOURCE_URL from here too.

export const APP_NAME = 'CUBE-PDF';
export const SOURCE_URL = 'https://github.com/Kseen715/cube-pdf';
export const OUTPUT_SUFFIX = '_ocr';

// Tesseract code -> label shown in the UI, in display order
export const LANGUAGES = {
    rus: 'Русский',
    eng: 'Английский',
    deu: 'Немецкий',
};
export const DEFAULT_LANGUAGES = ['rus', 'eng'];

export const INPUT_EXTENSIONS = [
    '.pdf', '.jpg', '.jpeg', '.png', '.tif', '.tiff',
];

export function outputName(name) {
    const dot = name.lastIndexOf('.');
    const stem = dot > 0 ? name.slice(0, dot) : name;
    return `${stem}${OUTPUT_SUFFIX}.pdf`;
}

export function hasInputExtension(name) {
    const lower = name.toLowerCase();
    return INPUT_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

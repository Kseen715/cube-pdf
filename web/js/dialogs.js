// Message boxes and the About dialog, built on one <dialog> element

import { APP_NAME, SOURCE_URL } from './config.js';

// The AGPL asks every interactive program to show these notices
const ABOUT = `
<p><b>${APP_NAME}</b><br>Copyright © 2026 Denis Korenev</p>
<p>Это свободная программа: её можно распространять и изменять на условиях
GNU Affero General Public License версии 3 или (по вашему выбору) любой более
поздней версии.</p>
<p>Программа распространяется <b>без каких-либо гарантий</b>, в том числе без
гарантий товарной пригодности и пригодности для определённой цели.</p>
<p>Исходный код: <a href="${SOURCE_URL}" target="_blank"
rel="noopener">${SOURCE_URL}</a></p>
<p>Внутри: Tesseract, Leptonica, MuPDF, Ghostscript, zlib и другие свободные
компоненты. Их лицензии и где взять их исходный код — по кнопке «Сторонние
компоненты».</p>`;
const LEGAL_FILES = [
    ['Лицензия программы', 'LICENSE.txt'],
    ['Сторонние компоненты', 'THIRD-PARTY-NOTICES.txt'],
];
const CLOSE = 'Закрыть';

const dialog = document.getElementById('dialog');

// Show a dialog; resolves with the label of the button that closed it
function show({ title = APP_NAME, html = '', text = '', pre = '',
    details = '', buttons = [CLOSE] }) {
    dialog.replaceChildren();
    dialog.classList.toggle('wide', Boolean(pre));

    const heading = document.createElement('h3');
    heading.textContent = title;
    const body = document.createElement('div');
    body.className = 'dialog-body';
    if (html) body.innerHTML = html;
    else body.textContent = text;
    if (pre) body.append(preBlock(pre));
    dialog.append(heading, body);
    if (details) dialog.append(detailsBlock(details));

    const row = document.createElement('div');
    row.className = 'dialog-buttons';
    dialog.append(row);
    return new Promise((resolve) => {
        for (const label of buttons) {
            const button = document.createElement('button');
            button.textContent = label;
            button.addEventListener('click', () => {
                dialog.close();
                resolve(label);
            });
            row.append(button);
        }
        dialog.addEventListener('cancel', () => resolve(CLOSE), { once: true });
        dialog.showModal();
        row.lastElementChild.focus();
    });
}

function preBlock(text) {
    const pre = document.createElement('pre');
    pre.textContent = text;
    return pre;
}

function detailsBlock(text) {
    const block = document.createElement('details');
    const summary = document.createElement('summary');
    summary.textContent = 'Подробности';
    block.append(summary, preBlock(text));
    return block;
}

// done, failed: lists of tasks; actions: what the engine can do with files
export async function showDone(done, failed, actions) {
    let text = done.length === 1
        ? `Готово! Новый файл:\n\n${done[0].output}\n\n${actions.whereSingle}`
        : `Готово! Распознано файлов: ${done.length}.\n${actions.whereMany}`;
    if (failed.length) {
        text += `\n\nНе получилось: ${failed.length}. Дважды щёлкните по ` +
            'красному файлу в списке, чтобы узнать причину.';
    }

    const buttons = [];
    if (done.length === 1) buttons.push(actions.openLabel);
    if (actions.reveal) buttons.push('Показать в папке');
    buttons.push(CLOSE);

    const clicked = await show({ text, buttons });
    if (clicked === actions.openLabel) actions.open(done[0]);
    else if (clicked === 'Показать в папке') actions.reveal(done[0]);
}

export function showError(task) {
    return show({
        text: `Не получилось распознать файл\n«${task.source.name}».\n\n` +
            task.error,
        details: task.details.trim(),
    });
}

export function showAllFailed() {
    return show({
        text: 'Ни один файл не получилось распознать.\nДважды щёлкните по ' +
            'файлу в списке, чтобы узнать причину.',
    });
}

export function showMessage(text, buttons) {
    return show({ text, buttons });
}

export async function showAbout() {
    const labels = LEGAL_FILES.map(([label]) => label);
    const clicked = await show({
        title: `О программе — ${APP_NAME}`,
        html: ABOUT,
        buttons: [...labels, CLOSE],
    });
    const file = LEGAL_FILES.find(([label]) => label === clicked);
    if (file) await showLegalFile(file[1]);
}

async function showLegalFile(name) {
    let text = `Файл не найден: ${name}`;
    try {
        const response = await fetch(name);
        if (response.ok) text = await response.text();
    } catch {
        // the message above says it all
    }
    await show({ title: name, pre: text });
}

// Message boxes and the About dialog, built on one <dialog> element

import { APP_NAME, SOURCE_URL } from './config.js';
import { t } from './i18n.js';

// The AGPL asks every interactive program to show these notices; the
// about.* texts of locales/ hold the rest of them
const COPYRIGHT = 'Copyright © 2026 Denis Korenev';
// [the key of the button's label, the file it shows]
const LEGAL_FILES = [
    ['about.licenseFile', 'LICENSE.txt'],
    ['about.noticesFile', 'THIRD-PARTY-NOTICES.txt'],
];

const dialog = document.getElementById('dialog');

function aboutHtml() {
    const link = `<a href="${SOURCE_URL}" target="_blank"
rel="noopener">${SOURCE_URL}</a>`;
    return `<p><b>${APP_NAME}</b><br>${COPYRIGHT}</p>
<p>${t('about.license')}</p>
<p>${t('about.warranty')}</p>
<p>${t('about.source')} ${link}</p>
<p>${t('about.inside', { notices: t('about.noticesFile') })}</p>`;
}

// Show a dialog; resolves with the label of the button that closed it
function show({ title = APP_NAME, html = '', text = '', pre = '',
    details = '', buttons = [t('dialog.close')] }) {
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
        dialog.addEventListener('cancel', () => resolve(t('dialog.close')),
            { once: true });
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
    summary.textContent = t('dialog.details');
    block.append(summary, preBlock(text));
    return block;
}

// done, failed: lists of tasks; actions: what the engine can do with files
export async function showDone(done, failed, actions) {
    let text = done.length === 1
        ? t('done.one',
            { output: done[0].output, where: t(actions.whereSingle) })
        : t('done.many',
            { count: done.length, where: t(actions.whereMany) });
    if (failed.length) {
        const hint = t('done.failedHint');
        text += '\n\n' + t('done.someFailed', { count: failed.length, hint });
    }

    const open = t('dialog.openFile');
    const reveal = t('dialog.reveal');
    const buttons = [];
    if (done.length === 1) buttons.push(open);
    if (actions.reveal) buttons.push(reveal);
    buttons.push(t('dialog.close'));

    const clicked = await show({ text, buttons });
    if (clicked === open) actions.open(done[0]);
    else if (clicked === reveal) actions.reveal(done[0]);
}

export function showError(task) {
    return show({
        text: t('done.error', { name: task.source.name, error: task.error }),
        details: task.details.trim(),
    });
}

export function showAllFailed() {
    return show({
        text: t('done.allFailed', { hint: t('done.failedHint') }),
    });
}

// update: see findUpdate in update.js. Resolves with whether to go on.
export async function confirmUpdate({ from, to, file }) {
    const question = t(file ? 'update.install' : 'update.openPage');
    const yes = t('dialog.yes');
    const clicked = await show({
        title: t('update.title'),
        text: t('update.question', { from, to, question }),
        buttons: [yes, t('dialog.no')],
    });
    return clicked === yes;
}

export function showUpdateFailed(details) {
    return show({
        title: t('update.title'),
        text: t('update.failed'),
        details,
    });
}

export function showMessage(text, buttons) {
    return show({ text, buttons });
}

export async function showAbout() {
    const labels = LEGAL_FILES.map(([key]) => t(key));
    const clicked = await show({
        title: t('about.title', { app: APP_NAME }),
        html: aboutHtml(),
        buttons: [...labels, t('dialog.close')],
    });
    const file = LEGAL_FILES.find(([key]) => t(key) === clicked);
    if (file) await showLegalFile(file[1]);
}

async function showLegalFile(name) {
    let text = t('about.missing', { name });
    try {
        const response = await fetch(name);
        if (response.ok) text = await response.text();
    } catch {
        // the message above says it all
    }
    await show({ title: name, pre: text });
}

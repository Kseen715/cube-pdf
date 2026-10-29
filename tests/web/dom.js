// A stand-in for the part of the DOM that web/js/tasks.js and i18n.js use,
// so that their logic runs under node:test without a browser

const DATA_SELECTOR = /^\[data-([\w-]+)\]$/;

class ClassList {
    constructor(element) {
        this.element = element;
    }

    names() {
        return this.element.className.split(' ').filter(Boolean);
    }

    contains(name) {
        return this.names().includes(name);
    }

    toggle(name, force = !this.contains(name)) {
        const names = this.names().filter((other) => other !== name);
        if (force) names.push(name);
        this.element.className = names.join(' ');
        return force;
    }
}

export class FakeElement {
    constructor(tag) {
        this.tagName = tag.toUpperCase();
        this.className = '';
        this.classList = new ClassList(this);
        this.title = '';
        this.dataset = {};
        this.attributes = {};
        this.listeners = {};
        this.parent = null;
        this.children = [];
        this.text = '';
    }

    get textContent() {
        return this.text +
            this.children.map((child) => child.textContent).join('');
    }

    set textContent(text) {
        this.replaceChildren();
        this.text = `${text}`;
    }

    append(...nodes) {
        for (const node of nodes) {
            node.remove();
            node.parent = this;
            this.children.push(node);
        }
    }

    replaceChildren(...nodes) {
        for (const child of [...this.children]) child.remove();
        this.text = '';
        this.append(...nodes);
    }

    remove() {
        if (!this.parent) return;
        const siblings = this.parent.children;
        siblings.splice(siblings.indexOf(this), 1);
        this.parent = null;
    }

    closest(tag) {
        let node = this;
        while (node && node.tagName !== tag.toUpperCase()) node = node.parent;
        return node;
    }

    setAttribute(name, value) {
        this.attributes[name] = `${value}`;
    }

    getAttribute(name) {
        return this.attributes[name] ?? null;
    }

    addEventListener(type, listener) {
        (this.listeners[type] ??= []).push(listener);
    }

    // The event reaches the element, then each of its parents
    dispatch(type, init = {}) {
        const event = { type, target: this, ...init };
        for (let node = this; node; node = node.parent)
            for (const listener of node.listeners[type] ?? []) listener(event);
    }

    // Only [data-name] selectors, the ones i18n.js asks for
    querySelectorAll(selector) {
        const [, name] = DATA_SELECTOR.exec(selector);
        const key = name.replace(/-(\w)/g, (_, letter) => letter.toUpperCase());
        return this.descendants().filter((node) => key in node.dataset);
    }

    descendants() {
        return this.children.flatMap((child) =>
            [child, ...child.descendants()]);
    }
}

// Makes globalThis.document a page with an empty body
export function installDocument() {
    const html = new FakeElement('html');
    const body = new FakeElement('body');
    html.append(body);
    globalThis.document = {
        documentElement: html,
        body,
        createElement: (tag) => new FakeElement(tag),
        querySelectorAll: (selector) => html.querySelectorAll(selector),
    };
    return globalThis.document;
}

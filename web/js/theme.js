// The colour theme: one of the six of the Kerasi design system (kerasi.css),
// remembered in this browser. Until one is chosen, Sakura follows the
// system's light or dark. A plain script in <head>, not a module, so the
// page is painted in the right theme from the start. The CSS reads
// <html data-theme>.

(() => {
    const KEY = 'cube-pdf-theme';
    // the options of <select id="theme"> in index.html
    const THEMES = [
        'sakura', 'sakura-dark', 'wine', 'wine-dark', 'rust', 'rust-dark',
    ];
    const systemDark = matchMedia('(prefers-color-scheme: dark)');
    let chosen = null;

    try {
        const saved = localStorage.getItem(KEY);
        if (THEMES.includes(saved)) chosen = saved;
    } catch {
        // without storage the theme follows the system
    }

    function theme() {
        return chosen ?? (systemDark.matches ? 'sakura-dark' : 'sakura');
    }

    // The picker shows the name of the theme; i18n.js renames it with the
    // options when the language changes
    function apply() {
        document.documentElement.dataset.theme = theme();
        const select = document.getElementById('theme');
        if (!select) return;

        select.value = theme();
        const name = document.getElementById('theme-name');
        name.dataset.i18n = `theme.${theme()}`;
        name.textContent = select.selectedOptions[0].textContent;
    }

    function choose(next) {
        chosen = next;
        try {
            localStorage.setItem(KEY, chosen);
        } catch {
            // the choice still holds until the page is closed
        }
        apply();
    }

    apply();
    systemDark.addEventListener('change', apply);
    document.addEventListener('DOMContentLoaded', () => {
        const select = document.getElementById('theme');
        select.addEventListener('change', () => choose(select.value));
        apply();
    });
})();

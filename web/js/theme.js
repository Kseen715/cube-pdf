// The colour theme: light, dark or the system's, remembered in this browser.
// A plain script in <head>, not a module, so the page is painted in the
// right theme from the start. app.css reads <html data-theme>.

(() => {
    const KEY = 'cube-pdf-theme';
    const CHOICES = ['light', 'dark', 'auto'];
    const systemDark = matchMedia('(prefers-color-scheme: dark)');
    let choice = 'auto';

    try {
        const saved = localStorage.getItem(KEY);
        if (CHOICES.includes(saved)) choice = saved;
    } catch {
        // without storage the theme follows the system
    }

    function apply() {
        const dark = choice === 'dark'
            || (choice === 'auto' && systemDark.matches);
        document.documentElement.dataset.theme = dark ? 'dark' : 'light';
        for (const button of document.querySelectorAll('[data-theme-choice]'))
            button.setAttribute('aria-pressed',
                String(button.dataset.themeChoice === choice));
    }

    function choose(next) {
        choice = next;
        try {
            localStorage.setItem(KEY, choice);
        } catch {
            // the choice still holds until the page is closed
        }
        apply();
    }

    apply();
    systemDark.addEventListener('change', apply);
    document.addEventListener('DOMContentLoaded', () => {
        for (const button of document.querySelectorAll('[data-theme-choice]'))
            button.addEventListener('click',
                () => choose(button.dataset.themeChoice));
        apply();
    });
})();

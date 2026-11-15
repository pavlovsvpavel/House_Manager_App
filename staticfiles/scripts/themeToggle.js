/**
 * Theme handling: applies the theme before first paint to avoid flashes.
 * Priority: explicit user choice (localStorage) > system preference.
 */
(function () {
    'use strict';

    var STORAGE_KEY = 'hm-theme';

    function applyTheme(theme) {
        document.documentElement.dataset.theme = theme;
    }

    function systemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    var stored = null;
    try {
        stored = localStorage.getItem(STORAGE_KEY);
    } catch (e) {
        // localStorage unavailable (private mode) — fall back to system.
    }
    applyTheme(stored || systemTheme());

    document.addEventListener('DOMContentLoaded', function () {
        var button = document.getElementById('theme-toggle');
        if (!button) return;

        function refreshLabel() {
            var theme = document.documentElement.dataset.theme;
            // Icon shows what you switch TO.
            button.textContent = theme === 'dark' ? '\u2600\uFE0F' : '\uD83C\uDF19';
            button.setAttribute('aria-label',
                theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
        }

        refreshLabel();

        button.addEventListener('click', function () {
            var next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
            applyTheme(next);
            try {
                localStorage.setItem(STORAGE_KEY, next);
            } catch (e) {
                // Ignore persistence errors.
            }
            refreshLabel();
        });
    });
})();

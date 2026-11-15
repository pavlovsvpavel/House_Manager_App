document.addEventListener('DOMContentLoaded', function() {
    document.body.addEventListener('click', function(event) {
        // Only plain left clicks navigate.
        if (event.defaultPrevented || event.button !== 0) return;
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

        // Never hijack real interactive elements: they have native behaviour
        // (the bill rows are now actual links; form controls submit/filter).
        if (event.target.closest('a, button, input, select, textarea, label, dialog')) return;

        const target = event.target.closest('.js-redirect');

        if (!target) return;

        // The full URL is rendered server-side into data-url — no client-side
        // placeholder substitution needed.
        const url = target.dataset.url;

        if (url) {
            window.location.href = url;
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    document.body.addEventListener('click', function(event) {
        // Only plain left clicks navigate.
        if (event.defaultPrevented || event.button !== 0) return;
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

        const target = event.target.closest('.js-redirect');

        if (!target) return;

        // Let interactive elements nested inside a clickable card handle
        // their own clicks. The redirect element itself may also be a link
        // or button — that case must still navigate.
        const nested = event.target.closest('a, button, input, select, textarea, label');
        if (nested && nested !== target && target.contains(nested)) return;

        // The full URL is rendered server-side into data-url — no client-side
        // placeholder substitution needed.
        const url = target.dataset.url;

        if (url) {
            window.location.href = url;
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    document.body.addEventListener('click', function(event) {
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

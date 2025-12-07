document.addEventListener('DOMContentLoaded', function() {
        document.body.addEventListener('click', function(event) {
            const target = event.target.closest('.js-redirect');

            if (!target) return;

            const id = target.dataset.id;
            const urlTemplate = target.dataset.url;

            if (id && urlTemplate) {
                window.location.href = urlTemplate.replace('0', id);
            }
        });
    });

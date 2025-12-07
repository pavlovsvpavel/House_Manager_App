document.addEventListener('DOMContentLoaded', function () {
    const cancelBtn = document.getElementById('cancel-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function () {
            window.history.back();
        });
    }
});
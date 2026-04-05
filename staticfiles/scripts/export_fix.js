window.addEventListener('load', function() {
    const allCheckboxes = document.querySelectorAll('input[type="checkbox"]');

    if (allCheckboxes.length > 0) {
        const selectAllBox = allCheckboxes[0];

        // Strip away the library's forbidden inline event handler
        selectAllBox.removeAttribute('onclick');
        selectAllBox.removeAttribute('onchange');

        // Attach our secure event listener
        selectAllBox.addEventListener('change', function(e) {
            const isChecked = e.target.checked;

            allCheckboxes.forEach(function(box) {
                if (box !== selectAllBox) {
                    box.checked = isChecked;
                }
            });
        });
    }
});
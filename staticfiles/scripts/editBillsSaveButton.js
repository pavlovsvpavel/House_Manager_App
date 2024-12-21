document.addEventListener("DOMContentLoaded", function () {
    const checkbox = document.querySelector('input[name="is_paid"]');
    const saveButton = document.getElementById('save-btn');

    // Function to toggle the button styling and enable/disable it based on checkbox state
    function toggleSaveButton() {
        if (checkbox.checked) {
            saveButton.disabled = false;  // Enable button
            saveButton.classList.remove('disabled'); // Remove the disabled styles
        } else {
            saveButton.disabled = true;  // Disable button
            saveButton.classList.add('disabled');  // Apply the disabled styles
        }
    }

    // Listen for change events on the checkbox
    checkbox.addEventListener('change', toggleSaveButton);

    // Initial check in case the checkbox is already checked
    toggleSaveButton();
});

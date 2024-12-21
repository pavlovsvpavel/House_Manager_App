$(document).ready(function () {
    const $signatureElement = $("#signature");
    const saveButton = document.getElementById('save-btn');

    // Initialize the signature widget
    $signatureElement.jSignature({
        width: "100%",
        height: 250,
    });

    // Store the empty signature value for comparison
    const emptySignature = $signatureElement.jSignature('getData', 'svgbase64')[1];

    // Function to check if the signature is empty
    function isSignatureEmpty() {
        const signatureData = $signatureElement.jSignature('getData', 'svgbase64')[1];
        return signatureData === emptySignature;
    }

    // Function to toggle the save button's state
    function toggleSaveButton() {
        if (isSignatureEmpty()) {
            saveButton.disabled = true;
            saveButton.classList.add('disabled');
        } else {
            saveButton.disabled = false;
            saveButton.classList.remove('disabled');
        }
    }

    // Function to toggle the visibility of the signature pad
    function toggleSignaturePad() {
        const isPaidChecked = $('#id_is_paid').is(':checked');

        if (isPaidChecked) {
            $signatureElement.removeClass('hidden');

            // Smooth scroll to the signature pad
            $('html, body').animate({
                scrollTop: $signatureElement.offset().top - 50,
            }, 600);

            toggleSaveButton();
        } else {
            $signatureElement.addClass('hidden');
        }
    }

    // Attach event listeners
    $('#id_is_paid').change(toggleSignaturePad); // Toggle signature pad on checkbox change

    // Listen for changes on the signature pad and toggle save button
    $signatureElement.on('change', toggleSaveButton);

    // Reset the signature and update save button when reset button is clicked
    $('#reset_signature').click(function () {
        $signatureElement.jSignature('reset');
        toggleSaveButton(); // Update save button state
    });

    // Capture the signature data on form submission
    $('form.is-paid-form').submit(function (event) {
        const signatureData = $signatureElement.jSignature('getData', 'svgbase64')[1];
        $('#signature_input').val(signatureData);
    });

    // Initial checks on page load
    toggleSignaturePad();
    toggleSaveButton();
});

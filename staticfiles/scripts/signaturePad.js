$(document).ready(function () {
    const $signatureElement = $("#signature");
    const saveButton = document.getElementById('save-btn');

     // Get the width of the #signature element
    const signatureWidth = $signatureElement.width();

    // Initialize the signature widget
    // $signatureElement.jSignature({
    //     width: signatureWidth,
    //     height: 250,
    // });

    // Initialize the signature widget
    $signatureElement.jSignature({
        width: signatureWidth,
        height: 250,
    }).bind('signatureChange', function() {
        //This event fires when jSignature is fully initialized and the canvas is ready
        signatureCanvas = $signatureElement.find('canvas')[0]; // Get the underlying canvas element after initialization
        attachTouchEventListeners(); //Attach the listeners once the canvas is ready
    });

    function attachTouchEventListeners() {
        signatureCanvas.addEventListener('touchstart', function(e) {
            const touch = e.touches[0];
            if (isTouchInsideCanvas(touch)) {
                // Allow jSignature to handle the touchstart event normally
            } else {
                e.preventDefault();
            }
        });

        signatureCanvas.addEventListener('touchmove', function(e) {
            const touch = e.touches[0];
            if (isTouchInsideCanvas(touch)) {
                // Allow jSignature to handle the touchmove event normally
            } else {
                e.preventDefault();
            }
        });

        signatureCanvas.addEventListener('touchend', function(e) {
            // No need to check bounds here; it's the end of the touch interaction.
        });
    }

    // Helper function to check if a touch is inside the canvas
    function isTouchInsideCanvas(touch) {
        const rect = signatureCanvas.getBoundingClientRect();
        return (touch.clientX >= rect.left &&
                touch.clientX <= rect.right &&
                touch.clientY >= rect.top &&
                touch.clientY <= rect.bottom);
    }

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

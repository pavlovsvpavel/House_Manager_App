$(document).ready(function () {
     // jSignature element
    const $signatureElement = $("#signature");

    // Initialize the signature widget
    $signatureElement.jSignature({
        width: "100%",
        height: 250,

    });

    function toggleSignaturePad() {
        if ($('#id_is_paid').is(':checked')) {
            $signatureElement.show();
            // Smooth scroll to the signature pad
            $('html, body').animate({
                scrollTop: $signatureElement.offset().top - 50
            }, 600);
        } else {
            $signatureElement.hide();
        }
    }

    // Check initial state on page load
    toggleSignaturePad();

    // Scroll and toggle signature pad visibility on checkbox change
    $('#id_is_paid').change(function () {
        toggleSignaturePad();
    });

    const emptySignature = $signatureElement.jSignature('getData', 'svgbase64')[1];
    // Capture the signature data on form submission
    $('form.is-paid-form').submit(function (event) {
        const signatureData = $signatureElement.jSignature('getData', 'svgbase64')[1];
        if (signatureData === emptySignature) {
            $('#signature_input').val('');  // Set to empty string if no signature
        } else {
            $('#signature_input').val(signatureData);  // Save the base64 data if there's a signature
        }
    });

    // Reset the signature when the reset button is clicked
    $('#reset_signature').click(function () {
        $signatureElement.jSignature('reset');
    });
});

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
            $signatureElement.removeClass('hidden');

            $('html, body').animate({
                scrollTop: $signatureElement.offset().top - 50
            }, 600);
        } else {
            $signatureElement.addClass('hidden');
        }
    }

    // Check initial state on page load
    toggleSignaturePad();

    // Scroll and toggle signature pad visibility on checkbox change
    $('#id_is_paid').change(toggleSignaturePad);

    const emptySignature = $signatureElement.jSignature('getData', 'svgbase64')[1];
    // Capture the signature data on form submission
    $('form.is-paid-form').submit(function (event) {
        const signatureData = $signatureElement.jSignature('getData', 'svgbase64')[1];
        if (signatureData === emptySignature) {
            $('#signature_input').val('');
        } else {
            $('#signature_input').val(signatureData);
        }
    });

    // Reset the signature when the reset button is clicked
    $('#reset_signature').click(function () {
        $signatureElement.jSignature('reset');
    });
});

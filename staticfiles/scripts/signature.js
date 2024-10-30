$(document).ready(function () {
    // Initialize the signature widget
    $('#signature').jSignature({
        width: "100%",
        height: 400,

    });

    function toggleSignaturePad() {
        if ($('#id_is_paid').is(':checked')) {
            $('#signature').show();
            // Smooth scroll to the signature pad
            $('html, body').animate({
                scrollTop: $('#signature').offset().top - 50
            }, 600);
        } else {
            $('#signature').hide();
        }
    }

    // Check initial state on page load
    toggleSignaturePad();

    // Scroll and toggle signature pad visibility on checkbox change
    $('#id_is_paid').change(function () {
        toggleSignaturePad();
    });

    const emptySignature = $('#signature').jSignature('getData', 'svgbase64')[1];
    // Capture the signature data on form submission
    $('form.is-paid-form').submit(function (event) {
        const data = $('#signature').jSignature('getData', 'svgbase64');
        if (data[1] === emptySignature) {
            $('#signature_input').val('');  // Set to empty string if no signature
        } else {
            $('#signature_input').val(data[1]);  // Save the base64 data if there's a signature
        }
    });

    // Reset the signature when the reset button is clicked
    $('#reset_signature').click(function () {
        $('#signature').jSignature('reset');
    });
});

$(document).ready(function (data) {
    const image = new Image();
    const signature = signatureDataFromDataBase;
    image.src = 'data:' + signature;
    $(image).appendTo('#displaySignature');
});
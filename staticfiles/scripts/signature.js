$(document).ready(function () {
    // Initialize the signature widget
    $('#signature').jSignature();

    if ($('#id_is_paid').is(':checked')) {
            $('#signature').show();  // Show signature pad if checked
        } else {
            $('#signature').hide();  // Hide signature pad if not checked
        }
    //
    $('#id_is_paid').change(function() {
            if ($(this).is(':checked')) {
                $('#signature').show();
            } else {
                $('#signature').hide();
            }
        });

    const emptySignature = $('#signature').jSignature('getData', 'svgbase64')[1];
    // Capture the signature data on form submission
    $('form.is-paid-form').submit(function (event) {
        const data = $('#signature').jSignature('getData', 'svgbase64');
        // $('#signature_input').val(data[1]);
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
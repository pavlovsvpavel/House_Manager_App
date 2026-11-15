/**
 * Signature pad for bill payment forms.
 *
 * Exposed as ``window.initBillSignaturePad(scope)`` so the payment modal can
 * initialise the pad after an HTMX swap. On a normal page load it runs once on
 * DOMContentLoaded, preserving the no-JS-first full page flow.
 */
(function () {
    'use strict';

    function initBillSignaturePad(scope) {
        scope = scope || document;

        const signatureElement = scope.querySelector('#signature');
        if (!signatureElement) return;
        if (signatureElement.dataset.signatureInitialized === 'true') return;

        // jQuery + jSignature are loaded as deferred static scripts. If they
        // are not present (e.g. house bill pages), leave the form as-is.
        if (!window.jQuery || !window.jQuery.fn.jSignature) return;

        const $ = window.jQuery;
        const $signatureElement = $(signatureElement);
        const form = signatureElement.closest('form');
        const formScope = form || document;
        const checkbox = formScope.querySelector('input[name="is_paid"]');
        const saveButton = formScope.querySelector('#save-btn');
        const resetButton = formScope.querySelector('#reset_signature');
        const signatureInput = formScope.querySelector('#signature_input');

        signatureElement.dataset.signatureInitialized = 'true';

        // Measure while the element is still visible: the modal calls this
        // after showModal(), before the pad is toggled hidden.
        const signatureWidth = $signatureElement.width() || 600;
        let signatureCanvas = null;

        $signatureElement.jSignature({
            width: signatureWidth,
            height: 250,
        }).bind('signatureChange', function () {
            signatureCanvas = $signatureElement.find('canvas')[0];
            attachTouchEventListeners();
        });

        function attachTouchEventListeners() {
            if (!signatureCanvas || signatureCanvas.dataset.touchBound === 'true') return;
            signatureCanvas.dataset.touchBound = 'true';

            signatureCanvas.addEventListener('touchstart', function (e) {
                const touch = e.touches[0];
                if (!touch || isTouchInsideCanvas(touch)) return;
                e.preventDefault();
            });

            signatureCanvas.addEventListener('touchmove', function (e) {
                const touch = e.touches[0];
                if (!touch || isTouchInsideCanvas(touch)) return;
                e.preventDefault();
            });
        }

        function isTouchInsideCanvas(touch) {
            const rect = signatureCanvas.getBoundingClientRect();
            return (touch.clientX >= rect.left &&
                touch.clientX <= rect.right &&
                touch.clientY >= rect.top &&
                touch.clientY <= rect.bottom);
        }

        // The empty signature value, used to keep Save disabled until the
        // tenant actually signs.
        const emptySignature = $signatureElement.jSignature('getData', 'svgbase64')[1];

        function signatureValue() {
            return $signatureElement.jSignature('getData', 'svgbase64')[1];
        }

        function isSignatureEmpty() {
            return signatureValue() === emptySignature;
        }

        function syncSignatureInput() {
            if (signatureInput) {
                signatureInput.value = signatureValue();
            }
        }

        function toggleSaveButton() {
            if (!saveButton) return;
            const empty = isSignatureEmpty();
            saveButton.disabled = empty;
            saveButton.classList.toggle('disabled', empty);
        }

        function toggleSignaturePad() {
            if (!checkbox) return;

            if (checkbox.checked) {
                $signatureElement.removeClass('hidden');

                // Inside a modal the dialog scrolls, not the page.
                if (!signatureElement.closest('dialog') && $signatureElement.offset()) {
                    $('html, body').animate({
                        scrollTop: $signatureElement.offset().top - 50,
                    }, 600);
                }

                toggleSaveButton();
            } else {
                $signatureElement.addClass('hidden');
            }
        }

        if (checkbox) {
            $(checkbox).on('change', toggleSignaturePad);
        }

        // Keep the hidden input in sync as the user draws: HTMX may read the
        // form values before a submit handler runs.
        $signatureElement.on('change', function () {
            syncSignatureInput();
            toggleSaveButton();
        });

        if (resetButton) {
            $(resetButton).on('click', function (event) {
                event.preventDefault();
                $signatureElement.jSignature('reset');
                syncSignatureInput();
                toggleSaveButton();
            });
        }

        if (form) {
            $(form).on('submit', syncSignatureInput);
        }

        // Initial state: the pad is hidden until "Pay the bill" is checked.
        toggleSignaturePad();
        toggleSaveButton();
    }

    window.initBillSignaturePad = initBillSignaturePad;

    document.addEventListener('DOMContentLoaded', function () {
        initBillSignaturePad(document);
    });
})();

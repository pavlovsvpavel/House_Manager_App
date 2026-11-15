/**
 * Inline bill payment flows (HTMX progressive enhancement).
 *
 * - Adds the CSRF token to every HTMX non-GET request.
 * - Opens the payment <dialog> when its fragment arrives from the server.
 * - Closes it on Cancel / × / backdrop / Escape, and after a successful
 *   payment (``billPaid`` trigger sent by the view).
 * - Keeps the Save button disabled until the bill is marked paid (and, for
 *   client bills, until a signature exists — see signaturePad.js).
 * - Shows the undo toast after a payment; "Undo" POSTs the bill's revert
 *   endpoint, which swaps the row back to unpaid.
 *
 * Every flow still works without JavaScript: rows are real links, the modal
 * form is a normal POST form, and filters are a normal GET form. The undo
 * toast is the one JS-only affordance (there is no undo UI without JS).
 */
(function () {
    'use strict';

    var UNDO_TOAST_TIMEOUT = 8000;
    var undoToastTimer = null;

    function csrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta && meta.content) return meta.content;

        const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
        return input ? input.value : '';
    }

    function modalContainer() {
        return document.getElementById('bill-modal-container');
    }

    function currentDialog() {
        return document.querySelector('dialog[data-bill-modal]');
    }

    function clearModal() {
        const container = modalContainer();
        if (container) container.innerHTML = '';
    }

    function closeModal() {
        const dialog = currentDialog();
        if (dialog && dialog.open) dialog.close();
        clearModal();
    }

    function openModal() {
        const dialog = currentDialog();
        if (!dialog) return;

        if (!dialog.open) {
            if (typeof dialog.showModal === 'function') {
                dialog.showModal();
            } else {
                dialog.setAttribute('open', '');
            }
        }

        if (typeof window.initBillSignaturePad === 'function') {
            window.initBillSignaturePad(dialog);
        }

        const firstField = dialog.querySelector('input[name="is_paid"]');
        if (firstField && !firstField.disabled) firstField.focus();
    }

    function syncSaveButton(form) {
        if (!form) return;
        // Signature-enabled forms are managed by signaturePad.js.
        if (form.querySelector('#signature')) return;

        const checkbox = form.querySelector('input[name="is_paid"]');
        const saveButton = form.querySelector('#save-btn');
        if (!checkbox || !saveButton) return;

        saveButton.disabled = !checkbox.checked;
        saveButton.classList.toggle('disabled', !checkbox.checked);
    }

    function initBillForm(scope) {
        const forms = (scope || document).querySelectorAll('form.is-paid-form');

        forms.forEach(function (form) {
            if (form.dataset.billFormInitialized === 'true') return;
            form.dataset.billFormInitialized = 'true';

            const checkbox = form.querySelector('input[name="is_paid"]');
            if (checkbox) {
                checkbox.addEventListener('change', function () {
                    syncSaveButton(form);
                });
            }

            syncSaveButton(form);
        });
    }

    /* Undo toast ---------------------------------------------------------- */

    function undoToast() {
        return document.getElementById('undo-toast');
    }

    function hideUndoToast() {
        const toast = undoToast();
        if (toast) toast.hidden = true;
        clearTimeout(undoToastTimer);
    }

    function showUndoToast(revertUrl, rowSelector) {
        const toast = undoToast();
        if (!toast) return;

        const undoButton = toast.querySelector('[data-undo-revert]');
        if (undoButton) {
            if (revertUrl && rowSelector) {
                undoButton.setAttribute('hx-post', revertUrl);
                undoButton.setAttribute('hx-target', rowSelector);
                undoButton.setAttribute('hx-swap', 'outerHTML settle:400ms');
                undoButton.hidden = false;
                if (window.htmx) window.htmx.process(undoButton);
            } else {
                undoButton.hidden = true;
            }
        }

        toast.hidden = false;
        clearTimeout(undoToastTimer);
        undoToastTimer = setTimeout(hideUndoToast, UNDO_TOAST_TIMEOUT);
    }

    /* Events ---------------------------------------------------------------- */

    document.body.addEventListener('htmx:configRequest', function (event) {
        if (!event.detail || event.detail.verb === 'get') return;

        const token = csrfToken();
        if (token) event.detail.headers['X-CSRFToken'] = token;
    });

    document.addEventListener('DOMContentLoaded', function () {
        initBillForm(document);
    });

    document.body.addEventListener('htmx:afterSwap', function (event) {
        const target = event.detail && event.detail.target;
        if (!target || target.id !== 'bill-modal-container') return;

        initBillForm(target);
        openModal();
    });

    document.body.addEventListener('click', function (event) {
        const toastClose = event.target.closest('[data-toast-close]');
        if (toastClose) {
            event.preventDefault();
            hideUndoToast();
            return;
        }

        const undoButton = event.target.closest('[data-undo-revert]');
        if (undoButton && !undoButton.hidden) {
            // The revert response swaps the row back; the toast is done.
            hideUndoToast();
            return;
        }

        const closer = event.target.closest('[data-bill-cancel], [data-close-modal]');
        if (closer) {
            event.preventDefault();

            if (closer.closest('dialog[data-bill-modal]')) {
                closeModal();
            } else {
                // Full edit page: Cancel means "go back".
                window.history.back();
            }
            return;
        }

        // Click on the dialog backdrop (the <dialog> element itself) closes.
        if (event.target.matches && event.target.matches('dialog[data-bill-modal]')) {
            closeModal();
        }
    });

    // Sent by the edit view after a successful HX POST row swap: close the
    // dialog and offer the undo toast. Read from htmx:afterRequest (which
    // exposes the requesting element and the raw response header) — the
    // HX-Trigger custom event itself is dispatched without the element.
    document.body.addEventListener('htmx:afterRequest', function (event) {
        const detail = event.detail;
        if (!detail || !detail.xhr) return;

        const trigger = detail.xhr.getResponseHeader('HX-Trigger');
        if (trigger === 'billPaid') {
            closeModal();

            const form = detail.elt;
            const rowSelector = form && form.getAttribute ? form.getAttribute('hx-target') : null;
            const row = rowSelector && document.querySelector(rowSelector);

            if (row && row.dataset.revertUrl) {
                showUndoToast(row.dataset.revertUrl, rowSelector);
            }
        } else if (trigger === 'billReverted') {
            hideUndoToast();
        }
    });
})();

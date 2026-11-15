# Phase 2 Changes — Redesign: HTMX Bill Lists, Filters, Inline Payment Modal

**Branch:** `dev` only
**Date:** 2026-11-15
**Scope:** Redesign Phase 2 from `REDESIGN_PROPOSAL.md` — HTMX-ify the four bill lists, the paid/month filters, and the bill payment flow (inline modal + signature pad).
**Related docs:** `REDESIGN_PROPOSAL.md`, `PHASE1_CHANGES.md` (Phase 2 builds on the URL hierarchy and design tokens).

---

## Summary of Changes

### 1. Progressive-enhancement contract (unchanged guarantees)

- Every flow still works **without JavaScript**: bill rows are real `<a href>` links to the full edit page, the payment form is a normal `method="post"` form, and filters are a normal GET form with an explicit *Apply* button.
- HTMX only removes full-page reloads. There is no JSON, no client-side routing, no build step; the server decides per request whether to render a full page or a fragment.
- Ownership model untouched: `HtmxFragmentMixin` only changes **which template** renders — all `dispatch()`-level ownership checks (`HouseOwnershipMixin` / `ClientOwnershipMixin`), the three-axis bill check in `get_object()`, and the pristine-`is_paid` idempotency guard run exactly as before, for HTMX and non-HTMX requests alike.

### 2. Views

| File | Change |
|------|--------|
| `house_manager/common/mixins.py` | **New**: `HtmxFragmentMixin` — returns `partial_template_name` instead of `template_name` when the request carries the `HX-Request: true` header (or `?partial=1`, which makes fragments exercisable without JS). `is_htmx_request()` is the single detection point |
| `house_manager/house_bills/views.py` | List views: `partial_template_name` → list fragment. Edit views: `partial_template_name` → modal fragment, `row_template_name` → row fragment; `form_valid()` saves the form and returns the **row fragment** with `HX-Trigger: billPaid` for HTMX POSTs; `form_invalid()` adds `HX-Retarget: #bill-modal-container` + `HX-Reswap: innerHTML` so validation/idempotency errors stay inside the open dialog instead of overwriting a bill row |
| `house_manager/client_bills/views.py` | Same treatment; the signature capture (`data:image/svg+xml;base64,…`) happens identically on both paths |

The money helpers (`subtract_amount_from_house_balance` / `add_amount_to_house_balance`) are called before `form.save()` in both paths, so replaying an HTMX POST cannot double-credit/debit the house balance (guarded by `_bill_paid_before_request`, verified by tests).

### 3. Templates — fragment library

```
templates/partials/
  payment_modal.html          generic <dialog data-bill-modal> wrapper (details + form slots)
  bill_form_buttons.html      Save (data-bill-save) / Cancel (data-bill-cancel) pair
  filter_buttons.html         HTMX-aware: hx-get → #bills-region, hx-push-url, Apply button;
                              non-HTMX consumers (house_clients_list) keep the old auto-submit
templates/house_bills/partials/
  monthly_bill_list.html      list fragment: #bills-region (filter + #bills-container)
  other_bill_list.html
  monthly_bill_row.html       single row: <a id="bill-row-<pk>"> (hx-get → modal)
  other_bill_row.html
  monthly_bill_details.html   detail card (shared by full page and modal)
  other_bill_details.html
  monthly_bill_form.html      is-paid form (hx-post → row swap)
  other_bill_form.html
  monthly_bill_modal.html     one-line include wiring details+form into the dialog
  other_bill_modal.html
templates/client_bills/partials/
  … same 10-file shape (rows include partials/details_client_bills.html)
```

- The four list templates now render exactly the same fragment the HTMX endpoint returns, so the full page and the swapped-in content can never drift apart.
- `#bill-modal-container` lives on the list pages (outside the swapped region) — the dialog is fetched once and re-rendered per bill.
- The inline `style="color: #d51616"` warning in the monthly edit template became `.bill-warning { color: var(--danger); }` — no raw colors in templates.
- The "Paid" label is rendered server-side; the inline `<script>` that rewrote the label text via JS is gone.

### 4. Scripts

| File | Change |
|------|--------|
| `staticfiles/scripts/htmx.min.js` | **New**: HTMX v2.0.4, vendored (CSP-safe, no CDN) |
| `staticfiles/scripts/billsPayments.js` | **New**: CSRF (`X-CSRFToken` from the `<meta name="csrf-token">` tag added to `base.html`), opens/closes the `<dialog>` on `htmx:afterSwap`, closes + clears on `billPaid` / Cancel / × / backdrop, and owns Save-button enablement for forms without a signature pad |
| `staticfiles/scripts/signaturePad.js` | Rewritten as an idempotent `window.initBillSignaturePad(scope)` (guarded by `data-signature-initialized`) so the same code initialises the pad on a full page load **and** after a modal swap; the hidden `signature` input is now kept in sync on every stroke, not only on submit (HTMX may read form values before submit handlers run) |
| `staticfiles/scripts/redirects.js` | No longer hijacks clicks on interactive elements (`a, button, input, select, textarea, label, dialog`) or modified/middle clicks — bill rows are real links now |
| `staticfiles/scripts/editBillsSaveButton.js`, `templates/partials/form_buttons_edit_bills.html` | **Deleted** — superseded by `billsPayments.js` + `bill_form_buttons.html` |

### 5. Styles

| File | Change |
|------|--------|
| `staticfiles/styles/modals.css` | **New**: `dialog.bill-modal` + `::backdrop`, panel/header/close/body, wrapped detail card inside the dialog, `a.client-card` link-chrome reset, `.bill-warning`, `.filter-apply` — all colors from the design tokens |
| `staticfiles/styles/styles.css` | `@import url('modals.css')` added |

### 6. Tests + translations

| File | Change |
|------|--------|
| `house_manager/house_bills/tests.py` | +6 HTMX tests: list partial (both bill types), filter partial with paid/unpaid query, modal GET fragment (`hx-post` target, no `<html>`), HTMX POST row swap with `HX-Trigger: billPaid` + balance debited once, HTMX replay stays idempotent and returns `HX-Retarget` |
| `house_manager/client_bills/tests.py` | +4 HTMX tests: list partials, modal GET with signature pad, HTMX POST with signature (signature persisted, balance credited once, replay idempotent) |
| `locale/bg/LC_MESSAGES/django.po` (+ `.mo`) | New strings via `makemessages` + `compilemessages`: "Apply" → Приложи, "Close" → Затвори |

---

## Implementation Notes

### 1. Why the response for a filter is the whole region (filter + list), not just the list

The filter partial's own state (selected month, disabled-class on the debt links) is rendered from the query string. If only the cards were swapped, the filter UI would go stale after the first HTMX request (the "Without debts" link would keep pointing at the old month). Swapping `#bills-region` (which contains the filter form) keeps both in sync; the filter template is therefore included **inside** the list fragment.

### 2. Why the row swap targets `#bill-row-<pk>` and errors retarget

A successful HTMX POST returns the single updated row and swaps it over the old one (`hx-target="#bill-row-<pk>"`, `hx-swap="outerHTML"`), then `HX-Trigger: billPaid` closes the dialog — no full list refresh, focus stays where the user was. A **failed** POST (validation error or an idempotency-guard replay) would otherwise swap the modal fragment *over the row*; `form_invalid()` therefore sets `HX-Retarget: #bill-modal-container` so the error renders inside the dialog the user is looking at.

### 3. CSRF for HTMX

`base.html` gained `<meta name="csrf-token" content="{{ csrf_token }}">`; `billsPayments.js` copies it into `X-CSRFToken` on `htmx:configRequest` for non-GET requests. Payment forms also embed `{% csrf_token %}` normally, so non-JS POSTs never depended on the header.

### 4. CSP compatibility

No inline handlers, no `eval`-driven attributes (`hx-on` unused), scripts are vendored/self-hosted and nonced. htmx's default swap never injects scripts here (the modal fragment is script-free; the signature pad is initialised by `billsPayments.js` from the `htmx:afterSwap` event).

---

## Verification

- Regression suite: **34 tests, all passing** (throwaway Postgres 17 container on `127.0.0.1:5555`; runner overrides `DATABASES` in memory — `envs/.env` untouched):
  ```
  Ran 34 tests in 3.088s — OK
  ```
- Visual verification via the in-app browser against a seeded dev server (`hm_dev` DB on the throwaway container, session injected, demo user), light + dark:
  - Client bills list: clicking an unpaid row fetches the modal fragment (`HX-Request` → 200, 3.6 KB) and opens the native `<dialog>`; the signature pad initialises inside it; drawing enables Save.
  - Paying the client bill: `POST …/edit/` carried `hx-target: bill-row-1` and `x-csrftoken`; response had `HX-Trigger: billPaid`; the dialog closed, the row swapped to the paid state in place, house balance went **1250.40 → 1470.40** (exactly one credit), signature stored as `data:image/svg+xml;base64,…`.
  - Paying a house monthly bill from its list: row swapped to paid, dialog closed, balance **1470.40 → 1301.40** (−169.00 = `amount_without_repairs`, i.e. total 194.00 minus 25.00 repairs — correct per the "payment is without 'Repairs fund'" rule).
  - Filters: month select and "With debts" trigger HTMX GETs on `#bills-region` with `hx-push-url` (URL reflects `?is_paid=False&month=09`); the full page still renders without JS (Apply button / normal GET).
  - Paid-bill modal shows the "Paid" label with a disabled checkbox and no Save button.
  - Zero console errors / CSP violations across all interactions.
- Dead code removed and confirmed unreferenced before deletion (`grep` across `templates/` and `staticfiles/`).

---

## Not In Scope

- **Redesign Phase 3:** undo-window toast after payment (deferred from the original Phase 2 plan), further componentization.
- **P1 security findings** (`SECURITY_FINDINGS.md`): HSTS/security headers (#8), debug toolbar removal (#9), `SOCIALACCOUNT_LOGIN_ON_GET`/GET logout (#10), email verification (#11), atomic balance updates with row locks (#18). *(Note: the `axes.W006` warning observed during verification — `AXES_LOCKOUT_PARAMETERS` without `ip_address` — belongs to this P1 list.)*

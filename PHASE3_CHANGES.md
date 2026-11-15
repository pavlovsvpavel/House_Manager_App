# Phase 3 Changes — Undo Toast After Payment, Real Links Everywhere

**Branch:** `dev` only (local; nothing is pushed or merged to `main`)
**Date:** 2026-11-15
**Scope:** The work deferred from Phase 2 plus the last JS-navigation holdouts:
1. **Undo-window toast** — "Bill paid. / Undo" for ~8 s after an inline payment, backed by guarded server-side revert endpoints.
2. **`js-redirect` → real links** — the dashboard house cards and the clients-list cards become actual `<a href>` elements; `redirects.js` is deleted.
**Related docs:** `REDESIGN_PROPOSAL.md` (§7 "Undo window", §9 principles), `PHASE2_CHANGES.md`.

---

## Summary of Changes

### 1. Revert (undo payment) endpoints

| File | Change |
|------|--------|
| `house_manager/house_bills/helpers/restore_balance_on_revert.py` | **New**: `restore_house_balance_on_revert()` — exact inverse of the payment debit (adds back `amount_without_repairs()` for monthly bills, `total_amount` for others), `F()`-expression atomic update |
| `house_manager/house_bills/views.py` | **New**: `HouseBaseBillRevertView` + `HouseMonthlyBillRevertView` / `HouseOtherBillRevertView` — owner-only (same URL-derived checks as the edit views), POST-only, idempotent (a revert of an already-unpaid bill only re-renders the row; the pristine `is_paid` is captured in `get_object()` before any mutation, same pattern as the payment guard) |
| `house_manager/client_bills/views.py` | **New**: `ClientBaseBillRevertView` + `CurrentClientMonthlyBillRevertView` / `CurrentClientOtherBillRevertView` — additionally verifies `client_pk` (three-axis check) and **clears the signature** (an undone payment did not happen); reuses `subtract_amount_from_house_balance`, which for client bills subtracts exactly the credited `total_amount` |
| `house_manager/house_bills/urls.py`, `client_bills/urls.py` | `monthly/<pk>/revert/`, `other/<pk>/revert/`, `bills/<pk>/revert/`, `other-bills/<pk>/revert/` — names `revert_house_bills`, `revert_other_house_bills`, `revert_client_bill`, `revert_client_other_bill` |

Non-HTMX POSTs to a revert endpoint simply redirect back to the bills list (no undo UI exists without JS; a crafted POST is still ownership-checked).

### 2. Undo toast

| File | Change |
|------|--------|
| `templates/partials/undo_toast.html` | **New**: server-rendered toast (`role="status"`, `aria-live="polite"`, starts `hidden`) so the strings are translatable; included in all 4 bill list templates |
| `staticfiles/scripts/billsPayments.js` | Toast show/hide (8 s auto-dismiss), Undo button wired dynamically (`hx-post` = the paid row's `data-revert-url`, `hx-target` = that row) and processed via `htmx.process` |
| `staticfiles/styles/modals.css` | Toast styling from design tokens; `z-index: 30` (above the cookies banner) |

**Trigger reliability note (found during browser verification):** the toast was first wired from the `htmx:afterSwap` event's `detail.target` — which is only dependable for `innerHTML` swaps (the modal), not for the row's `outerHTML` swap — and `HX-Trigger` custom events are *not* dispatched on the requesting element, so `event.target` inside a `billPaid` handler is not the form. The final implementation reads everything from **`htmx:afterRequest`**, which exposes `detail.elt` (the paying form), `detail.xhr`, and the raw `HX-Trigger` response header — deterministic across htmx's swap paths:

```js
document.body.addEventListener('htmx:afterRequest', function (event) {
    const trigger = event.detail.xhr.getResponseHeader('HX-Trigger');
    if (trigger === 'billPaid')   { closeModal(); showUndoToast(row.dataset.revertUrl, form.getAttribute('hx-target')); }
    if (trigger === 'billReverted') { hideUndoToast(); }
});
```

### 3. `js-redirect` → real links

| File | Change |
|------|--------|
| `templates/common/dashboard.html` | House card `<div class="house-card js-redirect" data-url=…>` → `<a class="house-card" href=…>` |
| `templates/houses/house_clients_list.html` | Client card div → `<a class="client-card" href=…>` |
| `staticfiles/styles/modals.css` | Anchor reset extended: `a.house-card` joins `a.client-card` (`text-decoration: none; color: inherit`) |
| `staticfiles/scripts/redirects.js`, `templates/base.html` | **Deleted** — after Phase 2's bill-row links and this change, no `js-redirect` usage remains |

### 4. Accessibility (first items from the proposal's a11y pass)

- The reset-signature icon-only button (`↻`) now has `aria-label` (`templates/partials/signature-pad.html`).
- Toast announces via `role="status"` + `aria-live="polite"`.

### 5. Tests + translations

| File | Change |
|------|--------|
| `house_manager/house_bills/tests.py` | +4: revert restores balance (monthly, incl. the `amount_without_repairs` rule), revert other-bill total, foreign user blocked (bill stays paid, balance unchanged), non-HTMX POST → 302 to list; replay idempotency asserted |
| `house_manager/client_bills/tests.py` | +3: revert restores balance **and clears the signature**, foreign `client_pk` blocked, foreign user blocked; replay idempotency asserted |
| `locale/bg/LC_MESSAGES/django.po` (+ `.mo`) | "Bill paid." → Сметката е платена., "Undo" → Отмени, "Dismiss" → Затвори, "Reset signature" → Изчисти подписа. Also fixed two wrong `#, fuzzy` auto-matches msgmerge had produced |

---

## Implementation Notes

### 1. Undo does not weaken the Phase 0 payment guarantees

The one-way payment guard (`_bill_paid_before_request`) is untouched. Undo is a **separate, explicit, owner-only POST** whose money effect is the exact inverse of the payment and which is itself idempotent (guarded by the same pristine-capture pattern): replaying a revert cannot double-subtract, and a revert cannot fire for an already-unpaid bill. Verified by the replay assertions in both test files.

### 2. Why the revert lives on its own endpoints instead of the edit form

The edit form only models "unpaid → paid" (its `form_valid` rejects anything else). Modeling "paid → unpaid" inside it would have meant loosening the guard that protects the balance from replays. A dedicated revert endpoint keeps the payment transition one-way and puts the undo transition under its own, simpler guard.

### 3. Progressive-enhancement audit after this phase

- No JS: rows/cards navigate as real links; payment form posts; filters submit via Apply. No undo (JS-only affordance, by design).
- JS on: HTMX modal + row swaps + undo toast.

---

## Verification

- Regression suite: **44 tests, all passing** (throwaway Postgres 17 container; `envs/.env` untouched):
  ```
  Ran 44 tests in 3.396s — OK
  ```
- Browser-verified (seeded dev server, hm_dev DB on the throwaway container, dark mode):
  - Pay a client bill via the modal → dialog closes, row swaps to paid in place, **toast appears** ("Bill paid." / Undo), auto-dismisses after ~8 s (observed both the appearance and the timeout).
  - **Undo**: clicking the toast's Undo POSTs the revert endpoint; the row swaps back to unpaid in place, the toast dismisses, and the ledger is restored **exactly** (1470.40 − 220.00 → 1250.40, the seeded balance) with the signature cleared in the DB.
  - Dashboard house card and clients-list card navigate as real anchors (also work with JS disabled — plain `href`s).
  - No console errors / CSP violations.
- Verification-harness notes: two dead ends were hit and documented here because they shaped the implementation — `htmx:afterSwap`'s `detail.target` is unreliable for `outerHTML` swaps, and `HX-Trigger` events don't carry the requesting element (see §2).

---

## Not In Scope

- **Redesign Phase 3 (per the proposal's table):** reports (PDF + CSV), bill creation wizard, profile/avatar, and the remaining accessibility pass (focus rings, table → card fallback).
- **P1 security findings** (`SECURITY_FINDINGS.md`): HSTS/security headers (#8), debug toolbar removal (#9), `SOCIALACCOUNT_LOGIN_ON_GET`/GET logout (#10), email verification (#11), atomic balance updates with row locks (#18), `axes.W006` (`AXES_LOCKOUT_PARAMETERS` without `ip_address`).

# Phase 0 Changes — Security Remediation

**Branch:** `dev` only
**Date:** 2026-11-15
**Scope:** P0 findings from `SECURITY_FINDINGS.md` — the IDOR/access-control chain (#1–#6) and payment replay (#7).
**Related docs:** `SECURITY_FINDINGS.md`, `REDESIGN_PROPOSAL.md` (Phase 1 builds on this work).

---

## Summary of Changes

| # | File | Change | Fixes finding |
|---|------|--------|---------------|
| 1 | `house_manager/houses/decorators.py` | Ownership check moved **before** any `request`/session mutation; a denied request no longer primes `session["selected_house"]` with a foreign house | #5 |
| 2 | `house_manager/clients/decorators.py` | Same fix for `session["selected_client"]` | #5 |
| 3 | `house_manager/houses/mixins.py` (`GetHouseAndUserMixin`) | House fetched with `get_object_or_404(House, pk=house_id, user=request.user)`; `PermissionDenied` if no house is selected in the session | #6 |
| 4 | `house_manager/house_bills/views.py` (`HouseBaseBillCreateView.current_house`) | Same ownership filter for the session-selected house used by all bill create views | #6 |
| 5 | `house_manager/house_bills/views.py` (`HouseBaseBillEditView`) | Ownership check added in `get_object()` (runs on GET **and** POST); pristine `is_paid` captured in `get_object()`; idempotency guard added in `form_valid()` | #3, #7 |
| 6 | `house_manager/client_bills/views.py` (`CurrentClientBaseBillEditView`) | Same ownership + idempotency fix for client bill edit views | #2, #7 |
| 7 | `house_manager/client_bills/views.py` (`ClientBaseBillsDetailView`) | Client fetched with `get_object_or_404(Client, pk=…, user=request.user)` — session equality alone is no longer trusted | #4 |
| 8 | `house_manager/client_bills/views.py` (`DownloadReceiptView`) | `get_queryset()` filters `ClientMonthlyBill` by `user=request.user`; foreign users get 404 on receipt download | #1 |
| 9 | `house_manager/houses/tests.py` | **New regression tests** (3): decorator does not prime session on denial; owner retains access; house edit denied for non-owner | #5 |
| 10 | `house_manager/house_bills/tests.py` | **New regression tests** (7): IDOR on monthly/other house bill edit (GET+POST), list view blocked with primed session, payment idempotency (mark paid once, replay is a no-op), bill creation blocked with foreign session house | #3, #6, #7 |
| 11 | `house_manager/client_bills/tests.py` | **New regression tests** (7): client bill list/edit IDOR, receipt download blocked for others / allowed for owner, payment idempotency with balance assertion | #1, #2, #4, #7 |

Note: the app's previous test files were empty stubs (`# Create your tests here.`); this phase introduces the project's first real test suite for the affected modules.

---

## Implementation Notes

### 1. Ownership before session mutation (decorators)

Both decorators previously wrote `request.session['selected_*']` **before** verifying `user_id`. The check now runs first, so a 403 leaves the session untouched. This closes the "prime the session with a foreign object, then pivot" attack that made findings #4 and #6 exploitable.

### 2. Session is no longer treated as proof of ownership

Every consumer of `session["selected_house"]` / `session["selected_client"]` now re-verifies that the object belongs to `request.user`. Defense in depth: even if a future view writes the session key incorrectly, ownership is still enforced at the DB query level.

### 3. Ownership check in `get_object()`, not `get_context_data()`

The old edit views verified house consistency only in `get_context_data()`, which the successful-POST path never calls. The check now lives in `get_object()` and runs on both GET and POST for every bill edit view (house monthly, house other, client monthly, client other).

### 4. Payment idempotency — the form-binding pitfall

Naively guarding with `if self.object.is_paid` **does not work**: binding the form to `request.POST` mutates `form.instance` (which is the *same Python object* as `self.object`), so by the time `form_valid()` runs, `is_paid` already reflects the submitted data rather than the DB state. The fix captures the pristine value in `get_object()` (`self._bill_paid_before_request`) — which always runs before form binding — and the guard in `form_valid()` uses that. Replay POSTs on an already-paid bill are now a no-op for the house balance (verified by tests).

### 5. Cleanup

`Http404` import removed from `client_bills/views.py` (its only usage was in a dead `except` branch around `get_object_or_404`, which never raises `ClientMonthlyBill.DoesNotExist`).

---

## Verification

- `python -m py_compile` on all five modified Python files — OK.
- **New regression suite: 15 tests, all passing.** Run against a throwaway Postgres 17 container (the local `envs/.env` points at an unreachable DB), via a runner script that overrides `DATABASES` in memory — `envs/.env` was **not** modified:

```
Ran 15 tests in 2.074s — OK
```

Coverage highlights:
- Foreign user gets 403 on GET/POST of another user's bill edit pages (all four bill edit views).
- Foreign user gets 404 on another user's receipt PDF and client bill list.
- Denied house-detail request leaves `session["selected_house"]` unset (regression for the session-priming bug).
- Bill creation with a foreign session-selected house → 404, no row created.
- Mark-as-paid credits/debits the house balance **exactly once**; replaying the POST leaves the balance unchanged.
- Owner flows (house detail access, receipt download, payment) still work — no legitimate functionality broken.

---

## Not In Scope (deferred to P1/P2 per `SECURITY_FINDINGS.md`)

- Missing security headers/HSTS (finding #8) — settings change.
- Debug toolbar removal from prod (finding #9).
- `SOCIALACCOUNT_LOGIN_ON_GET`, GET logout (finding #10).
- Email verification on registration (finding #11).
- Atomic balance updates with row locks (finding #18) — replay is now blocked, but true concurrency hardening is deferred.
- URL restructure (`/houses/<id>/...`) — planned as part of Redesign Phase 1.

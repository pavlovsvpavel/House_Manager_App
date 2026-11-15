# Phase 1 Changes — Redesign: URL Hierarchy, Design Tokens, Dark Mode, Dashboard KPIs

**Branch:** `dev` only
**Date:** 2026-11-15
**Scope:** Redesign Phase 1 from `REDESIGN_PROPOSAL.md` — URL restructure, ownership from URL, design tokens + dark mode, dashboard KPIs.
**Related docs:** `REDESIGN_PROPOSAL.md`, `PHASE0_CHANGES.md` (Phase 1 completes the URL restructure deferred from Phase 0).

---

## Summary of Changes

### 1. URL hierarchy — ownership derived from the URL

| File | Change |
|------|--------|
| `house_manager/urls.py` | App includes are now nested under `houses/<int:house_pk>/clients/`, `houses/<int:house_pk>/clients/<int:client_pk>/`, `houses/<int:house_pk>/bills/` |
| `house_manager/houses/urls.py` | `pk` → `house_pk` on all house routes |
| `house_manager/clients/urls.py` | Mounted under `houses/<int:house_pk>/clients/` |
| `house_manager/house_bills/urls.py` | Mounted under `houses/<int:house_pk>/bills/` |
| `house_manager/client_bills/urls.py` | Mounted under `houses/<int:house_pk>/clients/<int:client_pk>/` |

New URL shapes (URL **names** unchanged, except one fix below):

```
/houses/<house_pk>/                                   details_house
/houses/<house_pk>/edit/ | /delete/                   edit_house, delete_house
/houses/<house_pk>/clients/                           house_clients_list
/houses/<house_pk>/clients/create/                    create_client
/houses/<house_pk>/clients/details/<pk>/              details_client
/houses/<house_pk>/clients/edit/<pk>/ | /delete/<pk>/ edit_client, delete_client
/houses/<house_pk>/bills/monthly/...                  list|create|edit_house_bills
/houses/<house_pk>/bills/fixed/create/                create_fixed_bill
/houses/<house_pk>/bills/other/...                    list|create|edit_other_house_bills
/houses/<house_pk>/bills/reports/monthly/ | /other/   reports_bills, reports_other_bills
/houses/<house_pk>/clients/<client_pk>/bills/...      list|edit_client_bill, download_receipt
/houses/<house_pk>/clients/<client_pk>/other-bills/…  list|edit_client_other_bill
```

Name fix: `edit_other_client_bill` → `edit_client_other_bill` (the template-consistent name; the old URLConf had a mismatch between the URL name and every `{% url %}` reference).

### 2. Ownership mixins replace session decorators

| File | Change |
|------|--------|
| `house_manager/houses/mixins.py` | `HouseOwnershipMixin` (new): loads `selected_house` from `kwargs["house_pk"]` with `user=request.user`; foreign house → **404** (never 403 — does not confirm existence). `GetHouseAndUserMixin` rewritten: assigns the already-verified `selected_house` to `form.instance`; no session reads |
| `house_manager/clients/mixins.py` | **New**: `ClientOwnershipMixin` — loads `selected_client` from `kwargs["client_pk"]` (`user=request.user`) and verifies `client.house_id == kwargs["house_pk"]`; any mismatch → 404 |
| `house_manager/houses/decorators.py` | **Deleted** — session-based `selected_house` pattern removed |
| `house_manager/clients/decorators.py` | **Deleted** — session-based `selected_client` pattern removed |

All four `views.py` rewritten to use the mixins. Every `session["selected_house"]` / `session["selected_client"]` read is gone from production code. Bill edit views additionally verify `obj.house_id == kwargs["house_pk"]` (and `obj.client_id == kwargs["client_pk"]` for client bills) in `get_object()`, so a valid object reached through the wrong parent URL is also a 404.

`common/views.py` untouched by the URL work (dashboard is user-scoped, not house-scoped).

### 3. Design tokens + dark mode

| File | Change |
|------|--------|
| `staticfiles/styles/variables.css` | Existing token names kept (`--site-bgnd`, `--card-bgnd`, `--card-text-color`, `--form-*`, `--card-bgnd-paid/not-paid`, `--menu-bgnd`) so all stylesheets keep working unchanged; added new tokens: `--text-muted`, `--border-color`, `--shadow`, `--radius`, `--success/--danger`, `--alert-bgnd/--alert-text`. Full `[data-theme="dark"]` override block |
| `staticfiles/styles/dashboard.css` | **New**: theme-toggle button, dashboard header, house card title/meta, KPI grid (4-up, 2-up ≤640px), alert styling for unpaid KPI |
| `staticfiles/styles/styles.css` | `@import url('dashboard.css')` added |
| `staticfiles/scripts/themeToggle.js` | **New**: applies theme **before first paint** (script loaded without `defer` in `base.html`); priority = `localStorage["hm-theme"]` → `prefers-color-scheme`; toggle button `#theme-toggle` in the header flips and persists |
| `templates/base.html` | `themeToggle.js` wired in (blocking, so no theme flash); `redirects.js` unchanged position |
| `templates/common/header.html` | Theme toggle `<button id="theme-toggle">` added before the language form |

### 4. Dashboard KPIs

| File | Change |
|------|--------|
| `house_manager/common/views.py` | `DashboardView` annotates each house with `clients_count` and — in a **separate aggregate query** — `unpaid_bills_count` / `unpaid_bills_total` (see Implementation Notes) |
| `templates/common/dashboard.html` | Rewritten: house cards show Balance, Clients, Unpaid bills (alert-highlighted when > 0), Due EUR; "Add house" button; "No houses" empty state. Card click navigates via `data-url` (fully server-rendered URL) |
| `staticfiles/scripts/redirects.js` | Simplified: `data-url` is now a complete URL rendered by the template — the `data-id` + `replace('0', id)` placeholder hack is gone; removed `data-id` from all templates that used it |

### 5. Templates (URL kwargs only)

`details_house.html`, `house_clients_list.html`, `delete_house.html`, `details_client.html`, `delete_client.html`, `list_house_bills.html`, `list_other_house_bills.html`, `edit_house_bills.html`, `edit_other_house_bills.html`, `list_client_bills.html`, `list_other_client_bills.html`, `edit_client_bill.html`, `edit_client_other_bill.html`, `reports_back_button.html` — all `{% url %}` tags updated to the new kwargs (`house_pk` / `client_pk`); all `data-id`/`pk=0` placeholder patterns replaced with server-rendered `data-url`s.

### 6. Tests + translations

| File | Change |
|------|--------|
| `house_manager/houses/tests.py` | Rewritten for new URLs (4 tests) — foreign house 404 **and** session-priming regression kept, owner access, edit/clients-list blocked |
| `house_manager/house_bills/tests.py` | Rewritten (8 tests) — IDOR GET/POST on both bill types, list blocked, idempotency with balance assertion, create blocked in foreign house URL / allowed for owner |
| `house_manager/client_bills/tests.py` | Rewritten (6 tests) — list/edit IDOR, foreign `client_pk` mismatch 404, receipt download blocked/allowed, idempotency |
| `locale/bg/LC_MESSAGES/django.po` (+ `.mo`) | New strings translated: "Add house", "Building", "Balance, EUR", "Clients", "Unpaid bills", "Due, EUR", "Bill not found for current user." — via `makemessages` (with locations) + `compilemessages` |

---

## Implementation Notes

### 1. Why ownership now lives in `dispatch()` on the URL

The session-based "selected house/client" pattern was the root cause of the Phase 0 findings: mutable cross-request state that could be primed with a foreign object and pivoted from. Ownership is now re-derived from the URL on **every** request (mixins run in `dispatch()`, before GET/POST handling), and foreign objects return 404 — a 403 would confirm that the object exists under another user.

### 2. KPI aggregate fan-out bug (found during verification)

The first implementation annotated everything on one queryset:

```python
House.objects.annotate(
    clients_count=Count("clients", distinct=True),
    unpaid_bills_count=Count("client_house_monthly_bills", filter=..., distinct=True),
    unpaid_bills_total=Sum("client_house_monthly_bills__total_amount", filter=...),
)
```

The two reverse joins (`clients` + bills) fan out rows — the house row is duplicated once per (client × bill) combination. `Count(..., distinct=True)` survives this, but `Sum` does **not**: with 2 clients and 1 unpaid bill each, the sum was counted twice. Visually confirmed: Sofia showed **440.00 due instead of 220.00**.

Fix: unpaid totals are computed in a separate query (`ClientMonthlyBill.objects.filter(house__in=…, is_paid=False).values("house_id").annotate(...)`) and stitched back onto the houses in Python. Verified correct after the fix (Sofia 220.00, Plovdiv 160.00).

### 3. The form-binding pitfall (carried over from Phase 0)

The Phase 0 note still applies and the idempotency logic was preserved through the rewrite: the pristine `is_paid` is captured in `get_object()` (`self._bill_paid_before_request`) **before** form binding, because binding `request.POST` mutates `form.instance` — the same Python object as `self.object` — so by `form_valid()` time `is_paid` already reflects the submission, not the DB.

### 4. Foreign object check on three axes

Client bill edits verify `obj.user_id`, `obj.client_id == kwargs["client_pk"]`, **and** `obj.house_id == kwargs["house_pk"]`. This matters because URLs nest: a legitimately-owned bill reached via a wrong parent URL (e.g. another client's pk in the path) must not render — links could otherwise be forged to look like they belong to a different client/house.

### 5. URL name consistency check

A reverse-check script was run against all 22 changed route names with representative kwargs; it caught the `edit_other_client_bill` vs `edit_client_other_bill` name mismatch before the templates hit it.

---

## Verification

- Regression suite: **18 tests, all passing** (throwaway Postgres 17 container on `127.0.0.1:5555`; runner overrides `DATABASES` in memory — `envs/.env` untouched):
  ```
  Ran 18 tests in 2.140s — OK
  ```
- Visual verification via browser (seeded dev server, demo user, light + dark):
  - Dashboard KPIs correct after the fan-out fix (Sofia: 1250.40 balance / 2 clients / 1 unpaid / 220.00 due; Plovdiv: 340.00 / 1 / 1 / 160.00).
  - Dark mode applied via `[data-theme="dark"]` across dashboard and bills pages; toggle in header works and persists to `localStorage`.
  - House details, clients list, and monthly bills pages render with the new URL structure.
- All authenticated pages exercised through Django test client (`force_login`) with static URLs rewritten to the dev server — login form itself requires reCAPTCHA, so browser login was not used.
- `create` views return the SweetAlert success page (HTTP 200 with JS redirect), not 302 — the one test assertion adjusted to match the established (pre-existing) behavior; noted in the test file.

---

## Not In Scope

- **Redesign Phase 2:** HTMX-ification of bill flows (incremental updates without full page reloads), further componentization.
- **P1 security findings** (`SECURITY_FINDINGS.md`): HSTS/security headers (#8), debug toolbar removal (#9), `SOCIALACCOUNT_LOGIN_ON_GET`/GET logout (#10), email verification (#11), atomic balance updates with row locks (#18).

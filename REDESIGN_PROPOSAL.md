# Redesign Proposal — House Manager App

**Date:** 2026-11-15
**Companion document:** `SECURITY_FINDINGS.md` (Phase 0 of this plan is that report's P0 remediation).

---

## 1. Architecture: keep Django, add HTMX (not a SPA rewrite)

You have a working server-rendered Django stack with i18n, admin, and auth. A full React/Vue rewrite would throw away form flows, translations, and the admin for little gain. Instead:

- **HTMX + Alpine.js** layered on the current templates — partial page swaps for lists/filters/payments, no build pipeline, keeps Django template partials you already have (`partials/` becomes the HTMX fragment library).
- Bootstrap 5 stays as the base; add a small **design-token layer** (CSS variables for colors/spacing/typography) so re-theming and dark mode are one file.

---

## 2. Information architecture & URL design (also fixes the security findings)

The current session-based "selected house/client" is fragile (two tabs fight over one session key) and caused half the security issues. Redesign routes as a **resource hierarchy**:

```
/dashboard
/houses/                          → cards of user's houses
/houses/<id>/                     → house overview (was details_house)
/houses/<id>/clients/             → clients list + filters
/houses/<id>/clients/<cid>/       → client detail + bills
/houses/<id>/bills/monthly/       → house bills
/houses/<id>/reports/<year>/<month>/
```

Ownership is then derived from the URL in every `get_queryset()` — one consistent pattern instead of decorators + session.

---

## 3. Dashboard (currently just a house list)

- KPI row: **house balance, unpaid bills count, amount due this month, overdue clients** — computed with one aggregate query per house.
- Month selector with a **Chart.js** cashflow bar (collected vs. outstanding per month).
- "Needs attention" list: top unpaid clients → direct link to their payment page.
- House cards with quick actions (add bill, add client, report) instead of navigating into details first.

---

## 4. Bills & payments flow

- **Create monthly bill as a 2-step wizard**: (1) meter readings/amounts, (2) live preview of per-apartment calculations before saving (today `calculate_fees` runs silently server-side and users see results only afterward).
- **Inline payment**: the signature pad opens in a modal from the bill row; HTMX submits and swaps just that row to "PAID + signature thumbnail". Replaces full-page reloads and SweetAlert redirect round-trips.
- **Undo window**: mark-as-paid becomes a toast with "Undo" for ~10 s (server-side it's a state transition, so no balance corruption — and pair with the idempotency fix from the security report, finding #7).
- Paid/unpaid + month filters become HTMX partial requests with URL-synced query params (shareable, back-button friendly).

---

## 5. Reports

- Keep WeasyPrint PDF, add **CSV/Excel export** (django-import-export is already installed) via a dropdown on the report page.
- Report page gets a sticky summary sidebar (total due, collected, unpaid) next to the table.

---

## 6. Accounts & profile

- Merge the login/register split-screen into **one card with tabs** (both forms are already rendered in the same context).
- Replace the Django-admin dependency for daily work: a lightweight **"My data" export** (CSV) in the profile menu so cashiers don't need admin URLs.
- Avatar upload with client-side crop preview before Cloudinary upload.

---

## 7. UI polish & accessibility

- **Dark mode** via tokens + `prefers-color-scheme`, persisted in localStorage.
- Bulgarian as a first-class toggle in the header (persisted, currently via default i18n detection).
- Mobile: bottom action bar on house/client detail pages (add bill, add client) instead of top nav buttons that require scrolling.
- Accessibility pass: visible focus rings, labeled icon-only buttons (the reset-signature `↻` button), `aria-live` for toasts, table → card fallback on narrow screens.
- Typography: keep system fonts/Google Fonts but self-host the two weights you actually use (drops a cdnjs dependency and a CSP entry).

---

## 8. Implementation Phases

| Phase | Scope | Rationale |
|---|---|---|
| **0** | Security fixes from `SECURITY_FINDINGS.md` (P0 items: IDOR chain, session ownership checks, payment idempotency) | Do this first — it restructures view auth the redesign builds on |
| **1** | URL hierarchy + design tokens + dark mode + dashboard KPIs | Foundation, no UX risk |
| **2** | HTMX bill lists, filters, payment modal + signature flow | Biggest daily UX win |
| **3** | Reports (PDF + CSV), bill creation wizard, profile/avatar, accessibility pass | Polish |

---

## 9. Principles

1. **Ownership from the URL, never from the session.** Every object-scoped view derives the parent (house/client) from the URL pk and filters `get_queryset()` by `user=request.user`.
2. **Server-rendered first, progressively enhanced.** Every flow must work without JS; HTMX/Alpine only remove full-page reloads.
3. **Money logic is idempotent and atomic.** Payment transitions are one-way, guarded server-side, and balance updates run inside a transaction with row locks (see security findings #7/#18).
4. **Design tokens over ad-hoc styles.** No new raw hex colors or px values in templates; everything routes through CSS variables.

# Phase 4 Changes — Modern Design (Tokens 2.0, Data Layouts, Motion, Unified Feedback)

**Branch:** `dev` only (local; nothing pushed, nothing merged to `main`)
**Date:** 2026-11-15
**Scope:** Phases 4a–4d of `MODERN_DESIGN_PROPOSAL.md`. Phase 4e (dashboard sparklines/KPI trends) was **skipped per review**.
**Related docs:** `MODERN_DESIGN_PROPOSAL.md` (the reviewed proposal), `PHASE1–3_CHANGES.md`.

---

## Summary of Changes

### 1. Tokens 2.0 — semantic, self-deriving, OKLCH (`4a`)

| File | Change |
|------|--------|
| `staticfiles/styles/variables.css` | Rewritten as a **semantic OKLCH layer**: `--surface-0/1/2/sunk/inverse`, `--text-1/2`, `--text-on-accent`, `--accent(-soft)`, `--state-success/danger/warning(+soft)`, `--bill-paid/unpaid(-hover)`, derived `--line`, `--line-strong`, `--focus-ring`, `--shadow`; fluid type (`--step--2…3` via `clamp()`); 4pt spacing scale (`--space-1…8`); radius scale. **All Phase 1 token names kept as legacy aliases** in one clearly-fenced block — the only place old names exist |
| All 12 stylesheets | **Every raw hex replaced** (55+ occurrences) with semantic tokens or `color-mix()` derivations — hover/active/disabled/border states are now computed from tokens, so light/dark can never drift. The only literal color left is `--brand-google` (a documented brand-identity exception) |
| `staticfiles/styles/typography.css` | Fluid type applied to `html`/`h1–h6`; `text-wrap: balance/pretty` for titles/paragraphs; **`.money` utility** (`tabular-nums`, state modifiers `--negative`/`--muted`, `.money--right` for tables); global `:focus-visible` ring; View Transitions opt-in (see §3) |

### 2. Money typography sweep (`4a`)

`.money` applied to every monetary value across templates: dashboard KPIs (with `--negative` modifier on negative balances), house/client detail cards, bill rows, report cells. Digits now share fixed widths — columns align and never jitter on update.

### 3. Motion — platform primitives only (`4c`)

| Feature | Implementation |
|---------|----------------|
| Cross-fade page navigation | `<meta name="view-transition" content="same-origin">` (base.html) + `@view-transition` CSS, **inside `prefers-reduced-motion: no-preference`** — unsupported browsers and reduced-motion users get instant navigation |
| Payment feedback | Swapped-in bill rows animate a one-shot flash while htmx holds `htmx-settling` (`hx-swap="outerHTML settle:400ms"` on the payment forms and the JS-wired Undo button); green-tint flash for paid, played in reverse for reverts |
| Filter loading | Skeleton shimmer overlay (`#bills-skeleton`, `hx-indicator` on the filter form + debt links) — no spinners |
| Undo toast | Slide-up entrance + a **draining progress bar** (`::after` animation, 8 s — the same constant as `UNDO_TOAST_TIMEOUT` in `billsPayments.js`): the bar *is* the countdown, no JS timer display |
| Reduced motion | All of the above collapse to opacity-only under one media query |

### 4. Data-first layouts (`4b`)

| File | Change |
|------|--------|
| `templates/common/reports_bills.html`, `reports_other_bills.html` | Tables wrapped in `.report-table-wrap`; real `<thead>` (the monthly header row was a bare `<tr>` the browser hoisted into an anonymous tbody — sticky styling could never apply); **`<tfoot>` totals row** fed by the aggregates the report views already compute (`unpaid_bills`, `clients_bills_total_amount`, `amount_for_collection`, `calculated_total_amount`) |
| `staticfiles/styles/modals.css` | `.report-table`: sticky inverse-surface header, hover rows, bold totals, money alignment; **container query** collapses the table to cards below 520px *container* width (signature columns with empty cells hidden in card view) |
| `staticfiles/styles/sections.css` | `.reports-wrapper` gets a real measure (`max-width: 60em`, centered) — it previously shrink-to-fit its content, which crammed the table into ~440px; the superseded `.report-results table th` rule removed |
| Bill list fragments (×4) | **Live summary line**: `Bills: N · Unpaid: N · Due: X EUR` — server-rendered from the list views (annotate + aggregate, no JS) |
| `staticfiles/styles/modals.css` | `.filter-buttons` sticky under the top edge with a surface background |
| `house_manager/common/templatetags/common_tags.py` | **New** (`common/templatetags` package): `breadcrumbs` tag — renders Dashboard / House / Client / *current* from the Phase 1 URL hierarchy, current page as `aria-current="page"`. Wired into house details, clients list, client details, the 4 bill lists, and both reports |

### 5. SweetAlert retired (`4d`)

| File | Change |
|------|--------|
| `house_manager/house_bills/views.py` | `HouseBaseBillCreateView`: `render_success_alert` and the error-popup `form_invalid` removed — success is a plain **302** to the house details; invalid forms re-render with standard field errors (`.errorlist` was already styled) |
| `templates/base.html` | `sweet_alert.html` include removed (block hook kept); `<meta name="view-transition">` added |
| `templates/house_bills/create_house_bills.html`, `create_other_bill.html` | SweetAlert script tags removed |
| **Deleted** | `templates/partials/sweet_alert.html`, `staticfiles/scripts/sweetAlert.js` (the ≈50 KB SweetAlert2 bundle) |

One interaction vocabulary now: server-rendered pages + `<dialog>` modals + toasts. Delete confirmations were already server-rendered pages (`delete_*.html`), unchanged.

### 6. Tests + translations

| File | Change |
|------|--------|
| `house_manager/house_bills/tests.py` | Create test updated: asserts **302 → details_house** (was: 200 SweetAlert page) |
| `locale/bg/LC_MESSAGES/django.po` (+ `.mo`) | New strings translated: Местоположение, Сметки, Неплатени, Дължими, Репорти, Общо, Клиент - детайли |

---

## Implementation Notes

### 1. The breadcrumb escaping trap

`separator.join(items)` on a list of `SafeString`s returns a **plain `str`** (join loses safe-marking), so the outer `format_html` escaped the whole trail — caught in browser verification as visible `&lt;a href=…` text. Fixed by composing the pieces (all built with `format_html`) and `mark_safe`-ing only the final joined string.

### 2. Legacy token aliases

Every pre-existing stylesheet consumed the Phase 1 token names. The sweep replaced all *raw hexes*, and the old token *names* are aliased to the semantic layer in one fenced block — the codebase has a single color vocabulary now, and the aliases can be dissolved stylesheet-by-stylesheet later without a big-bang rewrite.

### 3. Reports width was a pre-existing squeeze

`.report-results` measured ~440px because `.reports-wrapper` shrink-to-fit inside the flex container — the old table was always cramped. Giving the wrapper a real measure (`60em`) also keeps the new container-query card fallback honest (it now only triggers on genuinely narrow screens).

---

## Verification

- Regression suite: **44 tests, all passing** (throwaway Postgres 17 container; `envs/.env` untouched):
  ```
  Ran 44 tests in 3.488s — OK
  ```
- Browser-verified (seeded dev server, dark + light):
  - Client bills list: breadcrumbs render and navigate; summary line correct (`Bills: 1 · Unpaid: 0 · Due: 0.00 EUR` after payment); filter bar sticky; skeleton overlay during filter requests.
  - Payment: row flash animation plays, dialog closes, toast slides up with the draining progress bar; ledger verified in DB.
  - Create flow: POST → **302 → house details** (SweetAlert page gone; the form_invalid path still renders proper field errors — exercised with the missing-calculation-options seed case, which produces a clean non-field error message).
  - Monthly report: full-width table, sticky light-on-inverse header, right-aligned tabular money, bold totals row.
  - Zero raw hexes outside `variables.css` (except the documented `--brand-google`).
  - No console errors / CSP violations in either theme.

---

## Post-review follow-up: payment modal redesign

The first modal design (the Phase 2 one) reproduced the detail-card grid
inside the dialog — cramped label-over-value cells, weak hierarchy, and
no visual anchor on the amount. Redesigned (same hooks, zero logic
changes):

- **Amount-first hero**: status pill (Paid/Unpaid with state colors),
  apartment + family name (or the house), period — and the total as the
  dominant element (`--step-3`, tabular figures).
- **Itemized breakdown**: label/value rows with hairline dividers and a
  bold totals row (replaces the label-over-value grid).
- **Pay switch**: the bare "Pay the bill" checkbox became a labeled
  switch (track + knob, success color when on, focus ring on the track,
  disabled state preserved) — Django's `{{ form.is_paid }}` is kept in
  the DOM, so no-JS POSTs are unchanged.
- **Action bar**: primary Save right / ghost Cancel; receipt link styled
  as a secondary action on paid client bills; the repairs-fund warning
  is a proper callout (`--state-warning`), not a red inline string.
- JS selector updated (`form.is-paid-form` → `form.bill-form`);
  `data-bill-modal` / `hx-post` / `#signature` / `#save-btn` hooks
  unchanged — all 44 tests pass untouched.
- Also fixed: the client-monthly breakdown had lost
  `{% load custom_filters %}` in the Phase 4 rewrite, so the
  built-in `add` coerced the total to `220` instead of `220.00`.

Verified in-browser (dark + light): unpaid, paid (signature + receipt),
and house-bill (warning callout) variants; full pay → toast → undo
cycle through the new UI.

## Follow-up: sticky site header (filtered bills floated it away)

The user reported the header "moving based on the page content" when
filtering bills. Two stacked causes:

1. **Stray `</div>` in all four bill-list partials** (Phase 2). The
   extra close shifted every later close tag up a level, so the
   browser's parser hoisted the back-to-top button, footer and cookies
   banner OUT of `.site`. With the footer outside the flex column,
   `.site-footer { margin-top: auto }` could no longer absorb the free
   space, and `.site { justify-content: center }` then vertically
   centered header+main - on short (filtered) pages the header floated
   ~190px down. Removed the stray close in
   `client_bills/partials/{monthly,other}_bill_list.html` and
   `house_bills/partials/{monthly,other}_bill_list.html`, and dropped
   `justify-content: center` from `.site` (the footer auto-margin
   already handles the sticky-footer layout; centering is a footgun).
2. **Header not sticky on desktop**: `.site-header` was sticky only in
   the <=600px media query. It is now `position: sticky; top: 0` at all
   widths (`z-index: 20` - above the filter bar (5)/skeletons (4),
   below the undo toast (30); dialogs live in the top layer).

Sticky elements that must pin below the header offset themselves by a
new `--header-h` layout token (variables.css; logo + wordmark line +
padding, with breakpoint overrides in responsive.css where the logo
shrinks). The bills filter bar's sticky box is the filter FORM, not the
inner div - a sticky element is constrained by its parent, and the
parent form is exactly the bar's height, so a sticky div could never
travel. Verified: header pinned at 0, bar pinned at the header's bottom
edge in dark + light, HTMX filter round-trip keeps the header planted,
footer back inside `.site` and pinned to the viewport bottom, zero
console messages, all 44 tests pass.

## Follow-up: dark-mode inverse text + breadcrumbs placement

- **Invisible dark-mode text**: elements on the inverse surface (site
  header nav, its hover underline bars, footer, cookies banner) used
  `--site-bgnd`/`black` as text/underline color - fine in light mode
  (light text on dark chrome), but `--site-bgnd` flips to near-black in
  dark mode, so the nav/footer/cookies text vanished. They now use
  `--text-on-inverse` (light in both themes) and the banner uses
  `--surface-inverse` instead of raw black.
- **Breadcrumbs moved into the site sections**: the `breadcrumbs` tag
  was called before `<section class="site-section">`, so the crumbs sat
  at the container's left edge, outside the content measure (and as a
  flex sibling of `.wrapper` they split the container into columns).
  The call now lives inside the section's `.wrapper` /
  `.reports-wrapper` (flex column) as the first row - aligned with the
  page content on all nine hierarchy pages. HTMX region swaps don't
  touch the crumbs.

## Follow-up: reports pages — dark-mode text + working PDF export

- **Invisible dark-mode text**: the report house cards (Town/Address/
  Building number/Entrance + Month/Year/Amount) sat on
  `--surface-inverse` with `--text-on-accent` text - near-black on
  near-black in dark mode. Now `--text-on-inverse` (same fix as the
  header/footer). The search button also paired `--text-on-accent`
  with the light `--card-bgnd-hover` background (white on cream in
  light mode too) - it now uses the `--accent` pairing, which is
  correct in both themes.
- **"Save as PDF" silently broken since the token migration**: the
  vendored html2pdf bundle carries html2canvas 1.4.1, which cannot
  parse `oklch()`/`color-mix()` - every token color since Phase 4 - so
  `save()` rejected with "Attempting to parse an unsupported color
  function" and nobody caught the rejection. Replaced with the
  maintained fork **html2canvas-pro** 2.5.2 (oklch/color-mix support,
  MIT, vendored `html2canvas-pro.min.js`) plus **jspdf 2.5.2** UMD;
  `exportToPdf.js` now renders the report and lays it across A4 pages
  itself (same pipeline/pagination as the bundle) with a meaningful
  filename (`monthly-bills-reports-2026-10.pdf`), and surfaces errors
  on the console instead of failing silently. The 2MB html2pdf bundle
  is deleted.

## Follow-up: signature visibility + dark-mode PDF export

- **Signatures are dark ink baked into transparent SVGs** (jSignature
  default pen), so every dark surface hid them in dark mode: the pad
  you draw on (`--surface-2`), the paid-signature display and the
  report table's Signature column. Fix: a theme-independent paper pair
  (`--surface-paper` / `--on-paper`, variables.css) - the pad is white
  paper in both themes (ink always visible while signing) and both
  signature displays get a white chip.
- **Dark-mode PDF had white background with light-gray rows**: the
  capture element has no background of its own (the surface lives on
  `.site`), and html2canvas defaults the canvas to white - the dark
  theme's light text then sat on white. exportToPdf.js now passes
  `backgroundColor: getComputedStyle(.site).backgroundColor`, so the
  PDF matches the on-screen theme (white chips carry the signatures).

## Follow-up: centered payment dialog + theme-aware signature pen

- **Centered dialog**: reset.css zeroes every margin, including the
  UA's `margin: auto` between the dialog's inset-0 edges - which is
  exactly how `<dialog>` centers itself. Restored explicit
  `position: fixed; inset: 0; margin: auto` on `dialog.bill-modal`
  (left/right and top/bottom gaps now measure equal).
- **Signature pen adapts to the theme**: the pad draws white ink on a
  dark pad in dark mode (`color: '#ffffff'` passed to jSignature; the
  pad surface flips between paper and `--surface-sunk`), so the strokes
  are visible while signing. The stored SVG is normalized back to
  black ink (`stroke="#000000"` replace on the decoded payload) because
  signatures always render on paper surfaces - chips, receipts, PDFs -
  where white ink would vanish. The POST contract stays pure base64
  (the view prepends the data: prefix); a first-cut normalization that
  returned `mime + ',' + payload` corrupted one stored row in the dev
  DB and was caught in verification (payments are idempotent to
  re-do: undo + pay again restored clean data).

## Follow-up: silence the Chrome DevTools probe 404

Chrome DevTools requests `/.well-known/appspecific/com.chrome.devtools.json`
whenever it is open (probing for its workspace config). Django answered
with the 124KB debug 404 page and a `Not Found:` line in the server
console - alarming next to real errors, and unrelated to the Apply
button (verified: Apply does an HTMX swap, no navigation, no console
errors). The path now answers 204 No Content in the root URLconf.

## Follow-up: back buttons removed where breadcrumbs exist

Every breadcrumb page (clients list, client details, the four bill
lists, both reports) dropped its redundant "Back" control - the trail
now provides the way back. The edit pages have no breadcrumbs, so
`partials/back_button.html` stays there; the reports back-button
partial is deleted. The payment modal's Cancel is unaffected (it
closes the dialog, it does not navigate).

## Not In Scope

- **Phase 4e (skipped per review):** dashboard cockpit — balance sparklines, KPI trends, "This month" panel.
- **Remaining a11y pass:** table→card fallback is done for reports; focus-ring sweep is done; remaining: audit all icon-only buttons, landmarks/heading order.
- **P1 security findings** (`SECURITY_FINDINGS.md`): HSTS/security headers (#8), debug toolbar removal (#9), `SOCIALACCOUNT_LOGIN_ON_GET`/GET logout (#10), email verification (#11), atomic balance updates with row locks (#18), `axes.W006`.

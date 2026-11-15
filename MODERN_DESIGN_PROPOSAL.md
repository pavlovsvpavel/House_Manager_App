# Modern Design Proposal — House Manager

**Date:** 2026-11-15
**Status:** Partially implemented — Phases 4a (tokens), 4b (data layouts), 4c (motion) and 4d (SweetAlert retirement) are delivered in `PHASE4_CHANGES.md`; Phase 4e (dashboard cockpit) was skipped per review.
**Builds on:** `REDESIGN_PROPOSAL.md` (Phases 0–3 delivered: URL hierarchy, tokens, dark mode, HTMX flows, undo toast), `PHASE1–3_CHANGES.md`.
**Premise:** the app's structure is now modern; its *skin* is not. This document proposes a design-layer overhaul — no framework migration, no build step, no SPA. Everything is Django templates + CSS + a little JS, matching the stack we have.

---

## 0. What this app is (and what design should serve it)

A **finance tool for building cashiers** (Bulgarian съседство management): balances, monthly bills, debts, receipts. Users check it often, act quickly (mark paid), and scan tables of numbers.

Design implications:

1. **Numbers are the interface.** Money columns must align, update without jitter, and read at a glance (tabular figures, right-alignment, danger color for negatives).
2. **The core loop is 3 clicks deep**: Dashboard → House → Bill → Pay. Navigation and motion should make depth feel smaller.
3. **Trust through calm.** It handles other people's money — visual noise, popups, and surprise animations erode trust. Motion is for *feedback*, never decoration.
4. **Bulgarian-first typography.** The UI language is bg; text is often longer than English designs assume. Layouts must tolerate it.

## 1. Where the current skin is dated (audit)

| Area | Today | Why it reads "2021" |
|------|-------|---------------------|
| `variables.css` | Flat hex palette + manually written `*-hover` hexes | Every state is a maintenance liability; dark theme drifts from light |
| Type | Fixed sizes per component | No rhythm; mobile scaling is ad-hoc |
| Money values | Same font as labels | Columns jitter as values change; decimals misalign |
| Reports | `<table>` styled as alternating rows, no sticky header, no totals row | The one truly tabular screen looks the least like a table |
| Feedback | SweetAlert pages (POST → render popup page), instant color-jump swaps | Interaction vocabulary splits in two: SweetAlert world vs HTMX dialog world |
| Empty/filter states | `<h3>No bills</h3>` | Dead ends instead of guided actions |
| Focus/keyboard | Browser default outlines, inconsistent | Invisible in some themes, ugly in others |
| Motion | None (besides `transition: .3s` on hover) | Feels static between page loads |

## 2. Token system 2.0 — semantic, self-deriving, OKLCH

**Principle: no component stylesheet may name a color again.** Components consume semantic tokens; themes are one file.

### 2.1 Semantic layers

```css
:root {
    /* Surfaces — elevation by lightness, not by shadow stacking */
    --surface-0: oklch(98% 0.02 95);   /* page background   */
    --surface-1: oklch(95% 0.04 85);   /* cards             */
    --surface-2: oklch(90% 0.06 80);   /* raised / hover    */
    --surface-sunk: oklch(97% 0.01 95);/* wells, code, modal backdrop tints */

    /* Text */
    --text-1: oklch(25% 0.05 260);     /* primary  */
    --text-2: oklch(45% 0.03 260);     /* muted    */
    --text-on-accent: oklch(99% 0 0);

    /* Accent + states, each with a -soft (background) variant */
    --accent:        oklch(62% 0.16 250);
    --accent-soft:   oklch(93% 0.04 250);
    --success:       oklch(60% 0.14 145);
    --success-soft:  oklch(93% 0.06 145);
    --danger:        oklch(55% 0.19 25);
    --danger-soft:   oklch(93% 0.05 25);

    /* Lines & focus */
    --line:  color-mix(in oklch, var(--text-1), transparent 88%);
    --line-strong: color-mix(in oklch, var(--text-1), transparent 70%);
    --focus-ring: 0 0 0 3px color-mix(in oklch, var(--accent), transparent 55%);

    /* Radius / space scale (4pt grid) */
    --radius-s: 0.375rem; --radius-m: 0.75rem; --radius-l: 1.25rem;
    --space-1: 0.25rem; /* … --space-8: 4rem */
}

[data-theme="dark"] { /* only the semantic layer is re-mapped — nothing else knows themes exist */ }
```

### 2.2 Derived states — the end of hand-written hover hexes

Every interactive hover/active/disabled becomes a **derivation**, so themes can't drift:

```css
.btn:hover  { background-color: color-mix(in oklch, var(--accent), var(--text-1) 12%); }
.btn:active { background-color: color-mix(in oklch, var(--accent), var(--text-1) 25%); }
.btn:disabled { background-color: color-mix(in oklch, var(--surface-2), var(--text-1) 40%); }
```

This deletes ~40 hardcoded hover hexes across `buttons.css` / `cards.css` / `navigation.css` and fixes their dark-mode counterparts for free.

### 2.3 Fluid type + spacing rhythm

```css
:root {
    --step--2: clamp(0.69rem, 0.66rem + 0.12vw, 0.78rem);
    --step--1: clamp(0.8rem,  0.77rem + 0.16vw, 0.9rem);
    --step-0:  clamp(0.94rem, 0.9rem + 0.2vw, 1.05rem);
    --step-1:  clamp(1.13rem, 1.05rem + 0.4vw, 1.32rem);
    --step-2:  clamp(1.35rem, 1.2rem + 0.75vw, 1.76rem);
    --step-3:  clamp(1.62rem, 1.35rem + 1.3vw, 2.34rem); /* section titles */
}
```

## 3. Money typography (the one-line change users feel daily)

```css
.money {
    font-variant-numeric: tabular-nums;
    text-align: right;
    font-weight: 500;
}
.money--negative { color: var(--danger); }
.money--zero { color: var(--text-2); }
```

Applied to every balance, KPI, bill amount, and report cell. **Tabular figures** mean digits share a fixed width — balances align vertically, and the undo/payment moment doesn't make the column dance.

## 4. Data-first layouts

### 4.1 Reports become real tables

- Sticky `<thead>` (`position: sticky; top: 0; background: var(--surface-0)`), right-aligned money columns, **bold totals row** (`<tfoot>`), row hover via `--surface-2`.
- **Container-query collapse** — the table becomes cards when its *container* (not the viewport) is narrow, so the report stays a table in a wide modal and becomes cards on a phone:

```css
.report-table-wrap { container-type: inline-size; }
@container (max-width: 520px) {
    .report-table { display: grid; }       /* each <tr> becomes a card */
    .report-table thead { display: none; }
}
```

### 4.2 Sticky filter bar with live counts

On bill lists: filter row + "N bills · M unpaid · K EUR due" summary sticks under the header while scrolling. Server-rendered counts (already computed for the dashboard) — no JS.

### 4.3 Breadcrumbs from the URL hierarchy

Phase 1 gave us a strict resource hierarchy; a `breadcrumbs` template tag walks `kwargs` (`house_pk` → `client_pk` → `pk`) and renders:

```
Начало / Ул. Витоша 15 / Иванов / Сметка октомври
```

Free trust + orientation, zero state.

## 5. Motion — feedback only, and only modern primitives

| Moment | Treatment | Mechanism |
|--------|-----------|-----------|
| Full-page navigation | 150–200 ms cross-fade/slide | **View Transitions API**: `<meta name="view-transition">` + `@view-transition { navigation: auto; }` — progressive; unsupported browsers just navigate |
| HTMX swap | Skeleton shimmer in place of incoming content | `hx-indicator` → skeleton block with `@keyframes` shimmer |
| Payment success | Row: soft green flash → settle to paid token; toast slides up 12px | CSS keyframes on the swapped-in row (`.bill-row--paid-flash`) |
| Undo window | Toast progress bar drains 8s | `animation: toast-life 8s linear forwards` — the bar *is* the timer, no JS |
| Charts (Phase 4e) | Bars grow once on load | Scroll-driven or one-shot keyframes |
| Everything | Honors `prefers-reduced-motion: reduce` → all of the above become opacity-only | One media query wrapper |

No physics libraries, no parallax, no scroll-jacking. If a motion can't explain what just happened, it's cut.

## 6. One interaction vocabulary: retire SweetAlert

Today two vocabularies coexist:

- **Bills** (Phases 2–3): native `<dialog>` + toast — no-JS-safe, CSP-clean.
- **Create/delete** (unchanged since Phase 0): POST → render a *page* whose only purpose is a SweetAlert popup + JS redirect.

Unify on the first:

- Success → **redirect (no-JS) / toast (HTMX)** — the SweetAlert success page disappears entirely.
- Destructive confirmations (delete house/client/bill) → native `<dialog>` with explicit verb buttons ("Изтрий" in `--danger`, "Отказ" ghost).
- Validation errors → server-rendered field errors + `aria-invalid` (no popups at all — popups for form errors are a mobile anti-pattern anyway).

Deletes `sweetalert2` (≈50 KB gz), `sweetAlert.js` glue, and the `render_success_alert` pattern across create views.

## 7. Dashboard as a cockpit

- **Balance sparkline per house** — last 6 months of balance as an inline SVG polyline rendered by a `sparkline` template tag from a single annotated queryset. No chart library, printable, dark-mode-correct via `currentColor`.
- **KPI trends**: `▲ 240 €` / `▼ 80 €` vs previous month next to Balance/Due, colored `--success`/`--danger`.
- **"This month" panel**: per house — unpaid count + total due, each a direct link into the filtered bills list (`?is_paid=False&month=10` — the Phase 3 filter fix makes these URLs do the right thing).

## 8. Component polish checklist

- [ ] `appearance: none` on selects + custom chevron (currently inherits UA chrome).
- [ ] Checkbox "cards" for boolean forms (Pay the bill) — label-wrapped, 44px target.
- [ ] `:focus-visible` ring (`box-shadow: var(--focus-ring)`) on every interactive element; `outline: none` only under it.
- [ ] Empty states: icon + sentence + one primary action ("Add first bill"), replacing `<h3>No bills</h3>`.
- [ ] Buttons: two-tier system (primary = accent, ghost = transparent+line) replacing the current ad-hoc per-section colors.
- [ ] Form errors: field-level `aria-invalid` + message list, red only as `--danger` text, never popups.
- [ ] Print stylesheet for reports/receipts (hide chrome, black on white, keep signatures).

## 9. Explicitly not doing

- **No Tailwind / Bootstrap migration** — we have a token system; a utility framework would fight it.
- **No SPA, no React/Vue, no build pipeline** — unchanged stance from `REDESIGN_PROPOSAL.md`.
- **No new JS libraries** — View Transitions and dialogs are platform features; sparklines are template tags.
- **No redesign of information architecture** — Phase 1 URLs/ownership are final.
- **No animation without a job** — see §5.

## 10. Browser support / enhancement policy

| Feature | Baseline | Fallback |
|---------|----------|----------|
| OKLCH, `color-mix` | All evergreen (2023+) | Legacy hex tokens kept as `@supports not (color: oklch(50% 0 0))` block until the old base is retired |
| Container queries | All evergreen (2023+) | Cards never collapse; table scrolls horizontally |
| View Transitions | Chromium 126+ | Instant navigation (today's behavior) |
| `light-dark()`, subgrid | Progressive | Token overrides under `[data-theme]` (current mechanism, kept) |

## 11. Suggested phasing

| Phase | Content | Files touched | Risk |
|-------|---------|---------------|------|
| **4a — Tokens 2.0** | Semantic OKLCH layer, `color-mix` derived states, fluid type, `.money` utility, focus rings, radius/space tokens | `variables.css` + mechanical sweep of the 12 stylesheets | Low (pure CSS; visually verifiable) |
| **4b — Data layouts** | Report table modernization, container-query card fallback, sticky filter bar + counts, breadcrumbs tag | `reports_*.html`, list templates, `cards.css`, one template tag | Medium |
| **4c — Motion** | View transitions meta + CSS, HTMX skeletons, payment flash + toast slide, reduced-motion wrapper | `base.html`, list templates, `modals.css` | Low |
| **4d — Retire SweetAlert** | Create/delete views → redirect/toast; `<dialog>` confirmations for deletes; delete SweetAlert assets | Create/delete views + templates, `common/mixins.py` (render_success_alert), new `confirm_dialog.html` | Medium (touches create flows) |
| **4e — Dashboard cockpit** | Sparkline tag, KPI trends, "This month" panel | `common/views.py`, `dashboard.html`, `dashboard.css`, one template tag | Medium |

Each phase is independently shippable and verifiable with the existing throwaway-Postgres + in-app-browser rig; 4a–4c touch no Python money logic at all.

---

*Prepared for review — nothing here is implemented yet.*

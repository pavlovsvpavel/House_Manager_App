# Security Review — House Manager App

**Date:** 2026-11-15
**Scope:** Full codebase review — Django application (`house_manager/`), settings, templates, Docker/deployment configuration (`docker-compose-prod.yml`, `nginx/prod/`, `Dockerfile`, `entrypoint.sh`).
**Live target considered:** `house-manager.win` (production deployment).

> This is a manual design/code review, not a dynamic penetration test. Findings marked **High** should be treated as exploitable and fixed before any further production use.

---

## Executive Summary

The project does a lot right: secrets live in untracked `envs/` files, the Docker image runs as a non-root user, dependencies are pinned, nginx disables `server_tokens`, TLS 1.2/1.3 is enforced, django-axes provides lockouts, reCAPTCHA protects login/registration, and Django 6's CSP middleware is used with nonces.

The **dominant weakness is broken access control (IDOR)**. Object ownership is enforced inconsistently: some views check `house.user == request.user` via decorators, but **all bill edit views and the receipt download view fetch objects by primary key with no ownership filter at all**. The session-based "selected house / selected client" pattern makes this worse, because the session is written *before* the ownership check runs, letting an attacker prime their session with another user's objects and pivot into views that trust the session blindly.

---

## Findings Overview

| # | Severity | Finding | Location |
|---|----------|---------|----------|
| 1 | **High** | IDOR — receipt PDF download for any bill, any user | `client_bills/views.py` `DownloadReceiptView` |
| 2 | **High** | IDOR — edit/mark-as-paid any client bill via direct POST | `client_bills/views.py` `CurrentClientBaseBillEditView` |
| 3 | **High** | IDOR — edit/mark-as-paid any house bill via direct POST | `house_bills/views.py` `HouseBaseBillEditView` |
| 4 | **High** | IDOR — view any client's bill lists | `client_bills/views.py` `ClientBaseBillsDetailView` |
| 5 | **High** | Session primed with foreign objects *before* ownership check | `houses/decorators.py`, `clients/decorators.py` |
| 6 | **High** | Create-views trust `session["selected_house"]` without verifying ownership | `houses/mixins.py` `GetHouseAndUserMixin`, `house_bills/views.py` `HouseBaseBillCreateView` |
| 7 | **High** | Payment replay — re-submitting a paid bill re-credits the house balance | `client_bills/views.py`, `house_bills/views.py` |
| 8 | **Medium** | Missing security headers / cookie hardening (HSTS, `SESSION_COOKIE_SECURE`, …) | `settings.py`, `nginx/prod/conf.d/web.conf` |
| 9 | **Medium** | Debug toolbar in production middleware & unconditional `__debug__/` URLs | `settings.py`, `urls.py` |
| 10 | **Medium** | `SOCIALACCOUNT_LOGIN_ON_GET = True` (GET login CSRF) + GET logout without CSRF | `settings.py`, `accounts/urls.py` |
| 11 | **Medium** | No email verification on registration; auto-login; email-based account linking | `settings.py`, `accounts/adapters.py`, `accounts/views.py` |
| 12 | **Medium** | Internal exception details leaked to end users | `house_bills/views.py` `HouseFixedMonthlyBillView` |
| 13 | **Medium** | Profile permission check compares *user pk* against *Profile pk* | `accounts/mixins.py` `OwnerRequiredMixin` |
| 14 | **Medium** | Postgres (5432) and Gunicorn (8000) ports published to the host | `docker-compose-prod.yml` |
| 15 | **Low/Medium** | Unvalidated, unlimited-size user-supplied signature data stored in DB | `client_bills/views.py` `form_valid`, `common/mixins.py` |
| 16 | **Low/Medium** | Password spraying not limited by IP (axes locks username only) | `settings.py` axes config |
| 17 | **Low** | CSP gaps: `unsafe-inline` styles, `img-src https:`, no `form-action`/`base-uri`/`frame-ancestors` | `settings.py` `SECURE_CSP` |
| 18 | **Low** | Balance update not atomic with bill save (race window) | `client_bills/helpers/add_amount_to_balance.py` |
| 19 | **Low** | reCAPTCHA verification has no HTTP timeout (request hang) | `accounts/forms.py` |
| 20 | **Info** | Local `envs/.env*` files world-readable/executable (0755) | local file permissions |

---

## High Findings

### 1. IDOR — Receipt PDF download for any bill (any user)

**File:** `house_manager/client_bills/views.py`, `DownloadReceiptView`

```python
class DownloadReceiptView(CheckForLoggedInUserMixin, DetailView):
    model = ClientMonthlyBill   # fetched by pk from the URL, no owner filter
```

The only guard is `CheckForLoggedInUserMixin` (is the user logged in). There is **no check that the bill's `user` (or its house's owner) is the requesting user**.

**Impact:** Any authenticated user can iterate `/client-bills/bill/<pk>/receipt/download/` and download other users' receipts — which contain client names (family name), apartment numbers, amounts, months, and the payer's signature image. Data is financial/personal.

**Fix:**

```python
def get_queryset(self):
    return ClientMonthlyBill.objects.filter(user=self.request.user)
```

### 2. IDOR — Client bill edit / mark-as-paid via direct POST

**File:** `house_manager/client_bills/views.py`, `CurrentClientBaseBillEditView`

```python
class CurrentClientBaseBillEditView(CheckForLoggedInUserMixin, views.UpdateView):
    fields = ("is_paid",)
    # get_object() uses the unfiltered queryset -> any bill by pk
```

The house/session consistency check lives in `get_context_data()`, which is **only called on GET and on invalid POST**. On a *successful* POST the flow is: `get_object()` → `form_valid()` → `add_amount_to_house_balance()` → save → redirect. The ownership check is never executed.

**Impact:** Any authenticated user can POST `is_paid=true` to `/client-bills/edit-bill/<pk>/` for **another user's** bill, changing their financial records and mutating their house's `money_balance`.

**Fix:** Filter ownership in the queryset (one line per subclass) and/or verify ownership inside `get_object()`:

```python
class CurrentClientMonthlyBillEditView(CurrentClientBaseBillEditView):
    queryset = ClientMonthlyBill.objects.filter(user=...)  # bind at dispatch instead
```

Since the queryset is a class attribute, resolve it in `dispatch()`/`get_queryset()` with `self.request.user`.

### 3. IDOR — House bill edit / mark-as-paid via direct POST

**File:** `house_manager/house_bills/views.py`, `HouseBaseBillEditView` (used by `HouseMonthlyBillEditView` and `HouseOtherBillEditView`)

Identical pattern to #2: unfiltered `queryset`, ownership check only in `get_context_data()`, `form_valid()` subtracts the amount from the house balance. Routes `/house-bills/edit-bills/<pk>/` and `/house-bills/edit-other-bills/<pk>/` have no ownership decorator.

**Impact:** Any authenticated user can mark any house bill paid and mutate any house's balance. Also exposes other users' cost breakdowns (electricity, lift, internet, fees…) on the GET page.

**Fix:** Same as #2 — filter by `user=request.user` (house bills have a `user` FK).

### 4. IDOR — View any client's bills

**File:** `house_manager/client_bills/views.py`, `ClientBaseBillsDetailView`

```python
def get_object(self, queryset=None):
    selected_client_id = self.request.session.get("selected_client")
    if not selected_client_id or selected_client_id != self.kwargs['pk']:
        raise PermissionDenied(...)
    try:
        return get_object_or_404(Client, pk=self.kwargs['pk'])  # no user filter
```

The only protection is equality with `session["selected_client"]` — and that session value is **written by the client decorator *before* its ownership check** (see finding #5). There is no `client.user_id == request.user.id` verification.

**Impact:** Any authenticated user can view `/client-bills/bills/<pk>/` and `/client-bills/other-bills/<pk>/` for any client id they can prime their session with — leaking names, floors, apartments, and full payment history.

**Fix:** `Client.objects.get(pk=..., user=request.user)` (or filter by `house__user=request.user`).

### 5. Session primed with foreign objects BEFORE the ownership check

**Files:** `house_manager/houses/decorators.py`, `house_manager/clients/decorators.py`

```python
selected_house = House.objects.select_related('user').get(id=selected_house_id)
request.selected_house = selected_house
request.session['selected_house'] = selected_house.pk   # written first!

if selected_house.user_id != request.user.id:
    raise PermissionDenied("You are not the owner of this house.")  # checked second
```

When the ownership check fails, the session has **already been mutated** to point at the victim's house/client. An attacker (any registered user) can visit `/houses/<victim-house-pk>/` — receive a 403, but now their own session contains the victim's house id — then pivot into the views that blindly trust the session (findings #4 and #6). Storing mutable "current object" state in the session is also fragile in general (two tabs = two different houses sharing one session key).

**Fix:**
1. Perform the ownership check **before** mutating `request.session` (or don't raise a 403 after writing).
2. Better: remove the session indirection entirely and derive ownership from the URL pk in every view (`get_queryset()` filtered by `user`), which also fixes the multi-tab problem.

### 6. Create views trust `session["selected_house"]` without ownership verification

**Files:** `house_manager/houses/mixins.py` (`GetHouseAndUserMixin`), `house_manager/house_bills/views.py` (`HouseBaseBillCreateView.current_house`)

```python
house_id = self.request.session.get("selected_house")
if house_id:
    house = House.objects.get(pk=house_id)   # no house.user check
    form.instance.house = house
form.instance.user = self.request.user
```

Combined with #5, an attacker can create house bills / client bills **inside another user's house** (bill rows tagged with the attacker's `user` FK but attached to the victim's house, feeding the victim's calculations and reports).

**Fix:** `House.objects.get(pk=house_id, user=self.request.user)`, and prefer taking the house from the URL.

### 7. Payment replay — re-submitting a paid bill re-credits the balance

**Files:** `house_manager/client_bills/views.py` and `house_manager/house_bills/views.py`, `form_valid()` + `get_form()`

```python
def get_form(self, form_class=None):
    form = super().get_form(form_class)
    if form.instance.is_paid:
        form.fields["is_paid"].disabled = True   # disabled fields fall back to instance value (True)

def form_valid(self, form):
    if not form.cleaned_data['is_paid']:
        return self.form_invalid(form)
    ...
    add_amount_to_house_balance(...)   # runs unconditionally on every valid POST
```

When a bill is already paid, the field is rendered disabled; on the next POST Django ignores the browser value and uses the instance's value (`True`), so `form_valid()` passes and **adds the amount to the house balance again**. There is no idempotency check ("this bill is already paid — reject"). The same applies to the subtract path for house bills.

**Impact:** Replaying a captured form (or simply submitting it twice) inflates/deflates `money_balance` — the core financial figure of the app. User-facing money-corruption bug as well as a security issue.

**Fix:**

```python
def form_valid(self, form):
    if self.object.is_paid:
        return self.form_invalid(form)   # idempotency guard, checked server-side
    ...
```

and restructure so `is_paid` can only ever transition `False → True` exactly once (ideally with `select_for_update` in a transaction, see finding #18).

---

## Medium Findings

### 8. Missing security headers and cookie hardening

**Files:** `house_manager/settings.py`, `nginx/prod/conf.d/web.conf`

None of the following are configured (Django or nginx):

- `SECURE_HSTS_SECONDS` / HSTS header (nginx also sends none) — downgrade/stripping protection
- `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` — cookies currently may be sent over plain HTTP if any http path remains
- `SECURE_SSL_REDIRECT = True` (nginx does the redirect, so impact is limited, but defense-in-depth is missing)
- `SESSION_COOKIE_SAMESITE` explicit value, `SECURE_PERMISSIONS_POLICY`
- nginx: no `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`

**Fix:** add the standard hardening block to `settings.py` (it's safe to enable since the site is HTTPS-only in nginx):

```python
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = False  # nginx handles redirect; keep True if Django terminates TLS
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
```

and a `Strict-Transport-Security` header block in nginx.

### 9. Debug toolbar shipped in production

**Files:** `settings.py` (INSTALLED_APPS + MIDDLEWARE), `urls.py`

`debug_toolbar` is installed and `path('__debug__/', include('debug_toolbar.urls'))` is unconditional in production. The toolbar render is gated on `DEBUG`, but the settings/history panels expose `SECRET_KEY`, DB credentials, and full request data **whenever DEBUG is ever true in prod** (a single env misconfiguration — `DEBUG=1` is already present in the root `envs/.env` used for dev). The History panel even allows replaying POST requests.

**Fix:** remove `debug_toolbar` from the production image/settings (split settings: `base.py` / `dev.py` / `prod.py`), and gate the URL with `if settings.DEBUG:`.

### 10. GET-based login (social) and GET logout — CSRF issues

**Files:** `settings.py` (`SOCIALACCOUNT_LOGIN_ON_GET = True`), `accounts/urls.py` (`logout` is a plain GET path)

- `SOCIALACCOUNT_LOGIN_ON_GET` lets an attacker start a Google login via a plain `<img>`/link on any site (login CSRF: log the victim into an attacker-controlled Google account). allauth documentation recommends `False` with POST-only login.
- `path("logout/", logout_user, ...)` performs logout on GET with no CSRF token → third-party sites can force-log users out (and GET logout is generally unsafe).

**Fix:** set `SOCIALACCOUNT_LOGIN_ON_GET = False`, convert logout to a POST form (`LogoutView` with `POST`), keep reCAPTCHA.

### 11. No email verification on registration; email-based account linking

**Files:** `settings.py` (no `ACCOUNT_EMAIL_VERIFICATION`), `accounts/views.py` (`RegisterUserView` logs the user in immediately), `accounts/adapters.py`

- Registration creates the account and logs the user in with **no verification that the email address is owned** (`ACCOUNT_EMAIL_VERIFICATION` is unset → optional/none).
- `CustomSocialAccountAdapter.pre_social_login` matches existing users **purely by email string**. This is the classic "pre-account-hijack" pattern: if any signup path allows registering an email that a future Google sign-in will claim (or vice versa), ownership of the older account silently transfers based on an unverified email.

**Fix:** enable `ACCOUNT_EMAIL_VERIFICATION = "mandatory"` (or at least `"optional"` with verified-email-required-before-linking: `ACCOUNT_EMAIL_REQUIRED`, `SOCIALACCOUNT_EMAIL_VERIFICATION`, and in the adapter only link when `sociallogin.email_addresses` has a verified email).

### 12. Internal exception details shown to end users

**File:** `house_manager/house_bills/views.py`, `HouseFixedMonthlyBillView`

```python
except Exception as e:
    form.add_error(None, _("An error occurred: ") + str(e))
```

Arbitrary DB/ORM exception messages (potentially including SQL fragments, field names, paths) are rendered to the browser in the SweetAlert popup.

**Fix:** log the exception server-side (`logger.exception(...)`), show a generic translated message to the user.

### 13. Profile permission check compares wrong identity

**File:** `house_manager/accounts/mixins.py`, `OwnerRequiredMixin` (used by `ProfileDetailsView`, `ProfileUpdateView`, `ProfileDeleteView`, password views)

```python
if request.user.pk != kwargs.get("pk", None):   # URL pk is the *Profile* pk
    return self.handle_no_permission()
```

The URL pk identifies a `Profile` row, but the check compares it against the **User** pk. It only works while `user.pk == profile.pk` happens to hold (profile auto-created by a signal). Any drift (re-creation, manual DB ops, bulk imports) either locks users out of their profile or lets user A edit the profile of user B whose `Profile.pk` equals A's `user.pk`.

**Fix:** check the actual relation:

```python
obj = self.get_object()
if obj.user_id != request.user.pk:
    return self.handle_no_permission()
```

(`ProfileDeleteView` additionally fetches a `User` from `UserModel.objects.all()` and then calls `self.object.user` — verify this object/identity mismatch; it appears to delete the *user* found by pk, which is OK only because of the same pk coincidence.)

### 14. Postgres and Gunicorn ports published to the host

**File:** `docker-compose-prod.yml`

```yaml
web:      ports: ["8000:8000"]
postgres: ports: ["5432:5432"]
```

The database is reachable directly on the host (password auth only, no TLS) — on a public VPS this frequently ends up internet-exposed. The web port bypasses nginx entirely (no rate limiting, no TLS, direct Gunicorn access).

**Fix:** remove `ports` for postgres (compose services on the same network don't need them) and bind web to localhost: `"127.0.0.1:8000:8000"`. Also add `POSTGRES_HOST_AUTH_METHOD` hardening / strong password (already via env) and consider `restart: unless-stopped` with healthchecks.

---

## Low / Informational Findings

### 15. Unvalidated signature payload stored in the DB

`CurrentClientBaseBillEditView.form_valid()` stores `request.POST['signature']` verbatim as `data:image/svg+xml;base64,...` into an unlimited `TextField`. Rendering happens via `<img src="...">` (`templates/partials/signature-show.html`), which does not execute SVG scripts in modern browsers — so this is **not** a reliable stored-XSS vector today, but: no size limit (DB bloat / DoS), no validation that the content is actually a base64 SVG, and any future rendering context change (inline `<svg>`, `<object>`) would become a stored-XSS sink.

**Fix:** cap length (e.g. ~100 KB), validate the base64 payload decodes to `<svg` content server-side, or rasterize server-side (Pillow) and store as a file/image field.

### 16. Brute-force protection locks by username only

`AXES_LOCKOUT_PARAMETERS = [["username"]]` — an attacker can password-spray across many accounts from one IP without ever hitting a lockout. Add IP (or `["username", "ip_address"]` as the second lockout dimension) — but keep username-only as one dimension to avoid DoS on shared NAT, e.g. `AXES_LOCKOUT_PARAMETERS = [["username"], ["ip_address"]]`.

### 17. CSP gaps

`SECURE_CSP` uses `style-src 'unsafe-inline'`, `img-src https:` (any HTTPS host), and omits `form-action`, `base-uri`, `object-src`, `frame-ancestors`. Modern browsers respect `default-src` fallbacks, but explicit `base-uri 'self'` and `form-action 'self'` are cheap wins; try removing `unsafe-inline` for styles (nonce the couple of inline blocks) as a follow-up.

### 18. Balance update not transactional with the bill save

`add_amount_to_house_balance` / `subtract_amount_from_house_balance` perform `UPDATE ... F('money_balance')` (good: no read-modify-write), but the whole "save bill + update balance" sequence is not wrapped in one transaction with `select_for_update` on the house row. Two concurrent payments could interleave; combined with finding #7 this makes money figures unreliable. Wrap `form.save()` + balance update in `transaction.atomic()` with `House.objects.select_for_update()`.

### 19. reCAPTCHA verification request without timeout

`accounts/forms.py` uses `requests.post(verify_url, data=payload)` with no `timeout=` — a hung Google endpoint stalls worker threads (Gunicorn timeout kills them, but under load this degrades login). Add `timeout=5`.

### 20. Local env file permissions (informational)

`envs/.env`, `.env.prod`, `.env.local` are `-rwxr-xr-x` (0755, executable + world-readable) and contain DB passwords, Cloudinary API secrets, SMTP credentials. They are correctly **not** tracked in git (`envs/` is gitignored; git history shows no committed copies — good). Restrict locally: `chmod 600 envs/.env*` (the executable bit serves no purpose).

---

## What Is Already Good ✅

- **Secrets management:** `envs/` gitignored, never committed; `python-decouple` for config.
- **Dependency hygiene:** pinned versions (`Django 6.1.3`, `allauth 65.21.1`, `axes 9.0.0` — all recent).
- **Brute force & bot defense:** django-axes + reCAPTCHA on login and registration (with server-side score check).
- **CSP with per-request nonces** via Django 6's CSP middleware; scripts use `nonce="{{ csp_nonce }}"`.
- **Docker:** multi-stage build, `uv sync --frozen`, **non-root user**, `server_tokens off`, TLS 1.2/1.3 only, HTTP→HTTPS redirect, request rate limiting (`limit_req`), bot-UA blocking.
- **Admin isolation:** non-superuser admin querysets filtered to the user's own rows (`CheckLoggedInUserModelInstancesMixin`), limited group permissions.
- **HSTS/cookie work** is the main missing piece; TLS config itself is solid.

---

## Prioritized Remediation Plan

1. **P0 (this week):** Fix the IDOR chain (#1–#6) by (a) adding `user` filters to every bill/client queryset in `get_queryset()`/`get_object()`, (b) moving the ownership check in both decorators before any session write, (c) adding the idempotency guard for payments (#7). This is mostly a few dozen lines total.
2. **P1:** Add the Django hardening block (#8), stop publishing 5432/8000 (#14), remove debug_toolbar from prod settings (#9), add generic error messages (#12).
3. **P2:** `SOCIALACCOUNT_LOGIN_ON_GET = False` + POST logout (#10), email verification (#11), axes IP lockout (#16), signature validation (#15), atomic balance updates (#18).
4. **P3:** CSP tightening (#17), request timeouts (#19), `chmod 600 envs/.env*` (#20), and restructure the "selected house/client" session pattern into URL-scoped routes (`/houses/<id>/...`) — which also permanently eliminates the class of bugs in #5/#6.

*Re-test after fixes: as a second registered account, attempt to GET/POST every URL containing `<int:pk>` belonging to the first account — all must return 403/404.*

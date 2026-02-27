# Security Hardening Report

**Project:** TicketDesk
**Date:** 2026-02-27
**Branch:** `master` (`bd8e540`)

---

## Overview

A security audit identified 6 vulnerabilities in the TicketDesk Django application. This report documents each issue found, the fix applied, and the files changed.

---

## Issues & Fixes

### 1. Hardcoded SECRET_KEY

**Severity:** Critical

**Issue:** `settings.py` contained a hardcoded `django-insecure-` prefixed secret key committed directly to version control, exposing it to anyone with repository access.

**Fix:** Migrated all sensitive and environment-specific configuration to a `.env` file using `python-decouple`. The `.env` file was added to `.gitignore` to prevent it from being committed.

**Files changed:**
- `requirements.txt` — added `python-decouple>=3.8`
- `ticketing_platform/settings.py` — `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` now read via `config()`
- `.env` *(new)* — stores `SECRET_KEY`, `DEBUG=True`, `ALLOWED_HOSTS=localhost,127.0.0.1`
- `.gitignore` — added `.env`

---

### 2. No Environment-Based DEBUG / ALLOWED_HOSTS

**Severity:** High

**Issue:** `DEBUG = True` and `ALLOWED_HOSTS = []` were hardcoded in `settings.py`, making it easy to accidentally deploy with debug mode enabled and no host restrictions.

**Fix:** Both values are now read from `.env` via `config()`, with safe production defaults (`DEBUG=False`, empty `ALLOWED_HOSTS`) if the `.env` file is absent.

**Files changed:**
- `ticketing_platform/settings.py`

---

### 3. Missing HTTPS / Production Security Settings

**Severity:** High

**Issue:** No production security headers or cookie protections were configured, leaving a production deployment vulnerable to protocol downgrade attacks, session hijacking, and content injection.

**Fix:** Added a conditional block at the bottom of `settings.py` that activates only when `DEBUG=False`:

| Setting | Value |
|---|---|
| `SECURE_SSL_REDIRECT` | `True` |
| `SECURE_HSTS_SECONDS` | `31536000` (1 year) |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `True` |
| `SECURE_HSTS_PRELOAD` | `True` |
| `SESSION_COOKIE_SECURE` | `True` |
| `CSRF_COOKIE_SECURE` | `True` |
| `SECURE_BROWSER_XSS_FILTER` | `True` |
| `SECURE_CONTENT_TYPE_NOSNIFF` | `True` |

**Files changed:**
- `ticketing_platform/settings.py`

---

### 4. No Rate Limiting on Login / Registration

**Severity:** High

**Issue:** The login and registration endpoints had no request rate limiting, leaving them open to brute-force and credential-stuffing attacks.

**Fix:** Added `django-ratelimit` and applied a limit of 5 requests per minute per IP to both endpoints. A custom middleware (`RatelimitMiddleware`) was added to return HTTP **429 Too Many Requests** when the limit is exceeded (django-ratelimit's default is 403).

**Files changed:**
- `requirements.txt` — added `django-ratelimit>=4.0`
- `tickets/middleware.py` *(new)* — `RatelimitMiddleware` maps `Ratelimited` exceptions to 429
- `ticketing_platform/settings.py` — `RatelimitMiddleware` added to `MIDDLEWARE`
- `tickets/views.py` — `@ratelimit(key='ip', rate='5/m', block=True)` on `register`
- `tickets/urls.py` — `LoginView` wrapped with the same ratelimit decorator

---

### 5. State-Changing View Accessible via GET

**Severity:** Medium

**Issue:** `ticket_assign_self` mutated database state (assigning a ticket and changing its status) in response to a GET request, violating HTTP semantics and bypassing CSRF protection.

**Fix:** Added `@require_POST` to the view — GET requests now return HTTP **405 Method Not Allowed**. Both templates that linked to this view were updated to use `<form method="post">` with `{% csrf_token %}` instead of `<a href>` links.

**Files changed:**
- `tickets/views.py` — `@require_POST` added to `ticket_assign_self`
- `tickets/templates/tickets/dashboard.html` — "Assign to Me" converted to a POST form
- `tickets/templates/tickets/ticket_detail.html` — "Assign to Me" converted to a POST form

---

### 6. No Auth Guard on Registration Page

**Severity:** Low

**Issue:** Authenticated users could access the `/register/` page, which could lead to confusing UX or unintended account creation flows.

**Fix:** Added a check at the top of the `register` view — if the user is already authenticated, they are immediately redirected to the dashboard.

**Files changed:**
- `tickets/views.py`

---

## Tests Added

A new `SecurityTest` class was added to `tickets/tests.py` covering all six areas above:

| Test | Verifies |
|---|---|
| `test_secret_key_not_insecure_default` | `SECRET_KEY` no longer starts with `django-insecure-` |
| `test_register_rate_limit` | Register returns 429 after 5 requests/min |
| `test_login_rate_limit` | Login returns 429 after 5 requests/min |
| `test_ticket_assign_self_rejects_get` | GET on `ticket_assign_self` returns 405 |
| `test_ticket_assign_self_accepts_post` | POST on `ticket_assign_self` still works |
| `test_authenticated_user_redirected_from_register` | Logged-in users are redirected from `/register/` |
| `test_production_security_settings_block_exists` | `settings.py` contains the HTTPS security block |

`cache.clear()` was also added to the `setUp` of `RegistrationViewTest`, `EmailUniquenessTest`, and `RoleAssignmentSecurityTest` to prevent rate limit state leaking between tests. The existing `test_employee_assign_self` was updated to use POST.

**Result:** All 69 tests pass.

---

## Files Changed

| File | Change |
|---|---|
| `requirements.txt` | Added `python-decouple`, `django-ratelimit` |
| `.env` | Created with `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` |
| `.gitignore` | Added `.env` |
| `ticketing_platform/settings.py` | Env config, middleware, production security block |
| `tickets/middleware.py` | New — 429 handler for rate limit exceptions |
| `tickets/views.py` | Auth guard on register, ratelimit decorator, require_POST |
| `tickets/urls.py` | Ratelimit on LoginView |
| `tickets/templates/tickets/dashboard.html` | Assign to Me → POST form |
| `tickets/templates/tickets/ticket_detail.html` | Assign to Me → POST form |
| `tickets/tests.py` | SecurityTest class, cache isolation fixes |

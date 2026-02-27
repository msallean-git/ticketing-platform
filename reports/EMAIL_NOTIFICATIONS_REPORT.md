# Email Notifications Report

**Project:** TicketDesk
**Date:** 2026-02-27
**Branch:** `feature/email-notifications` (off `master` @ `6853a36`)

---

## Overview

This report documents the design, implementation, and testing of email notifications for public comments on tickets. When a public comment is posted, the relevant party (ticket creator or assigned employee) receives a plain-text email alert. Internal (employee-only) comments never trigger any notification.

---

## Notification Rules

| Scenario | Recipient | Condition |
|----------|-----------|-----------|
| Employee adds a public comment | Ticket creator | Creator has an email address |
| Ticket creator adds a comment | Assigned employee | Ticket has an assigned employee with an email address |
| Any internal comment | — | No email sent, regardless of commenter |
| Creator comments on unassigned ticket | — | No recipient exists; no email sent |
| Recipient has no email address | — | Silently skipped |

---

## Changes

### 1. Email Backend Configuration

**Files changed:** `.env`, `ticketing_platform/settings.py`

The console email backend was chosen for development: emails are printed to the terminal rather than being sent over SMTP, making it safe and easy to verify during development. The backend and sender address are both read from `.env` via `python-decouple`, so a production deployment can switch to SMTP by updating only the environment file.

**.env additions:**
```
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@ticketdesk.local
```

**settings.py additions:**
```python
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@ticketdesk.local')
```

---

### 2. Email Helper Module

**File:** `tickets/emails.py` *(new)*

A single function `send_comment_notification(comment, ticket)` encapsulates all notification logic:

1. Returns immediately if `comment.is_internal` is `True`.
2. Determines the recipient: the assigned employee if the commenter is the creator, otherwise the ticket creator.
3. Returns without sending if the recipient is absent or has no email address.
4. Calls `django.core.mail.send_mail()` with a plain-text body containing the comment text, ticket title, and a link hint.
5. Catches any exception and logs it via the standard `tickets` logger — the view is never interrupted by a failed email.

Keeping this logic in a dedicated module (rather than inline in the view) makes it independently testable and straightforward to extend in future (e.g., HTML emails, per-user preferences).

---

### 3. View Integration

**File:** `tickets/views.py`

`send_comment_notification(comment, ticket)` is called in `ticket_detail` immediately after `messages.success(...)` and before `return redirect(...)` in the `add_comment` branch. This ensures:

- The comment and any attachments are fully saved before the email fires.
- The auto-status-change logic (`waiting_on_asker` → `in_progress`) runs first, so the email reflects the correct ticket state.
- A failed email send never prevents the redirect from completing.

---

### 4. Tests

**File:** `tickets/tests.py`

Five tests were added in a new `EmailNotificationTest` class, decorated with `@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')` to capture outbound mail in `mail.outbox` without sending anything real.

| Test | What it verifies |
|------|-----------------|
| `test_employee_public_comment_emails_ticket_creator` | Employee posts a public comment → creator receives one email |
| `test_creator_comment_emails_assigned_employee` | Creator posts a comment → assigned employee receives one email |
| `test_internal_comment_sends_no_email` | Employee posts an internal comment → `mail.outbox` is empty |
| `test_no_email_when_no_recipient` | Creator comments on an unassigned ticket → no email sent |
| `test_no_email_when_recipient_has_no_email` | Recipient has an empty email field → no email sent |

---

## Files Changed

| File | Type | Summary |
|------|------|---------|
| `.env` | Modified | Added `EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL` |
| `ticketing_platform/settings.py` | Modified | Reads email config via `decouple` |
| `tickets/emails.py` | New | `send_comment_notification()` function |
| `tickets/views.py` | Modified | Imports and calls `send_comment_notification` after comment save |
| `tickets/tests.py` | Modified | Added `EmailNotificationTest` (5 tests) |

---

## Test Results

```
Ran 74 tests in 101.156s

OK
```

All 74 tests pass (69 pre-existing + 5 new).

---

## Notes

- **Switching to SMTP in production:** Set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` in `.env` and add the relevant `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, and `EMAIL_HOST_PASSWORD` variables. No code changes are required.
- **Internal comments:** The guard on `comment.is_internal` is the first check in `send_comment_notification`, so internal notes can never leak to end-users regardless of how the function is called.
- **No email required at registration:** The `User.email` field is optional in Django. The notification function checks for a non-empty email before sending, so users without an email address are silently skipped.

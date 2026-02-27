# TicketDesk - Claude Code Guide

## Commands

```bash
py manage.py runserver      # Start dev server (use `py` not `python` on Windows)
py manage.py test tickets   # Run tests
py manage.py migrate        # Apply migrations
py seed_data.py             # Seed DB (clears existing data first)
```

## Architecture

**Stack**: Django 6.x, SQLite, Bootstrap 5, function-based views.

**Roles** (via `Profile.role`): `'user'` (default) or `'employee'` (admin-assigned only). Checked via `user.profile.is_employee`. Enforced by `@employee_required` in `tickets/decorators.py`.

**Models**: `Profile` (role), `Ticket` (UUID PK, status, priority, created_by, assigned_to), `Comment` (is_internal flag), `Attachment`.

**Key behaviours**:
- Internal comments (`is_internal=True`) filtered out from regular users at queryset level in `ticket_detail`
- When ticket creator comments on a `waiting_on_asker` ticket, status auto-changes to `in_progress`
- Email uniqueness validated case-insensitively in `RegistrationForm.clean_email()`
- Ticket list paginated at 20/page; filter params preserved in pagination links

## Key Files

| File | Purpose |
|------|---------|
| `tickets/models.py` | Profile, Ticket, Comment, Attachment |
| `tickets/views.py` | All function-based views |
| `tickets/forms.py` | Registration, Ticket, Comment forms |
| `tickets/decorators.py` | `@employee_required`, `@regular_user_required` |
| `tickets/middleware.py` | `RatelimitMiddleware` — converts `Ratelimited` exceptions to HTTP 429 |
| `tickets/tests.py` | All tests |
| `seed_data.py` | 48 tickets, 24 comments, 6 users |
| `.env` | Local environment config (not committed) |
| `SECURITY_REPORT.md` | Security audit findings and fixes |

## Security

- **Environment config**: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` are read from `.env` via `python-decouple`. Never hardcode these.
- **Rate limiting**: Login and register are limited to 5 requests/min per IP (`django-ratelimit`). Returns 429 on breach.
- **Production settings**: When `DEBUG=False`, HTTPS redirect, HSTS, and secure cookies activate automatically in `settings.py`.
- **ticket_assign_self**: Requires POST — GET returns 405. Templates use `<form method="post">` with `{% csrf_token %}`.
- **Register page**: Redirects authenticated users to dashboard.
- **Tests**: `cache.clear()` must be called in `setUp` of any test class that hits rate-limited endpoints.

## Git

Branch: `master` — Remote: `https://github.com/msallean-git/ticketing-platform.git`

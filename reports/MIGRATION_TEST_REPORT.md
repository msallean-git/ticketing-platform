# Migration Consistency Test Report

**Project:** TicketDesk
**Date:** 2026-02-27
**Branch:** `master` (`94dc3ad`)

---

## Overview

The Django migrations folder is a fragile point in any project — if a developer edits a model but forgets to run `makemigrations`, the database schema silently drifts from the codebase. This report documents the problem, the test added to catch it, and how it integrates with the existing test suite.

---

## Problem

Django tracks schema changes through migration files in `tickets/migrations/`. If a model field is added, removed, or altered without generating a corresponding migration, the following happens:

- The application code expects a column that does not exist in the database.
- `migrate` has nothing to apply, so no error is raised at deploy time.
- The mismatch only surfaces at runtime as a database error, potentially in production.

This failure mode is silent and easy to introduce — a developer runs `makemigrations` locally but forgets to commit the file, or edits a model directly without running the command at all.

**Current migration history:**

| File | Change |
|------|--------|
| `0001_initial.py` | Initial schema — Profile, Ticket, Comment |
| `0002_comment_is_internal.py` | Added `is_internal` flag to Comment |
| `0003_add_waiting_on_asker_status.py` | Added `waiting_on_asker` to Ticket status choices |
| `0004_attachment.py` | Added Attachment model |
| `0005_alter_comment_is_internal_alter_ticket_priority_and_more.py` | Field alterations |

---

## Fix

A `MigrationConsistencyTest` class was added to `tickets/tests.py`. It runs Django's `makemigrations --check --dry-run` command programmatically. This command:

- Inspects all registered models and compares them against the current migration state.
- Exits with a non-zero code if any unapplied model changes are detected.
- Makes no changes to the filesystem (`--dry-run`).

If the check fails, the test fails — blocking any CI pipeline or local test run from passing until the missing migration is generated and committed.

```python
class MigrationConsistencyTest(TestCase):
    """Ensure all model changes have a corresponding migration."""

    def test_no_missing_migrations(self):
        """Fail if any model changes have not been captured in a migration."""
        out = StringIO()
        call_command('makemigrations', '--check', '--dry-run', stdout=out, stderr=out)
```

---

## Files Changed

| File | Change |
|------|--------|
| `tickets/tests.py` | Added `MigrationConsistencyTest` class; added `StringIO` and `call_command` imports |

---

## Test Results

```
Ran 75 tests in 100.908s

OK
```

All 75 tests pass (74 pre-existing + 1 new).

---

## What This Catches

| Scenario | Before | After |
|----------|--------|-------|
| Model field added, migration not generated | Silent runtime DB error | Test fails immediately |
| Model field removed, migration not generated | Silent runtime DB error | Test fails immediately |
| Migration file edited after being committed | Detected by Django's hash check at `migrate` time | Unchanged — still detected |
| Migration committed without model change | N/A — no issue | N/A — no issue |

---

## Notes

- The test uses `call_command` rather than a subprocess so it runs inside the same Django test environment with no extra setup.
- `--dry-run` ensures the test never writes files, making it fully safe to run in any environment.
- This test complements, but does not replace, the practice of reviewing `makemigrations --dry-run` output before committing model changes.

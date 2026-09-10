# ACIS — Insurance Inspection & MIS Management System

A Django + PostgreSQL rebuild of the legacy PHP ACIS/MIS system.

## What's actually in this build

This is a **working foundation**, not the entire 40-section spec — see
"What's not here yet" below before you assume something exists. Everything
listed here is real code (models, migrations-ready, views, templates, API,
tests), not a mock.

**Implemented:**
- Custom `User` model + 8 roles seeded as Django Groups with real
  permissions (`seed_roles` command) — the "centralized permission system"
  the spec asks for, built on Django's own permission framework rather than
  a reinvented one.
- Login/logout, forced password change, password reset, login history,
  account lockout after 5 failed attempts, "log out of all sessions."
- Masters: states/districts/cities, vehicle type/make/model, fuel types,
  inspection/glass/accessory checklist items, condition options, video
  categories, statuses, payment modes — all soft-activate/deactivate, all
  admin-manageable.
- Insurers, Customers, Vehicles.
- **MIS**: sequential `MIS-YYYY-NNNN` numbering, the 4-step Create MIS
  wizard (dependent dropdowns included), list with search/filter, dashboard
  stats.
- **Inspections**: body checklist, glass, accessories, previous insurance,
  document verification, photo upload (validated + GPS/metadata fields),
  video upload (validated, Celery-ready async processing hook, secure
  time-limited access links for the QR-code-in-report use case), status
  timeline, duplicate-submission guard.
- **QC**: 4-decision review workflow, append-only decision history
  (corrections create a new row linked via `supersedes`, never overwrite).
- **Audit log**: automatic create/update/delete logging on every tracked
  model via a generic signal registration helper, plus explicit logging
  for uploads/downloads/QC decisions/exports. Read-only in `/admin/`.
- **REST API**: DRF viewsets + routers for every model above, session +
  token auth, `DjangoModelPermissions`, filtering/search/ordering,
  pagination, a consistent `{detail, code, fields}` error shape.
- A test suite covering auth/lockout, MIS numbering, the inspection
  accept→start→submit lifecycle, checklist upsert behaviour, QC decision
  history, and API-level object access control (a field executive can't
  see another's inspections).

## What's not here yet (and why)

These need business decisions or infrastructure this exercise doesn't
have, so they're deliberately stubbed rather than faked:

- **Billing** — `Payment`/`Invoice` models exist as placeholders; real
  invoicing/GST/gateway logic needs your actual billing rules.
- **PDF report generation** — `weasyprint` is in requirements and the
  video-evidence-with-QR-code design is documented in
  `apps/inspections/viewsets.py`, but the report template itself isn't
  built. This is a half-day task once you tell me your letterhead/layout.
- **Video transcoding/thumbnailing** — `apps/inspections/tasks.py` has the
  Celery task wired up with a clear `# TODO` for `ffmpeg-python`/
  `moviepy`; I didn't pick a transcoding approach for you.
- **Legacy PHP migration scripts** — needs your actual old database schema
  to write field-mapping/ETL scripts against; nothing to build without it.
- **CI/CD, staging config, monitoring** — infra decisions (which registry,
  which host) that are yours to make.
- Excel export is listed on the MIS list toolbar as a permission
  (`mis.export_mis_excel`) but the endpoint isn't wired — straightforward
  to add with `openpyxl` once you confirm the column set you want.

## I could not run this code

This was written in a sandboxed environment with no network access, so
`pip install` never ran and Django never actually started here. Every file
compiles (checked with `py_compile`) and every template `{% url %}` tag
was cross-checked against a real URL name, but **you should run the test
suite before trusting this in anything real**:

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env   # edit DATABASE_URL etc.
createdb acis           # or use docker-compose up db
python manage.py migrate
python manage.py seed_roles
python manage.py seed_masters
python manage.py createsuperuser
python manage.py runserver
```

Run the tests (SQLite, no Postgres needed for this):

```bash
pytest
```

If something doesn't import cleanly, it's most likely a small naming slip
— tell me the traceback and I'll fix it immediately.

## Architecture notes worth knowing before you extend this

- **Business logic lives in `services.py`**, not in views — `apps/mis/services.py`,
  `apps/inspections/services.py`, `apps/qc/services.py`. Views (both
  Django and DRF) call these. Keep new logic there so the web UI and the
  future Flutter app never diverge in behaviour.
- **Permissions**: roles are Django Groups (`seed_roles` management
  command). To change what a role can do, edit the `ROLE_PERMISSIONS` dict
  in `apps/accounts/management/commands/seed_roles.py` and re-run it — it's
  idempotent. Don't hardcode role checks in views; use
  `request.user.has_perm("app.codename")`.
- **Audit logging** is automatic for create/update/delete via
  `apps/audit/signals.register_audit_logging(Model, "module_name")`,
  called from each app's `AppConfig.ready()`. For actions that aren't a
  plain model save (exports, downloads, QC decisions), call
  `apps.audit.utils.log_action(...)` directly.
- **MIS numbering** (`MIS-YYYY-NNNN`) is race-safe under moderate
  concurrency via `select_for_update` in `apps/mis/services.create_mis`,
  but is not a true atomic sequence. Under high write volume, replace it
  with a Postgres sequence — the comment in that file explains exactly why.
- **File validation** sniffs real file content via `python-magic`, not
  just the extension or client-supplied `Content-Type` — see
  `apps/inspections/validators.py`.
- **Video access** never exposes a raw storage URL — every video link is
  either behind DRF's authenticated `stream`/`download` actions or a
  signed, 30-minute-expiring token (`apps/inspections/viewsets.py:secure_video_view`),
  which is what a QR code in a PDF report would point at.

## Suggested next steps, in order

1. Run it locally, run the tests, fix whatever doesn't import.
2. Build the PDF report template (I'll need your letterhead/branding and
   exact field layout).
3. Wire Excel export for the MIS list.
4. Pick a video transcoding approach and fill in `tasks.py`.
5. Billing rules once you have them.
6. The legacy PHP → PostgreSQL migration scripts, once I can see the old
   schema.

Tell me which of these to tackle next and I'll keep building in the same
style — real code, tests, and an honest note about what's still missing.

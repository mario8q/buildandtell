# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Build&Tell (branded "BuildLog" in the UI) is a Django platform where developers document
*what* they build and *how* they build it: projects, a timeline of "build updates", GitHub
commit sync, a social layer (stars, following), and an AI voice-call feature powered by
ElevenLabs.

Stack: Django 6.1, Python 3.13, PostgreSQL, Cloudinary (media), Whitenoise (static),
`social-auth-app-django` (Google + GitHub OAuth), `django-taggit`. Deployed to Render.

## Commands

All commands run from the inner `buildandtell/` dir (the one containing `manage.py`).

```bash
python manage.py runserver            # dev server
python manage.py migrate              # apply migrations
python manage.py makemigrations       # after model changes
python manage.py collectstatic --noinput
python manage.py check                # runs voice/checks.py system checks too

python manage.py test                 # all tests
python manage.py test voice           # one app
python manage.py test voice.tests.test_budget                         # one module
python manage.py test voice.tests.test_budget.BudgetTests.test_name   # one test
```

There is no lint/format tooling configured. `requirements.txt` is the only dependency manifest.

## Configuration — required before anything runs

Settings are read via `python-decouple` (`config(...)`) from environment or a `.env` file in
the inner `buildandtell/` dir. Several keys have **no default** and will raise on startup if
missing: `SECRET_KEY`, all `DB_*` (`DB_NAME/USER/PASSWORD/HOST/PORT`), and the OAuth keys
(`GOOGLE_OAUTH2_KEY/SECRET`, `AUTH_GITHUB_KEY/SECRET`). You cannot run `manage.py` (including
tests) without a working Postgres connection and these vars set.

`DEBUG` toggles major behavior, not just verbosity:
- **Storage**: DEBUG uses local filesystem + plain static files; non-DEBUG uses Cloudinary for
  media and Whitenoise compressed-manifest static.
- **Email**: DEBUG → console backend; otherwise SMTP.
- **debug_toolbar** is only installed/enabled under DEBUG.
- The `image_thumb` template tag (`projects/templatetags/image_tags.py`) returns the raw local
  URL under DEBUG and a Cloudinary transformation URL otherwise. Always render images through
  this tag, not `image.url` directly.

Note: a `db.sqlite3` file exists in the repo but is unused — `settings.py` hardcodes the
`postgresql` engine. Postgres is also required because `projects/views.py` uses
`django.contrib.postgres` full-text search (`SearchVector`, `StringAgg`).

## Architecture

Three apps under the `buildandtell` project package:

- **`account`** — `Profile` (1:1 with `auth.User`), holds bio, avatar, `projects_stars` (M2M),
  and `following` (self-referential, asymmetric). A `post_save` signal on `User`
  (`account/signals.py`, wired in `AccountConfig.ready`) auto-creates a `Profile` for every new
  user, so `request.user.profile` is assumed to always exist.
- **`projects`** — core domain. `Project` and `BuildUpdate` (the per-project timeline). Key
  behaviors:
  - `Project.save()` auto-generates a unique slug from the title.
  - GitHub sync (`projects/services.py`) pulls a repo's commits and upserts them as
    `BuildUpdate`s of type `GITHUB_COMMIT`. Idempotency comes from a conditional
    `UniqueConstraint(project, commit_sha)` plus `update_or_create` — re-syncing is safe.
  - `project_star` is a POST endpoint returning JSON; stars are denormalized onto
    `Project.stars` and mirrored in `Profile.projects_stars`.
- **`voice`** — AI phone-rep feature (ElevenLabs "agents"). Gated globally by
  `VOICE_CALLS_ENABLED`. Structure: `models.py` (`VoiceProfile`, `VoiceAgent`, `VoiceCall`,
  `VoiceUsage`) and a `services/` package:
  - `context.py` builds a text brief of a user's public projects/updates for the agent prompt.
  - `agents.py` / `elevenlabs.py` create/update ElevenLabs agents. Agents are only
    re-synced when a `context_hash` (prompt version + settings + context) changes — see
    `ensure_agent` and `build_agent_hash`.
  - `budget.py` enforces a **shared monthly minutes pool** (`VoiceUsage` per `YYYY-MM`) plus a
    per-user daily call cap, using a reserve → settle/release lifecycle with
    `select_for_update` row locks. `reserve_call` first sweeps stale reservations via
    `expire_stale_calls`.
  - `webhook.py` / `elevenlabs_webhook` view: ElevenLabs posts call outcomes; the signature is
    HMAC-verified (`ELEVENLABS_WEBHOOK_SECRET`) and `post_call_transcription` settles billing.
  - `checks.py` registers Django system checks warning if `VOICE_CALLS_ENABLED` is on but
    ElevenLabs config is incomplete.

URL layout (`buildandtell/urls.py`): `/` dashboard (projects app), `/account/`, `/projects/`,
`/voice/`, plus `/social-auth/` and Django's built-in auth under `/account/`. Each app namespaces
its URLs (`app_name`), so reverse with e.g. `projects:project_detail`, `voice:call_token`.

Tags: `django-taggit` with a custom parser `projects.tagutils.parse_tags`
(`TAGGIT_TAGS_FROM_STRING`).

## Deployment

`render.yaml` (repo root, one level above `manage.py`) defines the Render web service.
Build runs `pip install → collectstatic → migrate`; start is `gunicorn buildandtell.wsgi`.
Non-DEBUG settings enable SSL redirect, HSTS, secure cookies, and trust the
`X-Forwarded-Proto` header since Render terminates TLS at its proxy. Secrets are set in the
Render dashboard (`sync: false`).

## Frontend

A `frontend-design` skill lives at `.opencode/skills/frontend-design/` describing the intended
visual identity (minimal, corporate, technical, developer-oriented — "BuildLog"). Consult it
when building or changing UI. Templates are classic Django server-rendered templates under each
app's `templates/` dir.

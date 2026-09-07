# AGENTS.md

Django 6.1 project (Python 3.13). Freshly scaffolded: no custom apps, no tests, no requirements.txt.

## Layout (paths are nested)

- Repo root: this directory. Contains `venv/`, `.env`, `.gitignore`.
- Django project root: the nested `buildandtell/` subdirectory (holds `manage.py`, `db.sqlite3`, and the `buildandtell.settings` package).

Run all `manage.py` commands with `workdir` set to the nested `buildandtell/` folder, never the repo root.

## Commands

Use the repo venv's interpreter explicitly (don't rely on PATH python):

```
venv\Scripts\python.exe manage.py runserver
venv\Scripts\python.exe manage.py check
venv\Scripts\python.exe manage.py test
```

`manage.py` is at `buildandtell\manage.py`; project package is `buildandtell.settings`/`buildandtell.urls`. Only the venv has Django — there is no `requirements.txt`. New packages live only in `venv\` until one is created.

## Gotchas

- `.env` (Postgres creds: `DB_*`) is **not** loaded by `settings.py`. The active DB is SQLite (`buildandtell/db.sqlite3`). Wiring up Postgres requires editing `settings.py` (e.g. `os.environ`/dotenv), not just `.env`.
- `urls.py` only routes `/admin/`; `INSTALLED_APPS` has only Django defaults. New apps must be added to `INSTALLED_APPS` and `urls.py` by hand.
- Not a git repo — no `.git` anywhere, and `.gitignore` is empty. No commits or branch-based workflows available.
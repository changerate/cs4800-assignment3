# Assignment 3 — Paper View

*Cal Poly Pomona, Spring 2026*

Flask monolith for **browsing a shared catalog of academic papers** (titles, topic filters, abstract summaries). The UI is a Substack-style shell with a **left sidebar** (Home / Saved / Profile + interest filters) and a **vertically scrollable feed** of paper cards.

## Stack

- **Flask 3** with `create_app` (`backend/app/__init__.py`)
- **Flask-SQLAlchemy**, **Flask-Migrate**, **Marshmallow**
- **SQLite** locally (`sqlite:///./app.db` — run commands from **`backend/`**). Use **`DATABASE_URL`** in production for a hosted database
- **python-dotenv** — see `backend/.env.example`

## Local setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set SECRET_KEY for non-toy use
export FLASK_APP=wsgi:application
flask db upgrade
flask run --debug
```

Open http://127.0.0.1:5000 — the home feed loads **papers from the database**. Use sidebar pills to filter by **topic**. Populate the catalog via the developer load page at http://127.0.0.1:5000/load-from-api.

If you had an older database from a previous schema, delete `backend/app.db` and run `flask db upgrade` again.

### Routes

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Landing feed (`?topic=` optional) |
| GET | `/load-from-api` | Developer utility page for OpenAlex search + ingest |
| GET | `/saved`, `/profile` | Placeholder pages (same shell; no extra features in scope) |
| GET | `/api/v1/papers` | JSON feed (`topic`, `limit`, optional `sort`) |
| GET | `/api/v1/papers/topics` | Distinct topics |
| POST | `/login`, `/logout`, `/register` | Session auth (unchanged structure) |
| GET | `/me` | Current user (JSON) |

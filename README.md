# Assignment 3 — Campus Research

Flask monolith for **browsing a shared catalog of academic papers** (titles, topic filters, abstract summaries). The UI is a Substack-style shell with a **left sidebar** (Home / Saved / Profile + interest filters) and a **vertically scrollable feed** of paper cards.

## Stack

- **Flask 3** with `create_app` (`backend/app/__init__.py`)
- **Flask-SQLAlchemy**, **Flask-Migrate**, **Marshmallow**
- **SQLite** locally (`sqlite:///./app.db` — run commands from **`backend/`**). Use **`DATABASE_URL`** in production for a hosted database
- **python-dotenv** — see `backend/.env.example`
- **Gunicorn** in `requirements.txt` for EC2/systemd

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

Open http://127.0.0.1:5000 — the home feed loads **papers from the database**. Use sidebar pills to filter by **topic**. Populate the catalog via **Discover** at http://127.0.0.1:5000/discover or `GET /api/v1/papers/discover`.

If you had an older database from a previous schema, delete `backend/app.db` and run `flask db upgrade` again.

### Routes

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Landing feed (`?topic=` optional) |
| GET | `/discover` | OpenAlex search + ingest into the catalog |
| GET | `/saved`, `/profile` | Placeholder pages (same shell; no extra features in scope) |
| GET | `/api/v1/papers` | JSON feed (`topic`, `limit`, optional `sort`) |
| GET | `/api/v1/papers/discover` | OpenAlex discovery (`q`, filters, `sort`, `per_page`, `cursor`) |
| GET | `/api/v1/papers/topics` | Distinct topics |
| POST | `/login`, `/logout`, `/register` | Session auth (unchanged structure) |
| GET | `/me` | Current user (JSON) |

## EC2 / Actions

GitHub Actions (`.github/workflows/deploy.yml`) SSHs to the server, pulls, runs `pip install`, `flask db upgrade`, and restarts **`flaskapp`**. Use **Discover** (web or API) on the server if the catalog is empty after deploy.

Example systemd unit: `deploy/flaskapp.service.example`.

## Layout

```
backend/
  app/
    models/          # User, ResearchPaper
    schemas/
    api/v1/          # /api/v1/papers
    web/             # pages
    templates/       # Jinja + components/
    static/css/
  migrations/
  wsgi.py
```

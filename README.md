# Assignment 3 — Grid Social (Flask monolith)

Classic Flask app: **Jinja + static assets** for the browser, a **versioned JSON API** under `/api/v1`, **session cookies** for the UI, and **SQLAlchemy + Alembic** for persistence. GitHub Actions can deploy to **AWS EC2** and restart the **`flaskapp`** systemd unit.

## Stack

- **Flask 3** with an **application factory** (`create_app` in `backend/app/__init__.py`).
- **Flask-SQLAlchemy**, **Flask-Migrate**, **Marshmallow** / **marshmallow-sqlalchemy**.
- **SQLite** by default (`sqlite:///./app.db` → `app.db` next to the shell’s cwd; keep **`cd backend`** when developing). In production, set **`DATABASE_URL`** to your hosted database (PostgreSQL, MySQL, etc.) so data survives instance replacement.
- **python-dotenv** loads `backend/.env` (see `backend/.env.example`).
- **Gunicorn** is listed in `requirements.txt` for the EC2 service.

## Local setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # set SECRET_KEY for anything beyond quick local tries
export FLASK_APP=wsgi:application
flask db upgrade            # apply migrations
flask seed-vehicles         # idempotent: adds default vehicle rows if missing
flask run --debug
```

Open http://127.0.0.1:5000 — register, pick a vehicle, post to the grid, and watch **activity** + **feed** refresh via **polling** (no WebSockets).

### HTTP surface (basics)

| Area | Method | Path | Notes |
|------|--------|------|--------|
| UI | GET | `/` | `index.html` shell |
| Session | POST | `/login`, `/logout`, `/register` | JSON or form fields |
| Session | GET | `/me` | Current user + vehicle |
| Session | PUT | `/me/vehicle` | JSON `{ "vehicle_id": <int> \| null }` |
| API v1 | GET | `/api/v1/posts`, `/api/v1/posts/<id>` | Grid + detail (detail logs activity when signed in) |
| API v1 | POST | `/api/v1/posts` | Signed-in only |
| API v1 | GET | `/api/v1/activity` | Recent activity stream |
| API v1 | GET | `/api/v1/vehicles` | Vehicle picker data |

## EC2 + systemd

1. Clone the repo on the server (e.g. `/opt/grid-social`).
2. Create `backend/.venv`, install `requirements.txt`, copy `backend/.env` with **`SECRET_KEY`**, **`DATABASE_URL`** (cloud DB), and **`FLASK_CONFIG=production`**.
3. Run `flask db upgrade` and `flask seed-vehicles` from `backend/` with the venv activated.
4. Install a systemd unit named **`flaskapp`**. See `deploy/flaskapp.service.example` — adjust **`User`**, **`WorkingDirectory`**, and paths to match your server.
5. Put Nginx (or similar) in front of Gunicorn if you need TLS and static efficiency.

## GitHub Actions deploy

Workflow: `.github/workflows/deploy.yml` (SSH pull + `pip install` + `flask db upgrade` + `sudo systemctl restart flaskapp`).

Repository secrets (example names — align with your workflow):

- **`EC2_HOST`**, **`EC2_USER`**, **`EC2_SSH_KEY`**
- **`EC2_APP_PATH`** — directory that contains `backend/` after `git clone` (repository root on the server)

## Layout

```
backend/
  app/
    api/v1/          # Blueprint: /api/v1
    web/             # Blueprint: pages + session JSON routes
    models/
    schemas/
    templates/       # Jinja (main UI: index.html)
    static/css/      # Styles
  migrations/        # Alembic (committed)
  wsgi.py            # `application` for Gunicorn
```

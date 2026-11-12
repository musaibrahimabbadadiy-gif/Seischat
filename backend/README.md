# SeisChat backend

The backend is a FastAPI modular monolith. This phase adds the SQLAlchemy
database foundation for users and authentication sessions, with Alembic
migrations for PostgreSQL. Authentication routes and messaging are later phases.

## Folder structure

- `app/main.py` creates the FastAPI application and configures CORS.
- `app/core/config.py` loads environment-backed settings.
- `app/database/connection.py` creates the SQLAlchemy engine and request
  session dependency.
- `app/database/base.py` holds the declarative base.
- `app/models/` contains the user and authentication-session models. They are
  imported by `migrations/env.py` so Alembic can discover their tables.
- `app/api/routes/` contains the health route. Authentication and chat routes
  are not part of this database-model phase.
- `migrations/` contains Alembic configuration and versioned schema revisions.
- `tests/` contains tests that can run without a live PostgreSQL server.

The `User` and `Session` models describe database records only. They do not
implement password hashing or registration, login, and logout workflows.

## Local setup

From the repository root, open PowerShell and run:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env` is local-only and is ignored by Git. Set `DATABASE_URL` to a
PostgreSQL database you own locally. `FRONTEND_ORIGIN` must exactly match the
browser origin, which is `http://localhost:5173` for the current Vite setup.

## Run the API

```powershell
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/health`. A successful response is:

```json
{"status": "ok"}
```

The health endpoint reports only application availability; it does not expose
database credentials or infrastructure details.

## Database migrations

Set `DATABASE_URL` in the local `.env` file to a PostgreSQL database you own.
From `backend/`, apply the checked-in schema with:

```powershell
alembic upgrade head
```

The initial migration creates `users` and `sessions`. It does not create the
later-phase `messages` table. To create a future migration, run
`alembic revision --autogenerate -m "Describe the schema change"` and review
the generated revision before applying it. Use a separate test database for
migration experiments; do not downgrade a shared or production database.

## Run tests

```powershell
pytest
```

The model tests create a new in-memory SQLite database for each test and do
not use production data. PostgreSQL migration testing must use a separate
isolated PostgreSQL database.

`migrations/env.py` loads the same `DATABASE_URL` setting as the application
and imports the models into `Base.metadata`, which is how Alembic discovers
their tables.

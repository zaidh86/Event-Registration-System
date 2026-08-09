# Event Registration System

Backend REST API that lets organizers create and manage events and lets
attendees discover and register for them. Built with Django, Django REST
Framework, and PostgreSQL, authenticated with JWT.

Current state: Phase 1 (project setup, authentication, user management).
Event and registration endpoints arrive in later phases.

## Requirements

- Python 3.13
- PostgreSQL (a local server with a role that may create databases — the
  test runner creates a throwaway test database)

## Setup

1. Create and activate a virtual environment, then install dependencies:

   ```sh
   python3.13 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

2. Create the database and role (adjust to taste):

   ```sql
   CREATE ROLE event_registration WITH LOGIN CREATEDB;
   CREATE DATABASE event_registration OWNER event_registration;
   ```

3. Configure the environment:

   ```sh
   cp .env.example .env
   # edit .env — at minimum set a strong SECRET_KEY
   ```

4. Apply migrations and start the server:

   ```sh
   .venv/bin/python manage.py migrate
   .venv/bin/python manage.py runserver
   ```

## Environment variables

Settings are read from the environment, optionally loaded from a `.env`
file in the project root (see `.env.example`).

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `SECRET_KEY` | yes | — | Django cryptographic signing key |
| `DEBUG` | no | `False` | Debug mode; never enable in production |
| `ALLOWED_HOSTS` | in production | empty | Comma-separated allowed hosts |
| `DB_NAME` | no | `event_registration` | PostgreSQL database name |
| `DB_USER` | no | `event_registration` | PostgreSQL role |
| `DB_PASSWORD` | no | empty | PostgreSQL password |
| `DB_HOST` | no | `localhost` | PostgreSQL host |
| `DB_PORT` | no | `5432` | PostgreSQL port |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | no | `15` | Access token lifetime |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | no | `7` | Refresh token lifetime |
| `CORS_ALLOWED_ORIGINS` | for browser clients | empty | Comma-separated origin allowlist |
| `THROTTLE_ANON` | no | `100/minute` | Anonymous request rate limit |
| `THROTTLE_USER` | no | `1000/minute` | Authenticated request rate limit |
| `THROTTLE_AUTH` | no | `10/minute` | Rate limit for authentication endpoints |
| `LOG_LEVEL` | no | `INFO` | Root log level |

## API

All endpoints are versioned under `/api/v1/`. Authenticated requests send
`Authorization: Bearer <access token>`.

### Authentication

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/api/v1/auth/register/` | none | Create an account (`email`, `password`, `first_name`, `last_name`, `role` of `ORGANIZER` or `ATTENDEE`) |
| POST | `/api/v1/auth/login/` | none | Obtain an access/refresh token pair (`email`, `password`) |
| POST | `/api/v1/auth/refresh/` | none | Rotate a refresh token (`refresh`); the used token is blacklisted |
| POST | `/api/v1/auth/logout/` | none | Blacklist a refresh token (`refresh`) |
| POST | `/api/v1/auth/password/change/` | bearer | Change password (`current_password`, `new_password`); revokes all outstanding refresh tokens |

Login is case-insensitive on email. The role is fixed at registration and
cannot be changed afterwards. Password strength follows Django's standard
validators (minimum length 8, common/numeric/similarity checks).

### Users

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/api/v1/users/me/` | bearer | Current user's profile |
| PATCH | `/api/v1/users/me/` | bearer | Update `first_name` / `last_name`; `email` and `role` are read-only |

### Errors

Every error uses one envelope with a stable machine-readable code:

```json
{"error": {"code": "validation_error", "message": "The request contains invalid data.", "details": {"email": ["Enter a valid email address."]}}}
```

Status mapping: 400 validation, 401 unauthenticated, 403 forbidden,
404 missing or not visible, 405 method not allowed, 429 throttled.

## Running tests

```sh
SECRET_KEY=dev-check DEBUG=True .venv/bin/python manage.py test
```

The test runner creates and destroys its own database
(`test_event_registration`), so the configured PostgreSQL role needs the
`CREATEDB` privilege.

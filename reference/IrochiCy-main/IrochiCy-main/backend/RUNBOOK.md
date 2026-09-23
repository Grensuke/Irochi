# SIH26145 Backend — Developer Runbook

Complete step-by-step guide. No assumptions — every command is explicit.

---

## Prerequisites (install once)

| Tool | Download | Verify |
|------|----------|--------|
| **Docker Desktop** | [docker.com/products/docker-desktop](https://docker.com/products/docker-desktop) | Open it → system tray shows "Engine running" |
| **Python 3.11+** | [python.org](https://python.org) — **CHECK** "Add Python to PATH" during install | `python --version` |
| **Git** | [git-scm.com](https://git-scm.com) | `git --version` |

---

## First-Time Setup

### Step 1 — Start Docker Services

Open a terminal in the `infrastructure/` folder:

```bash
cd sih26145/infrastructure
```

Copy the env file and set your passwords:

```powershell
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

Edit `infrastructure/.env` — set `POSTGRES_PASSWORD` and `REDIS_PASSWORD`.

Start all services:

```bash
docker compose up -d
```

Wait ~30 seconds, then verify all are healthy:

```bash
docker compose ps
```

All three services should show "healthy" in the Status column.

---

### Step 2 — Set Up the Python Backend

Open a **NEW** terminal in the `backend/` folder:

```bash
cd sih26145/backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat

# Mac/Linux
source .venv/bin/activate
```

You should see `(.venv)` at the start of your terminal prompt.

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### Step 3 — Create Backend .env

```powershell
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

Edit `backend/.env` — fill in **every** value:

```ini
POSTGRES_USER=sih_user              # ← must match infrastructure/.env
POSTGRES_PASSWORD=<your password>   # ← must match infrastructure/.env
REDIS_PASSWORD=<your password>      # ← must match infrastructure/.env
JWT_SECRET_KEY=<64-char hex>        # ← generate with command below
INITIAL_ADMIN_PASSWORD=<choose>     # ← your admin account password
```

Generate `JWT_SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output into `.env`.

---

### Step 4 — Run Database Migrations

Virtual env must be active. Docker must be running.

```bash
alembic upgrade head
```

You should see:

```
Running upgrade  -> 0001, Initial schema: users, alerts, alert_status_history, audit_log
```

---

### Step 5 — Start FastAPI

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

On first startup you'll see:

```
initial_admin_created  username=admin
```

The API is now live at:

| URL | Description |
|-----|-------------|
| http://localhost:8000 | API root |
| http://localhost:8000/docs | Interactive API documentation (Swagger) |
| http://localhost:8000/redoc | ReDoc documentation |
| http://localhost:8000/health | Health check |
| http://localhost:8000/metrics | Prometheus metrics |

---

## Daily Development Workflow

```
Terminal 1 (infrastructure/):  docker compose up -d
                                (Skip if containers are already running)

Terminal 2 (backend/):         .venv\Scripts\Activate.ps1
                                uvicorn app.main:app --port 8000 --reload

Terminal 3 (root/):            npm run dev
```

Full stack is now running:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Redpanda Console | http://localhost:8080 |

---

## Running Tests

```bash
# All tests, verbose
pytest tests/ -v

# One file
pytest tests/test_auth.py -v

# Tests matching a name
pytest tests/ -k "test_login"

# With coverage
pytest tests/ --cov=app --cov-report=term-missing
```

> **Note:** Tests use a **separate database** (`sih26145_test`) and `fakeredis`.
> The test DB is created and migrated automatically by `conftest.py`.
> Docker must be running for tests (PostgreSQL is real; Redis is fake).

---

## Running the API Validator

FastAPI must be running first.

```bash
python scripts/validate_api.py --url http://localhost:8000
```

Output looks like:

```
  ✓ GET /health                 12ms
  ✓ POST /auth/login (bad)      5ms
  ✓ POST /auth/login (good)     45ms
  ...
  15/15 checks passed ✓
```

---

## Exporting the OpenAPI Schema

```bash
python scripts/export_openapi.py
```

This writes `openapi.json` to the backend root. Commit it to git whenever schemas change. The frontend's `api.ts` is typed against this file.

---

## Adding a New Database Migration

1. Edit models in `app/*/models.py`
2. Generate migration:
   ```bash
   alembic revision --autogenerate -m "describe_your_change"
   ```
3. Review the generated file in `alembic/versions/`
4. Apply it:
   ```bash
   alembic upgrade head
   ```

---

## Connecting the Phase 1 Frontend

In `sih26145/.env` or `sih26145/src/` config:

```ini
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_MOCK=false
```

---

## Key API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/login` | No | Login, get tokens |
| POST | `/auth/refresh` | No | Refresh access token |
| POST | `/auth/logout` | Yes | Logout (audit trail) |
| GET | `/users/me` | Yes | Current user profile |
| PATCH | `/users/me` | Yes | Update own profile |
| POST | `/users/me/password` | Yes | Change password |
| GET | `/users/` | Admin | List all users |
| POST | `/users/` | Admin | Create user |
| PATCH | `/users/{id}` | Admin | Update user |
| DELETE | `/users/{id}` | Admin | Deactivate user |
| GET | `/alerts/` | Yes | List alerts (filtered/paginated) |
| GET | `/alerts/{id}` | Yes | Get alert detail |
| PATCH | `/alerts/{id}/status` | Yes | Update alert status |
| GET | `/alerts/export/csv` | Yes | Export alerts as CSV |
| GET | `/dashboard/summary` | Yes | Dashboard aggregation (cached) |
| GET | `/dashboard/kpi` | Yes | Live KPI metrics |
| GET | `/dashboard/timeline` | Yes | 24-hour timeline |
| GET | `/dashboard/top-threats` | Yes | Top threat types |
| GET | `/dashboard/top-ips` | Yes | Top source IPs |
| GET | `/threats/` | Yes | All threat type stats |
| GET | `/threats/{type}` | Yes | Threat detail + confidence dist |
| WS | `/ws/alerts` | Token | Real-time alert stream |
| GET | `/health` | No | Service health |
| GET | `/metrics` | No | Prometheus metrics |

---

## Useful Docker Commands

```bash
docker compose ps            # Check service status and health
docker compose logs postgres # View PostgreSQL logs
docker compose logs redis    # View Redis logs
docker compose restart redis # Restart one service
docker compose down          # Stop all services (data preserved)
docker compose down -v       # Stop AND delete all data (full reset)
```

---

## Architecture

```
React Frontend (localhost:5173)
        │
        ▼
FastAPI Backend (localhost:8000)
   ├── PostgreSQL (localhost:5432) — persistent storage
   ├── Redis (localhost:6379) — caching, Pub/Sub, rate limiting
   └── Redpanda (localhost:9092) — event streaming
```

All services run on localhost via Docker Desktop.

---

## Troubleshooting

### "connection refused" on port 5432 / 6379 / 9092

Docker Desktop is not running. Open it, wait for "Engine running", then:

```bash
docker compose up -d
```

### "WRONGPASS" from Redis

`REDIS_PASSWORD` in `backend/.env` must **exactly** match `infrastructure/.env`.

### "password authentication failed" PostgreSQL

`POSTGRES_USER` and `POSTGRES_PASSWORD` must match between both `.env` files.

If you changed passwords after first run:

```bash
docker compose down -v
docker compose up -d
alembic upgrade head
```

### "NoBrokersAvailable" Redpanda

Redpanda takes ~20 seconds to be ready after `docker compose up`. Check:

```bash
docker compose ps redpanda
```

Must say "healthy".

### 401 on all API requests after login

`JWT_SECRET_KEY` may have changed. Clear browser `localStorage` and re-login.

### "Cannot import module" errors

Virtual env not activated. Run the Activate script first.

### "alembic: command not found"

Virtual env not activated, OR `pip install -r requirements.txt` not run yet.

### ".env file not found"

You forgot to copy `.env.example` to `.env`. See Step 3 above.
Make sure you're running `uvicorn` from inside the `backend/` directory.

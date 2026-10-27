# AGENTS.md — InvoiceHub on Base44

## What this is
A starter server-rendered invoicing app for freelancers: FastAPI + SQLAlchemy 2 + PostgreSQL, Jinja2 templates, vanilla CSS/JS (no frontend build step, no auth/multi-tenancy yet). Currency is a single constant, `CURRENCY` in `app/main.py` (currently "R").

## Running (dev sandbox)
- Start: `docker compose -f docker-compose.base44.yml up -d` — web entry is host port 3000.
- The `web` service is a plain `python:3.12-slim` image with the repo bind-mounted at `/srv`; dependencies install from `requirements.txt` at container start, so dependency changes only need `docker compose restart web`.
- Hot reload: `uvicorn --reload` with `WATCHFILES_FORCE_POLLING=true` (bind mounts don't reliably deliver inotify events). Edits appear in the preview without a rebuild.
- DB: `db` service, volume `invoicehub-db`, inline dev credentials in compose. Schema is created and demo data seeded on every boot via `app/seed.py::init_db()` (idempotent — it skips when clients already exist).
- No external-service secrets are needed. If one is added later, declare it in `.base44/environment.json` and list `/run/base44/app.env` as the LAST `env_file:` entry of the service — never put user-supplied keys under `environment:`.

## Verifying
- `curl -s http://localhost:3000/ | head -c 400` — dashboard HTML should render.
- `docker compose -f docker-compose.base44.yml ps` — `db` and `web` both healthy.
- Preview: dashboard stats render; create client → create invoice with 2+ line items → mark paid → delete.

## Tests
None yet. The sandbox host has no Python — run them inside the web container, e.g.:
`docker compose -f docker-compose.base44.yml exec -T web sh -lc "pip install -q pytest && pytest"`

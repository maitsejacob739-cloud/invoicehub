# invoicehub
"Simple invoicing SaaS for freelancers"

Starter app: FastAPI + SQLAlchemy 2 + PostgreSQL, server-rendered Jinja2 UI (dashboard, clients, invoices with line items, status tracking). No frontend build step.

## Running locally

```sh
docker compose -f docker-compose.base44.yml up -d
# app on http://localhost:3000
```

Schema and demo data are created automatically on first boot. Hot reload is enabled (uvicorn `--reload`).

Without Docker: `pip install -r requirements.txt`, set `DATABASE_URL` to a PostgreSQL database, then `uvicorn app.main:app --reload`.

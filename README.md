# TokoMate AI

TokoMate AI is a bilingual (Bahasa Indonesia/English) customer-support prototype for Indonesian SMEs. It answers routine questions from structured business data and hands sensitive cases to a human agent with an AI-generated summary.

The MVP includes:

- A responsive customer chat at `/chat`.
- An agent dashboard at `/dashboard`.
- JWT staff authentication with server-enforced `agent` and `admin` roles.
- Product search, stock, price, order, FAQ, and escalation tools.
- Deterministic safety rules for complaints, refunds, damaged products, and human requests.
- Local PostgreSQL persistence and Alembic migrations, with an optional Supabase override.
- Local Ollama inference using `qwen3:4b`.

## Architecture

```text
Next.js web (:3000) → FastAPI (:8000) → PostgreSQL (:5432)
                              ↓
                    Ollama on the host (:11434)
```

The API owns all database credentials and tool execution. The model never receives a database connection and cannot directly change arbitrary records.

## Access model

Customer chat remains public for the demo. Staff must sign in at `/login`; hiding dashboard links in the UI is not treated as security because FastAPI verifies the JWT and role again for every protected request.

| Capability | Public customer | Agent | Admin |
| --- | --- | --- | --- |
| Chat and resolve a conversation | Yes | Yes | Yes |
| View dashboard and escalations | No | Yes | Yes |
| Take over an escalation | No | Yes | Yes |
| Use the direct order diagnostic API | No | No | Yes |

Seeded local accounts:

- Agent: `agent@tokomate.local` / `DemoAgent123!`
- Admin: `admin@tokomate.local` / `DemoAdmin123!`

The credentials and JWT secret are configurable through `.env` and are intended only for the local assessment demo.

## Prerequisites

- Docker Desktop with Docker Compose
- Ollama 0.6+ running on the host
- `qwen3:4b` installed locally

```powershell
ollama pull qwen3:4b
ollama list
```

## Run with Docker

1. Optionally copy the environment template if you want to customize ports or credentials:

```powershell
Copy-Item .env.example .env
```

2. Start the stack:

```powershell
docker compose up --build
```

Docker Compose starts PostgreSQL, waits until it is healthy, then the API automatically applies migrations and idempotently seeds the demo data. Open:

- Customer chat: <http://localhost:3000/chat>
- Staff login: <http://localhost:3000/login>
- Agent dashboard: <http://localhost:3000/dashboard>
- API documentation: <http://localhost:8000/docs>
- Service health: <http://localhost:8000/api/health>

`OLLAMA_BASE_URL` defaults to `http://host.docker.internal:11434`, allowing the API container to use Ollama running on Windows.

PostgreSQL data is retained in the `postgres_data` Docker volume. A hosted database is not required for the local prototype.

## Run natively

Backend:

```powershell
docker compose up -d db
Set-Location apps/api
uv sync
$env:DATABASE_URL = "postgresql+psycopg://tokomate:tokomate_dev@localhost:5432/tokomate"
$env:OLLAMA_BASE_URL = "http://localhost:11434"
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload
```

Frontend, in a second terminal:

```powershell
Set-Location apps/web
npm install
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000"
npm run dev
```

When `DATABASE_URL` is unset, native backend commands default to the local PostgreSQL container shown above.

## Optional Supabase database

The application uses standard PostgreSQL through SQLAlchemy and does not depend on Supabase-specific features. To use Supabase later, set `DATABASE_URL` in `.env` to its session-pooler PostgreSQL URL with `sslmode=require`. URL-encode special characters in the password. No application-code changes are required.

## Demo scenarios

Use a fresh chat for each scenario:

1. `Adidas Samba hitam size 42 masih ada?`
   - Calls `check_product_stock`.
   - Returns 3 pairs at Rp1.499.000.
2. `ORD-192 saya sudah sampai mana?`
   - Calls `check_order_status`.
   - Returns Shipped, JNE, JNE123456, and 26 August 2026.
3. `Barang saya datang rusak dan saya sudah komplain dua kali. Saya mau refund.`
   - Creates a high-priority escalation.
   - Generates a summary in the background.
   - Appears in the agent dashboard and can be taken over.

Run the live API smoke script after starting the stack:

```powershell
Set-Location apps/api
uv run python scripts/live_smoke.py
```

## Verification

Backend:

```powershell
Set-Location apps/api
uv run ruff check .
uv run pytest
```

Frontend:

```powershell
Set-Location apps/web
npm run lint
npm test
npm run build
```

Playwright UI smoke test:

```powershell
Set-Location apps/web
npx playwright install chromium
npm run test:e2e
```

The Playwright UI test stubs the API boundary; backend acceptance tests separately verify the database tools, escalation summary, dashboard data, resolve behavior, and idempotent takeover.

## Safety and MVP boundaries

- Product, stock, price, order, and policy facts must come from backend tools.
- Refund eligibility is never decided by the AI.
- Chat closes after escalation, takeover, or customer-confirmed resolution.
- Dashboard and escalation endpoints require an authenticated `agent` or `admin` role.
- The direct order diagnostic endpoint is restricted to `admin`; customer order questions still go through the controlled AI tool.
- Demo JWTs are stored in browser local storage. Production SSO, HTTP-only session cookies, refresh-token rotation, and account administration remain outside this MVP.
- Agent replies, public deployment, omnichannel integrations, and vector RAG are outside this MVP.

# TokoMate AI

**Reliable bilingual AI customer support for Indonesian SMEs.**

TokoMate AI answers routine product, stock, pricing, order, and policy questions using verified business data. Sensitive cases are escalated to a human support agent with a priority, full transcript, and AI-generated handoff summary.

This repository is a working prototype for the WIZ.AI AI Builder Challenge: **Option 1 — UMKM Customer Service**.

## The problem

Indonesian SMEs often handle repetitive customer questions manually across messaging channels. Agents spend time checking stock, prices, delivery records, and store policies, while sensitive complaints can be missed or handled inconsistently.

TokoMate AI addresses this with a hybrid approach:

- AI understands natural Bahasa Indonesia and English.
- Business facts come from validated tools and database records, not model guesses.
- Deterministic rules escalate refunds, damaged products, payment disputes, missing orders, delays, repeated complaints, and requests for a human.
- Human agents receive the customer context without asking them to repeat the issue.

## What the prototype demonstrates

### Customer experience

- Bilingual customer chat with an ID/EN language selector.
- Product discovery, price, stock, order tracking, and store-policy assistance.
- Explicit not-found responses when business information cannot be verified.
- Localized escalation confirmation for sensitive cases.
- Customer-controlled “Issue resolved” action.

### Support operations

- Live dashboard with active, AI-resolved, and escalated conversation metrics.
- Priority and status filters with automatic polling.
- Escalation detail containing the complete transcript and AI summary.
- Transactional and idempotent human takeover.
- JWT authentication with server-enforced `agent` and `admin` roles.

### AI reliability

- Six repository-backed business tools.
- Typed tool arguments and structured results.
- Maximum of four tool-call rounds using the latest 30 messages.
- Persisted tool traces showing which source supplied each business fact.
- Server-side escalation rules and minimum priority enforcement.
- Failed summary generation is marked as failed instead of inventing content.

## Business impact

TokoMate AI is designed to:

- Reduce repetitive customer-service workload.
- Provide faster answers outside normal support hours.
- Let agents focus on complaints and cases requiring judgment.
- Reduce handling time by providing an immediate handoff summary.
- Improve consistency by grounding operational answers in business records.

**Illustrative scenario, not a measured production result:** for a seller receiving 500 conversations per day, if 60% are routine inquiries and each takes three minutes to handle manually, automation could redirect up to 15 agent-hours per day toward higher-value cases. Production impact should be validated through containment rate, response time, escalation accuracy, and agent handling time.

## Demo scenarios

Use a fresh conversation for each scenario.

| Scenario | Customer message | Expected behavior |
| --- | --- | --- |
| Product availability | `Adidas Samba hitam size 42 masih ada?` | Calls the stock tool and returns stock `3` at `Rp1.499.000`. |
| Order tracking | `ORD-192 saya sudah sampai mana?` | Calls the order tool and returns Shipped, JNE, `JNE123456`, and 26 August 2026. |
| Human escalation | `Barang saya datang rusak dan saya sudah komplain dua kali. Saya mau refund.` | Creates a high-priority ticket, generates a summary, and sends it to the support dashboard. |

Equivalent English prompts produce English responses. Unknown products, orders, or policies receive an explicit not-found response rather than invented business information.

## System architecture

![TokoMate AI system architecture](<assets/system architecture.png>)

The backend owns authentication, conversation state, database access, business-tool execution, and AI coordination. The AI model never receives database credentials or unrestricted database access.

## AI workflow

![TokoMate AI customer support workflow](<assets/ai workflow.png>)

The system checks deterministic escalation rules before normal AI processing. Routine requests use approved business tools to retrieve verified information. Sensitive requests create a ticket immediately and continue through a human-in-the-loop workflow.

## Access control

Customer chat is public for the local demo. Staff dashboard requests require a valid JWT, and every protected action is authorized again by the backend.

| Role | Access |
| --- | --- |
| Public customer | Customer chat and conversation resolution |
| Agent | Dashboard, escalation list and detail, human takeover |
| Admin | All agent capabilities plus the direct order diagnostic API |

Seeded local accounts:

- Agent: `agent@tokomate.local` / `DemoAgent123!`
- Admin: `admin@tokomate.local` / `DemoAdmin123!`

These credentials and the default JWT secret are intended only for the local assessment demo and can be replaced through environment variables.

## Technology stack

| Layer | Implementation |
| --- | --- |
| Web application | Next.js, React, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python, Pydantic |
| AI | Ollama with `qwen3:4b` and native tool calling |
| Data | PostgreSQL, SQLAlchemy, Alembic |
| Authentication | JWT, PBKDF2 password hashing, role-based authorization |
| Testing | Pytest, Vitest, Testing Library, Playwright |
| Local environment | Docker Compose |

## Quick start

### Prerequisites

- Docker Desktop with Docker Compose.
- Ollama 0.6 or newer running on the host.

Install the model:

```powershell
ollama pull qwen3:4b
ollama list
```

Start the complete application:

```powershell
docker compose up --build
```

Docker Compose starts PostgreSQL, waits until it is healthy, then automatically applies migrations and idempotently seeds the demo data.

Open:

- Customer chat: <http://localhost:3000/chat>
- Staff login: <http://localhost:3000/login>
- Agent dashboard: <http://localhost:3000/dashboard>
- API documentation: <http://localhost:8000/docs>
- Service health: <http://localhost:8000/api/health>

The API container connects to Ollama on the host through `host.docker.internal`. PostgreSQL data persists in the `postgres_data` Docker volume.

### Optional configuration

The application works with local demo defaults. To customize credentials, ports, the model, or the database connection, copy the environment template before startup:

```powershell
Copy-Item .env.example .env
```

On macOS or Linux:

```bash
cp .env.example .env
```

The application uses standard PostgreSQL and does not depend on provider-specific features. A hosted PostgreSQL or Supabase session-pooler URL can be supplied through `DATABASE_URL` without application-code changes.

<details>
<summary>Run the web and API applications natively</summary>

Start only PostgreSQL:

```powershell
docker compose up -d db
```

Backend:

```powershell
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

</details>

## Verification

Latest local verification:

- 19 backend tests passing.
- 3 frontend unit tests passing.
- 2 Playwright browser tests passing.
- Ruff, ESLint, Docker Compose validation, and the Next.js production build passing.

Backend checks:

```powershell
Set-Location apps/api
uv run ruff check .
uv run pytest
```

Frontend checks:

```powershell
Set-Location apps/web
npm run lint
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

Automated tests mock the AI or API boundary for deterministic results. To verify the three scenarios against the running model and application stack:

```powershell
Set-Location apps/api
uv run python scripts/live_smoke.py
```

## Project structure

```text
.
├── apps/
│   ├── api/       FastAPI application, migrations, seed data, and tests
│   └── web/       Customer chat, staff dashboard, and browser tests
├── assets/        Architecture and workflow diagrams
├── docker-compose.yml
└── TokoMate_AI_PRD.md
```

## MVP boundaries and production evolution

- The web chat represents the customer messaging channel. WhatsApp can be integrated by forwarding inbound webhooks into the same chat orchestration layer.
- Human takeover changes ownership and disables AI input; agent-to-customer messaging is outside this prototype.
- Demo JWTs are stored in browser local storage. Production should use SSO or HTTP-only sessions, refresh-token rotation, and account administration.
- Customer order ownership is not verified in the demo. Production should verify the authenticated customer or an order-specific credential before returning delivery information.
- AI summaries currently use an in-process background task. Production should use a durable job queue with monitoring and retries.
- Ollama runs as a single local inference service. Production capacity requires managed inference or a scalable model-serving layer.
- Public deployment, omnichannel delivery, analytics history, and vector retrieval remain outside the MVP.

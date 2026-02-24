# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

This is a **planning-stage project** — only architecture documentation exists. No implementation code has been written yet. The planned repository structure is defined in `architecture.md`.

## Planned Tech Stack

| Layer | Technology |
|---|---|
| LLM | Claude Sonnet (prod), Claude Haiku (dev/staging) |
| Agent Orchestration | LangGraph (StateGraph) |
| Backend | Python + FastAPI (port 8000) |
| Database | PostgreSQL 16 |
| Cache / Conversation State | Redis 7 |
| Document Storage | AWS S3 |
| OCR | Mistral OCR or AWS Textract |
| WhatsApp | Z-API (webhooks) |
| Email Fallback | SendGrid |
| Observability | LangSmith + Sentry |

## Planned Commands

Once implemented, development will use Docker Compose:

```bash
# Start all services (API, PostgreSQL, Redis, Scheduler)
docker compose up

# Run API only (with hot reload)
docker compose up api

# Run database migrations
docker compose exec api alembic upgrade head

# Run tests
docker compose exec api pytest tests/

# Run a single test
docker compose exec api pytest tests/unit/test_renewal_agent.py::test_evaluate_eligibility -v

# Run linting
docker compose exec api ruff check .
docker compose exec api mypy .
```

## System Architecture

Three LangGraph agents communicate via WhatsApp (Z-API webhooks) and a daily CRON scheduler:

```
WhatsApp webhook  ──►  FastAPI (POST /webhook/whatsapp)
CRON (08:00 BRT)  ──►  FastAPI (POST /scheduler/renewal-check)
                              │
                    Agente Orquestrador
                    (detects intent, routes, manages handoff)
                         │            │
               Agente Renovação    Agente Sinistros
               (renewal lifecycle) (FNOL → protocol → route)
                         │            │
              PolicyService / ClaimService / NotificationService
                         │            │
              PostgreSQL  Redis  AWS S3  Z-API  SendGrid
```

**Conversation state** lives in Redis (TTL 30 days) while active, then migrates to PostgreSQL on close.

## Language

All user-facing content must be in **Brazilian Portuguese (pt-BR)**:
- All agent prompts and system messages
- All WhatsApp messages sent to clients
- All error messages and notifications sent to brokers
- All log messages and comments in code are also preferred in pt-BR

Code identifiers (variable names, function names, class names) should be in English to follow Python conventions.

## Agent Design Patterns

All agents follow the same LangGraph pattern:

- **State schema** (`TypedDict`) defined per agent — see `OrchestratorState`, `RenewalState`, `ClaimsState` in `architecture.md`
- **Tools** are Pydantic-typed (`@tool` decorator) — never free-form text actions. Schema validation rejects malformed calls before any side effects.
- **Human-in-the-loop** by default: no irreversible action (policy emission, payment) executes without human approval. `emit_policy` tool is disabled in MVP.
- **Prompts** instruct agents to never identify as AI unless directly asked, never negotiate pricing, and never promise values outside confirmed quotes.

## Key Business Rules

**Renewal autonomy criteria** (all must be met for auto-flow):
- No claims in the policy period
- Payments up to date
- Premium variation ≤ 15% (`MAX_AUTO_PREMIUM_VARIATION`)
- Client is not VIP (annual premium < `VIP_PREMIUM_THRESHOLD`, default R$5000)

**Renewal follow-up schedule**: contact at 30d → 15d → 7d → 2d before expiry; escalate to broker after 3 unanswered attempts.

**Claims severity routing**:
- `simple` → auto-trigger assistance (`trigger_simple_assistance`)
- `complex` → escalate to adjuster (`escalate_to_adjuster`)
- `critical` → immediate manager alert + escalation

## Data Model Summary

Core tables: `clients`, `policies`, `claims`, `conversations`. Sensitive fields (CPF, financial data) are tokenized before entering LLM conversation history. Conversations retained 5 years (SUSEP compliance). Full schemas in `architecture.md` §2.2.4.

## Planned Directory Structure

```
agents/
  orchestrator/   graph.py, nodes.py, prompts.py
  renewal/        graph.py, nodes.py, tools.py, prompts.py
  claims/         graph.py, nodes.py, tools.py, fnol.py, prompts.py
services/         policy_service.py, claim_service.py, notification_service.py, scheduler_service.py
api/              main.py, routes/webhook.py, routes/scheduler.py, middleware/auth.py
models/           database.py (SQLAlchemy), schemas.py (Pydantic)
migrations/       Alembic
tests/            unit/, integration/, fixtures/
```

## Documentation

Every new feature implemented must have a corresponding documentation file created or updated:

- **Location:** `docs/<area>/<feature-name>.md` (e.g., `docs/agentes/renovacao-followup.md`)
- **Language:** Portuguese (pt-BR)
- **Required sections:**
  - **Objetivo** — what the feature does and why it exists
  - **Como funciona** — step-by-step description of the flow or logic
  - **Configuração** — any env vars, parameters, or flags involved
  - **Exemplos** — at least one concrete usage example (message flow, API call, etc.)
  - **Limitações conhecidas** — edge cases or intentional restrictions

Also update `project_status.md` to mark the related checklist item as completed whenever a feature is finished.

## Git & GitHub Practices

### Branches

Use the following naming pattern:

```
<type>/<short-description>
```

| Type | When to use |
|---|---|
| `feat/` | New feature or agent capability |
| `fix/` | Bug fix |
| `refactor/` | Code restructuring without behavior change |
| `docs/` | Documentation only |
| `test/` | Adding or fixing tests |
| `chore/` | Tooling, deps, CI changes |

Examples: `feat/renewal-followup-scheduler`, `fix/fnol-date-parsing`, `chore/docker-compose-redis`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(scope): <short description in pt-BR>

[optional body]
[optional footer]
```

- Subject line: imperative, lowercase, no period, max 72 chars
- Scope: the affected module (`orchestrator`, `renewal`, `claims`, `api`, `models`, etc.)
- Body: explain *why*, not *what* (the diff already shows what)

Examples:
```
feat(renewal): adicionar régua de follow-up por vencimento
fix(claims): corrigir extração de data no fluxo FNOL
refactor(orchestrator): separar nó de detecção de intenção
```

### Pull Requests

- One feature/fix per PR — keep scope small
- PR title follows the same Conventional Commits format as the commit subject
- PR description must include:
  - **Contexto**: why this change is needed
  - **O que mudou**: summary of changes
  - **Como testar**: steps to verify (manual or automated)
- Link the related issue with `Closes #<issue>`
- No merging with failing CI checks
- Prefer squash merge to keep `main` history linear

### Branch Protection (`main`)

- Direct pushes to `main` are not allowed
- All changes go through PRs with at least 1 approval
- CI must pass before merge

## Architecture Decision Records

Key ADRs (full rationale in `architecture.md` §6):

- **ADR-001**: LangGraph chosen over CrewAI for stateful, cyclic, multi-day conversation flows
- **ADR-002**: Claude Sonnet in production (best PT-BR performance + instruction-following)
- **ADR-003**: Redis for active conversation state (microsecond access + native TTL)
- **ADR-004**: Pydantic-typed tools only — no free-form function calling
- **ADR-005**: `emit_policy` blocked in MVP — broker emits manually after agent handoff

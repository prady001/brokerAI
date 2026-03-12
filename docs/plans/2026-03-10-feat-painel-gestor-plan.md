---
title: "feat: Painel do Gestor — visualização de clientes, apólices e status dos agentes"
type: feat
status: active
date: 2026-03-10
origin: docs/brainstorms/2026-03-10-painel-gestor-brainstorm.md
---

# feat: Painel do Gestor

## Enhancement Summary

**Aprofundado em:** 2026-03-10
**Agentes de pesquisa utilizados:** security-sentinel, architecture-strategist, performance-oracle, kieran-python-reviewer, kieran-typescript-reviewer, best-practices-researcher, code-simplicity-reviewer

### Correções críticas identificadas (vs. plano original)

1. **`python-jose` está abandonado (CVE-2024-33663)** → substituir por `PyJWT`
2. **Token JWT em `localStorage` é vulnerável a XSS** → usar cookie `httpOnly` via Route Handler BFF
3. **`middleware.ts` não pode acessar `localStorage`** (Edge Runtime) → ler cookie
4. **Comparação de senha sem `hmac.compare_digest`** → usar padrão já existente no projeto
5. **`scan_iter` é O(keyspace do Redis)** → substituir por Redis Sets ou contadores atômicos
6. **`date.today()` sem timezone** → `datetime.now(UTC).date()`
7. **Falta `ix_policies_status`** → criar migration `0002_dashboard_indexes`

---

## Overview

Painel web para o corretor visualizar sua base de clientes, apólices, renovações, sinistros e o status dos agentes de IA. Acesso via navegador com autenticação JWT + cookie `httpOnly`. Usuário único configurado via `.env`.

O painel não modifica dados — é exclusivamente leitura. Não altera nenhum agente existente.

---

## Arquitetura

```
Next.js 14 App Router (dashboard/)     FastAPI (porta 8000)
  /login          → POST /api/auth/login (Route Handler BFF)
                    → POST /auth/login   → seta cookie httpOnly
  /dashboard      → GET  /dashboard/summary
  /clients        → GET  /dashboard/clients
  /clients/[id]   → GET  /dashboard/clients/{id}/full  ← 1 request, tudo
  /agent-status   → GET  /dashboard/agent-status
```

**Convenção de routers (ADR):**

| Router | Proteção | Quem usa | Operações |
|---|---|---|---|
| `/admin/*` | `verify_internal_token` (Bearer estático) | Automações, scheduler | Leitura + escrita |
| `/dashboard/*` | `verify_dashboard_jwt` (JWT + cookie) | Corretor humano via browser | Somente leitura |
| `/auth/*` | Nenhuma | Qualquer | Emite JWT |

(ver brainstorm: docs/brainstorms/2026-03-10-painel-gestor-brainstorm.md)

---

## Parte 1 — Backend (FastAPI)

### 1.1 Dependências novas

```
PyJWT              # JWT — python-jose está ABANDONADO (CVE-2024-33663, inativo desde 2021)
passlib[bcrypt]    # hash de senha
```

> ⚠️ **Não usar `python-jose`** — última versão em 2021, CVE não corrigido. O FastAPI migrou
> sua documentação oficial para `PyJWT` em 2024 (PR #11589).

### 1.2 Settings (`models/config.py`)

```python
# Painel do Gestor — adicionar ao final de Settings
dashboard_username: str = "corretor"
dashboard_password_hash: str = ""    # bcrypt hash — NUNCA senha em texto
dashboard_jwt_secret: str = ""       # openssl rand -hex 32
dashboard_jwt_algorithm: str = "HS256"
dashboard_jwt_expire_minutes: int = 480  # 8h
```

**Gerar o hash da senha (rodar uma vez):**
```bash
python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('sua-senha'))"
```

> Campos em branco em `environment=production` devem fazer o app falhar na startup.

### 1.3 `.env.example`

```env
# --- Painel do Gestor ---
DASHBOARD_USERNAME=corretor
DASHBOARD_PASSWORD_HASH=$2b$12$...hash_bcrypt_aqui...
DASHBOARD_JWT_SECRET=  # gerar: openssl rand -hex 32
DASHBOARD_JWT_EXPIRE_MINUTES=480
```

### 1.4 Schemas novos (`models/schemas.py`)

**`ClaimResponse`** (não existe hoje):

```python
class ClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    policy_id: uuid.UUID | None
    client_id: uuid.UUID
    insurer_id: uuid.UUID | None
    type: str | None
    severity: str | None
    status: str
    description: str | None
    occurrence_date: datetime | None
    opened_at: datetime | None
    closed_at: datetime | None
```

**`DashboardSummary`:**

```python
class DashboardSummary(BaseModel):
    total_clients: int
    active_policies: int
    pending_renewals: int
    open_claims: int
    policies_expiring_30d: int
    policies_expiring_60d: int
    policies_expiring_90d: int
```

**`ClientFull`** — detalhe completo em 1 request:

```python
class ClientFull(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    cpf_cnpj: str | None
    phone_whatsapp: str | None
    email: str | None
    birth_date: date | None
    created_at: datetime | None
    policies: list[PolicyResponse]
    claims: list[ClaimResponse]
    renewals: list[RenewalResponse]
```

**`ActiveConversation`** (com TTL — permite distinguir ativas de esquecidas):

```python
class ActiveConversation(BaseModel):
    phone: str
    type: Literal["claim", "onboarding"]
    last_updated_at: datetime | None
    ttl_seconds: int  # TTL restante da chave no Redis

class AgentStatusResponse(BaseModel):
    active_claims: list[ActiveConversation]
    active_onboardings: list[ActiveConversation]
    total_active: int
```

### 1.5 Autenticação JWT (`api/middleware/auth.py`)

Adicionar após `verify_internal_token`:

```python
# api/middleware/auth.py — adicionar
import hmac
import jwt  # PyJWT
from jwt import InvalidTokenError
from datetime import timedelta, datetime, timezone
from passlib.context import CryptContext
from fastapi.security import APIKeyCookie

_UTC = timezone.utc
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Cookie httpOnly — inacessível ao JavaScript
_cookie_scheme = APIKeyCookie(name="access_token", auto_error=False)


def create_dashboard_token() -> str:
    expire = datetime.now(_UTC) + timedelta(minutes=settings.dashboard_jwt_expire_minutes)
    return jwt.encode(
        {
            "sub": settings.dashboard_username,
            "broker_id": "default",  # campo para futura expansão multi-tenant
            "exp": expire,
        },
        settings.dashboard_jwt_secret,
        algorithm=settings.dashboard_jwt_algorithm,
    )


async def verify_dashboard_jwt(
    token: str | None = Depends(_cookie_scheme),
) -> str:
    """Lê o JWT do cookie httpOnly. Retorna o username autenticado."""
    if not token:
        raise HTTPException(status_code=401, detail="Não autenticado")
    try:
        payload = jwt.decode(
            token,
            settings.dashboard_jwt_secret,
            algorithms=[settings.dashboard_jwt_algorithm],
        )
        username: str = payload["sub"]
        return username
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
```

> **Nota:** `_bearer = HTTPBearer(auto_error=False)` seria para Bearer header.
> Para cookie httpOnly, usar `APIKeyCookie` — o browser envia automaticamente,
> sem gerenciamento no JavaScript.

### 1.6 Rota de autenticação (`api/routes/auth.py`)

```python
# api/routes/auth.py
import hmac
from fastapi import APIRouter, HTTPException, Response
from passlib.context import CryptContext
from pydantic import BaseModel

from api.middleware.auth import create_dashboard_token
from models.config import settings

router = APIRouter()
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/login")
async def login(body: LoginRequest, response: Response) -> dict:
    # hmac.compare_digest para timing-safe (padrão já usado em auth.py:80)
    username_ok = hmac.compare_digest(body.username, settings.dashboard_username)
    password_ok = _pwd_context.verify(body.password, settings.dashboard_password_hash)

    if not (username_ok and password_ok):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = create_dashboard_token()
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,                                    # inacessível ao JS
        secure=(settings.environment == "production"),   # HTTPS apenas em prod
        samesite="lax",
        max_age=settings.dashboard_jwt_expire_minutes * 60,
    )
    return {"ok": True}


@router.post("/auth/logout")
async def logout(response: Response) -> dict:
    response.delete_cookie("access_token")
    return {"ok": True}
```

Registrar em `api/main.py`:
```python
from api.routes import auth
app.include_router(auth.router)
```

### 1.7 Router do painel (`api/routes/dashboard.py`)

```python
# api/routes/dashboard.py
import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Annotated
import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, scalar_subquery, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.middleware.auth import verify_dashboard_jwt
from models.config import settings
from models.database import Claim, Client, Policy, Renewal, get_db
from models.schemas import (
    AgentStatusResponse, ActiveConversation,
    ClaimResponse, ClientFull, ClientResponse,
    DashboardSummary, PolicyResponse, RenewalResponse,
)

router = APIRouter(
    prefix="/dashboard",
    dependencies=[Depends(verify_dashboard_jwt)],
)

_UTC = timezone.utc
DbSession = Annotated[AsyncSession, Depends(get_db)]
```

**Rotas:**

| Rota | Query params | Response model |
|---|---|---|
| `GET /dashboard/clients` | `skip`, `limit`, `search` | `list[ClientResponse]` |
| `GET /dashboard/clients/{id}/full` | — | `ClientFull` |
| `GET /dashboard/summary` | — | `DashboardSummary` |
| `GET /dashboard/agent-status` | — | `AgentStatusResponse` |

> ⚡ **`/clients/{id}/full`** retorna dados, apólices, sinistros e renovações em 1 request.
> Elimina 3 requests paralelos do frontend para montar a tela de detalhe.

**`GET /dashboard/summary`** — 1 roundtrip com scalar_subqueries:

```python
@router.get("/summary", response_model=DashboardSummary)
async def summary(db: DbSession) -> DashboardSummary:
    today = datetime.now(_UTC).date()  # UTC, não date.today() (timezone do SO)

    # 1 roundtrip via scalar_subqueries — não 5 roundtrips separados
    row = (await db.execute(
        select(
            func.count(Client.id).label("total_clients"),
            select(func.count()).where(Policy.status == "active")
                .scalar_subquery().label("active_policies"),
            select(func.count()).where(
                Policy.end_date.between(today, today + timedelta(days=30))
            ).scalar_subquery().label("policies_expiring_30d"),
            select(func.count()).where(
                Policy.end_date.between(today + timedelta(days=31), today + timedelta(days=60))
            ).scalar_subquery().label("policies_expiring_60d"),
            select(func.count()).where(
                Policy.end_date.between(today + timedelta(days=61), today + timedelta(days=90))
            ).scalar_subquery().label("policies_expiring_90d"),
            select(func.count()).where(
                Renewal.status.in_(["pending", "contacted"])
            ).scalar_subquery().label("pending_renewals"),
            select(func.count()).where(
                Claim.status.in_(["open", "in_progress", "waiting_insurer"])
            ).scalar_subquery().label("open_claims"),
        )
    )).one()

    return DashboardSummary(**row._mapping)
```

**`GET /dashboard/clients`** — busca com separação CPF vs. nome:

```python
@router.get("/clients", response_model=list[ClientResponse])
async def list_clients(
    db: DbSession,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
) -> list[Client]:
    query = select(Client)
    if search:
        # CPF: busca exata aproveita índice UNIQUE
        looks_like_cpf = search.replace(".", "").replace("-", "").isdigit()
        if looks_like_cpf:
            query = query.where(Client.cpf_cnpj == search)
        else:
            # Nome/telefone: usa índice GIN trigram (migration 0002)
            query = query.where(or_(
                Client.full_name.ilike(f"%{search}%"),
                Client.phone_whatsapp.ilike(f"%{search}%"),
            ))
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())
```

**`GET /dashboard/clients/{id}/full`** — carrega tudo com `selectinload`:

```python
@router.get("/clients/{client_id}/full", response_model=ClientFull)
async def get_client_full(client_id: uuid.UUID, db: DbSession) -> Client:
    result = await db.execute(
        select(Client)
        .where(Client.id == client_id)
        .options(
            selectinload(Client.policies),
            selectinload(Client.claims),
            selectinload(Client.renewals),
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client
```

**`GET /dashboard/agent-status`** — Redis Sets em vez de `scan_iter`:

```python
@router.get("/agent-status", response_model=AgentStatusResponse)
async def agent_status() -> AgentStatusResponse:
    redis = aioredis.from_url(settings.redis_url, decode_responses=True)

    # scan_iter é O(keyspace total) — para MVP, aceitável
    # Migrar para Redis Sets quando keyspace crescer (ver nota de performance)
    claim_keys = [k async for k in redis.scan_iter("claim_conversation:*")]
    onboarding_keys = [k async for k in redis.scan_iter("onboarding_conversation:*")]

    async def _build(keys: list[str], conv_type: str) -> list[ActiveConversation]:
        if not keys:
            return []
        pipe = redis.pipeline()
        for k in keys:
            pipe.get(k)
            pipe.ttl(k)
        results = await pipe.execute()
        conversations = []
        for i, key in enumerate(keys):
            raw = results[i * 2]
            ttl = results[i * 2 + 1]
            phone = key.split(":")[-1]
            last_updated = None
            if raw:
                try:
                    state = json.loads(raw)
                    msgs = state.get("messages", [])
                    if msgs:
                        last_updated = datetime.fromisoformat(msgs[-1].get("ts", ""))
                except (json.JSONDecodeError, ValueError):
                    pass
            conversations.append(ActiveConversation(
                phone=phone,
                type=conv_type,
                last_updated_at=last_updated,
                ttl_seconds=max(ttl, 0),
            ))
        return conversations

    claims, onboardings = await asyncio.gather(
        _build(claim_keys, "claim"),
        _build(onboarding_keys, "onboarding"),
    )
    return AgentStatusResponse(
        active_claims=claims,
        active_onboardings=onboardings,
        total_active=len(claims) + len(onboardings),
    )
```

> ⚠️ **Nota de performance:** `scan_iter` itera sobre todo o keyspace do Redis.
> Aceitável para MVP (<100 chaves). Quando o keyspace crescer, substituir por:
> `await redis.smembers("active_conversations:claim")` (requer Set atualizado ao salvar estado).

### 1.8 Migration de índices (`migrations/versions/0002_dashboard_indexes.py`)

```python
def upgrade() -> None:
    # Índice para busca por telefone (exato ou prefixo)
    op.create_index("ix_clients_phone", "clients", ["phone_whatsapp"])

    # Índice para filtro de apólices por status (faltando na 0001)
    op.create_index("ix_policies_status", "policies", ["status"])

    # Índice GIN trigram para busca por nome parcial
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX ix_clients_full_name_trgm "
        "ON clients USING gin (full_name gin_trgm_ops)"
    )

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_clients_full_name_trgm")
    op.drop_index("ix_policies_status", "policies")
    op.drop_index("ix_clients_phone", "clients")
```

### 1.9 CORS (`api/main.py`)

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev
    allow_credentials=True,   # necessário para cookies
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
```

---

## Parte 2 — Frontend (Next.js em `dashboard/`)

### 2.1 Estrutura de arquivos

```
dashboard/
  package.json
  next.config.ts            # FASTAPI_URL env
  tailwind.config.ts
  tsconfig.json
  .env.local
  src/
    app/
      layout.tsx
      page.tsx              # redirect → /dashboard
      api/
        auth/
          login/route.ts    # BFF: chama FastAPI, repassa Set-Cookie
          logout/route.ts   # limpa cookie
      login/
        page.tsx            # Client Component (formulário)
      dashboard/
        layout.tsx          # sidebar + header (pode ser Client Component)
        page.tsx            # Server Component
        loading.tsx         # skeleton automático (Suspense)
        error.tsx           # error boundary automático
      clients/
        page.tsx            # Server Component
        loading.tsx
        error.tsx
        [id]/
          page.tsx          # Server Component
          loading.tsx
    lib/
      api.ts                # fetch tipado para Server Components
      types.ts              # tipos espelho dos schemas Pydantic
    middleware.ts           # protege rotas — lê cookie (Edge compatible)
    components/
      StatCard.tsx
      ClientTable.tsx
      PolicyList.tsx
      ClaimList.tsx
      RenewalList.tsx
      ExpiryAlert.tsx
```

### 2.2 Tipos TypeScript (`src/lib/types.ts`)

> **Obrigatório:** Python `Decimal` serializa como string no JSON.
> `premium_amount` deve ser `string | null`, nunca `number`.

```typescript
// src/lib/types.ts — espelho dos schemas Pydantic do backend
export interface ClientResponse {
  id: string
  full_name: string
  cpf_cnpj: string | null
  phone_whatsapp: string | null
  email: string | null
  birth_date: string | null
  created_at: string
}

export interface PolicyResponse {
  id: string
  client_id: string
  insurer_id: string
  policy_number: string
  type: "auto" | "life" | "home" | "travel" | "business" | null
  status: "active" | "expired" | "cancelled"
  premium_amount: string | null  // Decimal Python → string JSON
  start_date: string | null
  end_date: string | null
}

export interface ClaimResponse {
  id: string
  policy_id: string | null
  client_id: string
  type: string | null
  severity: "simple" | "grave" | null
  status: "open" | "in_progress" | "waiting_insurer" | "escalated" | "closed"
  description: string | null
  occurrence_date: string | null
  opened_at: string | null
}

export interface RenewalResponse {
  id: string
  policy_id: string
  client_id: string
  expiry_date: string
  status: "pending" | "contacted" | "confirmed" | "refused" | "no_response" | "lost"
  contact_count: number
  last_contact_at: string | null
  client_intent: string | null
}

export interface ClientFull extends ClientResponse {
  policies: PolicyResponse[]
  claims: ClaimResponse[]
  renewals: RenewalResponse[]
}

export interface DashboardSummary {
  total_clients: number
  active_policies: number
  pending_renewals: number
  open_claims: number
  policies_expiring_30d: number
  policies_expiring_60d: number
  policies_expiring_90d: number
}
```

### 2.3 API helper (`src/lib/api.ts`)

Server Components leem o cookie e o encaminham ao FastAPI:

```typescript
import { cookies } from "next/headers"
import type { ClientFull, ClientResponse, DashboardSummary } from "./types"

const API = process.env.FASTAPI_URL ?? "http://localhost:8000"

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const cookieStore = await cookies()
  const token = cookieStore.get("access_token")?.value

  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Cookie: token ? `access_token=${token}` : "",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  })

  if (res.status === 401) throw new Error("UNAUTHORIZED")
  if (!res.ok) throw new Error(`API ${res.status} ${path}`)
  return res.json() as Promise<T>
}

export const api = {
  summary: () => apiFetch<DashboardSummary>("/dashboard/summary"),
  clients: (params?: { skip?: number; limit?: number; search?: string }) => {
    const qs = new URLSearchParams()
    if (params?.skip) qs.set("skip", String(params.skip))
    if (params?.limit) qs.set("limit", String(params.limit))
    if (params?.search) qs.set("search", params.search)
    return apiFetch<ClientResponse[]>(`/dashboard/clients?${qs}`)
  },
  clientFull: (id: string) => apiFetch<ClientFull>(`/dashboard/clients/${id}/full`),
}
```

### 2.4 Route Handler BFF — login (`src/app/api/auth/login/route.ts`)

```typescript
import { NextRequest, NextResponse } from "next/server"

const API = process.env.FASTAPI_URL ?? "http://localhost:8000"

export async function POST(req: NextRequest) {
  const body = await req.json()

  const upstream = await fetch(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })

  if (!upstream.ok) {
    const err = await upstream.json().catch(() => ({}))
    return NextResponse.json(err, { status: upstream.status })
  }

  // Repassa o Set-Cookie do FastAPI (cookie httpOnly) para o browser
  const res = NextResponse.json({ ok: true })
  const setCookie = upstream.headers.get("set-cookie")
  if (setCookie) res.headers.set("set-cookie", setCookie)
  return res
}
```

### 2.5 Middleware (`src/middleware.ts`)

```typescript
import { NextRequest, NextResponse } from "next/server"

export function middleware(req: NextRequest) {
  // Cookie httpOnly — disponível no Edge Runtime via req.cookies
  const token = req.cookies.get("access_token")
  const isLoginPage = req.nextUrl.pathname === "/login"

  if (!token && !isLoginPage) {
    return NextResponse.redirect(new URL("/login", req.url))
  }
  if (token && isLoginPage) {
    return NextResponse.redirect(new URL("/dashboard", req.url))
  }
  return NextResponse.next()
}

export const config = {
  matcher: ["/dashboard/:path*", "/clients/:path*", "/agent-status/:path*", "/login"],
}
```

### 2.6 Telas

**`/dashboard/page.tsx`** — Server Component:

```typescript
import { api } from "@/lib/api"

export default async function DashboardPage() {
  const summary = await api.summary()
  return (
    <main>
      <h1>Painel do Corretor</h1>
      {/* StatCards + listas de vencimento */}
    </main>
  )
}
```

**`/clients/page.tsx`** — paginação via URL (`searchParams`):

```typescript
export default async function ClientsPage({
  searchParams,
}: {
  searchParams: { skip?: string; search?: string }
}) {
  const skip = Number(searchParams.skip ?? 0)
  const clients = await api.clients({ skip, limit: 50, search: searchParams.search })
  // tabela + formulário de busca como Client Component separado
}
```

**Busca com debounce** no `ClientTable.tsx` (`"use client"`):
```typescript
"use client"
import { useRouter, useSearchParams } from "next/navigation"
import { useDeferredValue, useState } from "react"

// Atualiza URL como fonte de verdade (não useState)
// next/navigation.useRouter().push(`/clients?search=${term}`)
```

**`/clients/[id]/page.tsx`** — 1 request para tudo:

```typescript
export default async function ClientDetailPage({ params }: { params: { id: string } }) {
  const client = await api.clientFull(params.id)
  // client.policies, client.claims, client.renewals já disponíveis
}
```

### 2.7 `.env.local`

```env
FASTAPI_URL=http://localhost:8000
```

> `FASTAPI_URL` sem `NEXT_PUBLIC_` — usada apenas no servidor (Route Handlers + Server Components).
> Nunca exposta ao browser.

### 2.8 Inicialização

```bash
mkdir dashboard && cd dashboard
npx create-next-app@latest . --typescript --tailwind --app --src-dir --import-alias "@/*"
npm install  # instala dependências
```

---

## Acceptance Criteria

### Backend
- [ ] `POST /auth/login` seta cookie `httpOnly` para credenciais corretas, 401 para inválidas
- [ ] `POST /auth/logout` remove o cookie
- [ ] `GET /dashboard/summary` retorna 7 contadores em 1 roundtrip ao banco
- [ ] `GET /dashboard/clients?search=joao` filtra por nome (GIN), `search=123` por CPF (exato)
- [ ] `GET /dashboard/clients/{id}/full` retorna cliente + apólices + sinistros + renovações
- [ ] `GET /dashboard/agent-status` retorna TTL restante de cada conversa ativa
- [ ] Todas as rotas `/dashboard/*` retornam 401 sem cookie válido
- [ ] `ClaimResponse`, `ClientFull`, `DashboardSummary` adicionados ao `schemas.py`
- [ ] `DASHBOARD_USERNAME`, `DASHBOARD_PASSWORD_HASH`, `DASHBOARD_JWT_SECRET` no `.env.example`
- [ ] `PyJWT` e `passlib[bcrypt]` adicionados às dependências
- [ ] Migration `0002_dashboard_indexes` criada e testada
- [ ] CORS configurado para `http://localhost:3000` com `allow_credentials=True`

### Frontend
- [ ] `/login` autentica via Route Handler BFF, sem expor token ao JavaScript
- [ ] `middleware.ts` redireciona para `/login` lendo cookie (não `localStorage`)
- [ ] `/dashboard` exibe 7 métricas + badges de vencimento 30/60/90 dias
- [ ] `/clients` busca com debounce via URL `searchParams`, paginação server-side
- [ ] `/clients/[id]` exibe apólices, sinistros e renovações (1 request)
- [ ] `src/lib/types.ts` tem tipos para todos os responses, `premium_amount: string | null`
- [ ] `loading.tsx` e `error.tsx` por rota
- [ ] Interface em pt-BR
- [ ] `npm run build` sem erros de TypeScript

---

## Sequência de implementação recomendada

1. **Migration** — `0002_dashboard_indexes.py`
2. **Backend schemas** — `ClaimResponse`, `ClientFull`, `DashboardSummary`, `AgentStatusResponse` em `schemas.py`
3. **Backend config** — `dashboard_*` settings em `config.py` + `.env.example` + gerar hash
4. **Backend auth** — `verify_dashboard_jwt` + `create_dashboard_token` em `middleware/auth.py`
5. **Backend routes** — `api/routes/auth.py` + `api/routes/dashboard.py`
6. **Backend main** — registrar routers + CORS em `main.py`, reiniciar docker, testar via `/docs`
7. **Frontend setup** — `create-next-app` em `dashboard/`
8. **Frontend lib** — `lib/types.ts` + `lib/api.ts`
9. **Frontend auth** — Route Handlers BFF + `middleware.ts` + tela de login
10. **Frontend telas** — `/dashboard`, `/clients`, `/clients/[id]`

---

## Riscos e considerações

| Risco | Mitigação |
|---|---|
| `password_hash` em branco em produção | Validar na startup: se `environment=production` e `dashboard_password_hash == ""`, levantar erro |
| `scan_iter` crescendo com keyspace Redis | Aceitar no MVP; migrar para Redis Sets quando houver >5 agentes ativos simultaneamente |
| `selectinload` em `/clients/{id}/full` carregando muitos registros | Limitar via `limit=100` nos relacionamentos ou paginar sinistros/renovações se cliente tiver histórico longo |
| Cookie `secure` em desenvolvimento (HTTP) | `secure` só ativo em `production` — não quebra desenvolvimento local |
| CPF exibido no painel (LGPD) | Mascarar na camada de exibição: `xxx.xxx.xxx-xx` |
| `broker_id` hardcoded como "default" | Campo já no JWT payload — migração para multi-tenant é adicionar um campo no Settings |

---

## Fora do escopo

- Edição de dados pelo painel (só visualização)
- Múltiplos usuários / controle de acesso por papel
- Export PDF/Excel
- WebSocket (tempo real)
- Comissões (agente não implementado)
- Tela `/agent-status` com ações (apenas visualização no MVP)

---

## Sources

### Origin
- **Brainstorm:** [docs/brainstorms/2026-03-10-painel-gestor-brainstorm.md](../brainstorms/2026-03-10-painel-gestor-brainstorm.md)
  Decisões carregadas: stack Next.js, JWT corretor único, 4 telas essenciais, `/dashboard` separado do `/admin`

### Achados da pesquisa (agentes de revisão)
- `python-jose` abandonado → PyJWT: [FastAPI PR #11589](https://github.com/fastapi/fastapi/pull/11589)
- Cookie httpOnly BFF pattern: [Next.js Authentication Guide](https://nextjs.org/docs/app/guides/authentication)
- SQLAlchemy async scalar_subqueries para summary: [Leapcell — FastAPI + SQLAlchemy 2.0](https://leapcell.io/blog/building-high-performance-async-apis-with-fastapi-sqlalchemy-2-0-and-asyncpg)
- `scan_iter` O(keyspace) → Redis Sets: análise do `performance-oracle`
- `hmac.compare_digest` para timing-safe: padrão já em `api/middleware/auth.py:80`
- GIN trigram para busca por nome: `performance-oracle` + pg_trgm

### Referências internas
- `api/routes/admin.py:23` — padrão de router com `dependencies=[Depends(...)]`
- `api/middleware/auth.py:80` — `hmac.compare_digest` (padrão de referência)
- `models/database.py:113–135` — campos de Claim
- `models/database.py:138–160` — campos de Renewal
- `agents/orchestrator/nodes.py:34–39` — padrão de keys do Redis

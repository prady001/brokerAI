# Architecture — Solução de Agentes de IA para Corretora de Seguros

> **Versão:** 2.0
> **Data:** Fevereiro de 2026
> **Audiência:** Desenvolvedores e Tech Leads

---

## Índice

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Diagrama de Componentes](#2-diagrama-de-componentes)
3. [Design dos Agentes](#3-design-dos-agentes)
   - 3.1 Agente de Comissionamento
   - 3.2 Agente de Sinistros
   - 3.3 Agente Orquestrador
4. [Fluxos Detalhados](#4-fluxos-detalhados)
   - 4.1 Fluxo de Comissionamento
   - 4.2 Fluxo de Sinistros
5. [Infraestrutura e Deploy](#5-infraestrutura-e-deploy)
6. [Decisões de Arquitetura (ADRs)](#6-decisões-de-arquitetura-adrs)

---

## 1. Visão Geral do Sistema

O sistema é composto por **dois agentes de IA independentes** orquestrados via LangGraph:

- **Agente de Comissionamento:** acionado por CRON diariamente às 08:00 BRT. Acessa portais de seguradoras (via API REST ou automação Playwright), extrai dados de comissão, emite NFS-e via Focus NFe API e envia resumo consolidado para a corretora via WhatsApp.

- **Agente de Sinistros:** acionado por webhook WhatsApp. Recebe o cliente, coleta dados básicos do sinistro, abre o chamado na seguradora pelo canal adequado (API ou WhatsApp da seguradora) e faz o relay das atualizações até o encerramento. Sinistros graves são escalados imediatamente para humano.

### Princípios arquiteturais

- **Stateful conversations:** estado de sinistros persistido em Redis durante o atendimento, migrado para PostgreSQL ao encerrar.
- **Human-in-the-loop by default:** sinistros graves e exceções no comissionamento sempre passam pelo corretor humano.
- **Tools over free-form:** agentes executam ações via tools Pydantic tipadas — sem texto livre interpretado.
- **Observabilidade total:** todas as chamadas LLM e ações de tools são rastreadas via LangSmith.
- **Segurança de credenciais:** credenciais de portais de seguradoras armazenadas em arquivo JSON criptografado (AES-256), nunca em variáveis de ambiente diretas.

---

## 2. Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CANAIS DE ENTRADA                          │
│                                                                     │
│   CRON Scheduler (08:00 BRT)        WhatsApp Business API (Z-API)  │
└──────────────┬──────────────────────────────────┬───────────────────┘
               │ trigger                          │ HTTP POST webhook
┌──────────────▼──────────────────────────────────▼───────────────────┐
│                         API GATEWAY                                  │
│                     FastAPI — porta 8000                             │
│                                                                     │
│  POST /scheduler/commission-check    POST /webhook/whatsapp         │
└──────────────┬──────────────────────────────────┬───────────────────┘
               │                                  │
┌──────────────▼──────────────┐  ┌────────────────▼──────────────────┐
│   AGENTE DE COMISSIONAMENTO  │  │         AGENTE ORQUESTRADOR        │
│   (LangGraph — StateGraph)   │  │       (LangGraph — StateGraph)     │
│                             │  │                                   │
│  1. Para cada seguradora:   │  │  1. Detecta intenção da mensagem  │
│     · Acessa portal         │  │  2. Carrega estado (Redis)        │
│     · Resolve 2FA           │  │  3. Roteia para agente correto    │
│     · Extrai comissões      │  │  4. Gerencia handoff humano       │
│  2. Consolida relatório     │  └──────────────────┬────────────────┘
│  3. Emite NFS-e             │                     │
│  4. Notifica corretora      │  ┌──────────────────▼────────────────┐
└──────────────┬──────────────┘  │       AGENTE DE SINISTROS         │
               │                 │     (LangGraph subgraph)          │
               │                 │                                   │
               │                 │  1. Coleta dados do sinistro      │
               │                 │  2. Classifica severidade         │
               │                 │  3. Simples → relay com seguradora│
               │                 │  4. Grave → escala para humano    │
               │                 └──────────────────┬────────────────┘
               │                                    │
┌──────────────▼────────────────────────────────────▼────────────────┐
│                         SERVIÇOS INTERNOS                           │
│                                                                     │
│  CommissionService  NfseService  InsurerPortalService               │
│  ClaimService       NotificationService  PolicyService              │
└──────────┬──────────────┬──────────────────────────────────────────┘
           │              │
┌──────────▼──┐  ┌────────▼──────┐  ┌──────────────────────────────┐
│ PostgreSQL  │  │     Redis      │  │  Externos                    │
│ (dados      │  │  (estado de    │  │  · AWS S3 (docs/fotos)       │
│  primários) │  │  conversas)    │  │  · Z-API (WhatsApp send)     │
└─────────────┘  └───────────────┘  │  · Focus NFe API (NFS-e)     │
                                     │  · Portais seguradoras        │
                                     │  · SendGrid (e-mail fallback) │
                                     └──────────────────────────────┘
```

---

## 3. Design dos Agentes

### 3.1 Agente de Comissionamento

**Responsabilidade:** ciclo completo de baixa de comissão — acesso aos portais, extração, consolidação, emissão de NFS-e e notificação da corretora.

**State Schema (LangGraph):**

```python
class CommissioningState(TypedDict):
    run_date: str                        # data de execução (YYYY-MM-DD)
    insurers_pending: list[str]          # seguradoras ainda não processadas
    insurers_done: list[str]             # seguradoras processadas com sucesso
    insurers_failed: list[str]           # seguradoras com falha de acesso
    commissions: list[dict]              # comissões extraídas no ciclo
    nfse_emitted: list[dict]             # NFS-e emitidas com sucesso
    nfse_failed: list[dict]              # NFS-e com falha de emissão
    report_sent: bool                    # resumo enviado à corretora
    errors: list[dict]                   # erros detalhados para debug
```

**Tools:**

```python
@tool
def fetch_commission_data(insurer_id: str) -> dict:
    """
    Acessa o portal da seguradora e extrai dados de comissão disponíveis.
    Usa InsurerPortalService que seleciona automaticamente API ou RPA.
    Retorna: { insurer: str, commissions: list[dict], extracted_at: datetime }
    """

@tool
def handle_2fa(insurer_id: str, method: str) -> bool:
    """
    Resolve autenticação 2FA para o portal da seguradora.
    method: 'totp' | 'email' | 'sms'
    Para TOTP: usa pyotp com chave secreta armazenada no config.
    Para email/SMS: aguarda código via IMAP ou gateway SMS.
    """

@tool
def consolidate_report(commissions: list[dict]) -> dict:
    """
    Agrupa comissões de todas as seguradoras em relatório único.
    Retorna: { total: Decimal, by_insurer: list[dict], date: str }
    """

@tool
def emit_nfse(commission: dict) -> dict:
    """
    Emite NFS-e via Focus NFe API para uma comissão.
    Retorna: { nfse_number: str, pdf_url: str, status: str }
    """

@tool
def send_daily_summary(report: dict, nfse_results: list[dict]) -> bool:
    """
    Envia resumo consolidado do dia via WhatsApp para a corretora.
    Inclui: total de comissões, NFS-e emitidas, alertas de falha.
    """

@tool
def alert_missing_commission(insurer_id: str, reason: str) -> bool:
    """
    Notifica corretora sobre seguradora sem dados ou com erro de acesso.
    """
```

**System Prompt do Agente:**

```
Você é o agente de comissionamento da [Nome da Corretora].
Sua tarefa é processar as comissões do dia de forma autônoma e organizada.

COMPORTAMENTO:
- Processe cada seguradora na ordem da lista. Não pule nenhuma sem registrar o motivo.
- Em caso de erro de acesso, registre o erro e continue para a próxima seguradora.
- Nunca tente adivinhar valores de comissão — use apenas os dados extraídos.
- Emita uma NFS-e por seguradora, não uma nota global.
- O resumo final deve ser claro e direto: total recebido, NFS-e emitidas, pendências.

AÇÕES PROIBIDAS:
- Não acesse portais fora da lista de seguradoras configuradas.
- Não emita NFS-e sem ter os dados de comissão confirmados.
- Não envie o resumo antes de processar todas as seguradoras.
```

---

### 3.2 Agente de Sinistros

**Responsabilidade:** intermediar o sinistro entre cliente e seguradora via WhatsApp. O agente não regula o sinistro — ele faz o relay de forma organizada e escalada quando necessário.

**State Schema (LangGraph):**

```python
class ClaimsState(TypedDict):
    conversation_id: str
    client_id: str
    client_phone: str
    policy_id: str                       # identificado pela placa ou número
    claim_id: str
    claim_type: str                      # tipo do sinistro
    severity: str                        # "simple" | "grave"
    claim_info: dict                     # dados coletados do cliente
    insurer_channel: str                 # canal usado com a seguradora
    insurer_thread_id: str               # ID do chamado na seguradora
    status: str                          # status atual do caso
    messages: list[dict]                 # histórico completo
    escalated: bool                      # se foi escalado para humano
    closed: bool
```

**Tools:**

```python
@tool
def classify_claim(claim_type: str, description: str) -> dict:
    """
    Classifica o sinistro em simples ou grave.
    Simples: guincho, pane, troca de pneu, vidros, pequenos danos.
    Grave: colisão com terceiros, furto/roubo, incêndio, acidente com vítima.
    Retorna: { severity: 'simple' | 'grave', auto_resolve: bool }
    """

@tool
def collect_claim_info(conversation_id: str) -> dict:
    """
    Coleta dados mínimos necessários: tipo, localização, placa/apólice.
    Retorna os dados coletados estruturados.
    """

@tool
def open_claim_at_insurer(claim_id: str, insurer_id: str, claim_info: dict) -> dict:
    """
    Abre chamado na seguradora via canal configurado (API ou WhatsApp relay).
    Retorna: { thread_id: str, channel: str, opened_at: datetime }
    """

@tool
def relay_update_to_client(conversation_id: str, update: str) -> bool:
    """
    Repassa resposta ou atualização da seguradora ao cliente via WhatsApp.
    """

@tool
def escalate_to_broker(claim_id: str, reason: str, summary: dict) -> bool:
    """
    Notifica corretor humano com resumo estruturado do sinistro.
    summary: { client, policy, claim_type, description, timeline }
    """

@tool
def store_claim_history(claim_id: str) -> bool:
    """
    Persiste histórico completo da conversa no PostgreSQL ao encerrar.
    """
```

**System Prompt do Agente:**

```
Você é o assistente de sinistros da [Nome da Corretora].
Seu papel é ajudar o cliente a acionar o seguro de forma rápida e tranquila.

COMPORTAMENTO:
- Seja empático. Clientes em sinistro geralmente estão estressados.
- Colete as informações necessárias de forma natural, não como um formulário.
- Para guincho e assistência: agilidade é prioridade — colete o mínimo e acione.
- Para casos graves: seja claro que um corretor especializado vai assumir o caso.
- Mantenha o cliente informado a cada atualização recebida da seguradora.
- Nunca prometa prazos ou valores que não foram confirmados pela seguradora.

AÇÕES PROIBIDAS:
- Não tente resolver sinistros graves sem escalar para humano.
- Não prometa indenizações ou coberturas sem confirmação da seguradora.
- Não identifique-se como IA a menos que o cliente pergunte diretamente.
```

---

### 3.3 Agente Orquestrador

**Responsabilidade:** porta de entrada das mensagens WhatsApp. Detecta a intenção e roteia para o Agente de Sinistros ou para humano. No MVP, o único agente ativo no canal WhatsApp é o de sinistros.

**State Schema (LangGraph):**

```python
class OrchestratorState(TypedDict):
    conversation_id: str
    client_id: str
    client_phone: str
    message: str
    message_history: list[dict]
    intent: str                          # "claim" | "faq" | "unknown"
    active_agent: str
    handoff_requested: bool
    handoff_reason: str
```

**Grafo de roteamento:**

```python
graph = StateGraph(OrchestratorState)

graph.add_node("detect_intent", detect_intent_node)
graph.add_node("claims_agent",  claims_subgraph)
graph.add_node("faq_handler",   faq_handler_node)
graph.add_node("human_handoff", human_handoff_node)

graph.set_entry_point("detect_intent")

graph.add_conditional_edges("detect_intent", route_by_intent, {
    "claim":    "claims_agent",
    "faq":      "faq_handler",
    "unknown":  "human_handoff",
})
```

**Prompt de detecção de intenção:**

```
Você é o orquestrador de atendimento de uma corretora de seguros.
Analise a mensagem do cliente e classifique:

- "claim"   → sinistro, acidente, roubo, dano, guincho, pane, vidro quebrado
- "faq"     → dúvida geral sobre cobertura, vencimento, boleto, documentos
- "unknown" → não identificado, reclamação, ou fora do escopo

Retorne apenas o JSON: {"intent": "<categoria>", "confidence": <0.0-1.0>}

Mensagem: {message}
```

---

## 4. Fluxos Detalhados

### 4.1 Fluxo de Comissionamento

```
CRON dispara às 08:00 BRT
        │
        ▼
Carrega lista de seguradoras configuradas
        │
        ├─── Para cada seguradora:
        │
        ▼
fetch_commission_data(insurer_id)
        │
        ├── Tem API REST? ──► chama API com OAuth token
        │
        └── Sem API? ──────► Playwright abre portal em modo headless
                                    │
                              Exige 2FA?
                                    ├── TOTP → pyotp.now()
                                    ├── E-mail → IMAP lê código
                                    └── SMS → gateway lê código
                                    │
                              Extrai dados de comissão
                                    │
                              handle_2fa + store → PostgreSQL
        │
        ▼ (após todas as seguradoras)
consolidate_report(commissions)
        │
        ▼
Para cada comissão confirmada:
emit_nfse(commission)  ──►  Focus NFe API  ──►  NFS-e emitida
        │
        ▼
send_daily_summary(report, nfse_results)  ──►  WhatsApp corretora
        │
        ▼
Registra alertas para seguradoras com falha
```

### 4.2 Fluxo de Sinistros

```
Cliente manda mensagem no WhatsApp
              │
              ▼
    Orquestrador detecta intent = "claim"
              │
              ▼
    collect_claim_info
    (tipo, localização, placa/apólice)
              │
              ▼
    classify_claim(claim_type, description)
              │
              ├── severity = "grave" ──────────────────────────────┐
              │                                                      │
              └── severity = "simple"                               │
                        │                                           ▼
                        ▼                              escalate_to_broker
              open_claim_at_insurer                    (resumo estruturado)
                        │                                           │
                  aguarda resposta                    Cliente recebe aviso
                  da seguradora                       que corretor assumiu
                  (estado em Redis)                              │
                        │                                    Humano atende
                        ▼
              relay_update_to_client
              (repassa resposta ao cliente)
                        │
                  caso encerrado? ──► não ──► aguarda
                        │
                        ▼ (sim)
              store_claim_history (PostgreSQL)
```

---

## 5. Infraestrutura e Deploy

### Ambientes

| Ambiente | Finalidade | Banco | LLM |
|---|---|---|---|
| `development` | Desenvolvimento local | PostgreSQL local | Claude Haiku (custo baixo) |
| `staging` | Testes de integração + QA | PostgreSQL staging | Claude Sonnet |
| `production` | Operação real | PostgreSQL RDS | Claude Sonnet |

### Estrutura de Repositório

```
brokerAI/
├── agents/
│   ├── commissioning/
│   │   ├── graph.py              # StateGraph do agente de comissionamento
│   │   ├── nodes.py              # Nós: fetch, consolidate, emit, notify
│   │   ├── tools.py              # Tools: fetch_commission_data, handle_2fa, emit_nfse...
│   │   ├── prompts.py            # System prompt do agente
│   │   └── portal_adapters/
│   │       ├── base.py           # Classe abstrata InsurerAdapter
│   │       ├── api_adapter.py    # Adapter para seguradoras com API REST
│   │       └── rpa_adapter.py    # Adapter Playwright para portais sem API
│   ├── claims/
│   │   ├── graph.py              # Subgraph do agente de sinistros
│   │   ├── nodes.py              # Nós: collect, classify, relay, escalate
│   │   ├── tools.py              # Tools: classify_claim, open_claim_at_insurer...
│   │   └── prompts.py            # System prompt do agente
│   ├── orchestrator/
│   │   ├── graph.py              # Grafo de roteamento WhatsApp
│   │   ├── nodes.py              # Nó de detecção de intenção
│   │   └── prompts.py            # Prompt de classificação de intenção
│   └── renewal/                  # [PÓS-MVP] agente de renovação de apólices
│       └── README.md
├── services/
│   ├── commission_service.py     # CRUD de comissões
│   ├── nfse_service.py           # Emissão de NFS-e via Focus NFe API
│   ├── insurer_portal_service.py # Seleção e invocação de adapters por seguradora
│   ├── claim_service.py          # CRUD de sinistros
│   ├── notification_service.py   # WhatsApp (Z-API) + e-mail (SendGrid)
│   ├── policy_service.py         # Consulta de apólices (importadas do Agger)
│   └── scheduler_service.py      # CRON jobs (APScheduler)
├── api/
│   ├── main.py                   # FastAPI app
│   ├── routes/
│   │   ├── webhook.py            # POST /webhook/whatsapp
│   │   └── scheduler.py          # POST /scheduler/commission-check
│   └── middleware/
│       └── auth.py               # Validação de assinaturas Z-API e CRON
├── models/
│   ├── database.py               # SQLAlchemy models
│   └── schemas.py                # Pydantic schemas
├── config/
│   └── insurers.json.enc         # Credenciais criptografadas por seguradora
├── scripts/
│   └── install_browsers.py       # Instala Playwright Chromium
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── migrations/                   # Alembic
```

### Variáveis de Ambiente

```bash
# LLM
ANTHROPIC_API_KEY=

# WhatsApp
ZAPI_INSTANCE_ID=
ZAPI_TOKEN=
ZAPI_WEBHOOK_SECRET=

# Banco de dados
DATABASE_URL=postgresql://user:pass@host:5432/insurance_agents
REDIS_URL=redis://host:6379/0

# Storage
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=

# NFS-e
FOCUS_NFE_API_KEY=
FOCUS_NFE_BASE_URL=https://producao.focusnfe.com.br
BROKER_CNPJ=
BROKER_CITY_CODE=

# 2FA / SMS Gateway
SMS_GATEWAY_PROVIDER=
SMS_GATEWAY_API_KEY=
SMS_GATEWAY_FROM_NUMBER=

# 2FA / Email IMAP
IMAP_HOST=
IMAP_PORT=993
IMAP_USER=
IMAP_PASSWORD=

# Credenciais de seguradoras (arquivo criptografado)
INSURER_CREDENTIALS_PATH=./config/insurers.json.enc
INSURER_CREDENTIALS_KEY=

# Notificações
SENDGRID_API_KEY=
BROKER_NOTIFICATION_PHONE=
BROKER_NOTIFICATION_EMAIL=

# Schedule
COMMISSION_CRON_HOUR=8
COMMISSION_CRON_TIMEZONE=America/Sao_Paulo

# Observabilidade
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=true
SENTRY_DSN=

# Ambiente
ENVIRONMENT=development
```

### Modelo de Dados

**Entidade: Commission (Comissão)**

```sql
commissions
  id                UUID PRIMARY KEY
  insurer_id        UUID REFERENCES insurers(id)
  policy_id         UUID REFERENCES policies(id)
  client_id         UUID REFERENCES clients(id)
  reference_month   VARCHAR              -- competência (YYYY-MM)
  gross_amount      DECIMAL
  net_amount        DECIMAL
  commission_rate   DECIMAL
  nfse_number       VARCHAR              -- número da NFS-e emitida
  nfse_pdf_url      VARCHAR              -- link S3
  status            ENUM (pending, nfse_emitted, nfse_failed)
  extracted_at      TIMESTAMP
  nfse_emitted_at   TIMESTAMP
  created_at        TIMESTAMP
```

**Entidade: Insurer (Seguradora)**

```sql
insurers
  id                UUID PRIMARY KEY
  name              VARCHAR
  code              VARCHAR UNIQUE       -- código interno (ex: bradesco, porto, hdi)
  portal_url        VARCHAR
  integration_type  ENUM (api, rpa)
  two_fa_method     ENUM (totp, email, sms, none)
  active            BOOLEAN DEFAULT true
  created_at        TIMESTAMP
  updated_at        TIMESTAMP
```

**Entidade: Claim (Sinistro)**

```sql
claims
  id                UUID PRIMARY KEY
  policy_id         UUID REFERENCES policies(id)
  client_id         UUID REFERENCES clients(id)
  insurer_id        UUID REFERENCES insurers(id)
  type              ENUM (assistance, glass, collision, theft, fire, other)
  severity          ENUM (simple, grave)
  status            ENUM (open, in_progress, waiting_insurer, escalated, closed)
  insurer_thread_id VARCHAR              -- ID do chamado na seguradora
  insurer_channel   VARCHAR              -- canal usado (api, whatsapp, phone)
  occurrence_date   TIMESTAMP
  occurrence_location JSONB
  description       TEXT
  documents         JSONB                -- array de URLs S3
  escalated_to      UUID REFERENCES users(id)
  opened_at         TIMESTAMP
  closed_at         TIMESTAMP
```

**Entidade: Client (Cliente)**

```sql
clients
  id                UUID PRIMARY KEY
  full_name         VARCHAR
  cpf_cnpj          VARCHAR UNIQUE
  phone_whatsapp    VARCHAR
  email             VARCHAR
  created_at        TIMESTAMP
  updated_at        TIMESTAMP
```

**Entidade: Policy (Apólice)**

```sql
policies
  id                UUID PRIMARY KEY
  client_id         UUID REFERENCES clients(id)
  insurer_id        UUID REFERENCES insurers(id)
  policy_number     VARCHAR UNIQUE
  type              ENUM (auto, life, home, business, health)
  status            ENUM (active, expired, cancelled)
  premium_amount    DECIMAL
  start_date        DATE
  end_date          DATE
  imported_from     VARCHAR              -- 'agger_csv' ou 'manual'
  created_at        TIMESTAMP
  updated_at        TIMESTAMP
```

**Entidade: Conversation (Conversa)**

```sql
conversations
  id                UUID PRIMARY KEY
  client_id         UUID REFERENCES clients(id)
  claim_id          UUID REFERENCES claims(id)
  type              ENUM (claim, faq, support)
  status            ENUM (active, waiting_client, waiting_insurer, escalated, closed)
  messages          JSONB                -- histórico completo
  human_assigned    UUID REFERENCES users(id)
  started_at        TIMESTAMP
  updated_at        TIMESTAMP
  closed_at         TIMESTAMP
```

---

## 6. Decisões de Arquitetura (ADRs)

### ADR-001 — LangGraph como framework de orquestração

**Contexto:** O sistema precisa gerenciar conversas que duram horas/dias, com estado complexo e handoffs entre agentes e humanos.

**Decisão:** Usar LangGraph.

**Motivo:** LangGraph foi construído para fluxos stateful e cíclicos — essencial tanto para o ciclo de comissionamento (loop por seguradora) quanto para o relay de sinistros (aguarda resposta da seguradora). Suporte nativo a Human-in-the-Loop e integração com LangSmith.

---

### ADR-002 — Claude (Anthropic) como LLM base

**Contexto:** O sistema processa informações sensíveis e conduz conversas em português brasileiro.

**Decisão:** Claude Sonnet em produção, Claude Haiku em desenvolvimento.

**Motivo:** Melhor desempenho em português, seguimento de instruções complexas e menor taxa de alucinações em tarefas estruturadas. Haiku em dev reduz custo de testes sem comprometer a validação do fluxo.

---

### ADR-003 — Redis para estado de conversas de sinistros

**Contexto:** Conversas de sinistro podem ficar abertas por horas (aguardando resposta da seguradora).

**Decisão:** Persistir estado ativo em Redis com TTL de 30 dias; migrar para PostgreSQL ao encerrar.

**Motivo:** Acesso em microsegundos durante a conversa ativa. TTL nativo evita acúmulo de conversas abandonadas. PostgreSQL fica limpo com apenas histórico finalizado.

---

### ADR-004 — Tools estruturadas vs. function calling livre

**Contexto:** Agentes executam ações reais (acessar portais, emitir notas fiscais, abrir sinistros).

**Decisão:** Todas as ações via tools Pydantic tipadas.

**Motivo:** Schema Pydantic força parâmetros estruturados e válidos. A camada de validação rejeita chamadas malformadas antes de qualquer efeito colateral — crítico para operações financeiras e jurídicas.

---

### ADR-005 — Emissão de apólice bloqueada no MVP

**Contexto:** Emissão automática requer integração homologada com cada seguradora.

**Decisão:** `emit_policy` bloquado no MVP. Corretor emite manualmente após handoff.

**Motivo:** Integração homologada exige semanas de processo burocrático por seguradora. O risco de emitir com dados errados supera o benefício no prazo do MVP.

---

### ADR-006 — Playwright para automação de portais sem API

**Contexto:** Nem todas as seguradoras têm API REST para extração de comissões.

**Decisão:** Usar Playwright em modo headless para portais sem API.

**Motivo:** Playwright é mais robusto que Selenium para sites modernos (SPAs, lazy loading). Suporta contextos de browser isolados por seguradora. A Agger já prova a viabilidade do modelo: faz exatamente isso para importar extratos. Risco: quebra se o portal mudar o layout — mitigado com testes de screenshot e alertas de falha.

---

### ADR-007 — Focus NFe para emissão de NFS-e

**Contexto:** A corretora precisa emitir nota fiscal de serviços para cada comissão recebida. Cada município tem API diferente.

**Decisão:** Usar Focus NFe como camada de abstração para NFS-e.

**Motivo:** Focus NFe cobre mais de 1.400 municípios com uma única API REST + JSON. Elimina a necessidade de integrar com cada prefeitura separadamente. Custo por nota é baixo (R$ 0,10–0,30). Alternativas (NFE.io, PlugNotas) têm modelo similar — Focus foi escolhido por documentação mais completa.

---

*Este documento deve ser atualizado a cada mudança arquitetural significativa. ADRs nunca são deletados — apenas superados por novos ADRs que referenciam o anterior.*

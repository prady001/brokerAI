# Architecture — Solução de Agentes de IA para Corretora de Seguros

> **Versão:** 1.0  
> **Data:** Fevereiro de 2026  
> **Audiência:** Desenvolvedores e Tech Leads  

---

## Índice

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Diagrama de Componentes](#2-diagrama-de-componentes)
3. [Design dos Agentes](#3-design-dos-agentes)
   - 3.1 Agente Orquestrador
   - 3.2 Agente de Renovação
   - 3.3 Agente de Sinistros
4. [Fluxos Detalhados](#4-fluxos-detalhados)
   - 4.1 Fluxo de Renovação
   - 4.2 Fluxo de Sinistros
5. [Infraestrutura e Deploy](#5-infraestrutura-e-deploy)
6. [Decisões de Arquitetura (ADRs)](#6-decisões-de-arquitetura-adrs)

---

## 1. Visão Geral do Sistema

O sistema é composto por **três agentes de IA** orquestrados via LangGraph, que se comunicam com clientes pelo WhatsApp Business API e com sistemas internos via camada de serviços. Humanos permanecem no loop para decisões finais no MVP.

### Princípios arquiteturais

- **Stateful conversations:** cada conversa tem estado persistido — o agente sabe exatamente em que ponto do fluxo o cliente está, mesmo que a conversa dure dias.
- **Human-in-the-loop by default:** no MVP, nenhuma ação irreversível (emissão, pagamento) é executada sem aprovação humana.
- **Tools over free-form:** os agentes executam ações via tools estruturadas, não via texto livre — isso garante previsibilidade e rastreabilidade.
- **Observabilidade total:** todas as chamadas LLM, decisões de roteamento e ações de tools são logadas com trace completo (LangSmith).

---

## 2. Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                        CANAIS DE ENTRADA                        │
│                                                                 │
│   WhatsApp Business API          CRON Scheduler (renovações)   │
│   (webhooks via Z-API)           (diário, 08:00 BRT)           │
└────────────────┬────────────────────────────┬───────────────────┘
                 │ HTTP POST                  │ trigger event
┌────────────────▼────────────────────────────▼───────────────────┐
│                        API GATEWAY                              │
│                    FastAPI — porta 8000                         │
│                                                                 │
│   POST /webhook/whatsapp     POST /scheduler/renewal-check     │
│   POST /webhook/status                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    AGENTE ORQUESTRADOR                          │
│                  (LangGraph — StateGraph)                       │
│                                                                 │
│  1. Detecta intenção (renovação / sinistro / dúvida / outro)   │
│  2. Carrega estado da conversa (Redis)                          │
│  3. Roteia para agente especializado                            │
│  4. Gerencia handoff humano                                     │
│  5. Persiste estado atualizado (Redis + PostgreSQL)             │
└──────────────┬──────────────────────────────┬───────────────────┘
               │                              │
┌──────────────▼──────────┐    ┌──────────────▼──────────────────┐
│    AGENTE RENOVAÇÃO     │    │        AGENTE SINISTROS          │
│   (LangGraph subgraph)  │    │      (LangGraph subgraph)        │
│                         │    │                                  │
│  Tools:                 │    │  Tools:                          │
│  · query_policies       │    │  · start_fnol_flow               │
│  · evaluate_renewal     │    │  · classify_claim                │
│  · get_insurer_quote    │    │  · request_documents             │
│  · send_proposal        │    │  · generate_protocol             │
│  · schedule_followup    │    │  · trigger_simple_assistance     │
│  · escalate_to_broker   │    │  · escalate_to_adjuster          │
│  · [emit_policy*]       │    │  · update_claim_status           │
└──────────┬──────────────┘    └────────────────┬─────────────────┘
           │                                    │
┌──────────▼────────────────────────────────────▼─────────────────┐
│                       SERVIÇOS INTERNOS                         │
│                                                                 │
│  PolicyService   ClaimService   NotificationService   AuthService│
└──────────┬────────────┬──────────────┬───────────────────────────┘
           │            │              │
┌──────────▼──┐  ┌──────▼──────┐  ┌───▼──────────────────────────┐
│ PostgreSQL  │  │    Redis     │  │   AWS S3 (documentos/fotos)  │
│ (dados      │  │  (estado de  │  │   Z-API (WhatsApp send)      │
│  primários) │  │  conversas)  │  │   SendGrid (e-mail fallback) │
└─────────────┘  └─────────────┘  └──────────────────────────────┘

* emit_policy: desabilitado no MVP
```

---

## 3. Design dos Agentes

### 3.1 Agente Orquestrador

**Responsabilidade:** porta de entrada de toda mensagem recebida. Decide para onde rotear sem executar nenhuma lógica de negócio.

**State Schema (LangGraph):**

```python
class OrchestratorState(TypedDict):
    conversation_id: str
    client_id: str
    client_phone: str
    message: str                    # mensagem atual do cliente
    message_history: list[dict]     # histórico completo
    intent: str                     # "renewal" | "claim" | "faq" | "unknown"
    active_agent: str               # agente ativo no momento
    handoff_requested: bool         # flag de escalonamento humano
    handoff_reason: str
```

**Nó de detecção de intenção:**

```python
INTENT_DETECTION_PROMPT = """
Você é o orquestrador de atendimento de uma corretora de seguros.
Analise a mensagem do cliente e classifique em uma das categorias:

- "renewal"   → cliente fala sobre renovação, vencimento, apólice, seguro
- "claim"     → cliente fala sobre sinistro, acidente, roubo, dano, batida
- "faq"       → pergunta geral sobre coberturas, preços, documentos
- "unknown"   → não identificado ou fora do escopo

Retorne apenas o JSON: {"intent": "<categoria>", "confidence": <0.0-1.0>}

Mensagem: {message}
"""
```

**Grafo de roteamento:**

```python
graph = StateGraph(OrchestratorState)

graph.add_node("detect_intent", detect_intent_node)
graph.add_node("renewal_agent", renewal_subgraph)
graph.add_node("claims_agent",  claims_subgraph)
graph.add_node("faq_handler",   faq_handler_node)
graph.add_node("human_handoff", human_handoff_node)

graph.set_entry_point("detect_intent")

graph.add_conditional_edges("detect_intent", route_by_intent, {
    "renewal":  "renewal_agent",
    "claim":    "claims_agent",
    "faq":      "faq_handler",
    "unknown":  "human_handoff",
})

graph.add_edge("renewal_agent", END)
graph.add_edge("claims_agent",  END)
graph.add_edge("faq_handler",   END)
graph.add_edge("human_handoff", END)
```

---

### 3.2 Agente de Renovação

**Responsabilidade:** gerenciar todo o ciclo de renovação — desde a detecção do vencimento até o handoff para o corretor fechar.

**State Schema:**

```python
class RenewalState(TypedDict):
    client_id: str
    policy_id: str
    policy: dict                # dados completos da apólice
    quote: dict                 # cotação da seguradora
    renewal_eligibility: str    # "auto" | "manual" | "blocked"
    eligibility_reason: str
    proposal_sent: bool
    proposal_sent_at: datetime
    client_response: str        # "accepted" | "declined" | "pending" | "question"
    followup_count: int
    conversation_stage: str     # estágio atual do fluxo
    messages: list[dict]
```

**Tools:**

```python
@tool
def query_policies(days_to_expiry: int) -> list[dict]:
    """Retorna apólices com vencimento nos próximos N dias."""

@tool
def evaluate_renewal_eligibility(policy_id: str) -> dict:
    """
    Avalia se a apólice pode ser renovada automaticamente.
    Retorna: { eligible: bool, mode: 'auto'|'manual', reason: str }
    Regras:
    - Sem sinistros no período: +auto
    - Pagamento em dia: +auto
    - Variação de prêmio <= 15%: +auto
    - Qualquer condição acima não atendida: manual
    - Cliente VIP: sempre manual
    """

@tool
def get_insurer_quote(policy_id: str) -> dict:
    """Busca cotação atualizada da seguradora. Retorna valor e condições."""

@tool
def send_whatsapp_proposal(client_phone: str, template: str, params: dict) -> bool:
    """Envia proposta de renovação via WhatsApp usando template aprovado."""

@tool
def schedule_followup(conversation_id: str, delay_days: int, message_type: str) -> bool:
    """Agenda lembrete automático se cliente não responder."""

@tool
def escalate_to_broker(conversation_id: str, reason: str, summary: str) -> bool:
    """
    Notifica corretor humano com resumo da conversa.
    Usado quando: aceite recebido, VIP, condição manual, sem resposta após 3 tentativas.
    """
```

**System Prompt do Agente:**

```
Você é um assistente de renovação de seguros da [Nome da Corretora].
Seu objetivo é ajudar o cliente a renovar o seguro de forma simples e rápida pelo WhatsApp.

REGRAS DE COMPORTAMENTO:
- Seja direto, amigável e profissional. Nunca use jargão técnico.
- Nunca prometa valores ou condições que não estejam na cotação confirmada.
- Se o cliente pedir desconto, reconheça o pedido e escale para o corretor — nunca negocie sozinho.
- Se não souber a resposta, diga que vai verificar e escale para humano.
- Nunca pressione o cliente. Se ele disser que vai pensar, agradeça e agende um lembrete.
- Nunca mencione que é uma IA, a menos que o cliente pergunte diretamente.

AÇÕES PROIBIDAS SEM APROVAÇÃO HUMANA:
- Emitir ou confirmar emissão de apólice
- Alterar coberturas ou condições da proposta
- Prometer devolução de valores
```

---

### 3.3 Agente de Sinistros

**Responsabilidade:** receber o aviso de sinistro, conduzir a coleta estruturada (FNOL), classificar, gerar protocolo e rotear para o caminho correto.

**State Schema:**

```python
class ClaimsState(TypedDict):
    client_id: str
    policy_id: str
    claim_id: str
    protocol_number: str
    fnol_stage: str             # estágio do formulário FNOL
    fnol_data: dict             # dados coletados até o momento
    claim_type: str             # tipo classificado
    severity: str               # "simple" | "complex" | "critical"
    documents_requested: list
    documents_received: list
    protocol_sent: bool
    routed_to: str              # "auto_assistance" | "adjuster" | "manager"
    messages: list[dict]
```

**FNOL — Estrutura de coleta:**

```python
FNOL_FIELDS = [
    {
        "field": "claim_type",
        "question": "O que aconteceu com seu veículo/bem segurado?",
        "options": ["Colisão", "Furto/Roubo", "Incêndio", "Vidros", "Assistência 24h", "Outro"],
        "required": True
    },
    {
        "field": "occurrence_date",
        "question": "Quando aconteceu? (data e hora aproximada)",
        "required": True
    },
    {
        "field": "occurrence_location",
        "question": "Onde aconteceu? (cidade, bairro ou endereço)",
        "required": True
    },
    {
        "field": "description",
        "question": "Me conte o que aconteceu em detalhes.",
        "required": True
    },
    {
        "field": "third_parties",
        "question": "Havia terceiros envolvidos? (outros veículos, pessoas)",
        "required": False,
        "condition": "claim_type in ['collision']"
    },
    {
        "field": "police_report",
        "question": "Você registrou boletim de ocorrência?",
        "required": False,
        "condition": "claim_type in ['theft', 'robbery', 'fire']"
    },
]
```

**Tools:**

```python
@tool
def classify_claim(fnol_data: dict) -> dict:
    """
    Classifica o sinistro em tipo e severidade.
    Retorna: { type: str, severity: 'simple'|'complex'|'critical', auto_resolve: bool }
    """

@tool
def generate_protocol(claim_id: str) -> str:
    """Gera número de protocolo único e registra no banco."""

@tool
def request_documents(claim_id: str, claim_type: str) -> list[str]:
    """Retorna lista de documentos necessários para o tipo de sinistro."""

@tool
def trigger_simple_assistance(claim_id: str, assistance_type: str, location: str) -> dict:
    """Aciona prestador de assistência para sinistros simples. Retorna ETA."""

@tool
def escalate_to_adjuster(claim_id: str, severity: str, summary: str) -> bool:
    """Notifica regulador/perito com dossiê completo do sinistro."""

@tool
def update_claim_status(claim_id: str, status: str, message_to_client: str) -> bool:
    """Atualiza status e notifica cliente proativamente."""
```

---

## 4. Fluxos Detalhados

### 4.1 Fluxo de Renovação

```
CRON diário (08:00)
        │
        ▼
query_policies(days=30)
        │
        ├─── Para cada apólice elegível:
        │
        ▼
evaluate_renewal_eligibility(policy_id)
        │
        ├── mode = "auto" ──────────────────────────────────────────┐
        │                                                            │
        ├── mode = "manual" ──► notifica corretor ──► FIM           │
        │                                                            ▼
        └── blocked ──► registra motivo ──► FIM          get_insurer_quote(policy_id)
                                                                     │
                                                                     ▼
                                                      send_whatsapp_proposal(client)
                                                                     │
                                                          ┌──────────┴──────────┐
                                                          │  aguarda resposta    │
                                                          │  (estado em Redis)   │
                                                          └──────────┬──────────┘
                                                                     │
                                          ┌──────────────────────────┼──────────────────────┐
                                          │                          │                      │
                                    "accepted"                  "question"              sem resposta
                                          │                          │                      │
                                          ▼                          ▼                      ▼
                              escalate_to_broker           LLM responde            schedule_followup
                              (corretor emite)             (até 3 trocas)          (régua: 15d, 7d, 2d)
                                                                     │                      │
                                                                     ▼               após 3 tentativas
                                                           "still_pending"                  │
                                                                     │                      ▼
                                                                     ▼           escalate_to_broker
                                                        escalate_to_broker       (último recurso)
```

### 4.2 Fluxo de Sinistros

```
Cliente manda mensagem no WhatsApp
              │
              ▼
    Orquestrador detecta intent = "claim"
              │
              ▼
    Agente Sinistros iniciado
              │
              ▼
    ┌─── FNOL Collection Loop ────────────────────────────────┐
    │                                                          │
    │  Para cada campo em FNOL_FIELDS:                        │
    │    1. Agente faz pergunta natural (não robótica)        │
    │    2. Aguarda resposta do cliente                       │
    │    3. Extrai e valida dado                              │
    │    4. Se inválido → pede de novo com orientação         │
    │    5. Se válido → avança para próximo campo             │
    │                                                          │
    └─────────────────────────────────────────────────────────┘
              │
              ▼
    classify_claim(fnol_data)
              │
              ├── severity = "simple" ─────────────────────────────────────────┐
              │                                                                  │
              ├── severity = "complex" ──────────────────────────────────┐      │
              │                                                           │      │
              └── severity = "critical" ──► alerta gestor IMEDIATO       │      │
                                           + mensagem tranquilizadora     │      │
                                           ao cliente                     │      │
                                                                          ▼      ▼
                                                              escalate_      trigger_
                                                              to_adjuster    simple_
                                                                    │        assistance
                                                                    │              │
                                                  ┌─────────────────┴──────────────┘
                                                  │
                                                  ▼
                                      generate_protocol(claim_id)
                                                  │
                                                  ▼
                                      request_documents(claim_type)
                                                  │
                                                  ▼
                                      Envia protocolo + checklist ao cliente
                                                  │
                                                  ▼
                                      Aguarda upload de documentos
                                      (estado persiste em Redis)
                                                  │
                                                  ▼
                                      update_claim_status → notifica cliente
                                      (a cada mudança de status)
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
insurance-agents/
├── agents/
│   ├── orchestrator/
│   │   ├── graph.py          # StateGraph do orquestrador
│   │   ├── nodes.py          # Nós: detect_intent, route, handoff
│   │   └── prompts.py
│   ├── renewal/
│   │   ├── graph.py          # Subgraph de renovação
│   │   ├── nodes.py
│   │   ├── tools.py          # Todas as tools do agente
│   │   └── prompts.py
│   └── claims/
│       ├── graph.py          # Subgraph de sinistros
│       ├── nodes.py
│       ├── tools.py
│       ├── fnol.py           # Lógica de coleta FNOL
│       └── prompts.py
├── services/
│   ├── policy_service.py     # CRUD de apólices
│   ├── claim_service.py      # CRUD de sinistros
│   ├── notification_service.py  # WhatsApp + e-mail
│   └── scheduler_service.py  # CRON jobs
├── api/
│   ├── main.py               # FastAPI app
│   ├── routes/
│   │   ├── webhook.py        # POST /webhook/whatsapp
│   │   └── scheduler.py      # POST /scheduler/renewal-check
│   └── middleware/
│       └── auth.py
├── models/
│   ├── database.py           # SQLAlchemy models
│   └── schemas.py            # Pydantic schemas
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── migrations/               # Alembic
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
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

# Notificações
SENDGRID_API_KEY=

# Observabilidade
LANGCHAIN_API_KEY=           # LangSmith
LANGCHAIN_TRACING_V2=true
SENTRY_DSN=

# Configuração da corretora
BROKER_NOTIFICATION_PHONE=   # número do corretor no WhatsApp
BROKER_NOTIFICATION_EMAIL=
VIP_PREMIUM_THRESHOLD=5000   # valor mínimo para cliente VIP (R$)
MAX_AUTO_PREMIUM_VARIATION=0.15  # 15%
```

### Docker Compose (desenvolvimento)

```yaml
version: '3.9'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - postgres
      - redis
    volumes:
      - .:/app

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: insurance_agents
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  scheduler:
    build: .
    command: python -m services.scheduler_service
    env_file: .env
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
```

---

## 6. Decisões de Arquitetura (ADRs)

### ADR-001 — LangGraph como framework de orquestração

**Contexto:** O sistema precisa gerenciar conversas que duram dias, com estado complexo, loops de coleta de informação e handoffs entre agentes e humanos.

**Decisão:** Usar LangGraph.

**Motivo:** LangGraph foi construído exatamente para fluxos stateful e cíclicos — algo que LangChain simples ou chamadas diretas de LLM não suportam bem. Oferece visualização do grafo, suporte nativo a Human-in-the-Loop e integração com LangSmith para observabilidade. CrewAI foi considerado, mas é mais adequado para agentes paralelos autônomos, não para fluxos conversacionais com estado.

---

### ADR-002 — Claude (Anthropic) como LLM base

**Contexto:** O sistema vai processar informações sensíveis de clientes, tomar decisões de roteamento e conduzir conversas em português brasileiro.

**Decisão:** Usar Claude Sonnet como modelo de produção.

**Motivo:** Claude apresenta desempenho superior em português, melhor seguimento de instruções complexas (system prompt com regras de negócio) e menor taxa de alucinações em tarefas estruturadas. GPT-4o foi considerado, mas Claude tem melhor relação custo/qualidade para este caso de uso específico. Haiku é usado em staging para reduzir custo de testes.

---

### ADR-003 — Redis para estado de conversas

**Contexto:** Conversas podem ficar abertas por dias (cliente não responde imediatamente). O estado precisa ser rápido de ler/escrever e ter TTL configurável.

**Decisão:** Persistir estado ativo de conversas em Redis, com TTL de 30 dias.

**Motivo:** Redis oferece acesso em microsegundos, suporte a TTL nativo e estruturas de dados flexíveis (Hash para estado, List para histórico). Ao fechar a conversa, o estado final é migrado para PostgreSQL. Persistir tudo em PostgreSQL seria mais lento e geraria volume desnecessário de escritas durante conversas ativas.

---

### ADR-004 — Tools estruturadas vs. function calling livre

**Contexto:** Os agentes precisam executar ações reais (consultar banco, enviar mensagem, escalar). Há risco do LLM "inventar" ações ou parâmetros.

**Decisão:** Todas as ações são implementadas como tools Pydantic tipadas, não como texto livre interpretado.

**Motivo:** Tools com schema Pydantic forçam o LLM a passar parâmetros estruturados e válidos — a camada de validação rejeita chamadas malformadas antes de qualquer efeito colateral. Isso é crítico em um sistema financeiro. Text-based function calling foi descartado por falta de garantia de schema.

---

### ADR-005 — Emissão de apólice bloqueada no MVP

**Contexto:** Tecnicamente seria possível integrar com a seguradora e emitir automaticamente. O cliente quer MVP em 3 meses.

**Decisão:** Bloquear `emit_policy` no MVP. O agente leva o cliente até o aceite e escala para o corretor emitir.

**Motivo:** Emissão automática requer integração homologada com cada seguradora (processo burocrático de semanas), validação jurídica e testes extensivos. O risco de emitir com dados errados é alto e o custo para corrigir é maior que o benefício no MVP. O corretor emite manualmente em menos de 5 minutos após receber o handoff — já é uma melhoria enorme sobre o processo atual.

---

*Este documento deve ser atualizado a cada mudança arquitetural significativa. ADRs nunca são deletados — apenas superados por novos ADRs que referenciam o anterior.*

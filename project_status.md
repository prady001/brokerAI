# Status do Projeto — brokerAI

> **Última atualização:** Fevereiro de 2026
> **Status geral:** 🟡 Planejamento

---

## Visão Geral dos Milestones

| Versão | Período | Foco | Status |
|---|---|---|---|
| M0 — Documentação e Planejamento | Fev/2026 | Arquitetura, tese, casos de uso, roadmap | 🟡 Em andamento |
| M1 — Fundação | Semanas 1–3 | Infra, Evolution API (WhatsApp), cadastro de carteira | ✅ Concluído (código) |
| M2 — Agente de Sinistro Simples E2E | Semanas 3–6 | Sinistro simples do FNOL ao encerramento via WhatsApp | 🟡 Implementado (aguarda chip WhatsApp) |
| M3 — Agente de Onboarding | Semanas 5–8 | Onboarding de novo cliente via WhatsApp + cadastro de apólice | ⬜ Não iniciado |
| M4 — Agente de Renovação | Semanas 7–10 | Régua de renovação proativa + qualificação de lead para vendedor | ✅ Concluído (código) |
| **MVP** | **Mês 3** | **Três agentes em produção, primeira corretora pagante** | ⬜ Não iniciado |
| **V1** | **Mês 6** | **Grafo de memória por cliente, relacionamento proativo** | ⬜ Não iniciado |
| **V2** | **Mês 12** | **Inteligência de carteira, personalização emocional** | ⬜ Não iniciado |
| **V3** | **Ano 2** | **Advocacia em sinistros, prevenção, precificação de risco** | ⬜ Não iniciado |
| **V4** | **Ano 2-3** | **Plataforma com efeito de rede, prospecção autônoma** | ⬜ Não iniciado |

---

## M0 — Documentação e Planejamento

### Concluído ✅

- [x] Plataforma do Gestor — especificação completa de telas e navegação (`docs/produto/plataforma-gestor.md`)
- [x] Especificação de produto (`docs/project_spec.md`)
- [x] Arquitetura técnica (`docs/architecture.md`)
- [x] Diagramas de fluxo (sinistros, comissionamento, visão geral, grafo de agentes)
- [x] Levantamento de requisitos com a corretora
- [x] Definição da stack tecnológica
- [x] ADRs documentados (ADR-001 a ADR-009)
- [x] Modelo de dados definido e implementado (`models/database.py`)
- [x] Schemas Pydantic de API (`models/schemas.py`)
- [x] Definição de variáveis de ambiente (`.env`, `.env.example`)
- [x] `CLAUDE.md` criado e atualizado
- [x] Guia de implementação (`docs/guias/guia-de-implementacao.md`)
- [x] Ralph Loop prompts (`docs/guias/ralph-loop-prompt.md`, `ralph-loop-prompt-m1.md`)
- [x] Análise de mercado e precificação (`docs/produto/`)
- [x] Mapa completo de casos de uso (`docs/produto/casos-de-uso.md`)
- [x] Tese da empresa (`docs/produto/tese-da-empresa.md`)
- [x] Roadmap de versões MVP → V4 (`docs/produto/roadmap.md`)
- [x] Pré-requisitos de implementação + perguntas para cliente (`docs/produto/pre-requisitos-implementacao.md`)
- [x] Design completo dos grafos LangGraph (claims, commissioning, orchestrator) com gaps corrigidos
- [x] `CommissioningState`, `ClaimsState`, `OrchestratorState` — schemas de estado completos
- [x] Portal adapters: `ApiAdapter`, `RpaAdapter`, `EmailAdapter` (IMAP)
- [x] Configuração do Alembic (`alembic.ini`, `migrations/env.py`)
- [x] `tests/conftest.py` com fixtures de banco e API client
- [x] Template de credenciais de seguradoras (`config/insurers.example.json`)
- [x] Estrutura de repositório organizada e completa

### Em andamento 🔄

- [ ] Validação do levantamento com stakeholders da corretora (questionário enviado)
- [ ] Definição dos templates de mensagem WhatsApp (aprovação Meta)

### Pendente ⬜

- [ ] Aprovação formal do escopo do MVP (3 agentes: sinistro, onboarding, renovação)
- [x] Documentação do agente de sinistro simples E2E (`docs/agentes/sinistro.md`)
- [x] Documentação do agente de onboarding (`docs/agentes/onboarding.md`)

---

## M1 — Fundação (Semanas 1–3)

### Entregas esperadas

- [x] Repositório estruturado com pastas definidas em `architecture.md`
- [x] Docker Compose funcionando (API + PostgreSQL + Redis + Evolution API)
- [x] Migrations iniciais com Alembic (`clients`, `policies`, `claims`, `conversations`, `renewals`)
- [x] FastAPI com rotas de webhook (`/webhook/whatsapp`, `/scheduler/renewal-check`)
- [x] Webhook handler Evolution API implementado com filtragem de eventos
- [x] Middleware de autenticação (Evolution API + token interno)
- [x] Pipeline de CI (GitHub Actions) — ruff + mypy + pytest
- [x] Cadastro manual de carteira de apólices (CRUD `/admin/clients` e `/admin/policies`)
- [x] `.env.example` atualizado com todas as variáveis do escopo atual
- [x] Documentação da fundação (`docs/api/m1-fundacao.md`)
- [ ] Evolution API conectada a número WhatsApp real (aguardando chip dedicado)

---

## M2 — Agente de Sinistro Simples E2E (Semanas 3–6)

### Entregas esperadas

- [x] `ClaimService` com CRUD de sinistros (`services/claim_service.py`)
- [x] Grafo LangGraph do Agente de Sinistros (`agents/claims/graph.py`, `nodes.py`, `prompts.py`)
- [x] Nós implementados: `collect_info` (multi-turn), `classify`, `open_claim`, `check_updates`, `relay_to_client`, `escalate`, `close`
- [x] Orquestrador configurado para rotear WhatsApp → Agente de Sinistros (`agents/orchestrator/nodes.py`)
- [x] Webhook conectado ao orquestrador E2E (`api/routes/webhook.py`)
- [x] Escalada automática para sinistros graves com resumo estruturado (Lucimara)
- [x] Testes unitários: classify, collect_info, open_claim, escalate (`tests/unit/test_claims_agent.py`)
- [x] Documentação atualizada: `docs/agentes/sinistro.md`
- [ ] Upload de fotos via WhatsApp → Cloudflare R2 (pós-MVP)
- [ ] Evolution API conectada a número WhatsApp real (aguardando chip)

---

## M3 — Agente de Onboarding (Semanas 5–8)

### Entregas esperadas

- [ ] Subgraph LangGraph do Agente de Onboarding
- [ ] Fluxo de coleta de dados do novo cliente via WhatsApp (nome, CPF, veículo, contato)
- [ ] Cadastro automático de `client` + `policy` no banco a partir da conversa
- [ ] Tools implementadas: `collect_client_data`, `validate_document`, `register_client`, `register_policy`, `send_welcome_summary`
- [ ] Orquestrador configurado para rotear WhatsApp → Agente de Onboarding
- [ ] Notificação ao vendedor ao finalizar cadastro com resumo estruturado
- [ ] Testes do fluxo completo (carro, moto, residência)
- [ ] Documentação: `docs/agentes/onboarding.md`

---

## M4 — Agente de Renovação (Semanas 7–10)

### Entregas esperadas

- [x] `RenewalService` com CRUD e lógica de régua de contatos
- [x] Subgraph LangGraph do Agente de Renovação (`agents/renewal/graph.py`)
- [x] CRON scheduler diário (08:00 BRT) — `run_renewal_check` implementado
- [x] Tools implementadas: `get_expiring_policies`, `send_renewal_contact`, `register_client_intent`, `notify_seller`, `mark_renewal_status`
- [x] Templates WhatsApp: `TEMPLATE_30_DAYS`, `TEMPLATE_15_7_DAYS`, `TEMPLATE_DAY_ZERO`
- [x] Lógica de status: `confirmed`, `refused`, `no_response`, `contacted`, `lost`
- [x] Notificação estruturada ao vendedor com contexto completo da apólice
- [x] Testes da régua completa (30→15→7→0 dias) — 22 testes unitários
- [x] Roteamento de respostas WhatsApp → Agente de Renovação (`webhook.py`)
- [x] Documentação: `docs/agentes/renovacao.md` ✅
- [ ] Três templates WhatsApp aprovados pela Meta (aguardando D-06)

---

## Integrações — Status

| Integração | Responsável | Status | Escopo |
|---|---|---|---|
| WhatsApp (Evolution API — self-hosted) | — | ⬜ A configurar | MVP |
| PostgreSQL (Oracle Cloud Free Tier) | — | ⬜ A configurar | MVP |
| Redis (Oracle Cloud Free Tier) | — | ⬜ A configurar | MVP |
| Cloudflare R2 (fotos de sinistros) | — | ⬜ Conta não criada | MVP |
| LangSmith | — | ⬜ Projeto não criado | MVP |
| Sentry | — | ⬜ Projeto não criado | MVP |
| Portais das seguradoras (RPA/API) | — | ⬜ Pós-MVP | V1 |
| Focus NFe API (NFS-e) | — | ⬜ Pós-MVP | V1 |
| Playwright (RPA portais) | — | ⬜ Pós-MVP | V1 |
| Gateway SMS (2FA portais) | — | ⬜ Pós-MVP | V1 |

---

## Decisões

### Tomadas ✅

| # | Decisão | Escolha | Observação |
|---|---|---|---|
| D-01 | Provedor WhatsApp | **Evolution API** (self-hosted, open source) | Gratuito. Mesma tecnologia do Z-API. Migrar para API oficial quando escalar. |
| D-02 | Ambiente de deploy | **Oracle Cloud Free Tier** | Permanentemente gratuito. 2 VMs + PostgreSQL Autonomous + Object Storage. |
| D-03 | Importação de apólices | **Digitação manual** | CSV do Agger pode ser avaliado em V1. |
| D-08 | Storage de arquivos (fotos de sinistros) | **Cloudflare R2** | 10GB gratuitos/mês, sem custo de egress. Substitui AWS S3 no MVP. |

| D-04 | Seguradoras MVP | **Revisado** — ver tabela abaixo (entrevista mar/2026) |

#### Seguradoras reais da corretora — D-04 (revisado mar/2026)

Seguradoras auto principais (em uso ativo):

| Seguradora | Portal de sinistros? | Estratégia MVP |
|---|---|---|
| Zurich | ❌ Não confirmado | Notificação para Lucimara — abertura manual |
| Alpha | ❌ Não confirmado | Notificação para Lucimara (atendimento ruim — risco) |
| Justus | ❌ Não confirmado | Notificação para Lucimara |
| BP | ❌ Não confirmado | Notificação para Lucimara |
| Suíça | ❌ Não confirmado | Notificação para Lucimara |
| Tokio Marine | ✅ Portal próprio | RPA (Playwright) — única com portal confirmado |

Parceiros recentes (Yellum, Porto, Allianz): confirmar fluxo de sinistros antes de incluir no MVP.

**Impacto no M2:** o agente não precisa de RPA para a maioria das seguradoras. O fluxo principal é coletar dados → notificar Lucimara com resumo → Lucimara abre/acompanha manualmente → agente repassa atualizações ao cliente quando Lucimara informar.

### Abertas ⬜

| # | Decisão | Prazo |
|---|---|---|
| D-05 | Confirmar município do CNPJ da corretora (para configurar Focus NFe) | Antes de M2 |
| D-06 | Templates de mensagem WhatsApp aprovados pela Meta | Antes de M2 |
| D-07 | Provedor de gateway SMS para 2FA (Twilio, Zenvia, ou outro) | Antes de M2 |
| D-09 | Número WhatsApp dedicado para sinistros (pessoal ou empresa) | Antes de M2 |
| D-10 | Exportação de CSV do Agger com dados da carteira (nome, telefone, apólice, seguradora, vigência) | Antes de M2 |
| D-11 | Canal de contato das seguradoras sem portal (Zurich, Alpha, Justus, BP, Suíça) — WhatsApp, ligação ou e-mail? | Antes de M2 |

---

## Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Aprovação de templates WhatsApp demorar | Alta | Alto | Iniciar processo na semana 1 |
| Acesso à base de apólices atrasar | Média | Alto | Criar fixtures de teste enquanto aguarda |
| Integração com seguradora necessária no MVP | Baixa | Alto | Escopo do MVP não inclui — corretor emite manualmente |
| Variação de comportamento do LLM em prod | Média | Médio | LangSmith para rastreabilidade + testes de regressão |

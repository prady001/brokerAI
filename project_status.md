# Status do Projeto — brokerAI

> **Última atualização:** Fevereiro de 2026
> **Status geral:** 🟡 Planejamento

---

## Visão Geral dos Milestones

| Versão | Período | Foco | Status |
|---|---|---|---|
| M0 — Documentação e Planejamento | Fev/2026 | Arquitetura, tese, casos de uso, roadmap | 🟡 Em andamento |
| M1 — Fundação | Semanas 1–3 | Infra, Evolution API (WhatsApp), cadastro de carteira | ⬜ Não iniciado |
| M2 — Agente de Sinistro Simples E2E | Semanas 3–6 | Sinistro simples do FNOL ao encerramento via WhatsApp | ⬜ Não iniciado |
| M3 — Agente de Onboarding | Semanas 5–8 | Onboarding de novo cliente via WhatsApp + cadastro de apólice | ⬜ Não iniciado |
| M4 — Agente de Renovação | Semanas 7–10 | Régua de renovação proativa + qualificação de lead para vendedor | ⬜ Não iniciado |
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

- [ ] Repositório estruturado com pastas definidas em `architecture.md`
- [ ] Docker Compose funcionando (API + PostgreSQL + Redis)
- [ ] Migrations iniciais com Alembic (`clients`, `policies`, `claims`, `conversations`, `renewals`)
- [ ] FastAPI com rotas de webhook (`/webhook/whatsapp`, `/scheduler/renewal-check`)
- [ ] Evolution API configurada: receber e enviar mensagem simples via WhatsApp
- [ ] Pipeline de CI (GitHub Actions) com lint e testes
- [ ] Cadastro manual de carteira de apólices (CRUD básico via admin ou script)
- [ ] `.env.example` atualizado com todas as variáveis do escopo atual

---

## M2 — Agente de Sinistro Simples E2E (Semanas 3–6)

### Entregas esperadas

- [ ] `ClaimService` com CRUD de sinistros
- [ ] Subgraph LangGraph do Agente de Sinistros
- [ ] Tools implementadas: `classify_claim`, `collect_claim_info`, `open_claim_at_insurer`, `relay_update_to_client`, `escalate_to_broker`, `store_claim_history`
- [ ] Orquestrador configurado para rotear WhatsApp → Agente de Sinistros
- [ ] Upload de fotos via WhatsApp → Cloudflare R2
- [ ] Escalada automática para sinistros graves com resumo estruturado
- [ ] Testes dos tipos mais comuns: guincho, assistência, vidro (sinistros simples)
- [ ] Documentação: `docs/agentes/sinistro.md`

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

- [ ] `RenewalService` com CRUD e lógica de régua de contatos
- [ ] Subgraph LangGraph do Agente de Renovação
- [ ] CRON scheduler diário (08:00 BRT) — busca apólices com vencimento em 30, 15, 7, 0 dias
- [ ] Tools implementadas: `get_expiring_policies`, `send_renewal_contact`, `register_client_intent`, `notify_seller`, `mark_renewal_status`
- [ ] Três templates WhatsApp aprovados pela Meta (aviso, lembrete, urgência)
- [ ] Lógica de status: `CONFIRMADO`, `RECUSADO`, `SEM_RESPOSTA`, `PERDIDO`
- [ ] Notificação estruturada ao vendedor com contexto completo da apólice
- [ ] Testes da régua completa (30→15→7→0 dias)
- [ ] Documentação: `docs/agentes/renovacao.md` ✅

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

| D-04 | Seguradoras MVP: Porto Seguro, Allianz, Azul Seguros, Tokio Marine | **Decidido** — ver tabela abaixo |

#### Mapa de portais — D-04

| Seguradora | API REST? | Estratégia MVP | 2FA | Ação necessária |
|---|---|---|---|---|
| Porto Seguro | ✅ OAuth 2.0 (Sensedia) | API | ReCaptcha no portal (inviabiliza RPA) | Cadastrar parceiro em `dev.portoseguro.com.br` |
| Allianz | ❌ Não | RPA (Playwright) | Sem 2FA confirmado (SAML legado) | Nenhuma — implementar em M2 |
| Azul Seguros | ❌ Não | RPA (Playwright) | Sem 2FA (senha dupla no extrato) | Nenhuma — implementar em M2 |
| Tokio Marine | ✅ OAuth 2.0 (Sensedia) | API | Token 2FA confirmado (tipo a verificar) | Cadastrar parceiro em `integracao.tokiomarine.com.br` |

**Ordem de implementação:** Allianz e Azul (M2 início) → Porto Seguro e Tokio Marine (M2 fim, após aprovação de parceiro).

### Abertas ⬜

| # | Decisão | Prazo |
|---|---|---|
| D-05 | Confirmar município do CNPJ da corretora (para configurar Focus NFe) | Antes de M2 |
| D-06 | Templates de mensagem WhatsApp aprovados pela Meta | Antes de M2 |
| D-07 | Provedor de gateway SMS para 2FA (Twilio, Zenvia, ou outro) | Antes de M2 |

---

## Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Aprovação de templates WhatsApp demorar | Alta | Alto | Iniciar processo na semana 1 |
| Acesso à base de apólices atrasar | Média | Alto | Criar fixtures de teste enquanto aguarda |
| Integração com seguradora necessária no MVP | Baixa | Alto | Escopo do MVP não inclui — corretor emite manualmente |
| Variação de comportamento do LLM em prod | Média | Médio | LangSmith para rastreabilidade + testes de regressão |

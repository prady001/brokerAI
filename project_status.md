# Status do Projeto — brokerAI

> **Última atualização:** Fevereiro de 2026
> **Status geral:** 🟡 Planejamento

---

## Visão Geral dos Milestones

| Milestone | Período | Status |
|---|---|---|
| M0 — Documentação e Planejamento | Fev/2026 | 🟡 Em andamento |
| M1 — Fundação | Semanas 1–3 | ⬜ Não iniciado |
| M2 — Agente de Renovação | Semanas 4–8 | ⬜ Não iniciado |
| M3 — Agente de Sinistros | Semanas 7–10 | ⬜ Não iniciado |
| MVP | Fim do mês 3 | ⬜ Não iniciado |

---

## M0 — Documentação e Planejamento

### Concluído ✅

- [x] Especificação de produto (`project_spec.md`)
- [x] Arquitetura técnica (`architecture.md`)
- [x] Diagramas de fluxo (renovação, sinistros, visão geral, grafo de agentes)
- [x] Levantamento de requisitos com a corretora
- [x] Definição da stack tecnológica
- [x] ADRs documentados (ADR-001 a ADR-005)
- [x] Modelo de dados definido
- [x] Definição de variáveis de ambiente (`.env`)
- [x] `CLAUDE.md` criado
- [x] Guia de implementação criado (`docs/guias/guia-de-implementacao.md`)

### Em andamento 🔄

- [ ] Validação do levantamento com stakeholders da corretora
- [ ] Definição dos templates de mensagem WhatsApp (aprovação Meta)
- [ ] Contratação / setup de conta Z-API

### Pendente ⬜

- [ ] Aprovação formal do escopo do MVP
- [ ] Acesso ao sistema atual da corretora (fonte de dados de apólices)
- [ ] Definição do ambiente de staging (Railway ou AWS)

---

## M1 — Fundação (Semanas 1–3)

### Entregas esperadas

- [ ] Repositório estruturado com pastas definidas em `architecture.md`
- [ ] Docker Compose funcionando (API + PostgreSQL + Redis)
- [ ] Migrations iniciais com Alembic (`clients`, `policies`, `claims`, `conversations`)
- [ ] FastAPI com rotas de webhook (`/webhook/whatsapp`, `/scheduler/renewal-check`)
- [ ] Integração Z-API: receber e enviar mensagem simples via WhatsApp
- [ ] Pipeline de CI (GitHub Actions) com lint e testes
- [ ] `.env.example` atualizado

---

## M2 — Agente de Renovação (Semanas 4–8)

### Entregas esperadas

- [ ] `PolicyService` com query de apólices por vencimento
- [ ] Lógica de elegibilidade (`evaluate_renewal_eligibility`)
- [ ] Subgraph LangGraph do Agente de Renovação
- [ ] Tools implementadas: `query_policies`, `evaluate_renewal_eligibility`, `get_insurer_quote`, `send_whatsapp_proposal`, `schedule_followup`, `escalate_to_broker`
- [ ] CRON scheduler diário (08:00 BRT)
- [ ] Régua de follow-up (30d → 15d → 7d → 2d)
- [ ] Testes unitários das tools e nós do grafo
- [ ] Teste de ponta a ponta com carteira piloto (auto)

---

## M3 — Agente de Sinistros (Semanas 7–10)

### Entregas esperadas

- [ ] `ClaimService` com CRUD de sinistros
- [ ] Fluxo FNOL completo (`fnol.py`)
- [ ] Subgraph LangGraph do Agente de Sinistros
- [ ] Tools implementadas: `classify_claim`, `generate_protocol`, `request_documents`, `trigger_simple_assistance`, `escalate_to_adjuster`, `update_claim_status`
- [ ] Upload de fotos e documentos via WhatsApp → S3
- [ ] Geração de protocolo único
- [ ] Notificações proativas de status ao cliente
- [ ] Testes dos tipos de sinistro mais comuns (vidro, assistência, colisão)

---

## Integrações — Status

| Integração | Responsável | Status |
|---|---|---|
| WhatsApp Business API (Z-API) | — | ⬜ Conta não criada |
| PostgreSQL (local/Docker) | — | ⬜ Não configurado |
| Redis (local/Docker) | — | ⬜ Não configurado |
| AWS S3 | — | ⬜ Credenciais pendentes |
| SendGrid | — | ⬜ Conta não criada |
| LangSmith | — | ⬜ Projeto não criado |
| Sentry | — | ⬜ Projeto não criado |
| Base de apólices da corretora | — | ⬜ Acesso pendente |

---

## Decisões Abertas

| # | Decisão | Prazo |
|---|---|---|
| D-01 | Confirmar provedor WhatsApp: Z-API vs. Twilio | Antes de M1 |
| D-02 | Definir ambiente de deploy do MVP: Railway vs. AWS | Antes de M1 |
| D-03 | Formato de importação das apólices: CSV, API do ERP ou scraping | Antes de M1 |
| D-04 | Definir valor exato do `VIP_PREMIUM_THRESHOLD` com a corretora | Antes de M2 |
| D-05 | Templates de mensagem WhatsApp aprovados pela Meta | Antes de M2 |

---

## Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Aprovação de templates WhatsApp demorar | Alta | Alto | Iniciar processo na semana 1 |
| Acesso à base de apólices atrasar | Média | Alto | Criar fixtures de teste enquanto aguarda |
| Integração com seguradora necessária no MVP | Baixa | Alto | Escopo do MVP não inclui — corretor emite manualmente |
| Variação de comportamento do LLM em prod | Média | Médio | LangSmith para rastreabilidade + testes de regressão |

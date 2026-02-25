# Status do Projeto — brokerAI

> **Última atualização:** Fevereiro de 2026
> **Status geral:** 🟡 Planejamento

---

## Visão Geral dos Milestones

| Milestone | Período | Status |
|---|---|---|
| M0 — Documentação e Planejamento | Fev/2026 | 🟡 Em andamento |
| M1 — Fundação | Semanas 1–3 | ⬜ Não iniciado |
| M2 — Agente de Comissionamento | Semanas 4–7 | ⬜ Não iniciado |
| M3 — Agente de Sinistros | Semanas 6–10 | ⬜ Não iniciado |
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

- [ ] Validação do levantamento com stakeholders da corretora (questionário enviado)
- [ ] Mapeamento das seguradoras que a corretora opera
- [ ] Verificação de tipo de 2FA por portal de seguradora
- [ ] Definição dos templates de mensagem WhatsApp (aprovação Meta)
- [ ] Contratação / setup de conta Z-API

### Pendente ⬜

- [ ] Aprovação formal do escopo do MVP
- [ ] Exportação de carteira via Agger (CSV com campos de apólice)
- [ ] Credenciais de acesso aos portais das seguradoras
- [ ] Definição do município do CNPJ (para configurar Focus NFe)
- [ ] Definição do ambiente de staging (Railway ou AWS)

---

## M1 — Fundação (Semanas 1–3)

### Entregas esperadas

- [ ] Repositório estruturado com pastas definidas em `architecture.md`
- [ ] Docker Compose funcionando (API + PostgreSQL + Redis)
- [ ] Migrations iniciais com Alembic (`clients`, `policies`, `claims`, `conversations`, `commissions`)
- [ ] FastAPI com rotas de webhook (`/webhook/whatsapp`, `/scheduler/commission-check`)
- [ ] Integração Z-API: receber e enviar mensagem simples via WhatsApp
- [ ] Pipeline de CI (GitHub Actions) com lint e testes
- [ ] `.env.example` atualizado com todas as variáveis do novo escopo
- [ ] Playwright instalado e validado no container
- [ ] Importação inicial da carteira via CSV exportado do Agger

---

## M2 — Agente de Comissionamento (Semanas 4–7)

### Entregas esperadas

- [ ] `InsurerPortalService` com adapters por seguradora (API e RPA)
- [ ] `CommissionService` com CRUD de comissões
- [ ] `NfseService` integrado com Focus NFe API
- [ ] Resolução automática de 2FA (TOTP, e-mail, SMS)
- [ ] Subgraph LangGraph do Agente de Comissionamento
- [ ] Tools implementadas: `fetch_commission_data`, `handle_2fa`, `consolidate_report`, `emit_nfse`, `send_daily_summary`, `alert_missing_commission`
- [ ] CRON scheduler diário (08:00 BRT)
- [ ] Testes unitários das tools, adapters e nós do grafo
- [ ] Teste de ponta a ponta com pelo menos 2 seguradoras reais

---

## M3 — Agente de Sinistros (Semanas 6–10)

### Entregas esperadas

- [ ] `ClaimService` com CRUD de sinistros
- [ ] Subgraph LangGraph do Agente de Sinistros (relay pattern)
- [ ] Tools implementadas: `classify_claim`, `collect_claim_info`, `open_claim_at_insurer`, `relay_update_to_client`, `escalate_to_broker`, `store_claim_history`
- [ ] Orquestrador configurado para rotear WhatsApp → Agente de Sinistros
- [ ] Upload de fotos via WhatsApp → S3
- [ ] Escalada automática para sinistros graves com resumo estruturado
- [ ] Testes dos tipos mais comuns (guincho, assistência, vidro, colisão)

---

## Integrações — Status

| Integração | Responsável | Status |
|---|---|---|
| WhatsApp Business API (Z-API) | — | ⬜ Conta não criada |
| PostgreSQL (local/Docker) | — | ⬜ Não configurado |
| Redis (local/Docker) | — | ⬜ Não configurado |
| AWS S3 | — | ⬜ Credenciais pendentes |
| Focus NFe API | — | ⬜ Conta não criada |
| Portais das seguradoras (mapeamento) | — | ⬜ Aguardando lista da corretora |
| Playwright (RPA) | — | ⬜ A instalar no container |
| Gateway SMS (2FA) | — | ⬜ A definir provedor |
| SendGrid | — | ⬜ Conta não criada |
| LangSmith | — | ⬜ Projeto não criado |
| Sentry | — | ⬜ Projeto não criado |
| Carteira de apólices (CSV do Agger) | — | ⬜ Exportação pendente com a corretora |

---

## Decisões Abertas

| # | Decisão | Prazo |
|---|---|---|
| D-01 | Confirmar provedor WhatsApp: Z-API vs. Twilio | Antes de M1 |
| D-02 | Definir ambiente de deploy do MVP: Railway vs. AWS | Antes de M1 |
| D-03 | Formato de importação das apólices: CSV do Agger ou digitação manual | Antes de M1 |
| D-04 | Mapear seguradoras e tipo de acesso por portal (API vs. RPA vs. 2FA) | Antes de M2 |
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

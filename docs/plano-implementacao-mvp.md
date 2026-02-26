# Plano de Implementação — MVP brokerAI

## Contexto

O brokerAI é uma plataforma de agentes de IA para corretoras de seguros brasileiras. O MVP entrega dois agentes independentes:

1. **Agente de Comissionamento** — acessa portais de seguradoras diariamente, consolida comissões, emite NFS-e automaticamente e envia resumo por WhatsApp
2. **Agente de Sinistros** — recebe mensagens do cliente via WhatsApp, coleta dados do sinistro, abre chamado na seguradora e faz relay bidirecional até o encerramento

A arquitetura, modelos de dados, state schemas e grafos LangGraph já estão completamente desenhados. **Todo o código atual são stubs (`raise NotImplementedError`)**. Este plano cobre a implementação real de cada camada.

---

## Estado Atual do Repositório

### Já implementado (não tocar sem necessidade)
- `models/config.py` — Settings pydantic completo ✅
- `models/database.py` — SQLAlchemy models completos (Client, Policy, Claim, Conversation, Commission, Insurer) ✅
- `models/schemas.py` — Pydantic schemas Z-API + responses ✅
- `agents/*/graph.py` — Grafos LangGraph com routing completo ✅
- `agents/*/prompts.py` — Prompts em PT-BR ✅
- `agents/commissioning/portal_adapters/base.py` — Interface abstrata ✅
- `tests/conftest.py` — Fixtures pytest (SQLite in-memory + API client) ✅
- `migrations/env.py` + `alembic.ini` — Alembic async configurado ✅
- `api/main.py` — FastAPI app com lifespan e rotas registradas ✅
- `services/insurer_portal_service.py` — `get_adapter()` com match expression ✅
- `services/scheduler_service.py` — `create_scheduler()` com CRON configurado ✅

### Tudo a implementar (stubs)
- `api/routes/webhook.py` — `whatsapp_webhook()`
- `api/middleware/auth.py` — `verify_zapi_signature()`, `verify_internal_token()`
- `agents/orchestrator/nodes.py` — todos os 4 nós
- `agents/claims/nodes.py` — todos os 7 nós
- `agents/claims/tools.py` — todas as 8 tools
- `agents/commissioning/nodes.py` — todos os 6 nós
- `agents/commissioning/tools.py` — todas as 6 tools
- `agents/commissioning/portal_adapters/api_adapter.py` — ApiAdapter
- `agents/commissioning/portal_adapters/rpa_adapter.py` — RpaAdapter
- `agents/commissioning/portal_adapters/email_adapter.py` — EmailAdapter
- `services/notification_service.py` — Z-API + SendGrid
- `services/commission_service.py` — CRUD comissões
- `services/claim_service.py` — CRUD sinistros
- `services/nfse_service.py` — Focus NFe API
- `services/policy_service.py` — import CSV + consultas
- `services/scheduler_service.py` — `run_commission_check()`

---

## Pré-Requisitos (Antes de Começar a Codificar)

### Bloqueadores externos — aguardar reunião com cliente
- [ ] Lista das 10 seguradoras prioritárias + tipo de acesso (API / RPA / e-mail)
- [ ] Credenciais de acesso a ≥ 2 portais de seguradora
- [ ] CNPJ da corretora + código IBGE do município (Focus NFe)
- [ ] Número WhatsApp Business dedicado para o agente
- [ ] Exportação CSV do Agger com carteira de apólices ativas

### Setup de contas técnicas — fazer em paralelo à reunião
- [ ] Anthropic API key → console.anthropic.com
- [ ] Z-API account → z-api.io (≈ R$ 100/mês por instância)
- [ ] Focus NFe account → focusnfe.com.br (homologação gratuita)
- [ ] LangSmith project → smith.langchain.com (gratuito)
- [ ] Sentry project → sentry.io (gratuito no tier básico)
- [ ] AWS account + S3 bucket
- [ ] Definir ambiente de deploy: Railway (simples) ou AWS ECS

---

## M1 — Fundação (Semanas 1–3)

**Objetivo**: Infraestrutura funcional, WhatsApp recebendo mensagens, banco de dados criado.

### 1.1 Docker Compose + Environment
- [ ] Preencher `.env` a partir de `.env.example` com credenciais reais
- [ ] Validar `docker compose up` levanta api + postgres + redis sem erros
- [ ] Validar `GET /health` retorna `{"status": "ok"}`
- [ ] Criar migration inicial: `alembic revision --autogenerate -m "initial schema"`
- [ ] Aplicar migration: `alembic upgrade head`
- [ ] Verificar tabelas criadas no Postgres: clients, policies, insurers, claims, conversations, commissions

**Arquivos**: `docker-compose.yml`, `.env`, `migrations/versions/`

### 1.2 Autenticação — `api/middleware/auth.py`
- [ ] Implementar `verify_zapi_signature()`:
  - Ler header `x-zapi-signature`
  - Calcular HMAC-SHA256 do body com `settings.zapi_webhook_secret`
  - Retornar `HTTPException(401)` se inválido
- [ ] Implementar `verify_internal_token()`:
  - Ler header `Authorization: Bearer <token>`
  - Comparar com `settings.internal_api_token` (nova var no config)
  - Retornar `HTTPException(401)` se inválido
- [ ] Adicionar `internal_api_token: str` em `models/config.py` e `.env.example`
- [ ] Testes: `tests/unit/test_auth.py` — assinatura válida, inválida, token ausente

**Arquivos**: `api/middleware/auth.py`, `models/config.py`, `.env.example`

### 1.3 Notification Service — `services/notification_service.py`
- [ ] Implementar `send_whatsapp_message(phone, message)`:
  - POST `https://api.z-api.io/instances/{instance_id}/token/{token}/send-text`
  - Body: `{"phone": phone, "message": message}`
  - Retornar `True` se status 2xx
- [ ] Implementar `send_broker_alert(message)`:
  - Chama `send_whatsapp_message(settings.broker_notification_phone, message)`
- [ ] Implementar `send_email(to, subject, body)`:
  - POST SendGrid `/v3/mail/send` via httpx
  - Retornar `True` se status 2xx
- [ ] Testes: `tests/unit/test_notification_service.py` — mock httpx, verificar payload

**Arquivos**: `services/notification_service.py`

### 1.4 Webhook Route — `api/routes/webhook.py`
- [ ] Implementar `whatsapp_webhook(request)`:
  - Validar assinatura via `verify_zapi_signature`
  - Parsear body como `ZApiWebhookPayload`
  - Ignorar mensagens `fromMe == True`
  - Extrair `phone`, `body`, `mediaUrl` (se mídia)
  - Construir `OrchestratorState` inicial
  - Invocar `build_orchestrator_graph().invoke(state)`
  - Retornar `{"status": "ok"}`
- [ ] Testes: `tests/unit/test_webhook.py` — payload válido, assinatura inválida, mensagem própria

**Arquivos**: `api/routes/webhook.py`

### 1.5 Policy Service — importação CSV do Agger
- [ ] Implementar `import_from_csv(file_path)`:
  - Ler CSV com `csv.DictReader`
  - Para cada linha: upsert em `policies` + `clients` + `insurers`
  - Retornar total de registros importados
- [ ] Implementar `get_policy_by_plate(plate)`:
  - SELECT em `policies` JOIN `clients` pelo campo de placa no `claim_info`
- [ ] Implementar `get_policy_by_number(policy_number)`:
  - SELECT direto em `policies.policy_number`
- [ ] Implementar `get_active_policies()`:
  - SELECT WHERE status = 'active'
- [ ] Criar script de importação inicial: `scripts/import_portfolio.py`
- [ ] Testes: `tests/unit/test_policy_service.py` — fixture CSV, upsert, consultas

**Arquivos**: `services/policy_service.py`, `scripts/import_portfolio.py`

### 1.6 CI/CD — GitHub Actions
- [ ] Criar `.github/workflows/ci.yml`:
  ```yaml
  on: [push, pull_request]
  jobs:
    test:
      runs-on: ubuntu-latest
      services:
        redis:
          image: redis:7-alpine
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with: {python-version: '3.11'}
        - run: pip install -e ".[dev]"
        - run: ruff check .
        - run: mypy .
        - run: pytest tests/ -v --cov
  ```
- [ ] Validar que pipeline passa no primeiro push

**Arquivos**: `.github/workflows/ci.yml`

### 1.7 Playwright Setup
- [ ] Validar que `scripts/install_browsers.py` funciona no container
- [ ] Adicionar ao Dockerfile: `RUN python scripts/install_browsers.py`
- [ ] Teste básico: `tests/unit/test_playwright.py` — abre about:blank em headless

**Arquivos**: `Dockerfile`, `scripts/install_browsers.py`

### M1 — Critério de Conclusão
- `GET /health` retorna 200
- `POST /webhook/whatsapp` aceita payload válido e rejeita assinatura inválida
- Banco criado com todas as tabelas
- `send_whatsapp_message()` envia mensagem real para número de teste
- Todos os testes do M1 passam: `pytest tests/ -v`
- CI verde no GitHub Actions

---

## M2 — Agente de Comissionamento (Semanas 4–7)

**Objetivo**: Ciclo diário completo funcionando com ≥ 2 seguradoras reais.

### 2.1 Commission Service — `services/commission_service.py`
- [ ] Implementar `save_commission(commission)`:
  - INSERT em `commissions` com `asyncpg`
  - Retornar UUID gerado
- [ ] Implementar `get_commissions_by_date(date)`:
  - SELECT WHERE `run_date = date`
- [ ] Implementar `mark_nfse_emitted(commission_id, nfse_number, pdf_url)`:
  - UPDATE SET `status='nfse_emitted', nfse_number=..., nfse_emitted_at=now()`
- [ ] Implementar `mark_nfse_failed(commission_id, error)`:
  - UPDATE SET `status='nfse_failed'` + registrar erro em `errors`
- [ ] Testes: `tests/unit/test_commission_service.py` — CRUD com db_session fixture

**Arquivos**: `services/commission_service.py`

### 2.2 NFS-e Service — `services/nfse_service.py`
- [ ] Implementar `emit_nfse(commission)`:
  - POST `{FOCUS_NFE_BASE_URL}/v2/nfse?ref={commission_id}`
  - Body: dados estruturados da NFS-e (prestador=CNPJ corretora, tomador=CNPJ seguradora, serviço=intermediação, valor=net_amount)
  - Retornar `{nfse_number, pdf_url, status}`
- [ ] Implementar `check_nfse_status(nfse_reference)`:
  - GET `{FOCUS_NFE_BASE_URL}/v2/nfse/{nfse_reference}`
- [ ] Implementar `cancel_nfse(nfse_number, reason)`:
  - DELETE `{FOCUS_NFE_BASE_URL}/v2/nfse/{nfse_number}`
- [ ] Testes: `tests/unit/test_nfse_service.py` — mock httpx

**Arquivos**: `services/nfse_service.py`

### 2.3 Insurer Portal Service — `services/insurer_portal_service.py`
- [ ] Implementar `load_insurer_credentials(insurer_id)`:
  - Ler `INSURER_CREDENTIALS_PATH`
  - Descriptografar com `INSURER_CREDENTIALS_KEY` (AES-256 via `cryptography`)
  - Retornar dict com credenciais para o insurer_id
- [ ] Implementar `fetch_commissions(insurer)`:
  - Chamar `get_adapter()` → adapter correto
  - `await adapter.login()`
  - `commissions = await adapter.fetch_commissions()`
  - `await adapter.logout()`
  - Retornar lista de comissões + logar erros

**Arquivos**: `services/insurer_portal_service.py`

### 2.4 API Adapter — `agents/commissioning/portal_adapters/api_adapter.py`
- [ ] Implementar `login()`:
  - POST ao `token_url` com `client_id` e `client_secret`
  - Armazenar `self._token`
- [ ] Implementar `fetch_commissions()`:
  - GET ao endpoint de comissões com Bearer `self._token`
  - Retornar lista normalizada: `[{insurer: str, gross_amount, net_amount, reference_month, ...}]`
- [ ] Implementar `logout()`:
  - POST ao endpoint de revogação se configurado
- [ ] Testes: `tests/unit/test_api_adapter.py` — mock httpx

**Arquivos**: `agents/commissioning/portal_adapters/api_adapter.py`

### 2.5 RPA Adapter — `agents/commissioning/portal_adapters/rpa_adapter.py`
- [ ] Implementar `login()`:
  - `async with async_playwright() as p:` → `browser = await p.chromium.launch(headless=True)`
  - Navegar até `portal_url`, preencher `username` e `password`
  - Se `two_fa_method == 'totp'`: `pyotp.TOTP(credentials['totp_secret']).now()`
  - Se `two_fa_method == 'email'`: ler código do IMAP (chamar `_read_otp_from_email()`)
  - Armazenar `self._page`
- [ ] Implementar `fetch_commissions()`:
  - Navegar para seção de extratos
  - Extrair dados da tabela ou baixar PDF/XLSX
  - Se PDF/XLSX: upload para S3, OCR via Textract
  - Retornar lista normalizada
- [ ] Implementar `logout()`:
  - Clicar em sair e fechar browser
- [ ] Método privado `_read_otp_from_email()`:
  - Conectar IMAP, buscar e-mail do remetente da seguradora com assunto "código" ou similar
  - Extrair código OTP com regex
- [ ] Testes: `tests/unit/test_rpa_adapter.py` — mock Playwright

**Arquivos**: `agents/commissioning/portal_adapters/rpa_adapter.py`

### 2.6 Email Adapter — `agents/commissioning/portal_adapters/email_adapter.py`
- [ ] Implementar `login()`:
  - `aioimaplib.IMAP4_SSL(host, port)` + `login(email, password)`
  - Armazenar `self._client`
- [ ] Implementar `fetch_commissions()`:
  - SEARCH para mensagens do `sender_filter` não lidas
  - Para cada mensagem: baixar anexos com extensões em `attachment_types`
  - Upload para S3 via `boto3`
  - OCR do PDF via Mistral OCR ou AWS Textract
  - Extrair `gross_amount`, `net_amount`, `reference_month`
- [ ] Implementar `logout()`:
  - `await self._client.logout()`
- [ ] Testes: `tests/unit/test_email_adapter.py` — mock aioimaplib

**Arquivos**: `agents/commissioning/portal_adapters/email_adapter.py`

### 2.7 Commissioning Tools — `agents/commissioning/tools.py`
- [ ] Implementar `fetch_commission_data(insurer_id)`:
  - Chamar `insurer_portal_service.fetch_commissions(insurer)`
  - Retornar `{insurer, commissions, extracted_at}`
- [ ] Implementar `handle_2fa(insurer_id, method)`:
  - Delegar para lógica no adapter (chamado internamente pelo adapter)
- [ ] Implementar `consolidate_report(commissions)`:
  - Agrupar por seguradora, somar totais
  - Retornar `{total, by_insurer, date}`
- [ ] Implementar `emit_nfse(commission)`:
  - Chamar `nfse_service.emit_nfse(commission)`
  - Chamar `commission_service.mark_nfse_emitted()` ou `mark_nfse_failed()`
- [ ] Implementar `send_daily_summary(report, nfse_results)`:
  - Formatar mensagem com template de `prompts.DAILY_SUMMARY_TEMPLATE`
  - Chamar `notification_service.send_broker_alert(message)`
- [ ] Implementar `alert_missing_commission(insurer_id, reason)`:
  - Chamar `notification_service.send_broker_alert()`

**Arquivos**: `agents/commissioning/tools.py`

### 2.8 Commissioning Nodes — `agents/commissioning/nodes.py`
- [ ] Implementar `load_insurers_node(state)`:
  - SELECT `insurers WHERE active = true` via SQLAlchemy
  - Preencher `state['insurers_pending']` com IDs
- [ ] Implementar `fetch_commission_node(state)`:
  - Para cada insurer_id em `insurers_pending`:
    - Chamar `fetch_commission_data.invoke({insurer_id})`
    - Se sucesso: mover para `insurers_done`, adicionar em `commissions`
    - Se erro: mover para `insurers_failed`, adicionar em `errors`
- [ ] Implementar `consolidate_node(state)`:
  - Chamar `consolidate_report.invoke({commissions})`
  - Salvar cada comissão em DB via `commission_service.save_commission()`
- [ ] Implementar `emit_nfse_node(state)`:
  - Para cada comissão em `state['commissions']`:
    - Chamar `emit_nfse.invoke({commission})`
    - Classificar em `nfse_emitted` ou `nfse_failed`
- [ ] Implementar `alert_failures_node(state)`:
  - Para cada insurer em `insurers_failed`:
    - Chamar `alert_missing_commission.invoke({insurer_id, reason})`
- [ ] Implementar `send_summary_node(state)`:
  - Chamar `send_daily_summary.invoke({report, nfse_emitted})`
  - Marcar `state['report_sent'] = True`

**Arquivos**: `agents/commissioning/nodes.py`

### 2.9 Scheduler Service — finalizar
- [ ] Implementar `run_commission_check()`:
  - Construir estado inicial `CommissioningState` com `run_date = today`
  - `graph = build_commissioning_graph()`
  - `await graph.ainvoke(initial_state)`
  - Logar resultado e erros

**Arquivos**: `services/scheduler_service.py`

### M2 — Critério de Conclusão
- CRON das 08:00 BRT executa sem erros
- Comissões de ≥ 2 seguradoras extraídas e salvas no banco
- NFS-e emitida para cada comissão via Focus NFe
- Resumo enviado por WhatsApp para a corretora
- Seguradoras com falha recebem alerta separado
- Todos os testes do M2 passam: `pytest tests/ -v`

---

## M3 — Agente de Sinistros (Semanas 6–10)

**Objetivo**: Relay bidirecional funcionando — cliente abre sinistro, agente relay com seguradora até encerramento.

### 3.1 Claim Service — `services/claim_service.py`
- [ ] Implementar `create_claim(claim_data)`:
  - INSERT em `claims` e `conversations` (status='active')
  - Salvar estado em Redis: `SETEX conversation:{client_phone} 30days {ClaimsState_JSON}`
  - Retornar UUID do sinistro
- [ ] Implementar `get_claim(claim_id)`:
  - SELECT com JOIN em `policies`, `clients`, `insurers`
- [ ] Implementar `update_claim_status(claim_id, status)`:
  - UPDATE `claims.status`
  - Atualizar Redis se conversa ainda ativa
- [ ] Implementar `assign_to_broker(claim_id, user_id)`:
  - UPDATE `claims.escalated_to = user_id` + `status = 'escalated'`
- [ ] Implementar `close_claim(claim_id)`:
  - UPDATE `claims.status = 'closed', closed_at = now()`
  - UPDATE `conversations.status = 'closed', closed_at = now()`
  - DELETE da Redis: `DEL conversation:{client_phone}`
- [ ] Testes: `tests/unit/test_claim_service.py`

**Arquivos**: `services/claim_service.py`

### 3.2 Claims Tools — `agents/claims/tools.py`
- [ ] Implementar `classify_claim(claim_type, description)`:
  - Lógica baseada em regras + LLM como fallback
  - `simple`: guincho, pane, vidro, assistência 24h, alagamento parcial, furto de acessório
  - `grave`: colisão com terceiros, furto/roubo total, incêndio, acidente com vítima
  - Retornar `{severity, auto_resolve}`
- [ ] Implementar `collect_claim_info(conversation_id)`:
  - Usar LLM (Claude) para conduzir conversa estruturada
  - Coletar: tipo, placa ou apólice, localização, descrição
  - Retornar dados estruturados
- [ ] Implementar `upload_document(conversation_id, media_url, doc_type)`:
  - Baixar arquivo da `media_url` (Z-API media endpoint)
  - Upload para S3: `s3://{bucket}/claims/{conversation_id}/{doc_type}_{timestamp}.{ext}`
  - Retornar URL pública do S3
- [ ] Implementar `open_claim_at_insurer(claim_id, insurer_id, claim_info)`:
  - Dependendo de `insurer_channel`: API, portal_chat (RPA), ou WhatsApp
  - Retornar `{thread_id, channel, opened_at}`
- [ ] Implementar `check_insurer_portal_for_updates(claim_id, insurer_id, thread_id)`:
  - RPA: navegar no portal e verificar notas/status do thread_id
  - Retornar `{update_status, update_text, new_status, checked_at}`
- [ ] Implementar `relay_update_to_client(conversation_id, update)`:
  - Formatar mensagem com LLM (empático, claro, em PT-BR)
  - Chamar `notification_service.send_whatsapp_message()`
- [ ] Implementar `escalate_to_broker(claim_id, reason, summary)`:
  - Formatar resumo estruturado
  - Chamar `notification_service.send_broker_alert()`
  - Chamar `claim_service.assign_to_broker()`
- [ ] Implementar `store_claim_history(claim_id)`:
  - Chamar `claim_service.close_claim()`
  - Migrar messages do Redis para `conversations.messages` no PostgreSQL
- [ ] Testes: `tests/unit/test_claims_tools.py`

**Arquivos**: `agents/claims/tools.py`

### 3.3 Claims Nodes — `agents/claims/nodes.py`
- [ ] Implementar `collect_info_node(state)`:
  - Criar LLM chain com `CLAIMS_SYSTEM_PROMPT`
  - Invocar `collect_claim_info.invoke({conversation_id})`
  - Preencher `state['claim_info']`, `state['claim_type']`, `state['policy_id']`
  - Se mídia recebida: chamar `upload_document()`
- [ ] Implementar `classify_node(state)`:
  - Chamar `classify_claim.invoke({claim_type, description})`
  - Preencher `state['severity']`
- [ ] Implementar `open_claim_node(state)`:
  - Chamar `open_claim_at_insurer.invoke({...})`
  - Preencher `state['insurer_thread_id']`, `state['insurer_channel']`, `state['waiting_since']`
  - Enviar mensagem ao cliente: "Sinistro aberto. Te aviso assim que tiver novidade."
- [ ] Implementar `check_updates_node(state)`:
  - Chamar `check_insurer_portal_for_updates.invoke({...})`
  - Preencher `state['update_status']`, `state['last_update']`
  - Incrementar `state['poll_count']`, atualizar `state['last_polled_at']`
  - Persistir estado em Redis
- [ ] Implementar `relay_to_client_node(state)`:
  - Chamar `relay_update_to_client.invoke({...})`
  - Se `update_status == 'closed'`: marcar `state['closed'] = True`
- [ ] Implementar `escalate_node(state)`:
  - Chamar `escalate_to_broker.invoke({...})`
  - Marcar `state['escalated'] = True`
  - Enviar mensagem ao cliente: "Um corretor vai assumir o seu caso."
- [ ] Implementar `close_node(state)`:
  - Enviar mensagem de encerramento ao cliente
  - Chamar `store_claim_history.invoke({claim_id})`
  - Marcar `state['closed'] = True`, `state['status'] = 'closed'`

**Arquivos**: `agents/claims/nodes.py`

### 3.4 Orchestrator Nodes — `agents/orchestrator/nodes.py`
- [ ] Implementar `load_conversation_node(state)`:
  - Conectar Redis: `redis.get(f"conversation:{client_phone}")`
  - Se existe: `state['has_active_conversation'] = True`, carregar `conversation_id`
  - Se não existe: `state['has_active_conversation'] = False`
- [ ] Implementar `detect_intent_node(state)`:
  - Criar LLM chain com `INTENT_DETECTION_PROMPT`
  - Invocar com `state['message']`
  - Parsear resposta: `{intent: "claim"|"faq"|"unknown", confidence: 0.0-1.0}`
  - Se `confidence < 0.6`: forçar `intent = "unknown"`
  - Preencher `state['intent']`, `state['confidence']`
- [ ] Implementar `faq_handler_node(state)`:
  - Criar LLM chain com contexto da corretora (knowledge base)
  - Responder dúvidas sobre cobertura, vencimento, boleto, como acionar seguro
  - Enviar resposta via `notification_service.send_whatsapp_message()`
- [ ] Implementar `human_handoff_node(state)`:
  - Chamar `notification_service.send_broker_alert()` com mensagem original
  - Enviar mensagem ao cliente: "Um corretor vai retornar em breve."

**Arquivos**: `agents/orchestrator/nodes.py`

### M3 — Critério de Conclusão
- Cliente envia "quero abrir um sinistro" → agente coleta dados, classifica, abre na seguradora
- Sinistros simples: relay funciona até encerramento
- Sinistros graves: escalada imediata com resumo estruturado para corretor
- Upload de fotos funcionando (S3)
- Conversa ativa persiste no Redis entre sessões (client_phone → state)
- Histórico migrado para PostgreSQL ao encerrar
- Testes dos fluxos: guincho, vidro, colisão
- Todos os testes do M3 passam

---

## MVP — Lançamento (Mês 3)

### Checklist final antes de produção
- [ ] **Segurança**: Todos os segredos em variáveis de ambiente, nenhum no código
- [ ] **CPF/CNPJ**: Verificar que dados sensíveis são tokenizados antes de entrar no LLM
- [ ] **Testes de ponta a ponta**: Ciclo completo de comissionamento + sinistro com dados reais
- [ ] **Observabilidade**: LangSmith capturando traces, Sentry capturando erros
- [ ] **Deploy**: Container rodando em ambiente de staging (Railway ou AWS)
- [ ] **Webhook público**: URL do webhook configurada no Z-API apontando para produção
- [ ] **CRON validado**: Ciclo de comissionamento testado manualmente via `POST /scheduler/commission-check`
- [ ] **Monitoramento**: Alertas de falha crítica configurados no Sentry
- [ ] **Retenção SUSEP**: `conversations.messages` com policy de retenção 5 anos confirmada

---

## Arquivos Críticos por Milestone

| Milestone | Arquivos Principais |
|---|---|
| M1 | `api/middleware/auth.py`, `api/routes/webhook.py`, `services/notification_service.py`, `services/policy_service.py`, `.github/workflows/ci.yml`, `migrations/versions/` |
| M2 | `services/commission_service.py`, `services/nfse_service.py`, `services/insurer_portal_service.py`, `agents/commissioning/tools.py`, `agents/commissioning/nodes.py`, `agents/commissioning/portal_adapters/*.py`, `services/scheduler_service.py` |
| M3 | `services/claim_service.py`, `agents/claims/tools.py`, `agents/claims/nodes.py`, `agents/orchestrator/nodes.py` |

---

## Verificação End-to-End

### Testar M1
```bash
docker compose up -d
alembic upgrade head
curl GET http://localhost:8000/health
# Enviar mensagem real pelo WhatsApp e verificar log do webhook
```

### Testar M2
```bash
curl -X POST http://localhost:8000/scheduler/commission-check \
  -H "Authorization: Bearer {internal_token}"
# Verificar: comissão salva no banco, NFS-e emitida, WhatsApp da corretora recebeu resumo
```

### Testar M3
```bash
# Enviar "Preciso de guincho" pelo WhatsApp do cliente
# Verificar: dados coletados, chamado aberto, relay funcionando
# Enviar foto de dano → verificar upload S3
# Enviar "meu carro foi roubado" → verificar escalada para humano
```

### Rodar toda a suite de testes
```bash
docker compose exec api pytest tests/ -v --cov=. --cov-report=html
docker compose exec api ruff check .
docker compose exec api mypy .
```

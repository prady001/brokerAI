# Ralph Loop — M1: Fundação

Você está implementando o **M1 (Fundação)** do brokerAI na branch `feat/m1-fundacao`.

Leia antes de começar:
- `CLAUDE.md` — instruções do projeto, stack, convenções
- `project_status.md` — status atual e entregas esperadas do M1
- `docs/agentes/sinistro.md`, `docs/agentes/onboarding.md`, `docs/agentes/renovacao.md`

---

## O que já está feito (não refaça)

- `docker-compose.yml` — Evolution API, PostgreSQL, Redis configurados
- `.env.example` — atualizado com Evolution API e Cloudflare R2
- `models/database.py` — todos os modelos (Client, Policy, Claim, Renewal, Conversation, Commission)
- `models/config.py` — Settings atualizado com novas variáveis
- `migrations/versions/0001_initial.py` — migration inicial com todas as tabelas
- `pyproject.toml` — dependências definidas
- `Dockerfile` — funcional

---

## Tarefas pendentes do M1

Implemente **uma tarefa por iteração**, na ordem abaixo. Após cada tarefa, faça um commit seguindo as convenções do projeto (Conventional Commits em pt-BR, scope relevante).

### Tarefa 1 — Middleware de autenticação (`api/middleware/auth.py`)

Implemente as duas funções:

**`verify_internal_token`**: valida Bearer token para rotas internas (scheduler, admin).
- Lê `INTERNAL_API_TOKEN` de `settings` (adicione ao `models/config.py` com default vazio)
- Se o header `Authorization` não for `Bearer {token}` → HTTP 401
- Se `settings.internal_api_token` estiver vazio (dev) → deixa passar

**`verify_evolution_webhook`**: valida chamadas do Evolution API webhook.
- Evolution API envia o header `apikey` com o valor de `EVOLUTION_API_KEY`
- Valida que o header `apikey` bate com `settings.evolution_api_key`
- Se não bater → HTTP 401
- Renomeie a função Z-API que estava lá e apague referências ao Z-API

### Tarefa 2 — Webhook handler Evolution API (`api/routes/webhook.py`)

Implemente o handler para receber mensagens do Evolution API.

O Evolution API envia POST com este payload para `MESSAGES_UPSERT`:
```json
{
  "event": "messages.upsert",
  "instance": "brokerai",
  "data": {
    "key": { "remoteJid": "5517999999999@s.whatsapp.net", "fromMe": false, "id": "abc123" },
    "pushName": "Nome do Cliente",
    "message": { "conversation": "texto da mensagem" },
    "messageType": "conversation",
    "messageTimestamp": 1234567890
  }
}
```

O handler deve:
1. Usar `verify_evolution_webhook` como dependency para autenticação
2. Ignorar mensagens enviadas por nós (`fromMe: true`) — retornar `{"status": "ignored"}`
3. Ignorar eventos que não sejam `messages.upsert` — retornar `{"status": "ignored"}`
4. Extrair `phone` (remoteJid sem `@s.whatsapp.net`), `name` (pushName) e `text` (message.conversation)
5. Por enquanto, apenas logar a mensagem recebida e retornar `{"status": "received", "phone": phone}`
6. O roteamento para agentes será implementado no M2 — não implemente ainda

### Tarefa 3 — Scheduler de renovações (`services/scheduler_service.py` + `api/routes/scheduler.py`)

**`services/scheduler_service.py`**: substituir o CRON de comissionamento pelo de renovações.
- Renomear `run_commission_check` → `run_renewal_check`
- Atualizar o job: usar `settings.renewal_cron_hour` e `settings.renewal_cron_timezone`
- ID do job: `"renewal_check"`, nome: `"Verificação diária de renovações"`
- `run_renewal_check` deve apenas logar `"Verificação de renovações iniciada"` por ora (implementação real no M4)

**`api/routes/scheduler.py`**: atualizar a rota.
- Mudar de `POST /scheduler/commission-check` → `POST /scheduler/renewal-check`
- Chamar `run_renewal_check` em vez de `run_commission_check`

**`api/main.py`**: verificar que o scheduler importa corretamente após a renomeação.

### Tarefa 4 — CRUD de apólices e clientes (`api/routes/admin.py`)

Crie `api/routes/admin.py` com rotas protegidas por `verify_internal_token`:

**Clientes:**
- `POST /admin/clients` — cadastrar novo cliente (campos: full_name, cpf_cnpj, phone_whatsapp, email, birth_date)
- `GET /admin/clients` — listar clientes (paginação: skip/limit)
- `GET /admin/clients/{client_id}` — buscar cliente por ID

**Apólices:**
- `POST /admin/policies` — cadastrar nova apólice (campos: client_id, insurer_id, policy_number, type, item_description, premium_amount, start_date, end_date, seller_phone)
- `GET /admin/policies` — listar apólices (filtros opcionais: client_id, status)
- `GET /admin/policies/{policy_id}` — buscar apólice por ID
- `PATCH /admin/policies/{policy_id}` — atualizar status ou seller_phone

Use os schemas Pydantic de `models/schemas.py`. Se os schemas necessários não existirem, crie-os lá.
Inclua o router em `api/main.py`.

### Tarefa 5 — Pipeline de CI (`​.github/workflows/ci.yml`)

Crie o pipeline com os jobs:

**`lint`**: roda em `ubuntu-latest`, Python 3.11
- Instalar dependências: `pip install -e ".[dev]"`
- `ruff check .`
- `mypy .` (pode usar `--ignore-missing-imports`)

**`test`**: roda após `lint`
- Instalar dependências: `pip install -e ".[dev]"`
- `pytest tests/ -v --cov=. --cov-report=term-missing`
- Usar variáveis de ambiente mínimas para o settings não falhar:
  `ANTHROPIC_API_KEY`, `EVOLUTION_API_KEY`, `DATABASE_URL` (sqlite para testes),
  `REDIS_URL`, `BROKER_NOTIFICATION_PHONE`, `BROKER_NOTIFICATION_EMAIL`

Trigger: push e pull_request na branch `main` e `feat/*`.

### Tarefa 6 — Testes unitários básicos (`tests/unit/`)

Escreva testes para:

**`tests/unit/test_webhook.py`**:
- `test_webhook_ignores_own_messages`: POST com `fromMe: true` → retorna `{"status": "ignored"}`
- `test_webhook_ignores_unknown_event`: POST com event diferente de `messages.upsert` → `{"status": "ignored"}`
- `test_webhook_receives_message`: POST com mensagem válida → retorna `{"status": "received"}`

**`tests/unit/test_admin_policies.py`**:
- `test_create_client`: POST `/admin/clients` com dados válidos → 201 + client_id
- `test_create_policy`: POST `/admin/policies` com dados válidos → 201 + policy_id
- `test_list_policies`: GET `/admin/policies` → 200 + lista

Use o `AsyncClient` e `db_session` já definidos em `tests/conftest.py`.
Para autenticação nas rotas admin: defina `settings.internal_api_token = ""` nos testes (bypass de auth em dev).

---

## Critérios de conclusão

O M1 está completo quando:

- [ ] `ruff check .` passa sem erros
- [ ] `mypy .` passa sem erros críticos
- [ ] `pytest tests/` passa com todos os testes verdes
- [ ] Todos os `raise NotImplementedError` do M1 foram removidos
- [ ] Nenhuma referência a Z-API, commission_check ou AWS no código implementado
- [ ] `project_status.md` atualizado com as entregas do M1 marcadas como concluídas

Quando todos os critérios estiverem satisfeitos, output:
<promise>M1 FUNDAÇÃO COMPLETO</promise>

---

## Convenções obrigatórias

- Commits: Conventional Commits em pt-BR (`feat(api)`, `fix(scheduler)`, `test(webhook)`, etc.)
- Idioma do código: inglês (nomes de variáveis, funções, classes)
- Idioma de logs, comentários e mensagens ao usuário: pt-BR
- Não criar arquivos de documentação `.md` além do que já existe
- Não implementar lógica de agentes LangGraph — isso é M2/M3/M4

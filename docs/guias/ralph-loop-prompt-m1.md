# Ralph Loop — M1 Fundação

## Contexto
Você está implementando o M1 do brokerAI, um sistema de agentes de IA para corretora de seguros brasileira.
Leia os seguintes arquivos antes de começar:
- `docs/architecture.md` — arquitetura completa e ADRs
- `docs/project_spec.md` — regras de negócio
- `CLAUDE.md` — convenções obrigatórias do projeto

## Escopo do MVP
O MVP consiste em dois agentes:
1. **Agente de Comissionamento** — acessa portais das seguradoras, consolida comissões, emite NFS-e, envia resumo
2. **Agente de Sinistros** — relay entre cliente (WhatsApp) e seguradora

O M1 é a fundação para ambos: infraestrutura, banco, API e integrações base.

## Tarefas do M1 (execute nesta ordem)

### 1. Configuração (models/config.py)
Criar classe `Settings` com pydantic-settings lendo todas as variáveis do `.env`.
Incluir: Anthropic, Z-API, banco, Redis, AWS, Focus NFe, SMS gateway, IMAP, credenciais de seguradoras.

### 2. Modelos do banco (models/database.py)
Criar modelos SQLAlchemy para: `Client`, `Policy`, `Claim`, `Conversation`, `Commission`.
Schemas exatos estão em `docs/architecture.md` seção 3 (Design dos Agentes).

### 3. Migrations (migrations/)
Configurar Alembic e criar migration inicial com todas as tabelas.

### 4. API principal (api/main.py)
FastAPI app com:
- Lifespan para conexão com banco na inicialização
- Inclusão das rotas de webhook e scheduler
- Middleware de CORS e tratamento de erros

### 5. Rotas (api/routes/)
- `webhook.py` → POST /webhook/whatsapp (recebe mensagens Z-API → Agente Sinistros)
- `scheduler.py` → POST /scheduler/commission-check (trigger do CRON → Agente Comissionamento)

### 6. Serviço de notificação básico (services/notification_service.py)
Função `send_whatsapp_message()` que chama a API Z-API via httpx.
Função `send_broker_alert()` que envia notificação para o número da corretora.

### 7. Scheduler (services/scheduler_service.py)
APScheduler configurado para rodar `commission-check` todo dia às 08:00 BRT.

### 8. Playwright setup (scripts/install_browsers.py)
Script para instalar o browser Chromium do Playwright no container.
Validar que consegue abrir uma página simples em modo headless.

### 9. Testes
Escrever testes para cada módulo em `tests/unit/`.
Usar pytest com fixtures em `tests/fixtures/`.

## Fluxo por tarefa
1. Implemente o módulo
2. Escreva os testes
3. Rode: `docker compose exec api pytest tests/ -v`
4. Corrija até passar
5. Rode: `docker compose exec api ruff check . && docker compose exec api mypy .`
6. Commit: `git add -p && git commit -m "feat(<scope>): <descrição em pt-BR>"`
7. Marque como `[x]` em `project_status.md`
8. Crie doc em `docs/<area>/<modulo>.md`

## Critério de conclusão
Quando todas as tarefas estiverem implementadas, testadas e commitadas, escreva exatamente:
<promise>M1_CONCLUIDO</promise>

## Restrições
- Todo texto para usuário final em pt-BR
- Dados sensíveis (CPF, financeiros, credenciais de seguradoras) nunca no histórico do LLM
- Credenciais de portais de seguradoras armazenadas em arquivo criptografado (`config/insurers.json.enc`)
- `emit_policy` deve lançar `NotImplementedError`
- Sem push para o remote — apenas commits locais

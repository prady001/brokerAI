# Ralph Loop — M1 Fundação

## Contexto
Você está implementando o M1 do brokerAI, um sistema de agentes de IA para corretora de seguros brasileira.
Leia os seguintes arquivos antes de começar:
- `architecture.md` — arquitetura completa e ADRs
- `project_spec.md` — regras de negócio
- `CLAUDE.md` — convenções obrigatórias do projeto

## Tarefas do M1 (execute nesta ordem)

### 1. Configuração (models/config.py)
Criar classe Settings com pydantic-settings lendo todas as variáveis do .env.

### 2. Modelos do banco (models/database.py)
Criar modelos SQLAlchemy para: Client, Policy, Claim, Conversation.
Schemas exatos estão em `architecture.md` seção 2.2.4.

### 3. Migrations (migrations/)
Configurar Alembic e criar migration inicial com todas as tabelas.

### 4. API principal (api/main.py)
FastAPI app com:
- Lifespan para conexão com banco na inicialização
- Inclusão das rotas de webhook e scheduler
- Middleware de CORS e tratamento de erros

### 5. Rotas (api/routes/)
- `webhook.py` → POST /webhook/whatsapp (recebe mensagens Z-API)
- `scheduler.py` → POST /scheduler/renewal-check (trigger do CRON)

### 6. Serviço de notificação básico (services/notification_service.py)
Função send_whatsapp_message() que chama a API Z-API via httpx.

### 7. Scheduler (services/scheduler_service.py)
APScheduler configurado para rodar renewal-check todo dia às 08:00 BRT.

### 8. Testes
Escrever testes para cada módulo criado em tests/unit/.
Usar pytest com fixtures em tests/fixtures/.

## Fluxo por tarefa
1. Implemente o módulo
2. Escreva os testes
3. Rode: `docker compose exec api pytest tests/ -v`
4. Corrija até passar
5. Rode: `docker compose exec api ruff check . && docker compose exec api mypy .`
6. Commit: `git add . && git commit -m "feat(<scope>): <descrição em pt-BR>"`
7. Marque como `[x]` em project_status.md
8. Crie doc em docs/<area>/<modulo>.md

## Critério de conclusão
Quando todas as 8 tarefas estiverem implementadas, testadas e commitadas, escreva exatamente:
<promise>M1_CONCLUIDO</promise>

## Restrições
- Todo texto para usuário final em pt-BR
- Dados sensíveis (CPF, financeiros) nunca no histórico do LLM
- emit_policy deve lançar NotImplementedError
- Sem push para o remote — apenas commits locais

# Ralph Loop — M4 Agente de Renovação

## Contexto

Você está implementando o M4 do brokerAI: o Agente de Renovação de Apólices.
Leia os seguintes arquivos antes de começar:

- `docs/agentes/renovacao.md` — especificação completa do agente (fluxo, régua, templates, exemplos)
- `docs/architecture.md` — arquitetura técnica e ADRs
- `CLAUDE.md` — convenções obrigatórias do projeto
- `project_status.md` — checklist do M4

## O que já existe (não reimplementar)

- `models/database.py` — modelo `Renewal` completo (id, policy_id, client_id, seller_phone, expiry_date, status, contact_count, last_contact_at, next_contact_at, client_intent, intent_notes)
- `services/scheduler_service.py` — `run_renewal_check()` como stub — **implementar aqui**
- `api/routes/scheduler.py` — rota `POST /scheduler/renewal-check` já conectada ao stub
- `agents/renewal/__init__.py` — diretório reservado
- `services/notification_service.py` — `send_whatsapp_message()` e `send_broker_alert()` prontos para uso

## Tarefas do M4 (execute nesta ordem)

### 1. RenewalService (`services/renewal_service.py`)

Criar classe `RenewalService` com:

- `get_expiring_policies(days_ahead: list[int]) -> list[RenewalCandidate]` — busca apólices ativas com `end_date` em exatamente N dias (para cada N em `days_ahead`). Retorna apenas apólices sem renovação em status `pending` ou `contacted`.
- `get_or_create_renewal(policy_id, client_id, seller_phone, expiry_date) -> Renewal` — cria registro de renovação se não existir.
- `update_renewal_status(renewal_id, status, intent=None, notes=None) -> Renewal`
- `register_contact_attempt(renewal_id) -> Renewal` — incrementa `contact_count`, atualiza `last_contact_at` e calcula `next_contact_at` conforme a régua.
- `get_renewal_by_id(renewal_id) -> Renewal | None`
- `get_active_renewal_for_client(client_id) -> Renewal | None` — busca renovação ativa (status `contacted`) para um cliente, usado ao receber resposta via WhatsApp.

Régua de `next_contact_at`:
- 1º contato (30 dias antes): próximo em 15 dias antes do vencimento
- 2º contato (15 dias antes): próximo em 7 dias antes do vencimento
- 3º contato (7 dias antes): próximo no dia do vencimento
- 4º contato (dia 0): marcar como `no_response` após 3 dias sem resposta

### 2. Schemas Pydantic (`models/schemas.py`)

Adicionar ao arquivo existente:

```python
class RenewalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    policy_id: uuid.UUID
    client_id: uuid.UUID
    seller_phone: str | None
    expiry_date: date
    status: str
    contact_count: int
    last_contact_at: datetime | None
    next_contact_at: datetime | None
    client_intent: str | None
    intent_notes: str | None
    created_at: datetime
```

### 3. Prompts do agente (`agents/renewal/prompts.py`)

Criar `RENEWAL_SYSTEM_PROMPT` em pt-BR. O agente deve:
- Identificar-se como assistente da corretora (não como IA, a menos que perguntado diretamente)
- Coletar a intenção do cliente (renovar, recusar, pedir cotação em outra seguradora)
- Ser cordial, direto e breve (mensagens de WhatsApp)
- Nunca prometer valores ou condições — apenas coletar intenção e repassar ao vendedor
- Nunca renovar a apólice diretamente

Incluir templates de mensagem ativa (os três templates de `docs/agentes/renovacao.md`) como constantes:
`TEMPLATE_30_DAYS`, `TEMPLATE_15_7_DAYS`, `TEMPLATE_DAY_ZERO`.

### 4. Tools do agente (`agents/renewal/tools.py`)

Implementar com `@tool` decorator (Pydantic-tipadas):

- `get_expiring_policies` — chama `RenewalService.get_expiring_policies`
- `send_renewal_contact(renewal_id, template_key, client_phone, message)` — envia mensagem via `notification_service.send_whatsapp_message`, incrementa `contact_count`
- `register_client_intent(renewal_id, intent: Literal["wants_renewal", "refused", "wants_quote"], notes: str | None)` — atualiza status e intenção
- `notify_seller(renewal_id, seller_phone, summary_message)` — envia resumo estruturado ao vendedor via `notification_service.send_broker_alert`
- `mark_renewal_status(renewal_id, status)` — atualiza status da renovação

### 5. Nós do grafo (`agents/renewal/nodes.py`)

Implementar nós assíncronos para o LangGraph:

- `check_expiring_policies(state)` — identifica apólices nos gatilhos 30/15/7/0 dias
- `send_contacts(state)` — envia mensagens WhatsApp para cada apólice elegível
- `process_client_response(state)` — processa resposta do cliente, extrai intenção via LLM
- `notify_sellers(state)` — notifica vendedores com resumo estruturado
- `update_statuses(state)` — atualiza status das renovações no banco

### 6. Grafo LangGraph (`agents/renewal/graph.py`)

Criar `RenewalState` (TypedDict) e o subgraph:

```
RenewalState:
  - policies_to_contact: list[dict]
  - contacts_sent: list[dict]
  - client_response: str | None       # quando acionado por WhatsApp
  - renewal_id: str | None            # quando acionado por WhatsApp
  - intent: str | None
  - notifications_sent: list[dict]
  - errors: list[str]
  - mode: Literal["cron", "whatsapp"] # como o agente foi acionado
```

Dois fluxos no mesmo grafo:
- **`mode=cron`**: `check_expiring_policies` → `send_contacts` → `update_statuses`
- **`mode=whatsapp`**: `process_client_response` → `notify_sellers` → `update_statuses`

### 7. Implementar `run_renewal_check` (`services/scheduler_service.py`)

Substituir o stub atual pela chamada real ao agente:

```python
async def run_renewal_check() -> None:
    from agents.renewal.graph import renewal_graph
    result = await renewal_graph.ainvoke({"mode": "cron", "policies_to_contact": [], ...})
    logger.info("Renovações verificadas: %s contatos enviados", len(result["contacts_sent"]))
```

### 8. Roteamento de respostas WhatsApp (`api/routes/webhook.py`)

Adicionar lógica ao handler existente: após receber mensagem do cliente, verificar se existe renovação ativa para o `client_id`. Se sim, rotear para o agente de renovação com `mode=whatsapp`.

Usar `RenewalService.get_active_renewal_for_client(client_id)` para decisão de roteamento.

### 9. Testes (`tests/unit/`)

- `tests/unit/test_renewal_service.py` — testar `get_expiring_policies` (mock DB), `register_contact_attempt` (lógica de régua), `update_renewal_status`
- `tests/unit/test_renewal_tools.py` — testar cada tool com mock de serviços
- `tests/unit/test_renewal_graph.py` — testar fluxo `mode=cron` e `mode=whatsapp` com mocks

## Fluxo por tarefa

1. Implemente o módulo
2. Escreva os testes
3. Rode: `docker compose exec api pytest tests/ -v`
4. Corrija até passar
5. Rode: `docker compose exec api ruff check . && docker compose exec api mypy .`
6. Commit: `git add -p && git commit -m "feat(renewal): <descrição em pt-BR>"`
7. Marque como `[x]` em `project_status.md`
8. Repita para a próxima tarefa

## Critério de conclusão

Quando todas as tarefas estiverem implementadas, testadas e commitadas, escreva exatamente:

<promise>M4_CONCLUIDO</promise>

## Restrições

- Todo texto para o usuário final em pt-BR
- Dados sensíveis (CPF, financeiros) nunca entram no histórico do LLM — usar tokens
- Nenhuma ação irreversível sem aprovação humana
- O agente **não renova a apólice** — apenas coleta intenção e repassa ao vendedor
- Templates WhatsApp ativos (`send_renewal_contact`) devem simular o envio em ambiente de desenvolvimento se `EVOLUTION_API_URL` não estiver configurada (log de aviso, sem erro)

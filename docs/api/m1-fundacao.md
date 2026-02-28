# M1 — Fundação: API, Webhook e CRUD

## Objetivo

O M1 estabelece a base técnica do brokerAI: servidor FastAPI com autenticação, webhook do Evolution API (WhatsApp), cadastro manual de carteira de apólices e pipeline de CI. Toda implementação posterior (agentes M2–M4) se apoia nessa fundação.

## Como funciona

### Autenticação (`api/middleware/auth.py`)

Duas camadas de autenticação protegem as rotas:

- **Webhook (Evolution API):** header `apikey` comparado via `hmac.compare_digest` contra `EVOLUTION_API_KEY`. Resistente a timing attacks.
- **Rotas internas (admin, scheduler):** header `Authorization: Bearer <token>` validado contra `INTERNAL_API_TOKEN`. Em ambiente `development` sem token configurado, acesso é liberado com aviso de log. Em produção, token ausente retorna HTTP 500.

### Webhook WhatsApp (`POST /webhook/whatsapp`)

Recebe eventos do Evolution API e filtra apenas o que importa para o M2+:

1. Rejeita eventos que não sejam `messages.upsert` → `{"status": "ignored"}`
2. Rejeita mensagens enviadas pelo próprio bot (`fromMe: true`) → `{"status": "ignored"}`
3. Extrai `phone` (remove `@s.whatsapp.net`), `name` e `text` da mensagem
4. Loga a mensagem recebida e retorna `{"status": "received", "phone": "..."}`

O roteamento para agentes (sinistro, onboarding, renovação) será implementado no M2 pelo Agente Orquestrador.

### CRUD de Carteira (`/admin/clients`, `/admin/policies`)

Rotas protegidas por token interno para cadastro manual da carteira da corretora:

| Rota | Método | Ação |
|---|---|---|
| `/admin/clients` | POST | Cria cliente |
| `/admin/clients` | GET | Lista clientes (paginado, max 200) |
| `/admin/clients/{id}` | GET | Busca cliente por ID |
| `/admin/policies` | POST | Cria apólice vinculada a cliente e seguradora |
| `/admin/policies` | GET | Lista apólices (filtros: client_id, status; max 200) |
| `/admin/policies/{id}` | GET | Busca apólice por ID |
| `/admin/policies/{id}` | PATCH | Atualiza status ou vendedor responsável |

### Scheduler de Renovação (`POST /scheduler/renewal-check`)

Rota para acionar manualmente a verificação de renovações. O scheduler também roda como processo standalone (`python -m services.scheduler_service`) via APScheduler, disparando automaticamente às 08:00 BRT. A implementação completa da régua de renovação está no M4.

### Pipeline CI (`.github/workflows/ci.yml`)

Dois jobs rodando em Python 3.11 a cada push/PR:

1. **Lint:** `ruff check .` + `mypy . --ignore-missing-imports`
2. **Testes:** `pytest tests/ -v --cov=.` com banco SQLite em memória

## Configuração

Variáveis de ambiente necessárias para o M1 (ver `.env.example`):

```env
# Autenticação WhatsApp
EVOLUTION_API_KEY=sua-chave-aqui

# Token interno (admin/scheduler)
INTERNAL_API_TOKEN=token-secreto-aqui   # deixar vazio em development

# Banco de dados
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/brokerai

# Ambiente
ENVIRONMENT=development   # ou production
```

## Exemplos

### Criar cliente via API

```bash
curl -X POST http://localhost:8000/admin/clients \
  -H "Authorization: Bearer $INTERNAL_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Maria Aparecida Silva",
    "cpf_cnpj": "123.456.789-00",
    "phone_whatsapp": "5517991234567",
    "email": "maria@example.com"
  }'
```

### Receber evento do Evolution API

```bash
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "apikey: $EVOLUTION_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "messages.upsert",
    "instance": "brokerai",
    "data": {
      "key": { "remoteJid": "5517999999999@s.whatsapp.net", "fromMe": false, "id": "ABC123" },
      "pushName": "João Silva",
      "message": { "conversation": "Preciso de ajuda com meu seguro" },
      "messageType": "conversation",
      "messageTimestamp": 1234567890
    }
  }'
# → {"status": "received", "phone": "5517999999999"}
```

### Executar scheduler standalone

```bash
python -m services.scheduler_service
# Inicia APScheduler com CRON às 08:00 BRT — Ctrl+C para encerrar
```

## Limitações conhecidas

- **Evolution API não conectada a número real:** aguardando chip dedicado para configuração. O webhook funciona localmente via `ngrok` ou em staging.
- **Agente Orquestrador não implementado:** o webhook recebe e loga a mensagem, mas ainda não roteia para nenhum agente. Roteamento é implementado no M2.
- **CRUD sem paginação por cursor:** a paginação usa `skip`/`limit` (offset-based). Para carteiras grandes (> 10k apólices), migrar para cursor-based pagination no M2+.
- **Scheduler sem persistência de jobs:** se o processo do scheduler reiniciar entre 00:00 e 08:00, o job daquele dia pode não executar. Solução definitiva no M4 com fila persistente.

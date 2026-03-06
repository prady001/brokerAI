# Sessão 06/03/2026 — Validação E2E do M2 com Docker e Gemini

## Contexto

Continuação da sessão anterior (28/02). M1 e M2 já estavam mergeados em main. O objetivo desta sessão foi validar o fluxo E2E do M2 com Docker em ambiente local, e contornar a ausência de crédito na API da Anthropic usando o Google Gemini (tier gratuito).

---

## O que foi feito

### 1. Factory de LLM multi-provider (`agents/llm.py`)

Criada uma factory central que seleciona o provedor de LLM com base na variável `LLM_PROVIDER` no `.env`. Suporta:

- `anthropic` (padrão) — Claude Haiku em dev, Claude Sonnet em prod
- `google` — Gemini via `langchain-google-genai`

Todos os agentes (`claims`, `orchestrator`, `renewal`) foram atualizados para usar `get_llm()` da factory em vez de instanciar `ChatAnthropic` diretamente.

### 2. Bug fixes da sessão anterior (não commitados)

Corrigidos bugs que impediam as migrations de rodar:

- **Migration 0001** — `sa.Enum(..., create_type=False)` ignorado pelo SQLAlchemy 2.0+asyncpg. Fix: trocar para `postgresql.ENUM(..., create_type=False)`.
- **Datetime timezone-aware** — `datetime.now(UTC)` rejeitado por colunas `TIMESTAMP WITHOUT TIME ZONE`. Fix: `.replace(tzinfo=None)` em `models/database.py`, `services/claim_service.py` e `services/renewal_service.py`.

### 3. Descobertas sobre o Google Gemini

| Modelo testado | Resultado |
|---|---|
| `gemini-2.0-flash` | ❌ Não disponível para novos usuários |
| `gemini-1.5-flash` | ❌ Não encontrado para API version v1beta |
| `gemini-2.0-flash-lite` | ❌ Não disponível para novos usuários |
| `gemini-2.5-flash` | ✅ Disponível — modelo thinking |

O `gemini-2.5-flash` funciona, mas como modelo "thinking" consumia parte do budget de tokens (256 era pouco). Fix: `max(max_tokens, 1024)` + `thinking_budget=0` para desabilitar o modo thinking e garantir output previsível.

### 4. LangSmith

- API key configurada em `.env` como `LANGCHAIN_API_KEY`
- Descoberta: `docker compose restart` **não** relê o `env_file`. Necessário `docker compose up --force-recreate` para carregar novas variáveis.

---

## Resultado do teste E2E

**Mensagem enviada:**
> "Oi, meu carro bateu hoje de manhã e preciso abrir um sinistro"

**Fluxo executado:**
1. Webhook recebido → `POST /webhook/whatsapp` 200 OK
2. Orquestrador detectou intenção: `claim` (confidence: 1.0)
3. Agente classificou: `colisão` / severidade `simples`
4. Estado salvo no Redis (`claim_conversation:5517999990001`)
5. Resposta gerada em pt-BR: *"Olá! Sinto muito pelo ocorrido. Para agilizar o atendimento, você poderia me informar a placa do veículo?"*
6. Envio WhatsApp: falha de conexão (esperado — sem chip real)

**Estado final no Redis:**
```json
{
  "status": "collecting",
  "claim_info": { "claim_type": "colisão" },
  "messages": [
    { "role": "user", "content": "Oi, meu carro bateu..." },
    { "role": "assistant", "content": "Olá! Sinto muito..." }
  ]
}
```

---

## Estado final do projeto

| Milestone | Status |
|---|---|
| M1 — Fundação | ✅ Mergeado |
| M2 — Agente de Sinistros | ✅ Validado E2E (aguarda chip WhatsApp) |
| M4 — Agente de Renovação | ✅ Mergeado |
| M3 — Agente de Onboarding | ⬜ Próximo |

---

## Decisões tomadas

- **LLM_PROVIDER=google** — padrão temporário enquanto sem crédito Anthropic. Reverter para `anthropic` quando crédito disponível.
- **gemini-2.5-flash com thinking_budget=0** — comportamento equivalente a modelo não-thinking. Mais previsível para structured output.
- `anthropic_api_key` passou a ser campo opcional no `Settings` (default `""`) para permitir rodar com Google sem ter a key da Anthropic.

---

## Próxima sessão — M3: Agente de Onboarding

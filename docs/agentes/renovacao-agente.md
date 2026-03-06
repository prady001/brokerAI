# Agente de Renovação de Apólices — M4

## Objetivo

Automatizar o contato com clientes cujas apólices estão próximas do vencimento, coletar a intenção de renovação via WhatsApp e notificar o vendedor responsável com um resumo estruturado. O agente opera em dois modos: proativo (CRON diário) e reativo (resposta do cliente via WhatsApp).

## Como funciona

### Arquitetura

O agente é implementado como um grafo LangGraph com dois fluxos independentes, selecionados automaticamente pelo campo `mode` do state:

```
┌─────────────────────────────────────────────────────────┐
│                    MODO CRON (diário)                    │
│                                                         │
│  check_expiring_policies → send_contacts → update_statuses
│                                                         │
│  - Identifica apólices vencendo em 30/15/7/0 dias       │
│  - Envia mensagem personalizada ao cliente              │
│  - Registra tentativa de contato                        │
│  - Marca renovações vencidas como no_response           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│               MODO WHATSAPP (reativo)                   │
│                                                         │
│  process_client_response → notify_sellers → update_statuses
│                                                         │
│  - Classifica intenção do cliente via LLM               │
│  - Notifica vendedor com resumo + dados da apólice      │
│  - Atualiza status da renovação                         │
└─────────────────────────────────────────────────────────┘
```

### Régua de contatos

O agente segue uma régua progressiva de contatos antes do vencimento:

| Contato | Quando | Template | Próximo contato |
|---------|--------|----------|-----------------|
| 1º | 30 dias antes | `TEMPLATE_30_DAYS` | 15 dias antes |
| 2º | 15 dias antes | `TEMPLATE_15_7_DAYS` | 7 dias antes |
| 3º | 7 dias antes | `TEMPLATE_15_7_DAYS` | Dia do vencimento |
| 4º | Dia 0 | `TEMPLATE_DAY_ZERO` | Aguarda resposta |

Após o 4º contato, se o cliente não responder em `RENEWAL_OVERDUE_DAYS` (padrão: 3 dias), a renovação é automaticamente marcada como `no_response`.

### Classificação de intenção

Quando o cliente responde via WhatsApp, o agente usa Claude Haiku para classificar a intenção em:

| Intenção | Significado | Status resultante |
|----------|-------------|-------------------|
| `wants_renewal` | Cliente quer renovar | `confirmed` |
| `refused` | Cliente não quer renovar | `refused` |
| `wants_quote` | Cliente quer cotação em outra seguradora | `contacted` |
| `needs_review` | Não foi possível classificar (fallback seguro) | `contacted` |

### Notificação ao vendedor

Após classificar a intenção, o vendedor recebe uma mensagem estruturada via WhatsApp com dados reais do cliente, apólice e seguradora:

- **Renovação confirmada** — cliente quer renovar, aguardando ação do vendedor
- **Perda de renovação** — cliente recusou, com motivo registrado
- **Cotação em outra seguradora** — oportunidade para o vendedor
- **Sem resposta** — cliente não respondeu após N tentativas
- **Revisão necessária** — classificação automática falhou, verificar manualmente

### Roteamento automático via webhook

Quando uma mensagem chega pelo webhook do Evolution API (`POST /webhook/whatsapp`), o sistema:

1. Identifica o cliente pelo número de telefone
2. Verifica se há renovação ativa com status `contacted`
3. Se sim, roteia automaticamente para o Agente de Renovação (modo WhatsApp)
4. Se não, encaminha para o Orquestrador (M2+)

O webhook é protegido com `try/except` para nunca retornar HTTP 500 ao Evolution API.

## Componentes implementados

### Serviço (`services/renewal_service.py`)

| Método | Descrição |
|--------|-----------|
| `get_expiring_policies(days_ahead)` | Busca apólices ativas vencendo nos dias especificados |
| `get_or_create_renewal(policy_id, ...)` | Cria registro de renovação se não existir |
| `update_renewal_status(renewal_id, status, intent, notes)` | Atualiza status e intenção |
| `register_contact_attempt(renewal_id)` | Incrementa contador e calcula próximo contato |
| `get_renewal_with_details(renewal_id)` | JOIN com Client, Policy e Insurer para dados completos |
| `mark_overdue_renewals(overdue_days)` | Marca renovações vencidas sem resposta como `no_response` |
| `get_renewal_by_id(renewal_id)` | Busca renovação pelo ID |
| `get_active_renewal_for_client(client_id)` | Busca renovação ativa do cliente (para roteamento) |

### Tools (`agents/renewal/tools.py`)

Todas as tools são Pydantic-tipadas e recebem dependências via `RunnableConfig`:

| Tool | Descrição |
|------|-----------|
| `get_expiring_policies` | Busca apólices elegíveis para contato |
| `send_renewal_contact` | Envia mensagem ao cliente + registra tentativa |
| `register_client_intent` | Registra intenção e atualiza status |
| `notify_seller` | Envia resumo ao vendedor |
| `mark_renewal_status` | Atualiza status diretamente |

### Nós do grafo (`agents/renewal/nodes.py`)

| Nó | Modo | Descrição |
|----|------|-----------|
| `check_expiring_policies` | cron | Identifica apólices nos gatilhos da régua |
| `send_contacts` | cron | Envia mensagens e registra contatos |
| `process_client_response` | whatsapp | Classifica intenção via LLM |
| `notify_sellers` | whatsapp | Notifica vendedor com dados enriquecidos |
| `update_statuses` | ambos | Atualiza status + marca vencidas como no_response |

### Templates de mensagem (`agents/renewal/prompts.py`)

- **Para clientes:** 3 templates progressivos (30d, 15/7d, dia 0)
- **Para vendedores:** 5 templates por intenção (confirmado, recusado, sem resposta, cotação, revisão necessária)
- **System prompt:** Regras de comportamento do agente (nunca se identificar como IA, não negociar, etc.)

## Configuração

| Variável de ambiente | Descrição | Padrão |
|---------------------|-----------|--------|
| `RENEWAL_CRON_HOUR` | Hora do CRON diário | `8` |
| `RENEWAL_CRON_TIMEZONE` | Timezone do CRON | `America/Sao_Paulo` |
| `RENEWAL_ALERT_DAYS` | Dias antes do vencimento para contato | `30,15,7,0` |
| `RENEWAL_MAX_CONTACTS` | Máximo de tentativas de contato | `4` |
| `RENEWAL_OVERDUE_DAYS` | Dias sem resposta para marcar no_response | `3` |
| `BROKER_NAME` | Nome da corretora nos templates | `sua corretora` |

## Exemplos

### Fluxo CRON — contato proativo

```
08:00 BRT → CRON dispara POST /scheduler/renewal-check
         → Agente busca apólices vencendo em 30/15/7/0 dias
         → Para cada apólice:
           → Seleciona template conforme dias restantes
           → Envia WhatsApp ao cliente:
             "Olá, João! Aqui é da Souza Seguros.
              Seu seguro do Toyota Yaris / ABC1234 vence em 30 dias (15/04/2026).
              Quer renovar? É só responder aqui que cuidamos de tudo pra você."
           → Registra tentativa (contact_count=1, next_contact_at=15d antes)
         → Verifica renovações vencidas → marca como no_response
```

### Fluxo WhatsApp — resposta do cliente

```
Cliente responde: "Sim, pode renovar!"
  → Webhook recebe mensagem
  → Identifica cliente pelo telefone
  → Encontra renovação ativa (status=contacted)
  → Roteia para Agente de Renovação (mode=whatsapp)
  → LLM classifica: wants_renewal
  → Notifica vendedor:
    "✅ RENOVAÇÃO CONFIRMADA
     Cliente: João Silva
     Seguro: Toyota Yaris / ABC1234 | POL-001 | Allianz
     Vigência: 15/04/2026
     Cliente quer renovar. Aguardando sua ação."
  → Atualiza status: contacted → confirmed
```

## Modelo de dados

A tabela `renewals` armazena o estado de cada renovação:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador |
| `policy_id` | UUID (FK) | Apólice associada |
| `client_id` | UUID (FK) | Cliente |
| `seller_phone` | String | Telefone do vendedor |
| `expiry_date` | Date | Data de vencimento |
| `status` | Enum | pending, contacted, confirmed, refused, no_response, lost |
| `contact_count` | Integer | Número de tentativas |
| `last_contact_at` | DateTime | Último contato enviado |
| `next_contact_at` | DateTime | Próximo contato agendado |
| `client_intent` | String | wants_renewal, refused, wants_quote, needs_review |
| `intent_notes` | Text | Motivo livre (ex: "está muito caro") |

## Testes

| Arquivo | Testes | Cobertura |
|---------|--------|-----------|
| `test_renewal_service.py` | 9 | Régua de contatos, CRUD, get_active |
| `test_renewal_tools.py` | 9 | Todas as tools com mocks |
| `test_renewal_graph.py` | 7 | Fluxo cron, fluxo whatsapp, fallback needs_review, erro LLM |
| **Total** | **25** | |

## Limitações conhecidas

- Templates WhatsApp pendentes de aprovação pela Meta (mensagens ativas requerem templates pré-aprovados)
- Evolution API não configurada em dev — envios simulados com log de aviso
- `process_client_response` usa LLM real em produção (requer `ANTHROPIC_API_KEY`)
- Sem suporte a múltiplas renovações simultâneas por cliente (retorna a mais recente)
- Sem retry automático para falhas de envio — erros são logados e reportados no state

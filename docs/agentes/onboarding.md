# Agente de Onboarding de Novos Clientes

## Objetivo

Conduzir o cadastro de um novo cliente via WhatsApp do início ao fim, sem que o corretor precise preencher nada manualmente. O agente coleta dados do cliente e da apólice por conversa, valida as informações, registra no banco e entrega ao corretor uma notificação com o perfil completo.

O objetivo é transformar o onboarding — hoje feito por e-mail, planilha ou digitação manual — em uma conversa de 10 a 15 minutos no WhatsApp.

---

## Como funciona

### Modo de iniciação — Fluxo Híbrido

O onboarding pode ser iniciado de duas formas:

#### Push — Corretor inicia (proativo)

O corretor envia um comando no próprio WhatsApp para o bot:

```
Corretor → Bot: "/cadastrar 5517999991234"

Bot → Cliente (5517999991234):
  "Olá! Sou o assistente da corretora.
   O seu corretor pediu pra eu fazer seu cadastro rapidinho aqui no WhatsApp. 😊
   Pode me confirmar seu nome completo para começarmos?"
```

- Qualquer mensagem vinda do `BROKER_NOTIFICATION_PHONE` com prefixo `/cadastrar <número>` é tratada como comando.
- O bot aborda o cliente **proativamente** logo após receber o comando.
- Para cancelar um onboarding em andamento: `/cancelar <número>`.

#### Pull — Cliente chega sozinho (reativo)

```
Novo número (sem cadastro no banco) → manda mensagem
          │
          ▼
  Orquestrador: número existe em clients?
          │
      NÃO ──► LLM classifica intent:
                "onboarding" → inicia coleta (pull mode)
                "claim"      → coleta sinistro normalmente
                               + escala para corretor com flag "cliente sem cadastro"
                "unknown"    → resposta padrão + notifica corretor
```

### Fluxo principal (grafo LangGraph)

```
entry_router
    │
    ├── push_mode=True, status="" ──► contact_client ──► END (aguarda resposta)
    │
    └── demais casos ──► collect_client (multi-turn)
                                │
                    client_data_complete=True
                                │
                                ▼
                        collect_policy (multi-turn)
                                │
                    policy_data_complete=True
                                │
                                ▼
                            confirm
                    (envia resumo, aguarda confirmação)
                                │
                                ▼
                      handle_confirmation
                          │         │         │
                      "sim"      "não"    ambíguo
                          │         │         │
                       register  reset      END (pede esclarecimento)
                          │      coleta
                  registered=True │
                          │       │
                        welcome   END
                          │
                     notify_seller
                          │
                         END

    register (falha após 3 tentativas) ──► escalate ──► END
    cancelamento ──► cancel_onboarding ──► END
```

O estado persiste em Redis (TTL 30 dias) entre cada acionamento do webhook. O grafo é retomado a partir do `status` atual quando o cliente responde.

### Dados coletados por etapa

**Etapa 1 — Dados do cliente**

| Campo | Obrigatório | Observação |
|---|---|---|
| Nome completo | ✅ | Normalizado para Title Case |
| CPF | ✅ | Validado com algoritmo de dígito verificador |
| Telefone WhatsApp | ✅ | Extraído automaticamente do evento do webhook |
| E-mail | ⬜ | Opcional no MVP |

**Etapa 2 — Dados da apólice**

| Campo | Obrigatório | Observação |
|---|---|---|
| Seguradora | ✅ | Buscada/criada em `insurers` via `get_or_create_insurer` |
| Ramo / Tipo | ⬜ | Default `auto` se não informado |
| Item segurado | ✅ | Ex: "Toyota Yaris 1.3 Flex / ABC1234" |
| Número da apólice | ✅ | Único no banco (`unique=True`) |
| Vencimento (end_date) | ✅ | Aceita DD/MM/YYYY ou YYYY-MM-DD |
| Início (start_date) | ⬜ | Default: data atual |

### Nós do grafo LangGraph

| Nó | Responsabilidade |
|---|---|
| `entry_router` | Não-op; roteamento via `route_entry` com base no `status` atual |
| `contact_client` | (push only) Envia saudação proativa ao cliente e pede o nome |
| `collect_client` | Extrai nome e CPF das mensagens via LLM; valida CPF; pergunta campos faltantes |
| `collect_policy` | Extrai dados da apólice via LLM; pergunta campos obrigatórios faltantes |
| `confirm` | Envia resumo formatado dos dados coletados e aguarda confirmação |
| `handle_confirmation` | Processa "sim" / "não" / ambíguo; reseta estado em caso de rejeição |
| `register` | Cria cliente e apólice no banco (até 3 tentativas internas) |
| `welcome` | Envia mensagem de boas-vindas ao cliente após cadastro |
| `notify_seller` | Envia resumo completo do novo cadastro ao `BROKER_NOTIFICATION_PHONE` |
| `escalate` | Notifica corretor e informa cliente que o cadastro manual será necessário |
| `cancel_onboarding` | Notifica cliente do cancelamento; seta `failed=True` |

### Detecção de confirmação

O `handle_confirmation_node` usa matching por palavras inteiras (set intersection) para evitar falsos positivos:

```python
confirmed_words = {"sim", "confirmo", "pode", "ok", "certo", "isso", "correto", "cadastra"}
rejected_words  = {"não", "nao", "errado", "errada", "corrigir", "mudar", "alterar", "refazer"}
# "tudo certo" capturado como frase composta
```

Resposta ambígua → pede esclarecimento e aguarda próxima mensagem sem avançar no grafo.

---

## Configuração

### Variáveis de ambiente relevantes

```env
# Número do corretor — único autorizado a emitir comandos /cadastrar e /cancelar
BROKER_NOTIFICATION_PHONE=5517999999999

# Máximo de tentativas de registro no banco (hardcoded como _MAX_RETRIES = 3)
# Sem variável de ambiente — alterar em agents/onboarding/nodes.py se necessário
```

> **Nota:** não existe `ONBOARDING_REQUIRED_FIELDS` nem `ONBOARDING_DEFAULT_SELLER_PHONE` como variáveis de ambiente. Os campos obrigatórios estão hardcoded nos prompts e na lógica de `collect_policy_node`. A notificação final sempre vai para `BROKER_NOTIFICATION_PHONE`.

### Comandos do corretor

| Comando | Ação |
|---|---|
| `/cadastrar <número>` | Inicia onboarding proativo para o número informado |
| `/cancelar <número>` | Cancela onboarding em andamento para o número informado |

O número deve estar no formato E.164 sem `+` (ex: `5517999991234`). Comandos só são reconhecidos quando enviados pelo `BROKER_NOTIFICATION_PHONE`.

### Estado no Redis

Chave: `onboarding_conversation:{phone}` — TTL 30 dias.

O estado é removido automaticamente quando `registered=True` ou `failed=True` (cadastro concluído, cancelado ou após falha com escalada).

---

## Exemplos

### Exemplo 1 — Onboarding completo via push

```
Corretor → Bot: /cadastrar 5517999991234

Bot → Cliente:
  "Olá! Sou o assistente da corretora. O seu corretor pediu pra eu fazer
   seu cadastro rapidinho aqui no WhatsApp. 😊
   Pode me confirmar seu nome completo para começarmos?"

Cliente: João Silva

Bot: "Pode me informar seu CPF?"

Cliente: 529.982.247-25

Bot: "Agora me fale sobre o seguro — qual é a seguradora?"

Cliente: Porto Seguro, apólice 12345, Toyota Yaris ABC1234, vence 31/12/2026

Bot: "Perfeito! Vou confirmar os dados antes de finalizar o cadastro:

     👤 Nome: João Silva
     📄 CPF: 529.982.247-25
     🏢 Seguradora: Porto Seguro
     📋 Apólice: 12345
     🚗 Item segurado: Toyota Yaris ABC1234
     📅 Vencimento: 31/12/2026

     Está tudo correto? Responda *sim* para confirmar ou *não* para corrigir."

Cliente: sim

Bot → Cliente: "Cadastro realizado com sucesso! ✅
   Seus dados estão registrados e você já pode contar com nosso atendimento via WhatsApp.
   Qualquer dúvida sobre o seguro, é só chamar aqui! 😊"

Bot → Corretor: "✅ NOVO CLIENTE CADASTRADO
   👤 Nome: João Silva | 📄 CPF: 529.982.247-25
   📱 WhatsApp: 5517999991234
   🏢 Porto Seguro | 📋 12345 | 🚗 Toyota Yaris ABC1234
   📅 Vencimento: 31/12/2026
   Cadastrado em: 31/03/2026 às 14h22"
```

### Exemplo 2 — CPF inválido, correção solicitada

```
Cliente: Meu CPF é 111.111.111-11

Bot: "Hmm, esse CPF parece inválido — pode ter sido um erro de digitação.
     Consegue conferir e informar novamente?"

Cliente: Desculpa! É 529.982.247-25

Bot: [prossegue para próxima pergunta]
```

### Exemplo 3 — Rejeição na confirmação

```
Bot: "Está tudo correto? Responda *sim* para confirmar ou *não* para corrigir."

Cliente: não, o número da apólice está errado

Bot: "Tudo bem! Vamos recomeçar a coleta. Pode me confirmar seu nome completo?"

[Reinicia collect_client com dados zerados]
```

### Exemplo 4 — Falha após retries, escalada ao corretor

```
[Banco de dados indisponível — 3 tentativas falham]

Bot → Cliente: "Não conseguimos concluir seu cadastro automaticamente. 😔
   Um dos nossos atendentes vai entrar em contato com você em breve para finalizar.
   Obrigado pela paciência!"

Bot → Corretor: "⚠️ ONBOARDING INCOMPLETO — AÇÃO NECESSÁRIA
   📱 Cliente: 5517999991234
   ❌ Motivo: Falha no cadastro automático após múltiplas tentativas.
   Por favor, entre em contato para finalizar o cadastro manualmente."
```

---

## Limitações conhecidas

- **Sem OCR no MVP:** o cliente não pode enviar foto do documento para extração automática de dados. Todos os dados são coletados por conversa. OCR (Mistral/Textract) é planejado para V1.
- **Sem validação de apólice na seguradora:** o agente registra o que o cliente informa, sem verificar se a apólice realmente existe no sistema da seguradora. Validação cruzada é planejada para V1.
- **Uma apólice por onboarding:** o fluxo cadastra uma apólice por sessão. Clientes com múltiplas apólices precisam de um novo onboarding para cada uma.
- **Ramo limitado ao MVP:** o fluxo é otimizado para automóvel. Residência, vida e outros ramos são suportados mas sem perguntas específicas do ramo — apenas dados gerais.
- **Seguradora nova cria registro mínimo:** se a seguradora informada não existir no banco, um registro com `integration_type="manual"` é criado automaticamente. O corretor deve revisar e configurar a integração posteriormente.
- **Sem retomada de onboarding após `failed`:** se o onboarding foi cancelado ou falhou, um novo `/cadastrar` reinicia do zero — não há retomada de onde parou.

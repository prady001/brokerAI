# Guia de Avaliação de Conversas — Agente Orquestrador BrokerAI

O orquestrador é a **primeira camada de decisão** de toda mensagem que chega ao sistema.
Ele não conduz conversas longas — ele toma uma decisão por mensagem e roteia corretamente.
Por isso, os critérios de qualidade aqui são diferentes dos outros agentes.

---

## O que o orquestrador faz

Para cada mensagem recebida no webhook, o orquestrador executa esta sequência:

```
Mensagem chega
     │
     ▼
[1] Há onboarding ativo para este número? → sim → Agente de Onboarding
     │ não
     ▼
[2] Há renovação ativa para este cliente no banco? → sim → Agente de Renovação
     │ não
     ▼
[3] Cliente está cadastrado no banco?
     │ não → Detecta intenção da mensagem
     │           → "onboarding" → inicia onboarding pull
     │           → qualquer outra → mensagem de "entre em contato"
     │ sim
     ▼
[4] Há conversa de sinistro ativa no Redis? → sim → Retoma Agente de Sinistros
     │ não
     ▼
[5] Detecta intenção da mensagem (LLM, confiança ≥ 0.6)
     → "claim"      → Agente de Sinistros (nova conversa)
     → "faq"        → FAQ Handler
     → "onboarding" → Informa que já está cadastrado
     → "unknown"    → Human Handoff (notifica corretor)
```

**Regra de prioridade:** onboarding ativo > renovação ativa > sinistro ativo > nova intenção.

---

## Intents reconhecidos pelo LLM

| Intent | Quando classificar | Exemplos |
|---|---|---|
| `claim` | Sinistro, acidente, dano, assistência, guincho | "bati o carro", "preciso de guincho", "vidro quebrou" |
| `onboarding` | Pedido de cadastro | "quero me cadastrar", "como faço meu cadastro?" |
| `faq` | Dúvida geral sobre seguro | "meu boleto venceu", "o que cobre meu seguro?" |
| `unknown` | Fora do escopo ou ambíguo | "oi", "tudo bem?", reclamações sem contexto |

**Threshold de confiança:** `< 0.6` → reclassifica como `unknown`.

---

## Regras duras — o que nunca pode acontecer

| Regra | Exemplo de violação |
|---|---|
| Não rotear para claims se não houver intent claro | "oi" → agente de sinistros |
| Não ignorar conversa ativa de sinistro | Cliente tem sinistro aberto, manda "oi", orquestrador inicia nova conversa |
| Não ignorar onboarding ativo no Redis | Cliente está no meio do cadastro, orquestrador trata como nova mensagem |
| Não deixar cliente sem cadastro sem resposta humana | Cliente desconhecido com intenção não-onboarding recebe mensagem de dead-end sem handoff |
| Não rotear renovação para sinistros | Cliente com renovação ativa manda mensagem, orquestrador ignora e vai para sinistros |

---

## Critérios de pass/fail por situação

### Situação 1 — Onboarding ativo no Redis

| Critério | Pass | Fail |
|---|---|---|
| Continuidade do onboarding | Mensagem do cliente vai para `_resume_onboarding` | Orquestrador ignora estado e detecta intenção do zero |
| Estado preservado | Estado do Redis é carregado e atualizado com nova mensagem | Estado é sobrescrito com estado inicial |

### Situação 2 — Renovação ativa no banco

| Critério | Pass | Fail |
|---|---|---|
| Prioridade correta | Mensagem vai para Agente de Renovação, não para sinistros | Orquestrador detecta "preciso de guincho" e inicia sinistro, ignorando renovação ativa |

### Situação 3 — Cliente não cadastrado

| Critério | Pass | Fail |
|---|---|---|
| Intent onboarding → pull | Inicia onboarding pull corretamente | Inicia sinistro ou envia mensagem de dead-end |
| Outro intent → resposta útil | Mensagem clara + handoff humano para o corretor | Envia "entre em contato" sem notificar o corretor |

### Situação 4 — Detecção de intenção (cliente cadastrado, sem conversa ativa)

| Critério | Pass | Fail |
|---|---|---|
| Claim com confiança ≥ 0.6 | Inicia agente de sinistros | Vai para FAQ ou handoff |
| Mensagem ambígua | Confidence < 0.6 → unknown → handoff | Classifica "oi" como claim e abre sinistro |
| FAQ respondido | Resposta clara e dentro do que a corretora pode responder sem dados do cliente | Resposta inventa coberturas específicas da apólice do cliente |
| Unknown → handoff | Notifica corretor + responde ao cliente | Silêncio ou mensagem de erro |

### Situação 5 — Sinistro ativo (continuação)

| Critério | Pass | Fail |
|---|---|---|
| Retomada correta | Estado do Redis é carregado; mensagem vai para `_resume_claims_agent` | Nova conversa de sinistro é iniciada paralelamente |
| Contexto mantido | Agente de sinistros retoma do ponto certo | Agente recomeça coletando informações já fornecidas |

---

## Avaliação do FAQ Handler

O `faq_handler_node` responde dúvidas gerais **sem acesso a dados do cliente**. Avalie:

| Critério | Pass | Fail |
|---|---|---|
| Não inventa dados do cliente | "Para saber sobre sua apólice, me informe seu nome ou número de apólice" | "Seu seguro cobre colisão total" (sem ter dados do cliente) |
| Resposta em português claro | Explicação acessível, sem jargão excessivo | Resposta com termos técnicos sem explicação |
| Encaminha para corretor quando necessário | "Para questões específicas da sua apólice, entre em contato com a corretora" | Responde com dados inventados para não decepcionar |
| Tamanho adequado ao WhatsApp | 2–5 frases no máximo | Resposta de 10+ linhas para pergunta simples |

---

## Avaliação do Human Handoff

O `human_handoff_node` é o último recurso. Avalie:

| Critério | Pass | Fail |
|---|---|---|
| Corretor é notificado | Alerta enviado com mensagem original + dados do cliente | Handoff silencioso (cliente recebe mensagem mas corretor não é notificado) |
| Cliente recebe resposta | "Um dos nossos atendentes vai retornar para você em breve." | Silêncio |
| Resposta não é genérica demais | Minimamente personalizada ou contextualizada | "Erro no sistema." |

---

## Sinais de alerta "cara de IA" no orquestrador

| Situação | Red flag |
|---|---|
| FAQ handler | Resposta muito formal, longa, com bullets e headers para pergunta simples de WhatsApp |
| Human handoff | Mensagem ao cliente idêntica sempre, mesmo para situações diferentes |
| FAQ handler | Inventa informações específicas para parecer útil ("Seu seguro cobre...") |

---

## Checklist rápido

Antes de finalizar a avaliação de uma conversa com o orquestrador:

1. **Identifiquei o caminho de roteamento** esperado para aquela mensagem.
2. **Verifiquei a prioridade** — onboarding > renovação > sinistro ativo > nova intenção.
3. **Checei se a intent foi classificada corretamente** dado o threshold de 0.6.
4. **Avaliado o FAQ ou handoff** com os critérios específicos de cada um.
5. **Verifiquei se o corretor foi notificado** nos casos em que deveria ser.
6. **Raciocínio rastreável** — O que, Onde, Por que.

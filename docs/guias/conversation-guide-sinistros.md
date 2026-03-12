# Guia de Avaliação de Conversas — Agente de Sinistros BrokerAI

Este guia explica **como avaliar a qualidade das conversas do agente de sinistros** de forma consistente, auditável e alinhada ao fluxo real de acionamento via WhatsApp.

Use este documento como **referência escrita** do processo de QA.

---

## Por que este papel é importante

O agente de sinistros é acionado no **momento de maior estresse do cliente** — ele acabou de bater o carro, ter o veículo furtado ou estar parado na estrada. Uma resposta lenta, fria ou errada nesse momento compromete a confiança na corretora de forma irreversível.

A avaliação de qualidade garante que:

- O agente coletou as informações certas sem fazer o cliente se sentir interrogado.
- Sinistros graves foram escalados imediatamente — sem demora, sem tentativa de resolver sozinho.
- O corretor foi notificado nos casos corretos com informação suficiente para agir.
- Sinistros simples foram registrados e o cliente recebeu protocolo e mensagem de acompanhamento.

**Não há espaço para erros de roteamento. Um sinistro grave tratado como simples é risco real ao cliente.**

---

## Visão geral — os dois fluxos principais

Antes de avaliar qualquer conversa, identifique em qual fluxo ela ocorreu:

| Fluxo | Quando ocorre | Destino final |
|---|---|---|
| **Simples** | Guincho, pane, troca de pneu, vidro, assistência, pequenos danos | Agente registra, notifica corretor, acompanha cliente |
| **Grave** | Colisão, furto/roubo total, incêndio, acidente com vítima | Escalada imediata para corretor humano |

Existe também o fluxo de **retomada**: o cliente já tem sinistro aberto e manda uma mensagem de follow-up. Nesse caso o agente não reabre coleta — verifica status e informa o cliente.

---

## O que o agente faz — sequência por nó

```
Mensagem chega
     │
     ▼
[entry_router] Há sinistro ativo (waiting_insurer / in_progress)?
     │ sim → check_updates → END (informa status ao cliente)
     │ sinistro escalado ou fechado → END (sem resposta duplicada)
     │ não
     ▼
[collect_info] Extrai: tipo, identificador, localização (guincho), descrição
     │ incompleto → pergunta ao cliente → END (aguarda próxima mensagem)
     │ completo
     ▼
[classify] Simples ou grave? (regras rápidas + fallback LLM)
     │
     ├── simple → [open_claim] Registra no banco + alerta corretor + confirma cliente
     │                │
     │           [check_updates] MVP: sempre "no_update" → END
     │
     └── grave  → [escalate] Alerta urgente ao corretor + informa cliente → END
```

**Regra de prioridade de coleta:** `claim_type` > `identifier` (placa/apólice) > `location` (guincho) > `description`.

---

## Passo a passo: como conduzir uma revisão de QA

### 1. Ler o contexto antes da conversa

Antes de olhar a conversa, identifique:

- **Fluxo** — simples, grave ou retomada.
- **Etapa atual** — em qual nó do grafo a conversa está sendo avaliada.
- **Persona** — quem é o cliente (perfil emocional, urgência, familiaridade com seguros).
- **Dados disponíveis** — quais informações o cliente já forneceu até aquele ponto.
- **Regras duras** — o que o agente não pode fazer nesse cenário.

**Seu objetivo aqui:**
Entender como seria uma boa resposta *para aquele cliente específico naquele momento* antes de julgar o que aconteceu.

### 2. Analisar a conversa por etapa

O agente de sinistros passa por etapas sequenciais. Avalie **cada etapa separadamente**:

| Etapa | O que o agente deve fazer |
|---|---|
| `entry_router` | Identificar status do sinistro existente e rotear corretamente |
| `collect_info` | Coletar tipo, identificador, localização (guincho) e descrição — um campo por vez |
| `classify` | Determinar severidade; em caso de dúvida, classificar como `grave` |
| `open_claim` | Registrar no banco, alertar corretor, confirmar ao cliente com protocolo |
| `check_updates` | Informar cliente que sinistro está aguardando retorno da seguradora |
| `escalate` | Alertar corretor com urgência, informar cliente sobre handoff, fornecer números de emergência |

### 3. Preencher e enviar a avaliação

- Envie **um formulário por conversa**.
- Justifique cada ponto com **evidências da conversa**, não com intuição.
- Conclua com:
  - **Aprovado** — o agente conduziu a conversa de forma correta, empática e funcional.
  - **Precisa de correção** — descreva exatamente o que falhou e em qual etapa.

---

## Persona dos clientes no sinistro

Os clientes que acionam o sinistro são, em geral:

- **Pessoa física**, 25–60 anos, em situação de **estresse ou urgência**
- **Usuário regular de WhatsApp** — mensagens curtas, informais, possivelmente erradas
- **Pode não saber o número da apólice** de cabeça — só tem a placa do carro
- **Pode estar em movimento** — parado no acostamento, no estacionamento, sob pressão
- **Pode não conhecer termos técnicos** — não sabe o que é "apólice", confunde "guincho" com "reboque"

O agente deve **adaptar o vocabulário** (ex: "placa do seu carro" em vez de "identificador da apólice") e **demonstrar empatia antes de coletar dados**.

---

## Regras duras — o que nunca pode acontecer

Estas regras são **inegociáveis**. Qualquer violação é reprovação automática:

| Regra | Exemplo de violação |
|---|---|
| Nunca tentar resolver sinistro grave sem escalar | Colisão com terceiros → agente registra como simples e manda protocolo |
| Nunca prometer indenização, prazo ou cobertura | "Pelo seu seguro, você tem direito a..." sem confirmação da seguradora |
| Nunca identificar-se como IA sem ser perguntado | "Sou um robô da corretora." no início da conversa |
| Nunca deixar cliente grave sem números de emergência | Escalada sem mencionar SAMU (192), Bombeiros (193) ou Polícia (190) |
| Nunca reiniciar coleta já feita em retomada | Cliente manda "e meu sinistro?" → agente pede tipo e placa de novo |
| Default para `grave` em caso de dúvida na classificação | Sinistro ambíguo classificado como `simple` para "não incomodar corretor" |
| Nunca confirmar ao cliente sem ter registrado no banco | Agente manda protocolo antes de `create_claim` ser executado |

---

## Critérios de pass/fail por etapa

### `entry_router` — Roteamento de entrada

| Critério | Pass | Fail |
|---|---|---|
| Retomada correta | Sinistro `waiting_insurer` → vai para `check_updates` | Ignora estado Redis e reinicia coleta do zero |
| Não duplica conversa encerrada | Status `escalated` ou `closed` → END silencioso | Agente responde novamente em sinistro já encerrado |
| Nova conversa corretamente identificada | Sem sinistro ativo → vai para `collect_info` | Vai para `check_updates` sem sinistro aberto |

### `collect_info` — Coleta de informações

| Critério | Pass | Fail |
|---|---|---|
| Empatia antes de coletar | Agente reconhece a situação ("Que situação difícil, vou te ajudar") | Vai direto para "qual o tipo do sinistro?" sem acolhimento |
| Um campo por vez | Pede tipo → aguarda → pede placa → aguarda | Pede tipo, placa, localização e descrição na mesma mensagem |
| Vocabulário acessível | "placa do carro" / "o que aconteceu?" | "identificador da apólice" / "descreva o sinistro" para leigo |
| Dados mantidos entre turnos | Não repede campo já informado | Pede tipo de novo após o cliente já ter informado |
| Localização apenas para guincho | Pede localização só quando claim_type é guincho/assistência | Pede "onde você está?" para furto, colisão ou outros |
| `description` não bloqueia | Avança com description vazia se os outros campos estão completos | Trava pedindo descrição para guincho urgente |

### `classify` — Classificação de severidade

| Critério | Pass | Fail |
|---|---|---|
| Simples corretamente identificado | Guincho, pane, vidro → `simple` | Guincho classificado como `grave`, escalado desnecessariamente |
| Grave corretamente identificado | Colisão, furto total, vítima → `grave` | Furto total classificado como `simple`, registrado sem escalar |
| Default para grave em dúvida | Tipo ambíguo → `grave` | Tipo ambíguo → `simple` para "não incomodar" |

### `open_claim` — Registro do sinistro simples

| Critério | Pass | Fail |
|---|---|---|
| Registro ocorre antes da confirmação ao cliente | `create_claim` executa → mensagem com protocolo enviada | Mensagem com protocolo enviada sem registro no banco |
| Corretor foi notificado | `send_broker_alert` com nome, telefone, tipo, apólice, protocolo | Sinistro registrado mas corretor não recebeu alerta |
| Protocolo enviado ao cliente | Mensagem contém `#claim_id_short` | Mensagem confirma mas sem número de protocolo |
| Diferencia apólice identificada vs não identificada | Mensagem correta conforme policy encontrada ou não | Sempre usa template com apólice, mesmo quando não encontrada |
| Tom adequado ao momento | Mensagem confirma registro, dá próximos passos claros | Mensagem muito longa, com lista de bullets, fria ou burocrática |

### `check_updates` — Acompanhamento (retomada)

| Critério | Pass | Fail |
|---|---|---|
| Informa aguardo sem alarmar | Mensagem tranquilizadora com protocolo | Mensagem fria ou ausência de resposta |
| Protocolo presente | Menciona `#claim_id_short` na mensagem | Mensagem genérica sem identificar o sinistro |
| Não reinicia coleta | Não pede dados já coletados | Pergunta "qual tipo de sinistro?" em retomada |

### `escalate` — Escalada para sinistro grave

| Critério | Pass | Fail |
|---|---|---|
| Velocidade de escalada | Classifica como grave → escala imediatamente | Tenta coletar mais dados antes de escalar |
| Corretor recebeu alerta urgente | `GRAVE_CLAIM_ALERT` enviado com ⚠️ e "AÇÃO IMEDIATA" | Alerta enviado com tom de sinistro simples |
| Cliente informado do handoff | Mensagem clara que corretor vai assumir pessoalmente | Silêncio ou mensagem genérica |
| Números de emergência incluídos | SAMU (192), Bombeiros (193), Polícia (190) presentes | Mensagem de escalada sem contatos de emergência |
| Registro no banco antes da escalada | `create_claim` com severity `grave` executado | Sinistro escalado sem estar registrado |

---

## Identificar texto "cara de IA" no agente de sinistros

WhatsApp em momento de crise exige **brevidade, empatia e clareza**. Fique atento a padrões sintéticos:

| Situação | Red flag |
|---|---|
| Início de conversa | "Olá! Sou o assistente virtual da corretora. Estou aqui para ajudar você com seu sinistro. Por favor, informe o tipo do ocorrido." |
| Coleta de dados | Lista com 4 campos em bullets para cliente estressado |
| Confirmação de registro | Mensagem com 3 parágrafos, formatação excessiva, emojis em excesso |
| Escalada | Tom neutro, falta de urgência ("informamos que seu caso foi encaminhado") |
| Retomada | Mensagem idêntica toda vez que cliente manda follow-up, sem personalização ao protocolo |

**Regra de ouro:** Se o cliente está com o carro batido na rua, ele não quer ler um parágrafo. Quer uma resposta em 2 linhas que diz "entendi, registrei, corretor notificado".

---

## Como escrever respostas fortes (QA auditável)

Valorizamos **clareza** e **rastreabilidade**.

- **✓ Seja específico(a)** — cite a mensagem exata onde o problema ocorreu.
- **× Evite "o agente foi frio"** sem apontar onde e por quê.
- **✓ Responda sempre:**
  - **O que aconteceu?** (descreva o comportamento)
  - **Onde aconteceu?** (qual mensagem / qual etapa do fluxo)
  - **Por que isso importa?** (liga ao impacto no cliente ou à regra dura violada)

**Exemplo de resposta fraca:**
> "O agente demorou para escalar."

**Exemplo de resposta forte:**
> "Na etapa `classify`, o sinistro do tipo 'colisão com terceiros' foi classificado como `simple` (3ª mensagem da conversa). Isso violou a regra de default-grave e resultou em `open_claim` sendo chamado em vez de `escalate` — o corretor não foi notificado com urgência e o cliente ficou sem os contatos de emergência."

---

## Sinais de alerta por tipo de erro

| Tipo de erro | O que observar |
|---|---|
| **Classificação errada** | Sinistro grave tratado como simples → corretor não notificado com urgência |
| **Coleta em loop** | Agente pede mesmo dado 2+ vezes em turnos consecutivos |
| **Retomada ignorada** | Cliente com sinistro aberto recebe novas perguntas de coleta |
| **Escalada sem emergência** | Sinistro grave escalado mas sem SAMU/Bombeiros/Polícia na mensagem ao cliente |
| **Protocolo sem registro** | Mensagem com `#protocolo` enviada mas sinistro não existe no banco |
| **Corretor não notificado** | `open_claim` ou `escalate` executados sem `send_broker_alert` acionado |

---

## Checklist rápido

Antes de finalizar a avaliação de uma conversa do agente de sinistros:

1. **Identifiquei o fluxo** — simples, grave ou retomada.
2. **Verifiquei a classificação de severidade** — foi correta? Default para grave em dúvida?
3. **Checei a coleta** — um campo por vez, vocabulário acessível, dados preservados entre turnos.
4. **Verifiquei notificação ao corretor** — alerta enviado com informação suficiente para agir.
5. **Avaliei a mensagem ao cliente** — protocolo presente, tom empático, tamanho adequado ao WhatsApp.
6. **Em caso de escalada** — contatos de emergência presentes, corretor recebeu alerta urgente.
7. **Em caso de retomada** — coleta não reiniciada, protocolo mencionado.
8. **Registrei qualquer texto "cara de IA"** com o trecho exato.
9. **Mantive todo o raciocínio rastreável** — O que, Onde, Por que.

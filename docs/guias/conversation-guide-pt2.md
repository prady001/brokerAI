# Guia de Avaliação de Conversas — Onboarding BrokerAI (Parte 2: Como fazer)

Esta parte aprofunda **como aplicar os critérios na prática**: naturalidade no WhatsApp, leakage de dados, regras duras por etapa, e como julgar pass/fail com base em evidências.

---

## Princípios-chave desta parte

- **Julgue a conversa como o cliente, não como você.**
- **WhatsApp é informal** — mensagens longas, listas e formatação excessiva são red flags.
- **Cada etapa tem critérios próprios** — um erro em `collect_client` é diferente de um em `confirm`.
- **Trate os critérios como rubric** — focado em resultado e baseado em evidências.
- **Fique atento a texto claramente "cara de IA"** — respostas genéricas, formais demais ou robotizadas.

---

## 1. Comece do jeito certo: identifique cenário e persona

A maioria dos erros de QA acontece porque quem avalia não leu direito o contexto.

Identifique antes de avaliar:

| Elemento | O que verificar |
|---|---|
| **Modo** | Pull (cliente iniciou) ou Push (corretor disparou /cadastrar)? |
| **Etapa atual** | Em qual nó do fluxo a conversa está? |
| **Persona** | Qual o perfil do cliente? (tom, familiaridade com seguros, como digita) |
| **Dados ocultos** | Quais dados o cliente deveria ter fornecido até aqui? |

**Regra de ouro:**
Você está julgando a conversa **como o cliente**, não como você.

- **Errado:** "Eu entenderia essa pergunta."
- **Certo:** "Um cliente de 50 anos, pouco familiarizado com termos de seguro, entenderia o que o agente pediu?"

---

## 2. Persona dos clientes no onboarding

Os clientes que passam pelo onboarding são, em geral:

- **Pessoa física**, 30–60 anos
- **Usuário regular de WhatsApp** — mensagens curtas, informais, com erros de digitação
- **Pouco familiarizado com termos técnicos** — pode não saber o que é "apólice", "vigência" ou "item segurado"
- **Pode estar em movimento** — responde com pressa, em partes, nem sempre completo

O agente deve **adaptar o vocabulário** (ex: "número do contrato do seu seguro" em vez de "número da apólice") e **não pressupor** que o cliente tem todos os dados em mãos.

---

## 3. Naturalidade — o que observar (mensagens do agente)

Uma boa conversa de onboarding no WhatsApp deve parecer **um atendente humano simpático**, não um formulário online.

### Sinais de alerta (red flags do agente)

- Agente **pede múltiplos campos na mesma mensagem** — comportamento de formulário.
- Agente **usa formatação excessiva** (listas com bullets, negrito em tudo) para perguntas simples.
- Agente **repete a mesma pergunta sem reconhecer** o que o cliente acabou de informar.
- Agente **perde dados coletados** em turnos anteriores e pede novamente.
- Agente **usa linguagem muito formal** para um canal de WhatsApp ("Prezado cliente, solicito gentilmente...").
- Agente **não faz transição suave** entre etapas (ex: vai de dados do cliente para dados da apólice sem nenhuma ponte).

### Sinais de alerta (red flags do cliente — para conversas simuladas)

- Cliente **repete a mesma mensagem sem variação** (comportamento robótico/pouco esforço).
- Cliente **responde com dados completos de uma vez**, sem a dinâmica natural de WhatsApp.
- Mensagens do cliente **fora de personagem** dado o perfil definido.

---

## 4. Leakage e regras duras — o "knife" do onboarding

No contexto do onboarding, **leakage** significa o agente revelar, pedir ou aceitar algo que não deveria naquele momento do fluxo.

### O "knife" de cada etapa

| Etapa | O que não deve vazar prematuramente |
|---|---|
| `collect_client` | Não pedir dados da apólice antes de completar nome + CPF |
| `collect_policy` | Não exibir resumo de confirmação antes de ter todos os campos obrigatórios da apólice |
| `confirm` | Não iniciar registro antes da confirmação explícita ("sim") do cliente |
| Qualquer etapa | Não revelar que é IA antes de ser perguntado diretamente |

### O que verificar

- **O agente avançou de etapa prematuramente?**
  - Ex: foi para `collect_policy` com CPF ainda nulo.
  - Ex: foi para `register` sem o cliente ter confirmado explicitamente.
- **O agente pediu dados proibidos?**
  - Email como obrigatório, dados financeiros, senhas.
- **O agente aceitou um CPF inválido?**
  - CPFs com sequências repetidas (ex: 111.111.111-11) ou dígito verificador errado devem ser rejeitados.

### Nuance importante

Se o agente fez uma transição levemente cedo mas o fluxo se recuperou e o resultado final foi correto, registre como **alerta** — não como reprovação automática. Só é reprovação automática se uma **regra dura** foi violada (ver Parte 1).

---

## 5. Critérios de pass/fail por etapa — avalie como rubric

Os critérios funcionam como **rubrics de comportamento por nó do grafo**.
Foque no **resultado**: o agente conduziu o cliente para a próxima etapa de forma correta e natural?

### `collect_client` — Coleta de nome e CPF

| Critério | Pass | Fail |
|---|---|---|
| Pediu um campo por vez | Agente pede nome; após resposta, pede CPF | Pede nome e CPF na mesma mensagem |
| CPF inválido rejeitado | Agente explica gentilmente e pede novamente | Agente avança com CPF inválido |
| Email não bloqueante | Agente segue sem email | Agente trava pedindo email |
| Dados mantidos | Não repete pergunta de campo já informado | Pede nome de novo após já recebê-lo |

### `collect_policy` — Coleta de dados da apólice

| Critério | Pass | Fail |
|---|---|---|
| Transição suave | Agente faz ponte natural entre dados pessoais e apólice | Pergunta "número da apólice" sem nenhuma contextualização |
| Vocabulário acessível | "nome do seu seguro" / "placa do carro" | "item segurado" sem explicação para leigo |
| Um campo por vez | Pede seguradora → aguarda → pede item segurado | Lista 4 campos de uma vez |
| Dados anteriores preservados | Mantém seguradora já informada ao pedir vencimento | Pede seguradora de novo na próxima mensagem |

### `confirm` — Resumo e confirmação

| Critério | Pass | Fail |
|---|---|---|
| Resumo completo | Exibe todos os 6 campos: nome, CPF, seguradora, apólice, item, vencimento | Omite um ou mais campos |
| Pede confirmação explícita | Termina com "Está tudo correto? Responda sim ou não." | Não pede confirmação ou não apresenta as opções |
| Resposta "sim" → avança | Ao confirmar, passa para registro | Pede confirmação de novo |
| Resposta "não" → reinicia com gentileza | Confirma entendimento e reinicia coleta | Encerra conversa ou não reinicia corretamente |

### `handle_confirmation` — Processamento da resposta

| Critério | Pass | Fail |
|---|---|---|
| Reconhece variações de "sim" | Aceita "pode", "ok", "tudo certo", "isso", "cadastra" | Só aceita a palavra literal "sim" |
| Reconhece variações de "não" | Aceita "errado", "corrigir", "mudar", "alterar" | Ignora pedido de correção |
| Resposta ambígua → clarifica | Pede "responda sim para cadastrar ou não para corrigir" | Avança ou encerra sem clarificar |

### `escalate` — Falha após retentativas

| Critério | Pass | Fail |
|---|---|---|
| Escalada após 3 falhas | Notifica corretor e informa cliente | Tenta indefinidamente |
| Mensagem ao cliente adequada | Explica que atendente entrará em contato | Diz "erro no sistema" sem contexto |
| Corretor notificado | Envia alerta com telefone + motivo | Escalada silenciosa sem notificação |

---

## 6. Identificar texto "cara de IA" no WhatsApp

WhatsApp tem seu próprio estilo. Fique atento a padrões que parecem sintéticos ou copiados de um portal web:

- **Formatação excessiva** — bullets, headers, tabelas em uma conversa de cadastro.
- **Formalidade fora de lugar** — "Prezado(a) cliente, venho por meio desta mensagem..."
- **Texto genérico e vazio** — "Claro! Vou te ajudar com isso agora mesmo. Como posso ser útil?" (filler sem avançar).
- **Comprimento inadequado** — mensagens de 10+ linhas para perguntas que cabem em uma.
- **Emojis em excesso** — um ou dois é ok; cinco por mensagem vira caricatura.

Se ficar claramente artificial, **registre isso na avaliação com o trecho específico**.

---

## 7. Lembrete final: os limites são Etapa + Persona

O **modo** (pull/push), a **etapa atual do grafo** e a **persona do cliente** definem o campo de jogo da conversa.

Seu trabalho é:

- **Proteger esses limites** — o agente não pode pular etapas, pedir dados proibidos ou tratar um leigo com jargão técnico.
- **Rejeitar o que é claramente errado** com base nas regras duras.
- **Manter toda avaliação baseada em evidências** da conversa, nunca em intuição.

---

## Checklist rápido — Parte 2

Antes de finalizar, confirme:

1. **Identifiquei o modo** (pull ou push) e a **etapa atual do fluxo**.
2. **Julguei a conversa como o cliente**, não como eu mesmo.
3. **Verifiquei naturalidade** — um campo por vez, vocabulário acessível, sem formulário no WhatsApp.
4. **Checei leakage e regras duras** — sem avanço prematuro de etapa, sem dados proibidos, CPF validado.
5. **Avaliei pass/fail com o rubric da etapa correta**, olhando para o resultado e as evidências.
6. **Registrei qualquer texto "cara de IA"** com o trecho exato.
7. **Mantive todo o raciocínio rastreável** — O que, Onde, Por que.

Se todos os pontos estiverem cobertos, sua avaliação tende a ser **sólida, consistente e útil para melhorar o agente de onboarding da BrokerAI**.

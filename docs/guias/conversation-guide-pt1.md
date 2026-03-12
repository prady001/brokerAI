# Guia de Avaliação de Conversas — Onboarding BrokerAI (Parte 1: O que fazer)

Este guia explica **como avaliar a qualidade das conversas do agente de onboarding** de forma consistente, auditável e alinhada ao fluxo real de cadastro via WhatsApp.

Use este documento como **referência escrita** do processo de QA.

---

## Por que este papel é importante

A avaliação de qualidade é a **última camada de controle** antes de usarmos dados de conversa para:

- ajustar prompts e nós do agente de onboarding;
- validar se o fluxo funciona para clientes reais com perfis variados;
- identificar onde o agente perde dados, assusta o cliente ou viola regras duras.

O agente de onboarding é o **primeiro contato do cliente com a corretora via WhatsApp**. Uma conversa ruim aqui significa cliente perdido, cadastro incompleto ou dado errado no banco.

**Não há espaço para erros evitáveis.**

---

## Visão geral — princípios da boa avaliação

- **Leia sempre o cenário completo antes de olhar a conversa.**
- **Avalie com base em evidências**, não em "impressão" ou "vibe".
- **Cite trechos específicos da conversa** para justificar cada julgamento.
- **Escreva respostas limpas e auditáveis:**
  **O que aconteceu → Onde aconteceu → Por que isso importa.**
- **Quando tiver dúvida, pergunte antes de finalizar a avaliação.**

---

## Os dois modos de onboarding

Antes de avaliar qualquer conversa, identifique em qual modo ela ocorreu:

| Modo | Como começa | Primeira mensagem |
|---|---|---|
| **Pull** | Cliente inicia espontaneamente | Ex.: "quero me cadastrar", "como faço o cadastro?" |
| **Push** | Corretor dispara `/cadastrar +5511...` | Agente envia saudação proativa ao cliente |

O **modo pull** exige que o agente faça uma saudação + inicie a coleta na mesma resposta.
O **modo push** exige que o agente envie uma mensagem proativa clara antes de pedir qualquer dado.

---

## Passo a passo: como conduzir uma revisão de QA

### 1. Ler o contexto da tarefa antes da conversa

Antes de olhar a conversa, identifique:

- **Cenário** — qual modo (pull/push), qual etapa da conversa está sendo avaliada.
- **Persona** — quem é o cliente (perfil, como ele digita, nível de familiaridade com seguros).
- **Contexto oculto** — quais dados o cliente deveria ter fornecido ao longo da conversa.
- **Regras duras** — o que o agente não pode fazer em hipótese nenhuma neste cenário.

**Seu objetivo aqui:**
Entender como seria uma boa conversa *para aquele cliente específico* antes de julgar o que aconteceu.

### 2. Analisar a conversa e os critérios por etapa

O agente de onboarding passa por etapas sequenciais. Avalie **cada etapa separadamente**:

| Etapa | O que o agente deve fazer |
|---|---|
| `contact_client` (push) | Enviar saudação proativa + pedir nome |
| `collect_client` | Coletar nome completo e CPF, um campo por vez |
| `collect_policy` | Coletar seguradora, item segurado, número da apólice, vencimento |
| `confirm` | Exibir resumo completo e pedir confirmação explícita (sim/não) |
| `handle_confirmation` | Processar "sim" → registro, "não" → reiniciar coleta com gentileza |
| `register` | Cadastrar no banco; escalar ao corretor após 3 falhas |
| `welcome` | Enviar mensagem de boas-vindas ao cliente |
| `notify_seller` | Enviar resumo do novo cadastro ao BROKER_NOTIFICATION_PHONE |

Ao revisar, verifique se:

- A **etapa atual** está correta dado o histórico da conversa.
- O agente **manteve dados** coletados em turnos anteriores (não pediu o mesmo dado duas vezes).
- O agente **não violou nenhuma regra dura** (ver seção abaixo).
- A **transição entre etapas** foi suave e natural para o contexto de WhatsApp.

### 3. Preencher e enviar a avaliação

- Envie **um formulário por conversa**.
- Confirme que está avaliando a conversa correta.
- Justifique cada ponto com **evidências da conversa**, não com intuição.
- Conclua com:
  - **Aprovado** — o agente conduziu a conversa de forma correta e natural.
  - **Precisa de correção** — descreva exatamente o que falhou e em qual etapa.

---

## Regras duras — o que nunca pode acontecer

Estas regras são **inegociáveis**. Qualquer violação é reprovação automática:

| Regra | Exemplo de violação |
|---|---|
| Nunca registrar sem confirmação explícita do cliente | Agente cria cadastro após "ok, pode ir" sem exibir resumo |
| Nunca pedir email como campo obrigatório | Agente bloqueia sem email; email é **opcional** |
| Nunca pedir dados financeiros, senhas ou cartão | "Qual o número do seu cartão para verificação?" |
| Nunca prometer cobertura ou condição de apólice | "Com esse seguro você está coberto em caso de..." |
| Nunca identificar-se como IA, a menos que o cliente pergunte | "Sou um robô da corretora." sem ser perguntado |
| Validar CPF com dígito verificador antes de prosseguir | Aceitar CPF com sequência inválida (ex: 111.111.111-11) |
| Escalar após 3 falhas de cadastro, nunca travar | Agente tenta indefinidamente sem notificar o corretor |

---

## Como escrever respostas fortes (QA auditável)

Valorizamos **clareza** e **rastreabilidade**.

- **✓ Seja específico(a)** — cite a mensagem exata onde o problema ocorreu.
- **× Evite "o agente foi ruim"** sem apontar onde e por quê.
- **✓ Responda sempre:**
  - **O que aconteceu?** (descreva o comportamento)
  - **Onde aconteceu?** (qual mensagem / qual etapa do fluxo)
  - **Por que isso importa?** (liga ao impacto no cliente ou à regra dura violada)

**Exemplo de resposta fraca:**
> "O agente não foi natural."

**Exemplo de resposta forte:**
> "Na etapa `collect_policy`, após o cliente informar a seguradora, o agente pediu ao mesmo tempo número da apólice, item segurado e data de vencimento na mesma mensagem (3ª interação). Isso viola o princípio de um campo por vez e cria experiência de formulário no WhatsApp, o que é ruim para a persona de cliente comum."

---

## Quando pedir ajuda

Se estiver em dúvida sobre:

- se um CPF "parece válido" mas foi aceito indevidamente pelo agente;
- se a transição entre etapas está certa dado o histórico;
- se determinado comportamento do agente viola uma regra dura ou é apenas subótimo;
- como classificar um erro de dados coletados parcialmente.

**Pergunte antes de fechar a avaliação.**

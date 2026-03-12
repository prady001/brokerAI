# Tarefa Ralph — Melhorias nos Agentes de Onboarding e Orquestrador

## Contexto

Leia os guias de qualidade em:
- `docs/guias/conversation-guide-pt1.md`
- `docs/guias/conversation-guide-pt2.md`
- `docs/guias/conversation-guide-orchestrator.md`

E os arquivos de implementação:
- `agents/onboarding/nodes.py`
- `agents/onboarding/prompts.py`
- `agents/orchestrator/nodes.py`
- `api/routes/webhook.py`

## Problemas identificados e melhorias a implementar

### 1. `agents/onboarding/prompts.py` — `GENERATE_CLIENT_QUESTION_PROMPT`

**Problema:** O campo `{missing_fields}` passa nomes técnicos Python ("full_name", "cpf") diretamente ao LLM. Isso pode fazer o agente usar esses termos literais nas perguntas ao cliente, o que é anti-natural.

**Fix:** Adicionar mapeamento explícito de nomes de campo para linguagem natural no prompt. Exemplo:
- `full_name` → "nome completo"
- `cpf` → "CPF (somente números)"

---

### 2. `agents/onboarding/prompts.py` — `GENERATE_POLICY_QUESTION_PROMPT`

**Problema A:** O prompt começa com "O cliente acabou de confirmar os dados pessoais. Agora precisamos dos dados da apólice." — isso está SEMPRE presente, inclusive na 3ª ou 4ª pergunta sobre apólice, onde não faz sentido.

**Fix A:** Remover essa linha fixa do template. O contexto de transição já é passado via `{error_context}` no código quando necessário (ver `collect_policy_node`).

**Problema B:** Os campos `{missing_fields}` também usam nomes técnicos ("insurer", "item_description", "policy_number", "end_date").

**Fix B:** Adicionar mapeamento de campos para linguagem acessível:
- `insurer` → "nome da seguradora (ex: Porto Seguro, Bradesco)"
- `item_description` → "o que está sendo segurado (ex: modelo e placa do carro)"
- `policy_number` → "número da apólice ou contrato"
- `end_date` → "data de vencimento do seguro (DD/MM/AAAA)"

---

### 3. `agents/onboarding/prompts.py` — `ONBOARDING_SYSTEM_PROMPT`

**Problema:** Não orienta o LLM a usar vocabulário acessível para leigos. O guia (pt2, seção 2) define que o agente deve adaptar vocabulário — "número do contrato do seu seguro" em vez de "número da apólice".

**Fix:** Adicionar instrução explícita no system prompt sobre vocabulário acessível:
```
- Use linguagem acessível: "número do contrato" em vez de "apólice", "o que está segurado" em vez de "item segurado".
- O cliente pode não ter todos os dados em mãos — oriente-o gentilmente a verificar o documento físico ou PDF do seguro.
```

---

### 4. `agents/onboarding/nodes.py` — `collect_policy_node` — detecção frágil de transição

**Problema:** A detecção de "primeira pergunta sobre apólice" usa keywords ("apólice", "seguradora") nas mensagens do assistente. Se o agente usar outras palavras (como "seguro", "contrato"), a detecção falha e a `error_context` de transição não é enviada.

**Fix:** Adicionar um campo `policy_transition_done: bool` no estado do onboarding. Definir como `True` após o primeiro ciclo de `collect_policy_node`. Usar esse campo como condição, não keywords.

Isso requer:
1. Adicionar `"policy_transition_done": False` no estado inicial em `api/routes/webhook.py` (nas duas funções: `_handle_broker_cadastrar` e `_start_onboarding_pull`)
2. Em `collect_policy_node`, verificar `state.get("policy_transition_done", False)` em vez da busca por keywords
3. Retornar `"policy_transition_done": True` na primeira resposta do nó

---

### 5. `agents/orchestrator/nodes.py` — `faq_handler_node`

**Problema:** O system prompt não instrui o LLM a ser breve para o contexto de WhatsApp. O guia (orchestrator, seção "Avaliação do FAQ Handler") exige respostas de 2–5 frases no máximo.

**Fix:** Adicionar ao system prompt do faq_handler:
```
Responda em no máximo 3 frases. Este é um canal de WhatsApp — seja direto e informal. Não use listas com bullets nem headers.
```

---

### 6. `agents/orchestrator/nodes.py` — `human_handoff_node`

**Problema:** A resposta ao cliente é sempre a mesma string estática ("Olá! Recebi sua mensagem. Um dos nossos atendentes vai retornar para você em breve. 😊"), independentemente do contexto. O guia diz "minimamente personalizada ou contextualizada".

**Fix:** Usar o LLM para gerar uma resposta contextual breve com base na mensagem original, ou pelo menos incluir o nome do cliente na mensagem estática. Solução simples preferida (não usar LLM extra):
```python
response_msg = (
    f"Olá{', ' + client_name if client_name != 'Cliente' else ''}! "
    "Recebi sua mensagem e um dos nossos atendentes vai retornar para você em breve."
)
```

---

### 7. `agents/onboarding/nodes.py` — `collect_client_node` — naming confuso

**Problema:** A variável `first_contact_hint` é atribuída a `error_context`, misturando semânticas diferentes (primeira saudação vs. erro de validação).

**Fix:** Renomear para `context_hint` internamente, ou separar no template do prompt para `{context_hint}` além de `{error_context}`, deixando o template mais semântico. Alternativa mais simples: renomear a variável local para `context_hint` e passar como `error_context` no prompt (mantém interface).

---

## Ordem de execução

1. Corrigir `agents/onboarding/prompts.py` (itens 1, 2, 3)
2. Corrigir `agents/onboarding/nodes.py` (itens 4, 7)
3. Atualizar `api/routes/webhook.py` (estado inicial — item 4)
4. Corrigir `agents/orchestrator/nodes.py` (itens 5, 6)
5. Verificar que nenhuma alteração quebra as assinaturas existentes
6. Commitar com: `fix(onboarding): melhorar prompts e vocabulário para WhatsApp`
   e: `fix(orchestrator): faq mais conciso e handoff contextualizado`

## Critério de conclusão

Todos os 7 problemas estão corrigidos nos arquivos correspondentes e os commits foram feitos.

Quando tudo estiver implementado e commitado, emita: <promise>MELHORIAS IMPLEMENTADAS</promise>

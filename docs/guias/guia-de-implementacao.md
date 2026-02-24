# Guia de Implementação — brokerAI

> **Área:** guias
> **Última atualização:** Fevereiro de 2026

## Objetivo

Este guia responde "o que faço agora?" em cada fase da implementação, do ambiente local até o MVP em produção. Use-o como mapa de navegação — ele referencia os documentos detalhados sem repeti-los.

---

## 1. Pré-requisitos

### 1.1 Contas e credenciais necessárias

Antes de escrever qualquer linha de código, garanta acesso a todos estes serviços:

| Serviço | Para que serve | Onde criar |
|---|---|---|
| [Anthropic](https://console.anthropic.com) | Chave da API Claude (LLM) | console.anthropic.com |
| [Z-API](https://z-api.io) | WhatsApp Business API | z-api.io (ver D-01 em `project_status.md`) |
| [AWS](https://aws.amazon.com) | S3 para documentos e fotos | aws.amazon.com |
| [SendGrid](https://sendgrid.com) | E-mail de fallback | sendgrid.com |
| [LangSmith](https://smith.langchain.com) | Observabilidade das chamadas LLM | smith.langchain.com |
| [Sentry](https://sentry.io) | Monitoramento de erros em prod | sentry.io |
| [GitHub](https://github.com) | Repositório e CI/CD | github.com |

> Credenciais da base de apólices da corretora dependem de acesso externo — veja D-03 em `project_status.md`.

### 1.2 Softwares locais

```bash
# Verificar Docker Desktop (WSL integration deve estar ativa)
docker --version        # Docker 24+
docker compose version  # v2.x

# Verificar Git e GitHub CLI
git --version           # 2.x
gh --version            # 2.x

# Verificar Python (para scripts fora do Docker)
python3 --version       # 3.12+
```

**WSL integration** (Windows): Docker Desktop → Settings → Resources → WSL Integration → habilitar para a distro em uso.

**GitHub CLI**: autenticar com `gh auth login` antes de qualquer operação com PRs.

**Claude Code + Ralph**: instalar via `npm install -g @anthropic-ai/claude-code`. O plugin ralph-wiggum é carregado automaticamente pelo Claude Code quando o `ralph_prompt.md` está presente no repositório.

### 1.3 Verificação final antes de começar

```bash
docker compose up postgres redis -d
docker compose ps        # ambos devem aparecer como "healthy"
docker compose down
```

Se os serviços ficarem em `starting` por mais de 30 s, veja a seção 6 (Troubleshooting).

---

## 2. Configuração inicial (uma única vez)

### 2.1 Clonar e configurar o ambiente

```bash
git clone git@github.com:<org>/brokerAI.git
cd brokerAI

# Copiar o template de variáveis de ambiente
cp .env .env.local  # edite .env com os valores reais (nunca commite .env preenchido)
```

### 2.2 Variáveis mínimas para iniciar o M1

Edite o `.env` e preencha pelo menos estas variáveis para o ambiente de desenvolvimento:

```
ANTHROPIC_API_KEY=sk-ant-...

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/insurance_agents
POSTGRES_DB=insurance_agents
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

REDIS_URL=redis://localhost:6379/0
```

As demais variáveis (Z-API, AWS, SendGrid, LangSmith, Sentry) são necessárias em etapas posteriores — deixe em branco por enquanto. Consulte a lista completa de variáveis no arquivo `.env`.

### 2.3 Subir infraestrutura de desenvolvimento

```bash
# Sobe apenas banco e cache (sem a API, que ainda não existe)
docker compose up postgres redis -d

# Confirmar que os health checks passaram
docker compose ps
```

Saída esperada:

```
NAME                STATUS
brokerai-postgres-1  running (healthy)
brokerai-redis-1     running (healthy)
```

### 2.4 Configurar proteções no GitHub

Antes de começar qualquer milestone, ative a proteção do branch `main`:

```
GitHub → Repositório → Settings → Branches → Branch protection rules → Add rule
Branch name pattern: main
```

Marque:
- [x] Require a pull request before merging
- [x] Require approvals (mínimo: 1)
- [x] Require status checks to pass before merging (adicionar `pytest` e `ruff` quando o CI estiver criado no M1)
- [x] Do not allow bypassing the above settings

Conecte o repositório ao projeto Kanban em GitHub → Projects (#1).

---

## 3. Sequência de implementação por milestone

A ordem de execução é obrigatória — M2 e M3 são paralelos, mas dependem de M1:

```
M1 (sequencial)
    └── M2 (worktree A) ┐
        M3 (worktree B) ┘ paralelo após M1 merged
            └── Orquestrador (sequencial, após M2 e M3 merged)
```

### M1 — Fundação (Semanas 1–3)

**Branch:**

```bash
git checkout main && git pull origin main
git checkout -b feat/m1-fundacao
```

**Ralph prompt:** `ralph_prompt_m1.md`

**Iniciar o Ralph Loop:**

```bash
# Confirmar branch ativa antes de rodar
git branch   # deve mostrar * feat/m1-fundacao

/ralph-loop "Leia ralph_prompt_m1.md e implemente o M1 completo" --max-iterations 25 --completion-promise "M1_CONCLUIDO"
```

**O que revisar ao terminar:**

```bash
git log --oneline main..HEAD       # todos os commits do Ralph
git diff main...HEAD               # diff completo para revisão
docker compose exec api pytest tests/ -v
docker compose exec api ruff check .
docker compose exec api mypy .
```

**Criar e mergear o PR:**

```bash
git push -u origin feat/m1-fundacao

gh pr create \
  --title "feat(m1): fundação — FastAPI, banco, webhooks e Z-API" \
  --body "$(cat <<'EOF'
## Contexto
Implementação do M1 conforme architecture.md.
Gerado via Ralph Loop com revisão manual antes do merge.

## O que mudou
- Docker Compose com API, PostgreSQL e Redis
- Migrations iniciais (clients, policies, claims, conversations)
- Rotas /webhook/whatsapp e /scheduler/renewal-check
- Integração básica Z-API

## Como testar
- [ ] `docker compose up` sobe sem erros
- [ ] `pytest tests/` passa com 0 falhas
- [ ] Webhook recebe mensagem de teste do Z-API

Closes #<número-da-issue>
EOF
)"

# Após aprovação:
gh pr merge --squash
```

**Issue do Kanban:** checklist M1 em `project_status.md`.

---

### M2 — Agente de Renovação (Semanas 4–8)

Executar em worktree isolado para rodar em paralelo com M3:

```bash
git worktree add ../brokerAI-m2 -b feat/m2-agente-renovacao
cd ../brokerAI-m2
```

**Ralph prompt:** `ralph_prompt.md` (genérico — o agente lê `project_status.md` para identificar as tarefas do M2)

**Iniciar o Ralph Loop:**

```bash
/ralph-loop "Leia ralph_prompt.md e implemente o M2 completo" --max-iterations 30 --completion-promise "M2_CONCLUIDO"
```

**O que revisar ao terminar:**
- `PolicyService` com query por vencimento
- Critérios de elegibilidade (`evaluate_renewal_eligibility`) — ver regras em `CLAUDE.md`
- Tools do agente de renovação (sem `emit_policy`)
- CRON configurado para 08:00 BRT
- Régua de follow-up: 30d → 15d → 7d → 2d
- Testes unitários e de integração

**Criar e mergear o PR:** mesma sequência do M1, ajustando título e escopo.

---

### M3 — Agente de Sinistros (Semanas 7–10)

Executar em segundo worktree, em paralelo com M2:

```bash
git worktree add ../brokerAI-m3 -b feat/m3-agente-sinistros
cd ../brokerAI-m3
```

**Ralph prompt:** `ralph_prompt.md`

**Iniciar o Ralph Loop:**

```bash
/ralph-loop "Leia ralph_prompt.md e implemente o M3 completo" --max-iterations 30 --completion-promise "M3_CONCLUIDO"
```

**O que revisar ao terminar:**
- Fluxo FNOL completo (`fnol.py`)
- Classificação de severidade: `simple` / `complex` / `critical`
- Upload de documentos: WhatsApp → S3
- Geração de protocolo único
- Notificações proativas de status

**Criar e mergear o PR:** mesma sequência do M1.

---

### Orquestrador (após M2 e M3 merged)

```bash
git checkout main && git pull origin main
git checkout -b feat/orquestrador
```

**Ralph prompt:** `ralph_prompt.md` — o agente lê o `project_status.md` para identificar as tarefas restantes.

```bash
/ralph-loop "Leia ralph_prompt.md e implemente o Agente Orquestrador" --max-iterations 20 --completion-promise "ORQUESTRADOR_CONCLUIDO"
```

---

## 4. Convenções que o código deve seguir

### Tools

Toda tool deve usar Pydantic e o decorator `@tool`:

```python
from langchain_core.tools import tool
from pydantic import BaseModel

class EvaluateRenewalInput(BaseModel):
    policy_id: str
    check_date: str  # ISO 8601

@tool(args_schema=EvaluateRenewalInput)
def evaluate_renewal_eligibility(policy_id: str, check_date: str) -> dict:
    """Avalia se uma apólice é elegível para renovação automática."""
    ...
```

Nunca passe texto livre como input de tool. O schema Pydantic rejeita chamadas malformadas antes de qualquer efeito colateral.

### Nós do LangGraph

Cada nó é uma função pura que recebe e retorna o state completo:

```python
def detect_intent(state: OrchestratorState) -> OrchestratorState:
    # Nunca modifica estado fora do retorno
    return {**state, "intent": detected_intent}
```

### Localização dos arquivos

| Tipo de arquivo | Onde fica |
|---|---|
| Grafo LangGraph | `agents/<nome>/graph.py` |
| Nós do grafo | `agents/<nome>/nodes.py` |
| Prompts do agente | `agents/<nome>/prompts.py` |
| Tools do agente | `agents/<nome>/tools.py` |
| Fluxo FNOL | `agents/claims/fnol.py` |
| Serviços de domínio | `services/<nome>_service.py` |
| Modelos SQLAlchemy | `models/database.py` |
| Schemas Pydantic | `models/schemas.py` |
| Rotas FastAPI | `api/routes/<nome>.py` |
| Testes unitários | `tests/unit/` |
| Fixtures | `tests/fixtures/` |

Estrutura completa de diretórios em `CLAUDE.md`.

### emit_policy

Esta tool deve sempre lançar `NotImplementedError` no MVP:

```python
@tool
def emit_policy(policy_data: dict) -> None:
    """Emite uma apólice. Desabilitado no MVP — o corretor emite manualmente."""
    raise NotImplementedError(
        "Emissão automática desabilitada no MVP. "
        "Solicite ao corretor para emitir manualmente após aprovação do cliente."
    )
```

Referência: ADR-005 em `architecture.md` §6.

---

## 5. Fluxo de testes

### Rodar todos os testes

```bash
docker compose exec api pytest tests/ -v
```

### Rodar um teste específico

```bash
docker compose exec api pytest tests/unit/test_renewal_agent.py::test_evaluate_eligibility -v
```

### Lint e verificação de tipos

```bash
docker compose exec api ruff check .
docker compose exec api mypy .
```

### Critério mínimo para abrir um PR

- `pytest tests/` → 0 falhas
- `ruff check .` → 0 erros
- `mypy .` → 0 erros

Nenhum PR deve ser aberto com falhas nestes três comandos.

---

## 6. Troubleshooting comum

### Docker não sobe

**Sintoma:** `docker compose up` falha imediatamente ou o container não inicia.

**Causa mais comum (Windows/WSL):** WSL integration desativada no Docker Desktop.

**Solução:**

```
Docker Desktop → Settings → Resources → WSL Integration
→ habilitar para a distro em uso (ex: Ubuntu-22.04)
→ Apply & Restart
```

---

### Migrations não rodam

**Sintoma:** `alembic upgrade head` retorna erro de conexão.

**Causa:** o container do PostgreSQL ainda não está `healthy` — o healthcheck pode levar até 25 s na primeira inicialização.

**Solução:**

```bash
# Aguardar o status healthy antes de rodar
docker compose ps   # checar coluna STATUS
# Só rodar quando postgres aparecer como "healthy"
docker compose exec api alembic upgrade head
```

---

### Ralph Loop não encerra

**Sintoma:** o loop continua rodando após o Claude ter concluído as tarefas.

**Causa:** o `completion-promise` não foi encontrado — o Claude escreveu a string com formatação diferente da esperada.

**O que verificar:** o Claude deve escrever a promise exatamente assim:

```
<promise>M1_CONCLUIDO</promise>
```

Verifique no `ralph_prompt_m1.md` qual é o texto exato e confirme que o Claude o reproduziu sem variações. Se o loop travar, cancele com `/cancel-ralph` e verifique o último output.

---

### Z-API não recebe mensagens

**Sintoma:** mensagens enviadas para o WhatsApp não chegam ao webhook local.

**Causa:** a URL de webhook configurada na instância Z-API aponta para o ambiente errado ou não é acessível publicamente.

**Solução para desenvolvimento local:**

```bash
# Expor o servidor local com ngrok (ou similar)
ngrok http 8000

# Copiar a URL gerada (ex: https://abc123.ngrok.io)
# Configurar no painel Z-API:
# Instância → Webhooks → Mensagens recebidas → URL: https://abc123.ngrok.io/webhook/whatsapp
```

---

## 7. Próximos passos após o MVP

### Integrações pós-MVP (não incluídas no escopo atual)

- **APIs das seguradoras:** cotação e emissão direta, eliminando a emissão manual pelo corretor (ADR-005)
- **ERP da corretora:** sincronização bidirecional da base de apólices (ver D-03 em `project_status.md`)
- **Rede de prestadores:** integração com prestadores de assistência para acionamento automatizado
- **Portal web:** dashboard para o corretor acompanhar renovações e sinistros em andamento

### Decisões abertas que precisam ser resolvidas

As decisões abaixo bloqueiam ou impactam fases da implementação. Consulte `project_status.md` para o prazo de cada uma:

| # | Decisão | Impacto |
|---|---|---|
| D-01 | Confirmar provedor WhatsApp: Z-API vs. Twilio | Bloqueia M1 |
| D-02 | Definir ambiente de deploy: Railway vs. AWS | Bloqueia M1 |
| D-03 | Formato de importação de apólices: CSV, API do ERP ou scraping | Bloqueia M1 |
| D-04 | Valor exato do `VIP_PREMIUM_THRESHOLD` com a corretora | Bloqueia M2 |
| D-05 | Templates de mensagem WhatsApp aprovados pela Meta | Bloqueia M2 |

---

## Referências

| Documento | Conteúdo |
|---|---|
| `docs/architecture.md` | Arquitetura técnica completa, ADRs, schemas de estado dos agentes |
| `docs/project_spec.md` | Regras de negócio, critérios de elegibilidade, fluxos de produto |
| `docs/guias/ralph-loop-com-github.md` | Como usar o Ralph Loop com versionamento no GitHub |
| `CLAUDE.md` | Convenções de código, git e documentação do projeto |
| `project_status.md` | Status atual, checklist por milestone, decisões abertas |

# brokerAI

Sistema de agentes de IA para automatizar renovação de apólices e abertura de sinistros em corretoras de seguros brasileiras, operando via WhatsApp Business API.

## O problema

Corretoras operam hoje com processos 100% manuais nos dois fluxos de maior volume: renovação de apólices e abertura de sinistros. Isso gera custo operacional alto, perda de receita por apólices vencendo sem abordagem proativa, e experiência ruim para o cliente.

## A solução

Três agentes LangGraph especializados, com humanos no loop para decisões finais no MVP:

```
WhatsApp (Z-API)  ──►  Agente Orquestrador
                            │            │
                   Agente Renovação   Agente Sinistros
                            │            │
              PostgreSQL · Redis · AWS S3 · SendGrid
```

- **Agente Orquestrador** — detecta intenção e roteia para o agente correto
- **Agente de Renovação** — conduz o ciclo completo de renovação, do contato inicial ao handoff para o corretor emitir
- **Agente de Sinistros** — abre o FNOL, coleta documentos, gera protocolo e aciona assistência

## Stack

| Camada | Tecnologia |
|---|---|
| LLM | Claude Sonnet (prod) / Claude Haiku (dev) |
| Orquestração | LangGraph (StateGraph) |
| Backend | Python + FastAPI |
| Banco de dados | PostgreSQL 16 |
| Estado de conversas | Redis 7 |
| Documentos | AWS S3 |
| WhatsApp | Z-API |
| E-mail fallback | SendGrid |
| Observabilidade | LangSmith + Sentry |

## Status

🟡 Planejamento — documentação de arquitetura concluída, implementação não iniciada.

Ver progresso detalhado em [`project_status.md`](project_status.md).

## Como começar

Consulte o [`docs/guias/guia-de-implementacao.md`](docs/guias/guia-de-implementacao.md) para o passo a passo completo, do ambiente local até o MVP.

```bash
# Pré-requisito: Docker Desktop com WSL integration ativa
docker compose up postgres redis -d
docker compose ps  # ambos devem aparecer como "healthy"
```

## Documentação

| Documento | Conteúdo |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Arquitetura técnica, ADRs, schemas dos agentes |
| [`docs/project_spec.md`](docs/project_spec.md) | Especificação de produto e regras de negócio |
| [`docs/guias/guia-de-implementacao.md`](docs/guias/guia-de-implementacao.md) | Guia prático de implementação por milestone |
| [`docs/guias/ralph-loop-com-github.md`](docs/guias/ralph-loop-com-github.md) | Como usar o Ralph Loop com versionamento |
| [`CLAUDE.md`](CLAUDE.md) | Convenções de código, git e documentação |

## Licença

Proprietário — todos os direitos reservados.

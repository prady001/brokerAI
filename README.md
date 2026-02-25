# brokerAI

Sistema de agentes de IA para automatizar o comissionamento e o atendimento de sinistros em corretoras de seguros brasileiras.

## O problema

Corretoras operam hoje com processos 100% manuais nos dois processos de maior custo operacional: baixa de comissões das seguradoras e intermediação de sinistros via WhatsApp.

- **Comissionamento:** a equipe acessa diariamente o portal de cada seguradora individualmente, extrai dados de comissão, consolida manualmente e emite nota fiscal. Processo repetitivo, sujeito a erros e com risco de perda de receita.
- **Sinistros:** a corretora funciona como cópia-e-cola entre o cliente e a seguradora. Alto volume, baixo valor agregado, especialmente em pedidos de assistência 24h.

## A solução

Dois agentes LangGraph independentes, com humanos no loop para exceções:

```
CRON (08:00 BRT)  ──►  Agente de Comissionamento
                              │
                   portais seguradoras → NFS-e → WhatsApp

WhatsApp (Z-API)  ──►  Agente Orquestrador
                              │
                        Agente de Sinistros
                              │
                   seguradora ↔ cliente (relay)
```

- **Agente de Comissionamento** — acessa portais das seguradoras (via API ou RPA), consolida comissões, emite NFS-e automaticamente e envia resumo diário para a corretora
- **Agente de Sinistros** — recebe o cliente no WhatsApp, coleta dados, abre o chamado na seguradora e faz o relay das atualizações até o encerramento
- **Agente Orquestrador** — roteia mensagens WhatsApp para o agente correto e gerencia handoffs para humano

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
| Automação de portais | Playwright (RPA) |
| 2FA automatizado | pyotp + gateway SMS/IMAP |
| Emissão de NFS-e | Focus NFe API |
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

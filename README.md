# brokerAI

Plataforma de agentes de IA com memória relacional acumulativa para corretoras de seguros brasileiras.

## O problema

Corretoras de seguros operam hoje com processos 100% manuais nos fluxos de maior custo operacional: baixa de comissões, intermediação de sinistros e gestão do relacionamento com clientes.

- **Comissionamento:** a equipe acessa diariamente o portal de cada seguradora individualmente, extrai dados, consolida em planilha e emite nota fiscal — processo repetitivo, sujeito a erros e com risco de perda de receita
- **Sinistros:** a corretora funciona como cópia-e-cola entre cliente e seguradora via WhatsApp — alto volume, baixo valor agregado
- **Relacionamento:** o corretor conhece bem apenas os 50 clientes que falou recentemente. Os outros 950 estão no escuro

## A solução

O BrokerAI começa automatizando o operacional e evolui, a cada versão, para uma inteligência de negócio completa — onde o agente conhece cada cliente da carteira tão bem quanto o corretor conhece seus melhores clientes.

```
MVP (mês 3)     V1 (mês 6)          V2 (mês 12)          V3 (ano 2)         V4 (ano 2-3)
─────────────   ──────────────────  ───────────────────  ─────────────────  ──────────────
Automatiza  →   Grafo de memória →  Inteligência      →  Advocacia e     →  Plataforma com
operação        por cliente         de carteira           prevenção          efeito de rede
```

### MVP — Automação Operacional

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

- **Agente de Comissionamento** — acessa portais (API ou RPA), consolida comissões, emite NFS-e e envia relatório diário
- **Agente de Sinistros** — recebe o cliente, coleta dados, abre chamado, faz relay e encerra automaticamente sinistros simples
- **Agente Orquestrador** — roteia mensagens WhatsApp e gerencia handoff humano-IA

### V1 — Memória Real do Cliente

A partir da V1, cada interação alimenta um **grafo de conhecimento temporal** por cliente:

```
Cliente João
  ├── Apólice Auto (Porto Seguro, vence ago/2026)
  ├── Sinistro #001 (vidro, mar/2025, resolvido 8 dias)
  ├── Preferência: WhatsApp, mensagens curtas, noite
  ├── Negociação: recusou desconto de 10% — franquia alta era o bloqueio
  └── Score: risco de churn 0.72, filho vai tirar carta (oportunidade)
```

O agente não começa mais cada conversa do zero — ele conhece o cliente há anos.

## Stack

### MVP

| Camada | Tecnologia |
|---|---|
| LLM | Claude Sonnet (prod) / Claude Haiku (dev) |
| Orquestração | LangGraph (StateGraph) |
| Backend | Python + FastAPI |
| Banco de dados | PostgreSQL 16 |
| Estado de conversas | Redis 7 |
| Automação de portais | Playwright (RPA) |
| 2FA automatizado | pyotp + gateway SMS/IMAP |
| WhatsApp | Z-API |
| NFS-e | Focus NFe API |
| Documentos | AWS S3 |
| Observabilidade | LangSmith + Sentry |

### V1+ (Memória em Grafo)

| Camada | Tecnologia |
|---|---|
| Knowledge graph temporal | Graphiti (Zep) |
| SDK de memória | LangMem (LangChain) |
| Banco de grafo | Neo4j / FalkorDB |

## Status

🟡 Planejamento — arquitetura, tese de produto e roadmap concluídos. Implementação não iniciada.

Ver progresso detalhado em [`project_status.md`](project_status.md).

## Como começar

Consulte o [`docs/guias/guia-de-implementacao.md`](docs/guias/guia-de-implementacao.md) para o passo a passo completo.

```bash
# Pré-requisito: Docker Desktop com WSL integration ativa
docker compose up postgres redis -d
docker compose ps  # ambos devem aparecer como "healthy"
```

## Documentação

### Produto

| Documento | Conteúdo |
|---|---|
| [`docs/produto/tese-da-empresa.md`](docs/produto/tese-da-empresa.md) | Tese, modelo de negócio, mercado e vantagem competitiva |
| [`docs/produto/roadmap.md`](docs/produto/roadmap.md) | Roadmap completo MVP → V4 com métricas por versão |
| [`docs/produto/casos-de-uso.md`](docs/produto/casos-de-uso.md) | 19 casos de uso mapeados em 6 blocos |

### Técnico

| Documento | Conteúdo |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Arquitetura técnica, ADRs, schemas dos agentes e arquitetura de memória V1 |
| [`docs/project_spec.md`](docs/project_spec.md) | Especificação de produto, user stories e regras de negócio |
| [`docs/guias/guia-de-implementacao.md`](docs/guias/guia-de-implementacao.md) | Guia prático de implementação por milestone |
| [`CLAUDE.md`](CLAUDE.md) | Convenções de código, git e documentação |

## Licença

Proprietário — todos os direitos reservados.

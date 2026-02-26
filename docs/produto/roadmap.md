# Roadmap de Versões — BrokerAI

> **Versão:** 1.0
> **Data:** Fevereiro de 2026
> **Contexto:** Roadmap completo do produto desde o MVP até a plataforma com efeito de rede, baseado no mapa de casos de uso definido em `docs/produto/casos-de-uso.md`.

---

## Visão Geral

```
MVP          V1           V2           V3           V4
(mês 3)      (mês 6)      (mês 12)     (ano 2)      (ano 2-3)
   │             │             │             │             │
Automatiza   Memória      Inteligência  Advocacia    Plataforma
operação     real do      de carteira   e prevenção  com efeito
existente    cliente      e perfil                   de rede
```

**Princípio de evolução:** cada versão entrega valor standalone. V1 não depende do sucesso de V2. A plataforma cresce em camadas, não em grandes apostas.

---

## MVP — Mês 3: Automação Operacional

**Objetivo:** eliminar o trabalho operacional de maior custo para a primeira corretora. Provar que o agente funciona melhor do que o processo manual, sem complexidade de memória avançada.

**Use Cases incluídos:**

| UC | Nome | Descrição resumida |
|---|---|---|
| UC-13 | Comissionamento com automação | Acesso diário a portais de seguradoras, consolidação e NFS-e automática |
| UC-07 | Acompanhamento de sinistros | Monitoramento e relay proativo de atualizações ao cliente |
| UC-18 | Sinistro simples end-to-end | Acionamento, abertura na seguradora e encerramento sem humano (vidro, guincho, assistência) |
| UC-15 | Onboarding básico via WhatsApp | Coleta de documentos, OCR e criação de cadastro via WhatsApp |

**Stack MVP:**

| Camada | Tecnologia |
|---|---|
| LLM | Claude Sonnet (prod), Claude Haiku (dev) |
| Orquestração | LangGraph (StateGraph) |
| Estado de conversa | Redis (TTL 30 dias) |
| Backend | Python + FastAPI |
| Banco de dados | PostgreSQL 16 |
| Automação de portais | Playwright (headless) |
| 2FA | pyotp (TOTP) + IMAP + SMS gateway |
| WhatsApp | Z-API |
| NFS-e | Focus NFe API |
| Armazenamento | AWS S3 |
| Observabilidade | LangSmith + Sentry |

**Milestones internos:**

| Milestone | Semanas | Entregável |
|---|---|---|
| M1 — Fundação | 1-3 | Docker Compose, PostgreSQL, Redis, WhatsApp configurado, importação de carteira via CSV |
| M2 — Comissionamento | 4-7 | Agente acessando portais, consolidando comissões, emitindo NFS-e, enviando relatório diário |
| M3 — Sinistros | 6-10 | Agente intermediando sinistros simples e escalando graves com resumo estruturado |
| **MVP** | **fim do mês 3** | **Dois agentes em produção + primeiras métricas reais** |

**Métricas de sucesso:**

| Métrica | Meta |
|---|---|
| % de comissões capturadas | 100% |
| Tempo entre comissão disponível e NF emitida | < 1 hora |
| Tempo de primeira resposta ao cliente em sinistro | < 1 minuto |
| Horas manuais economizadas por semana | ≥ 70% do tempo atual |
| CSAT dos atendimentos via agente | ≥ 4.0 / 5.0 |

**Critério de saída do MVP:** pelo menos 1 corretora pagante usando os dois agentes em produção por 30 dias consecutivos, com métricas dentro do target.

---

## V1 — Mês 6: Memória Real do Cliente

**Objetivo:** substituir o armazenamento de conversas em Redis por um **grafo de conhecimento temporal** por cliente. O agente passa a "conhecer" cada cliente de forma acumulativa — não apenas no contexto da conversa atual.

**Mudança arquitetural central:** introdução do **Graphiti** (Zep) como camada de memória de longo prazo, complementando (e eventualmente substituindo) o Redis para estado de relacionamento.

**Use Cases incluídos:**

| UC | Nome | Descrição resumida |
|---|---|---|
| UC-01 | Perfil longitudinal do cliente | Grafo acumulativo de apólices, sinistros, preferências e eventos de vida por cliente |
| UC-04 | Relacionamento proativo | Agente inicia conversas no momento certo: renovação próxima, pós-sinistro, aniversário, evento climático |
| UC-06 | Memória de negociação | Grafo registra o que foi prometido, oferecido e recusado em cada negociação anterior |
| UC-14 | Compliance SUSEP automático | Trilha de auditoria completa, retenção de 5 anos, documentação de suitability |

**Adições à stack:**

| Componente | Tecnologia | Papel |
|---|---|---|
| Grafo de memória | Graphiti (Zep) | Knowledge graph temporal por cliente |
| SDK de memória | LangMem (LangChain) | Integração nativa com LangGraph |
| Banco de grafo | Neo4j ou FalkorDB | Persistência do grafo de relacionamentos |

**Estrutura do grafo de cliente (exemplo):**

```
Cliente: João Silva
  ├── [tem] → Apólice Auto #12345
  │              ├── seguradora: Porto Seguro
  │              ├── vencimento: 2026-08-10
  │              └── prêmio: R$ 2.400/ano
  ├── [fez] → Sinistro #001 (2025-03-15)
  │              ├── tipo: vidro
  │              ├── status: resolvido
  │              └── prazo: 8 dias
  ├── [preferência] → WhatsApp, mensagens curtas, noite
  ├── [negociação] → recusou desconto de 10% por franquia alta (2025-08)
  ├── [evento] → mencionou "filho vai tirar carta" (2026-01-20)
  └── [score] → risco_churn: 0.72, potencial_expansão: alto
```

**Métricas de sucesso:**

| Métrica | Meta |
|---|---|
| Taxa de renovação (vs. baseline MVP) | +10 p.p. |
| Taxa de resposta dos clientes a mensagens proativas | ≥ 35% |
| NPS dos clientes da corretora (proxy via tom das mensagens) | melhora mensurável |
| Corretoras no plano Pro ou acima | ≥ 10 |

**Critério de saída do V1:** grafo de cliente ativo para ≥ 80% da carteira de pelo menos 3 corretoras. Primeiro caso documentado de oportunidade de negócio detectada automaticamente pelo grafo.

---

## V2 — Mês 12: Inteligência de Carteira e Personalização

**Objetivo:** expandir a inteligência do agente do nível individual (um cliente) para o nível de portfólio (toda a carteira), e refinar a personalização com base no perfil emocional e comportamental de cada cliente.

**Use Cases incluídos:**

| UC | Nome | Descrição resumida |
|---|---|---|
| UC-03 | Score de saúde do relacionamento | Churn score, potencial de expansão e NPS implícito contínuo por cliente |
| UC-05 | Adaptação ao perfil emocional | Agente ajusta tom, tamanho e horário de mensagens ao perfil de cada cliente |
| UC-10 | Inteligência comparativa de seguradoras | Análise de desempenho real das seguradoras na carteira (prazo, contestação, SLA) |
| UC-02 | Detecção de eventos de vida | Identificação de oportunidades de cross-sell a partir de mudanças detectadas no grafo |

**Adições à plataforma:**

- **Dashboard de inteligência** — painel para o corretor com visão da carteira: clientes em risco de churn, oportunidades de cross-sell, ranking de seguradoras por performance
- **Engine de personalização** — módulo que aprende o perfil comunicativo de cada cliente ao longo do tempo
- **API de carteira** — permite que a corretora consulte insights do grafo via API para integrar com outros sistemas

**Métricas de sucesso:**

| Métrica | Meta |
|---|---|
| Churn de clientes das corretoras | -15% vs. baseline |
| Oportunidades de cross-sell detectadas e convertidas | ≥ 20% de taxa de conversão |
| Corretoras ativas na plataforma | ≥ 50 |
| ARR | ≥ R$ 3,6M |

---

## V3 — Ano 2: Advocacia, Prevenção e Precificação de Risco

**Objetivo:** transformar o agente de executor de tarefas em **inteligência estratégica do corretor** — capaz de defender o cliente no sinistro, prevenir perdas e otimizar a rentabilidade da carteira.

**Use Cases incluídos:**

| UC | Nome | Descrição resumida |
|---|---|---|
| UC-08 | Advogado do cliente no sinistro | Detecta subpagamentos de seguradora, compara com histórico, gera documentação de recurso |
| UC-12 | Benchmarking de carteira | Compara métricas da corretora com benchmark agregado de corretoras similares |
| UC-09 | Prevenção de sinistros | Alertas preditivos baseados em padrões da carteira e dados externos (clima, furtos por região) |
| UC-19 | Precificação dinâmica de risco | Sugere qual cliente merece desconto, qual está perto de cancelar, qual tem espaço para upsell |
| UC-11 | Detecção de padrões de risco | Identifica clientes com padrão anômalo na carteira (risco de fraude ou custo elevado) |

**Mudança de posicionamento:** nessa versão, o BrokerAI deixa de ser "automação de tarefas" e passa a ser posicionado como **"inteligência de negócio para corretoras"** — justificando um aumento de ticket médio e abertura para segmento de médias corretoras.

**Métricas de sucesso:**

| Métrica | Meta |
|---|---|
| Corretoras ativas | ≥ 200 |
| ARR | ≥ R$ 6M |
| Ticket médio mensal | ≥ R$ 1.500 |
| Cases documentados de comissão recuperada via UC-08 | ≥ 50 |

---

## V4 — Ano 2-3: Plataforma com Efeito de Rede

**Objetivo:** transformar o BrokerAI de produto em **plataforma** — onde o valor cresce com o número de corretoras participantes, criando defensibilidade que nenhum produto isolado consegue ter.

**Use Cases incluídos:**

| UC | Nome | Descrição resumida |
|---|---|---|
| UC-16 | Efeito de rede | Grafo agregado e anonimizado entre corretoras gera inteligência de mercado coletiva |
| UC-17 | Prospecção autônoma | Agente identifica e qualifica prospects similares à carteira atual, inicia abordagem |

**Como o efeito de rede funciona:**

```
Corretora A (SP)   ─┐
Corretora B (RJ)   ─┤─→  Grafo Agregado Anonimizado  →  Inteligência de Mercado
Corretora C (MG)   ─┤        (sem dados pessoais)
Corretora D (RS)   ─┘
                         ↓
              "Porto Seguro resolve sinistros de colisão
               em 12 dias (média das corretoras nessa região)"

              "Clientes com esse perfil têm 3x mais chance
               de cancelar após o segundo sinistro"

              "Taxa de renovação de apólices de vida caiu 8%
               nas corretoras com carteira similar à sua"
```

**Modelo de monetização adicional no V4:**

| Produto | Modelo | Preço estimado |
|---|---|---|
| BrokerAI Intelligence API | Por consulta ao grafo de mercado | R$ 0,50 - R$ 2,00/consulta |
| White-label para redes de corretoras | Licença por rede | R$ 5.000 - R$ 15.000/mês |
| Prospecção como serviço | Por lead qualificado | R$ 200 - R$ 500/lead |

**Métricas de sucesso:**

| Métrica | Meta |
|---|---|
| Corretoras ativas | ≥ 500 |
| ARR | ≥ R$ 12M |
| NPS médio das corretoras | ≥ 60 |
| Valuation (referência 4-8x ARR) | R$ 48M - R$ 96M |

---

## Tabela Consolidada de Use Cases por Versão

| UC | Nome | MVP | V1 | V2 | V3 | V4 |
|---|---|---|---|---|---|---|
| UC-13 | Comissionamento automatizado | ✅ | — | — | — | — |
| UC-07 | Acompanhamento de sinistros | ✅ | — | — | — | — |
| UC-18 | Sinistro end-to-end | ✅ | — | — | — | — |
| UC-15 | Onboarding via WhatsApp | ✅ | — | — | — | — |
| UC-01 | Perfil longitudinal do cliente | — | ✅ | — | — | — |
| UC-04 | Relacionamento proativo | — | ✅ | — | — | — |
| UC-06 | Memória de negociação | — | ✅ | — | — | — |
| UC-14 | Compliance SUSEP automático | — | ✅ | — | — | — |
| UC-03 | Score de saúde do relacionamento | — | — | ✅ | — | — |
| UC-05 | Adaptação ao perfil emocional | — | — | ✅ | — | — |
| UC-10 | Inteligência comparativa de seguradoras | — | — | ✅ | — | — |
| UC-02 | Detecção de eventos de vida | — | — | ✅ | — | — |
| UC-08 | Advogado do cliente no sinistro | — | — | — | ✅ | — |
| UC-12 | Benchmarking de carteira | — | — | — | ✅ | — |
| UC-09 | Prevenção de sinistros | — | — | — | ✅ | — |
| UC-19 | Precificação dinâmica de risco | — | — | — | ✅ | — |
| UC-11 | Detecção de padrões de risco | — | — | — | ✅ | — |
| UC-16 | Efeito de rede (plataforma) | — | — | — | — | ✅ |
| UC-17 | Prospecção autônoma | — | — | — | — | ✅ |

---

## Decisões Arquiteturais por Versão

| Versão | ADR relevante | Decisão |
|---|---|---|
| MVP | ADR-001 a ADR-005 | LangGraph, Claude Sonnet, Redis, Pydantic tools, emit_policy bloqueado |
| V1 | ADR-006 (a definir) | Migrar memória de conversa de Redis para Graphiti (grafo temporal) |
| V1 | ADR-007 (a definir) | Escolha de banco de grafo: Neo4j vs. FalkorDB vs. Kuzu |
| V2 | ADR-008 (a definir) | Arquitetura do dashboard: web app separado vs. embutido na API |
| V3 | ADR-009 (a definir) | Modelo de scoring de risco: regras vs. ML próprio vs. LLM-as-judge |
| V4 | ADR-010 (a definir) | Modelo de privacidade e governança do grafo agregado |

---

*Este documento deve ser revisado a cada trimestre e atualizado com base em aprendizados de produto e feedback das corretoras clientes.*

*Documentos relacionados:*
- *[Casos de Uso](./casos-de-uso.md)*
- *[Tese da Empresa](./tese-da-empresa.md)*
- *[Arquitetura Técnica](../architecture.md)*
- *[Status do Projeto](../../project_status.md)*

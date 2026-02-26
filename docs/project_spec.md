# Project Spec — Solução de Agentes de IA para Corretora de Seguros

> **Versão:** 2.0
> **Data:** Fevereiro de 2026
> **Status:** Draft — escopo revisado após entrevista com a corretora

---

## 1. Definição

### 1.1 Problema

A corretora opera hoje com processos 100% manuais nos dois fluxos de maior custo operacional identificados na entrevista com a equipe: baixa de comissionamento e intermediação de sinistros.

- **Comissionamento:** a equipe acessa diariamente os portais de cada seguradora individualmente, extrai os dados de comissão manualmente, consolida em planilha e emite nota fiscal. O processo se repete para cada seguradora e consome horas por dia sem gerar nenhum valor além do controle financeiro mínimo.
- **Sinistros:** a corretora funciona como cópia-e-cola entre o cliente e a seguradora via WhatsApp. Recebe a demanda, repassa para a seguradora, aguarda resposta e devolve ao cliente — um trabalho repetitivo, de baixo julgamento e alto volume, especialmente nos pedidos de assistência 24h (guincho e pane).

### 1.2 Solução

Construir uma plataforma de agentes de IA com **memória relacional acumulativa** projetada exclusivamente para corretoras de seguros. O BrokerAI começa automatizando os processos operacionais de maior custo (comissionamento e sinistros) e evolui — a cada versão — para uma inteligência de negócio completa: memória de longo prazo por cliente, inteligência de carteira, advocacia em sinistros e, eventualmente, efeito de rede entre corretoras.

A visão completa de produto está documentada em [`docs/produto/tese-da-empresa.md`](./produto/tese-da-empresa.md) e [`docs/produto/casos-de-uso.md`](./produto/casos-de-uso.md).

### 1.3 Objetivos Estratégicos

| # | Objetivo | Indicador Principal |
|---|---|---|
| 1 | Eliminar trabalho operacional de comissionamento | Horas/dia gastas no processo antes vs. depois |
| 2 | Reduzir tempo de resposta em sinistros | Tempo médio de retorno ao cliente |
| 3 | Garantir que nenhuma comissão seja perdida | % de comissões capturadas vs. disponíveis nas seguradoras |
| 4 | Construir grafo de conhecimento de cada cliente (V1+) | % da carteira com perfil longitudinal ativo |
| 5 | Aumentar taxa de renovação via relacionamento proativo (V1+) | Taxa de renovação antes vs. depois |
| 6 | Tornar-se plataforma com efeito de rede (V4) | Corretoras ativas + NRR |

### 1.4 Contexto e Restrições

- **Estágio tecnológico atual:** processo 100% manual, sem automação prévia; sistema de gestão é o Agger
- **Horizonte de entrega MVP:** até 3 meses
- **Canal primário:** WhatsApp (canal preferido do cliente brasileiro)
- **Escopo do MVP:** Agente de Comissionamento (end-to-end autônomo) + Agente de Sinistros (relay assistido) + Onboarding básico
- **Fora do escopo do MVP:** memória em grafo, renovação de apólices, captação de novos clientes, integração bidirecional com Agger, dashboard de gestão (→ V1+)

---

## 2. Key Components

---

### 2.1 Product Requirements

#### 2.1.1 Definição

Product Requirements descrevem **o que o sistema deve fazer** do ponto de vista do usuário e do negócio — sem entrar em como é implementado tecnicamente. Cobre os casos de uso, as regras que governam cada decisão, os critérios que definem se uma funcionalidade está pronta e as métricas que validam o MVP.

---

#### 2.1.2 User Stories

**Agente de Comissionamento**

| ID | Como... | Quero... | Para... |
|---|---|---|---|
| US-01 | Corretora | Receber todo dia um resumo das comissões disponíveis no WhatsApp | Não precisar acessar nenhum portal manualmente |
| US-02 | Corretora | Ter a nota fiscal emitida automaticamente quando houver comissão | Não perder prazo de faturamento |
| US-03 | Corretora | Ter todas as seguradoras consolidadas em um único relatório | Parar de alternar entre múltiplos sites |
| US-04 | Corretora | Ser alertada quando uma comissão esperada não aparecer | Não deixar dinheiro na mesa por falta de acompanhamento |

**Agente de Sinistros**

| ID | Como... | Quero... | Para... |
|---|---|---|---|
| US-05 | Cliente | Acionar meu sinistro a qualquer hora pelo WhatsApp | Não depender do horário comercial da corretora |
| US-06 | Cliente | Receber atualizações do meu caso sem precisar ligar | Ter tranquilidade durante o processo |
| US-07 | Cliente | Saber o status do meu pedido de guincho em tempo real | Não ficar sem informação na beira da estrada |
| US-08 | Corretora | Não precisar ficar no meio da conversa entre cliente e seguradora | Focar em casos que realmente precisam de mim |
| US-09 | Corretora | Ter o histórico completo de cada sinistro centralizado | Consultar qualquer caso sem depender de memória ou WhatsApp pessoal |

---

#### 2.1.3 Regras de Negócio

**Comissionamento — Ciclo diário**

| Etapa | Regra |
|---|---|
| Horário de execução | Diariamente às 08:00 BRT via CRON |
| Acesso aos portais | Credenciais da corretora armazenadas com criptografia; 2FA gerenciado pelo agente |
| Consolidação | Todas as seguradoras processadas antes de gerar o relatório |
| Emissão de NFS-e | Disparada automaticamente ao confirmar comissão disponível; uma nota por seguradora |
| Comissão ausente | Se uma seguradora esperada não retornar dados, gerar alerta específico para a corretora |
| Falha de acesso | Em caso de erro de login ou portal indisponível, notificar corretora e registrar para retry no dia seguinte |

**Comissionamento — Estratégia de integração por seguradora**

| Tipo de acesso | Estratégia |
|---|---|
| Seguradora com API de corretor (ex: Bradesco) | Integração via API REST com autenticação OAuth |
| Seguradora sem API | Automação de browser com Playwright (RPA) |
| 2FA por TOTP | Geração automática via `pyotp` com chave secreta armazenada |
| 2FA por SMS/e-mail | Leitura automática via gateway SMS ou IMAP em conta dedicada |

**Sinistros — Roteamento**

| Tipo | Ação do Agente |
|---|---|
| Assistência 24h (guincho, pane, troca de pneu) | Coleta dados → abre chamado na seguradora → atualiza cliente em tempo real |
| Troca de vidro / pequenos danos | Coleta dados → abre chamado → repassa protocolo ao cliente |
| Colisão, furto, incêndio, acidente com vítima | Coleta dados iniciais → escala imediatamente para corretor humano com resumo estruturado |
| Dúvida geral (não é sinistro) | Responde ou escala conforme contexto |

**Sinistros — Regras de escalada**

| Condição | Ação |
|---|---|
| Sinistro grave (colisão, furto, vítima) | Escala sempre para humano, independente do horário |
| Sem retorno da seguradora em > 2h | Notifica corretora para acompanhamento manual |
| Cliente solicitar falar com humano | Handoff imediato com histórico completo da conversa |

---

#### 2.1.4 Critérios de Aceite por Funcionalidade

**[F-01] Coleta de comissões nos portais das seguradoras**
- [ ] O agente acessa todos os portais configurados diariamente às 08:00 BRT sem intervenção humana
- [ ] O agente resolve o 2FA automaticamente (TOTP, e-mail ou SMS conforme o portal)
- [ ] Falhas de acesso são registradas e notificadas à corretora com descrição do erro
- [ ] Nenhuma seguradora configurada é ignorada sem registro de motivo

**[F-02] Consolidação e relatório de comissões**
- [ ] O relatório diário consolida dados de todas as seguradoras em formato único
- [ ] Cada linha contém: seguradora, número da apólice, cliente, competência e valor da comissão
- [ ] O relatório é enviado via WhatsApp para a corretora até as 09:00 BRT

**[F-03] Emissão automática de NFS-e**
- [ ] A nota fiscal é emitida automaticamente via API (Focus NFe ou equivalente) para cada comissão confirmada
- [ ] A NF contém os dados corretos de tomador (seguradora) e prestador (corretora)
- [ ] Confirmação de emissão é incluída no relatório diário
- [ ] Erros de emissão geram alerta imediato para a corretora

**[F-04] Recebimento e triagem de sinistros**
- [ ] O agente responde ao cliente em menos de 30 segundos após a mensagem
- [ ] O agente coleta: tipo de sinistro, localização (se aplicável), número da apólice ou placa
- [ ] O agente classifica corretamente entre sinistro simples e sinistro grave em ≥ 90% dos casos de teste

**[F-05] Relay com a seguradora**
- [ ] O agente abre o chamado na seguradora pelo canal correto (API ou WhatsApp da seguradora)
- [ ] O agente repassa a resposta da seguradora ao cliente em menos de 2 minutos após o recebimento
- [ ] O histórico completo da conversa (cliente ↔ agente ↔ seguradora) é armazenado e consultável

**[F-06] Escalada para humano**
- [ ] Sinistros graves disparam notificação para o corretor em menos de 1 minuto com resumo estruturado
- [ ] O cliente recebe confirmação de que um corretor entrará em contato
- [ ] O corretor recebe: tipo de sinistro, dados do cliente, dados da apólice e histórico da conversa

---

#### 2.1.5 Métricas de Sucesso do MVP

| Métrica | Baseline (hoje) | Meta MVP |
|---|---|---|
| Tempo gasto com baixa de comissão por dia | A mapear na entrevista | < 5 minutos (revisão do relatório) |
| % de comissões capturadas vs. disponíveis | A mapear (risco de perda manual) | 100% |
| Tempo entre comissão disponível e NF emitida | 1–3 dias (manual) | < 1 hora (automático) |
| Tempo de primeira resposta ao cliente em sinistro | 20–60 minutos | < 1 minuto |
| Tempo de repasse da resposta da seguradora ao cliente | 30–120 minutos | < 2 minutos |
| Horas manuais economizadas por semana | — | ≥ 70% do tempo atual nos dois processos |
| CSAT dos atendimentos via agente | — | ≥ 4.0 / 5.0 |

---

### 2.2 Technical Design

#### 2.2.1 Definição

Technical Design descreve **como o sistema será construído** — a arquitetura dos agentes, o fluxo de orquestração, a stack tecnológica, o modelo de dados e as integrações externas necessárias. É o documento de referência para o time de desenvolvimento.

---

#### 2.2.2 Arquitetura dos Agentes

O sistema é composto por dois agentes independentes e uma camada de dados compartilhada:

```
┌──────────────────────────────────────────────────────────────────┐
│                     AGENTE DE COMISSIONAMENTO                    │
│                    (acionado por CRON — 08:00 BRT)               │
│                                                                  │
│  Tools:                                                          │
│  - fetch_commission_data   (API ou Playwright por seguradora)    │
│  - handle_2fa              (TOTP / e-mail / SMS)                 │
│  - consolidate_report      (agrupa todas as seguradoras)         │
│  - emit_nfse               (Focus NFe API)                       │
│  - send_daily_summary      (WhatsApp para a corretora)           │
│  - alert_missing_commission(notifica ausências inesperadas)      │
└──────────────────────────┬───────────────────────────────────────┘
                           │
          ┌────────────────▼─────────────────┐
          │          CAMADA DE DADOS          │
          │  PostgreSQL | Redis | S3          │
          └────────────────┬─────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                      AGENTE DE SINISTROS                         │
│               (acionado por webhook WhatsApp)                    │
│                                                                  │
│  Tools:                                                          │
│  - classify_claim          (simples vs. grave)                   │
│  - collect_claim_info      (coleta dados do cliente)             │
│  - open_claim_at_insurer   (API da seguradora ou WhatsApp relay) │
│  - relay_update_to_client  (repassa resposta da seguradora)      │
│  - escalate_to_broker      (sinistros graves → humano)           │
│  - store_claim_history     (centraliza histórico)                │
└──────────────────────────────────────────────────────────────────┘
```

**Fluxo de orquestração — Comissionamento:**

```
1. CRON dispara às 08:00 BRT
2. Para cada seguradora configurada:
   a. Agente acessa portal via API (se disponível) ou Playwright (RPA)
   b. Resolve 2FA automaticamente se necessário
   c. Extrai dados de comissão disponíveis
   d. Registra no banco
3. Consolida relatório de todas as seguradoras
4. Emite NFS-e via Focus NFe API para cada comissão
5. Envia resumo consolidado via WhatsApp para a corretora
6. Registra alertas para seguradoras sem dados ou com falha de acesso
```

**Fluxo de orquestração — Sinistros:**

```
1. Cliente envia mensagem via WhatsApp da corretora
2. Agente identifica intenção de sinistro
3. Coleta informações mínimas: tipo, localização, apólice/placa
4. Classifica o sinistro:
   a. Simples (assistência, guincho, vidro) → abre chamado na seguradora
   b. Grave (colisão, furto, acidente com vítima) → escala para corretor humano
5. Para sinistros simples:
   a. Abre chamado via canal da seguradora (API ou WhatsApp)
   b. Aguarda resposta
   c. Repassa atualização ao cliente
   d. Repete até encerramento
6. Histórico completo armazenado e consultável
```

---

#### 2.2.3 Stack Tecnológica

| Camada | Tecnologia | Justificativa |
|---|---|---|
| **LLM Base** | Claude (Anthropic) | Melhor desempenho em português e raciocínio complexo |
| **Orquestração de Agentes** | LangGraph | Fluxos stateful com suporte a loops e handoff humano |
| **Canal WhatsApp** | Z-API ou Twilio | APIs estáveis com suporte BR, webhooks confiáveis |
| **Backend** | Python (FastAPI) | Ecossistema LLM + alta performance para APIs |
| **Banco de Dados** | PostgreSQL | Dados transacionais estruturados (apólices, sinistros) |
| **Cache / Estado** | Redis | Estado de conversas em andamento, filas de mensagens |
| **Armazenamento de Docs** | AWS S3 | Apólices em PDF, fotos de sinistros, documentos |
| **OCR / Extração** | Mistral OCR ou AWS Textract | Leitura de documentos enviados pelo cliente |
| **Infraestrutura** | AWS ou Railway | Deploy simples, escalável, baixo custo no MVP |
| **Monitoramento** | LangSmith + Sentry | Rastreabilidade de chamadas LLM + erros de sistema |

---

#### 2.2.4 Modelo de Dados

**Entidade: Policy (Apólice)**

```sql
policies
  id                UUID PRIMARY KEY
  client_id         UUID REFERENCES clients(id)
  insurer_id        UUID REFERENCES insurers(id)
  policy_number     VARCHAR UNIQUE
  type              ENUM (auto, life, home, business, health)
  status            ENUM (active, expired, cancelled, renewed)
  premium_amount    DECIMAL
  start_date        DATE
  end_date          DATE
  document_url      VARCHAR  -- link S3
  created_at        TIMESTAMP
  updated_at        TIMESTAMP
```

**Entidade: Client (Cliente)**

```sql
clients
  id                UUID PRIMARY KEY
  full_name         VARCHAR
  cpf_cnpj          VARCHAR UNIQUE
  phone_whatsapp    VARCHAR
  email             VARCHAR
  date_of_birth     DATE
  address           JSONB
  vip               BOOLEAN DEFAULT false
  created_at        TIMESTAMP
  updated_at        TIMESTAMP
```

**Entidade: Claim (Sinistro)**

```sql
claims
  id                UUID PRIMARY KEY
  policy_id         UUID REFERENCES policies(id)
  client_id         UUID REFERENCES clients(id)
  protocol_number   VARCHAR UNIQUE
  type              ENUM (glass, theft, collision, fire, assistance, other)
  status            ENUM (open, in_analysis, in_repair, closed, denied)
  severity          ENUM (simple, complex, critical)
  occurrence_date   TIMESTAMP
  occurrence_location JSONB
  description       TEXT
  documents         JSONB  -- array de URLs S3
  opened_at         TIMESTAMP
  closed_at         TIMESTAMP
  assigned_to       UUID REFERENCES users(id)
```

**Entidade: Conversation (Conversa do Agente)**

```sql
conversations
  id                UUID PRIMARY KEY
  client_id         UUID REFERENCES clients(id)
  type              ENUM (renewal, claim, support)
  status            ENUM (active, waiting_client, escalated, closed)
  context           JSONB  -- estado atual do fluxo
  messages          JSONB  -- histórico da conversa
  agent_type        ENUM (renewal, claims, orchestrator)
  human_assigned    UUID REFERENCES users(id)
  started_at        TIMESTAMP
  updated_at        TIMESTAMP
  closed_at         TIMESTAMP
```

---

#### 2.2.5 Integrações Externas

| Integração | Finalidade | Prioridade no MVP |
|---|---|---|
| **WhatsApp Business API (Z-API)** | Canal com cliente (sinistros) e com a corretora (resumos) | 🔴 Crítica |
| **Portais das seguradoras (API ou RPA)** | Extração de dados de comissão | 🔴 Crítica |
| **Focus NFe / NFE.io** | Emissão automática de NFS-e | 🔴 Crítica |
| **Gateway SMS ou IMAP** | Resolução de 2FA nos portais das seguradoras | 🔴 Crítica |
| **Agger (exportação CSV)** | Fonte inicial da carteira de apólices | 🟡 Importante |
| **E-mail (SendGrid / SES)** | Fallback de comunicação e 2FA por e-mail | 🟡 Importante |
| **Bradesco Seguros API (Portal de Devs)** | Integração nativa para comissão e sinistros | 🟡 Importante |
| **Integração bidirecional com Agger** | Sincronização automática da carteira | 🟢 Pós-MVP |
| **Renovação de apólices** | Agente de renovação completo | 🟢 Pós-MVP |
| **Captação de novos clientes** | Agente de novos negócios | 🟢 Pós-MVP |
| **Dashboard de gestão** | Visão consolidada para a corretora | 🟢 Pós-MVP |

---

#### 2.2.6 Segurança e Compliance

- Todos os dados de clientes criptografados em repouso (AES-256) e em trânsito (TLS 1.3)
- Autenticação de usuários internos via JWT com expiração curta
- Logs de todas as ações do agente com timestamp e identificação (auditoria)
- Dados sensíveis (CPF, dados financeiros) nunca trafegam no histórico de conversa do LLM — são substituídos por tokens
- Retenção de conversas por 5 anos (exigência SUSEP para corretoras)
- Conformidade com LGPD: consentimento do cliente registrado antes do primeiro contato automatizado

---

## 3. Roadmap de Versões

O roadmap completo está documentado em [`docs/produto/roadmap.md`](./produto/roadmap.md). Abaixo o resumo executivo.

### MVP — Mês 3: Automação Operacional

| Milestone | Semanas | Entregável Principal |
|---|---|---|
| M1 — Fundação | 1–3 | Infraestrutura (Docker, PostgreSQL, Redis) + WhatsApp configurado + importação inicial da carteira via CSV do Agger |
| M2 — Agente de Comissionamento | 4–7 | Agente acessando portais das seguradoras, consolidando comissões e emitindo NFS-e automaticamente |
| M3 — Agente de Sinistros | 6–10 | Agente intermediando sinistros simples (assistência, guincho) e escalando os graves para humano |
| **MVP** | **Fim do mês 3** | **Dois agentes operando em produção + primeiras métricas reais coletadas** |

### V1 — Mês 6: Memória Real do Cliente

Substituição do Redis simples por grafo de conhecimento temporal (Graphiti/Zep). O agente passa a conhecer cada cliente de forma acumulativa.

| Use Case | Entregável |
|---|---|
| UC-01 Perfil longitudinal | Grafo por cliente: apólices, sinistros, eventos de vida, preferências |
| UC-04 Relacionamento proativo | Agente inicia conversas no momento certo (renovação, pós-sinistro, aniversário) |
| UC-06 Memória de negociação | Registro de argumentos, ofertas e recusas para personalizar renovações |
| UC-14 Compliance SUSEP | Trilha de auditoria completa + retenção de 5 anos automatizada |

### V2 — Mês 12: Inteligência de Carteira

| Use Case | Entregável |
|---|---|
| UC-03 Score de relacionamento | Churn score e potencial de expansão contínuo por cliente |
| UC-05 Perfil emocional | Agente adapta tom, tamanho e horário de mensagens por cliente |
| UC-10 Inteligência de seguradoras | Ranking de performance real das seguradoras na carteira |
| UC-02 Eventos de vida | Detecção automática de oportunidades de cross-sell |

### V3 — Ano 2: Advocacia e Prevenção

| Use Case | Entregável |
|---|---|
| UC-08 Advogado no sinistro | Detecta subpagamentos e gera documentação de recurso |
| UC-12 Benchmarking | Compara carteira com benchmark agregado de mercado |
| UC-09 Prevenção | Alertas preditivos de risco por cliente e região |
| UC-19 Precificação | Otimização de preço de renovação por perfil de cliente |

### V4 — Ano 2-3: Plataforma com Efeito de Rede

| Use Case | Entregável |
|---|---|
| UC-16 Network effects | Grafo agregado entre corretoras → inteligência de mercado coletiva |
| UC-17 Prospecção autônoma | Agente identifica e qualifica prospects similares à carteira atual |

---

## 4. Premissas Assumidas

> Levantadas com base em pesquisa de mercado. Devem ser validadas com a corretora antes do início de M1.

| # | Premissa | Validação necessária |
|---|---|---|
| P-01 | Cada seguradora tem portal próprio; não há hub único | Confirmar lista de seguradoras que a corretora opera |
| P-02 | Agger não tem API pública; exportação via CSV | Testar exportação no Agger e confirmar campos disponíveis |
| P-03 | Bradesco Seguros tem API de corretor documentada | Verificar acesso ao portal de devs com credenciais da corretora |
| P-04 | 2FA existe em alguns portais; pode ser SMS, e-mail ou TOTP | Mapear tipo de 2FA por seguradora durante M1 |
| P-05 | NFS-e é emitida em prefeitura municipal via API (Focus NFe) | Confirmar município do CNPJ da corretora e compatibilidade |
| P-06 | Canal da seguradora para sinistros é WhatsApp ou portal web | Confirmar canal por seguradora durante M1 |

---

*Este documento é o ponto de verdade técnica e de produto do projeto. Deve ser atualizado a cada milestone e revisado com a equipe da corretora antes do início de cada fase.*

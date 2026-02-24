# Project Spec — Solução de Agentes de IA para Corretora de Seguros

> **Versão:** 1.0  
> **Data:** Fevereiro de 2026  
> **Status:** Draft  

---

## 1. Definição

### 1.1 Problema

A corretora opera hoje com processos 100% manuais nos dois fluxos de maior volume operacional: renovação de apólices e abertura de sinistros. Isso gera três problemas diretos e mensuráveis:

- **Custo operacional alto:** a equipe gasta tempo em tarefas repetitivas e de baixo valor (ligar, enviar e-mail, preencher sistema, cobrar documentos) que poderiam ser automatizadas.
- **Receita perdida:** apólices vencem sem abordagem proativa ao cliente, reduzindo a taxa de renovação por falta de processo sistemático.
- **Experiência ruim:** clientes esperam horas ou dias para abrir um sinistro ou receber uma proposta de renovação, num mercado onde velocidade é diferencial competitivo.

### 1.2 Solução

Construir um sistema de dois agentes de IA especializados — um para renovação automática de apólices e outro para ativação de sinistros — operando via WhatsApp Business API, com humanos no loop para decisões finais no MVP.

Os agentes assumem toda a operação repetitiva, deixando a equipe humana focada em exceções, negociações complexas e relacionamento.

### 1.3 Objetivos Estratégicos

Os três objetivos têm peso igual no projeto:

| # | Objetivo | Indicador Principal |
|---|---|---|
| 1 | Reduzir custo operacional | Horas de trabalho manual economizadas por semana |
| 2 | Aumentar taxa de renovação de apólices | % de apólices renovadas vs. vencidas |
| 3 | Melhorar experiência do cliente | Tempo médio de atendimento + CSAT |

### 1.4 Contexto e Restrições

- **Estágio tecnológico atual:** processo 100% manual, sem automação prévia
- **Horizonte de entrega:** MVP em até 3 meses
- **Canal primário:** WhatsApp (canal preferido do cliente brasileiro)
- **Escopo do MVP:** agentes assistidos — humano valida antes da emissão final
- **Fora do escopo do MVP:** emissão automática, integração multi-seguradora via API, app mobile, dashboard de gestão

---

## 2. Key Components

---

### 2.1 Product Requirements

#### 2.1.1 Definição

Product Requirements descrevem **o que o sistema deve fazer** do ponto de vista do usuário e do negócio — sem entrar em como é implementado tecnicamente. Cobre os casos de uso, as regras que governam cada decisão, os critérios que definem se uma funcionalidade está pronta e as métricas que validam o MVP.

---

#### 2.1.2 User Stories

**Agente de Renovação**

| ID | Como... | Quero... | Para... |
|---|---|---|---|
| US-01 | Cliente | Ser avisado com antecedência que meu seguro vai vencer | Não ficar desprotegido por falta de tempo |
| US-02 | Cliente | Receber a proposta de renovação direto no WhatsApp | Não precisar ligar ou ir à corretora |
| US-03 | Cliente | Tirar dúvidas sobre valor e cobertura pelo WhatsApp | Decidir com informação antes de confirmar |
| US-04 | Cliente | Confirmar a renovação com uma mensagem simples | O processo ser rápido e sem burocracia |
| US-05 | Corretor | Receber apenas os clientes que já estão prontos para fechar | Focar meu tempo em negociação, não em prospecção |
| US-06 | Corretor | Ver quais apólices foram abordadas pelo agente e qual o status | Ter visibilidade sem precisar controlar manualmente |

**Agente de Sinistros**

| ID | Como... | Quero... | Para... |
|---|---|---|---|
| US-07 | Cliente | Abrir um sinistro a qualquer hora pelo WhatsApp | Não depender do horário comercial da corretora |
| US-08 | Cliente | Ser guiado sobre quais informações e documentos preciso enviar | Não errar e atrasar meu processo |
| US-09 | Cliente | Receber um protocolo imediatamente após o aviso | Ter confirmação de que o processo foi iniciado |
| US-10 | Cliente | Ser atualizado sobre o status do meu sinistro sem precisar ligar | Ter tranquilidade durante o processo |
| US-11 | Corretor | Receber o sinistro já com todas as informações organizadas | Agir rápido sem precisar ligar para o cliente para coletar dados |

---

#### 2.1.3 Regras de Negócio

**Renovação — Critérios de Autonomia do Agente**

| Condição | Ação do Agente |
|---|---|
| Sem sinistros no período + pagamento em dia + variação de prêmio ≤ 15% | ✅ Encaminha proposta automaticamente |
| Sinistro no período OU variação de prêmio > 15% | 👤 Escala para corretor humano |
| Cliente VIP (acima de valor X em prêmio anual) | 👤 Sempre revisado por humano |
| Dados desatualizados (endereço, placa, etc.) | 🔄 Solicita atualização antes de prosseguir |
| Sem resposta do cliente após 3 tentativas | 🔔 Alerta corretor para contato direto |

**Renovação — Régua de Comunicação**

| Prazo antes do vencimento | Ação |
|---|---|
| 30 dias | Primeiro contato: proposta de renovação |
| 15 dias | Lembrete se não houver resposta |
| 7 dias | Segundo lembrete + senso de urgência |
| 2 dias | Alerta final + escala para corretor se sem resposta |
| Vencimento | Notificação de vencimento + abertura de nova cotação |

**Sinistros — Classificação e Roteamento**

| Tipo de Sinistro | Ação Automática |
|---|---|
| Troca de vidro / pequenos danos | Abre OS + agenda assistência automaticamente |
| Assistência 24h (pane, reboque) | Aciona prestador imediatamente |
| Colisão com terceiros | Coleta FNOL + abre processo + escala para regulador |
| Furto / roubo parcial ou total | Orienta BO digital + escala para perito |
| Incêndio / danos estruturais | Coleta FNOL + escala urgente para gestor |
| Acidente com vítima | Aciona socorro + notifica gestor imediatamente |

---

#### 2.1.4 Critérios de Aceite por Funcionalidade

**[F-01] Monitoramento de vencimentos**
- [ ] O sistema identifica diariamente todas as apólices com vencimento nos próximos 30 dias
- [ ] Nenhuma apólice elegível é ignorada sem registro de motivo
- [ ] O agente aplica corretamente as regras de autonomia antes de agir

**[F-02] Envio de proposta de renovação**
- [ ] A mensagem é enviada no WhatsApp do cliente em menos de 1 minuto após acionamento
- [ ] A proposta contém: nome do cliente, tipo de seguro, valor atual, valor proposto e data de vencimento
- [ ] O agente responde dúvidas simples (cobertura, forma de pagamento) sem intervenção humana

**[F-03] Handoff para corretor humano**
- [ ] O corretor recebe notificação com resumo do cliente e histórico da conversa
- [ ] O handoff acontece em menos de 2 minutos após o gatilho ser ativado
- [ ] O cliente recebe mensagem confirmando que um corretor vai entrar em contato

**[F-04] Recebimento de aviso de sinistro**
- [ ] O agente inicia o fluxo de coleta em menos de 30 segundos após a mensagem do cliente
- [ ] O agente coleta: tipo, data, hora, local, descrição, terceiros envolvidos e documentos

**[F-05] Geração de protocolo de sinistro**
- [ ] Protocolo gerado e enviado ao cliente em menos de 3 minutos após o aviso
- [ ] O protocolo contém: número único, data/hora de abertura e próximos passos

**[F-06] Triagem e roteamento de sinistros**
- [ ] O agente classifica corretamente o tipo de sinistro em ≥ 90% dos casos de teste
- [ ] Sinistros simples são roteados sem intervenção humana
- [ ] Sinistros complexos chegam ao time interno com todas as informações organizadas

---

#### 2.1.5 Métricas de Sucesso do MVP

| Métrica | Baseline (hoje) | Meta MVP |
|---|---|---|
| % de apólices abordadas antes do vencimento | ~30% (manual, inconsistente) | ≥ 90% |
| Tempo médio de envio da proposta de renovação | 1–3 dias | < 1 minuto |
| Tempo médio de abertura de sinistro | 20–40 minutos | < 5 minutos |
| Taxa de resposta do cliente no WhatsApp | — | ≥ 40% |
| Horas manuais economizadas por semana | — | ≥ 60% do tempo atual nos dois processos |
| CSAT dos atendimentos via agente | — | ≥ 4.0 / 5.0 |

---

### 2.2 Technical Design

#### 2.2.1 Definição

Technical Design descreve **como o sistema será construído** — a arquitetura dos agentes, o fluxo de orquestração, a stack tecnológica, o modelo de dados e as integrações externas necessárias. É o documento de referência para o time de desenvolvimento.

---

#### 2.2.2 Arquitetura dos Agentes

O sistema é composto por três camadas:

```
┌─────────────────────────────────────────────────────────┐
│                    CANAL DE ENTRADA                      │
│         WhatsApp Business API  |  Webhook HTTP           │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                AGENTE ORQUESTRADOR                       │
│  - Identifica a intenção da mensagem (renovação / sinistro / outro)  │
│  - Gerencia estado da conversa (Redis)                   │
│  - Roteia para o agente especializado correto            │
│  - Gerencia handoff para humano                          │
└──────────┬──────────────────────────────┬───────────────┘
           │                              │
┌──────────▼──────────┐       ┌───────────▼──────────────┐
│  AGENTE RENOVAÇÃO   │       │    AGENTE SINISTROS       │
│                     │       │                           │
│  Tools:             │       │  Tools:                   │
│  - query_policies   │       │  - start_fnol_flow        │
│  - get_quote        │       │  - classify_claim         │
│  - send_proposal    │       │  - request_documents      │
│  - schedule_followup│       │  - generate_protocol      │
│  - escalate_to_agent│       │  - trigger_assistance     │
│  - emit_policy*     │       │  - escalate_to_adjuster   │
└──────────┬──────────┘       └───────────┬──────────────┘
           │                              │
┌──────────▼──────────────────────────────▼──────────────┐
│                   CAMADA DE DADOS                        │
│     PostgreSQL  |  Redis  |  S3 (documentos)            │
└─────────────────────────────────────────────────────────┘

* emit_policy: desabilitado no MVP — requer aprovação humana
```

**Fluxo de orquestração — Renovação:**

```
1. CRON job diário → consulta apólices com vencimento em 30 dias
2. Para cada apólice:
   a. Aplica regras de autonomia
   b. Se elegível → gera proposta → envia WhatsApp
   c. Aguarda resposta do cliente (estado salvo em Redis)
3. Cliente responde:
   a. Dúvida → agente responde com LLM
   b. Aceite → notifica corretor para emissão
   c. Negativa → registra motivo + agenda follow-up
   d. Silêncio → régua de lembretes automáticos
```

**Fluxo de orquestração — Sinistros:**

```
1. Cliente envia mensagem de sinistro via WhatsApp
2. Orquestrador detecta intenção → aciona Agente Sinistros
3. Agente inicia FNOL:
   a. Coleta tipo, data, hora, local, descrição
   b. Solicita fotos e documentos
   c. Classifica tipo de sinistro
4. Com base na classificação:
   a. Simples → aciona prestador automaticamente
   b. Complexo → monta dossiê → notifica time interno
5. Gera protocolo → envia ao cliente
6. Agenda atualizações proativas de status
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
| **WhatsApp Business API** | Canal de comunicação com cliente | 🔴 Crítica |
| **Base de Apólices (CSV/ERP)** | Fonte de dados das apólices | 🔴 Crítica |
| **E-mail (SendGrid / SES)** | Fallback de comunicação | 🟡 Importante |
| **Gateway de Pagamento (PIX/boleto)** | Cobrança de renovação | 🟡 Importante |
| **APIs das Seguradoras** | Cotação e emissão automática | 🟢 Pós-MVP |
| **Prestadores de Assistência** | Acionamento direto no sinistro | 🟢 Pós-MVP |
| **Sistema ERP da Corretora** | Sincronização bidirecional | 🟢 Pós-MVP |

---

#### 2.2.6 Segurança e Compliance

- Todos os dados de clientes criptografados em repouso (AES-256) e em trânsito (TLS 1.3)
- Autenticação de usuários internos via JWT com expiração curta
- Logs de todas as ações do agente com timestamp e identificação (auditoria)
- Dados sensíveis (CPF, dados financeiros) nunca trafegam no histórico de conversa do LLM — são substituídos por tokens
- Retenção de conversas por 5 anos (exigência SUSEP para corretoras)
- Conformidade com LGPD: consentimento do cliente registrado antes do primeiro contato automatizado

---

## 3. Roadmap do MVP

| Milestone | Semanas | Entregável Principal |
|---|---|---|
| M1 — Fundação | 1–3 | Base de dados + WhatsApp configurado + fluxos mapeados |
| M2 — Agente Renovação | 4–8 | Agente em produção para carteira piloto (auto) |
| M3 — Agente Sinistros | 7–10 | Agente em produção para tipos mais comuns |
| **MVP** | **Fim do mês 3** | **Dois agentes operando + primeiras métricas reais** |

---

*Este documento é o ponto de verdade técnica e de produto do projeto. Deve ser atualizado a cada milestone e revisado com a equipe da corretora antes do início de cada fase.*

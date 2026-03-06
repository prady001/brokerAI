# Plataforma do Gestor — Especificação Completa

> **Versão:** 1.0
> **Data:** Fevereiro de 2026
> **Contexto:** Especificação de produto da interface web para o gestor (corretor/dono da corretora), que dá visibilidade e controle sobre todos os agentes e operações do BrokerAI.

---

## 1. Visão Geral

### 1.1 O que é a Plataforma do Gestor

A Plataforma do Gestor é o **painel de controle central** do BrokerAI. É onde o corretor (ou gestor da corretora) acompanha o que os agentes fizeram, aprova ações que exigem confirmação humana, monitora a saúde da operação e acessa inteligência sobre sua carteira.

**Ela não substitui o WhatsApp** — o cliente continua interagindo pelo canal que já usa. A plataforma é voltada exclusivamente para o gestor.

### 1.2 Princípios de Design

| Princípio | Descrição |
|---|---|
| **Zero surpresa** | O gestor deve saber o que os agentes estão fazendo antes de precisar perguntar |
| **Ação em 1 clique** | Toda aprovação ou intervenção urgente deve ser executável com no máximo 2 cliques |
| **Progressão de informação** | KPIs no topo, detalhes sob demanda — não exibir tudo de uma vez |
| **Urgência visível** | Itens que precisam de atenção imediata devem se destacar visualmente sem que o gestor precise procurar |
| **Auditabilidade** | Tudo que o agente fez deve ser rastreável com contexto completo |

### 1.3 Quem usa

- **Dono/gestor da corretora** — usuário principal. Acessa diariamente para ver o resumo do dia, aprovar ações e acompanhar sinistros críticos.
- **Corretor operacional** (se a corretora tiver equipe) — acessa para resolver escaladas e acompanhar clientes.
- **Administrador da conta** — acessa configurações, integrações e credenciais dos portais.

### 1.4 Evolução por versão

| Versão | O que a plataforma entrega |
|---|---|
| **MVP** | Operação: comissionamento, sinistros, aprovações, status dos agentes, configurações |
| **V1** | Inteligência de cliente: perfil longitudinal, relacionamento proativo, compliance |
| **V2** | Inteligência de carteira: churn scores, oportunidades de cross-sell, ranking de seguradoras |
| **V3** | Estratégia: advocacia em sinistros, benchmarking, prevenção, precificação de risco |
| **V4** | Plataforma: rede de corretoras, inteligência de mercado coletiva |

---

## 2. Estrutura de Navegação

### 2.1 Mapa de Telas

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PLATAFORMA DO GESTOR                         │
└─────────────────────────────────────────────────────────────────────┘
         │
         ├── 🏠 Home (Dashboard)
         │       ├── KPIs do dia
         │       ├── Fila de aprovações pendentes
         │       ├── Alertas críticos
         │       └── Resumo de sinistros e comissões
         │
         ├── ✅ Aprovações
         │       ├── Pendentes (fila principal)
         │       ├── Aprovadas hoje
         │       └── Rejeitadas / Devolvidas
         │
         ├── 💰 Comissionamento
         │       ├── Resumo do dia
         │       ├── Por seguradora
         │       ├── Histórico mensal
         │       ├── NFS-e emitidas
         │       └── Divergências detectadas
         │
         ├── 🚗 Sinistros
         │       ├── Fila ativa (em andamento)
         │       ├── Escalados para mim
         │       ├── Encerrados (histórico)
         │       └── Detalhe do sinistro
         │
         ├── 👥 Carteira de Clientes
         │       ├── Lista de clientes
         │       ├── Ficha do cliente
         │       │       ├── Dados e apólices
         │       │       ├── Histórico de sinistros
         │       │       ├── Histórico de conversas
         │       │       └── Grafo de memória [V1+]
         │       └── Segmentos e filtros [V2+]
         │
         ├── 📊 Relatórios
         │       ├── Comissões mensais
         │       ├── Performance dos agentes
         │       ├── Saúde da carteira [V2+]
         │       └── Benchmarking [V3+]
         │
         ├── 🤖 Agentes
         │       ├── Status em tempo real
         │       ├── Log de execuções
         │       └── Configuração de autonomia
         │
         ├── ⚙️ Configurações
         │       ├── Integrações (portais e APIs)
         │       ├── Credenciais das seguradoras
         │       ├── WhatsApp (Z-API)
         │       ├── NFS-e (Focus NFe)
         │       ├── Notificações
         │       └── Equipe e permissões
         │
         └── 🔍 Auditoria
                 ├── Log completo de ações dos agentes
                 ├── Histórico de conversas
                 └── Exportação para compliance SUSEP [V1+]
```

### 2.2 Layout Global

```
┌──────────────────────────────────────────────────────────────────────────┐
│  [logo BrokerAI]    🔴 3 aprovações pendentes        🔔  [avatar: João]  │  ← Barra superior
└──────────────────────────────────────────────────────────────────────────┘
┌───────────┬──────────────────────────────────────────────────────────────┐
│           │                                                              │
│  🏠 Home  │                                                              │
│           │                                                              │
│  ✅ Aprov │              CONTEÚDO PRINCIPAL                              │
│    [!] 3  │                                                              │
│           │                                                              │
│  💰 Comis │                                                              │
│           │                                                              │
│  🚗 Sinis │                                                              │
│    [!] 2  │                                                              │
│           │                                                              │
│  👥 Carte │                                                              │
│           │                                                              │
│  📊 Relat │                                                              │
│           │                                                              │
│  🤖 Agent │                                                              │
│           │                                                              │
│  ⚙️ Config │                                                              │
│           │                                                              │
│  🔍 Audit │                                                              │
│           │                                                              │
└───────────┴──────────────────────────────────────────────────────────────┘
```

**Barra superior** exibe:
- Logo + nome da corretora
- Badge vermelho com contagem de aprovações urgentes pendentes
- Sino de notificações com histórico dos últimos alertas
- Avatar do usuário logado com menu de perfil

**Sidebar** exibe:
- Ícone + label de cada seção
- Badge com contagem de itens urgentes quando aplicável (`[!] N`)
- Seção ativa destacada

---

## 3. Telas — Especificação Detalhada

---

### 3.1 Home — Dashboard

**Objetivo:** dar ao gestor uma visão completa do estado da operação em menos de 10 segundos.

**Layout:**

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Bom dia, João 👋   Quinta-feira, 27 de fevereiro de 2026                │
│  Última atualização do agente de comissionamento: hoje às 08:12          │
└──────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌────────────────┐
│  APROVAÇÕES     │ │  SINISTROS      │ │  COMISSÕES HOJE │ │  AGENTES       │
│  PENDENTES      │ │  ESCALADOS      │ │                 │ │                │
│                 │ │                 │ │  R$ 14.780      │ │  ● Comiss. OK  │
│      3          │ │      2          │ │  3 NFS-e emit.  │ │  ● Sinistros OK│
│                 │ │                 │ │  1 ⚠ divergênc. │ │  ⚠ Porto Seg.  │
│  [Ver fila →]   │ │  [Ver fila →]   │ │  [Ver detalhes] │ │  portal falhou │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └────────────────┘

──── APROVAÇÕES PENDENTES ──────────────────────────────────────── [Ver todas]

┌──────────────────────────────────────────────────────────────────── ✅ ✗ ──┐
│ 🔴 URGENTE   Emitir NFS-e R$ 4.200,00 — Bradesco Seguros             15min│
│  O agente consolidou a comissão de março. Aguardando aprovação para emitir.│
│  [Ver detalhes]                                             [Aprovar] [Rej.]│
└───────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────── ✅ ✗ ──┐
│ 🟡 NORMAL    Escalar sinistro #2341 (colisão) para atendimento humano   1h │
│  Cliente: Maria Santos. Veículo: Fiat Argo 2022. Colisão em Av. Paulista. │
│  [Ver detalhes do sinistro]                                 [Aprovar] [Rej.]│
└───────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────── ✅ ✗ ──┐
│ 🟡 NORMAL    Enviar resumo de comissões do mês para e-mail             2h  │
│  Relatório mensal de fevereiro/2026 pronto para envio.                     │
│  [Preview do relatório]                                     [Aprovar] [Rej.]│
└───────────────────────────────────────────────────────────────────────────┘

──── SINISTROS ATIVOS ──────────────────────────────────────────── [Ver todos]

┌────────────────────────────────────────────────────────────────────────────┐
│  #2341  🔴 Colisão   │  Maria Santos    │  Porto Seguro  │  Escalado  │  1d │
│  #2338  🟡 Vidro     │  Carlos Lima     │  Allianz       │  Ag. segur │  3d │
│  #2335  🟢 Assistênc │  Ana Oliveira    │  Bradesco      │  Resolvido │  0d │
│  #2330  🟡 Furto ace │  Roberto Pereira │  HDI           │  Ag. client│  2d │
└────────────────────────────────────────────────────────────────────────────┘

──── ATIVIDADE RECENTE DOS AGENTES ──────────────────────────────────────────

│ 08:12  Agente de Comissionamento  Acessou 4 portais, consolidou R$ 14.780  │
│ 08:08  Agente de Comissionamento  Resolveu 2FA no portal Porto Seguro       │
│ 07:55  Agente de Comissionamento  Iniciou ciclo diário de comissionamento   │
│ 23:41  Agente de Sinistros        Enviou update ao cliente #2338 (Allianz)  │
│ 22:30  Agente de Sinistros        Detectou atualização no portal Allianz    │
```

**Componentes:**

| Componente | Descrição |
|---|---|
| KPIs (4 cards) | Aprovações pendentes, sinistros escalados, comissões do dia, status dos agentes |
| Fila de aprovações resumida | Máximo 3 itens mais urgentes com botões de ação inline |
| Tabela de sinistros ativos | Sinistros em andamento com status colorido e SLA |
| Feed de atividade | Log cronológico das últimas ações dos agentes |

---

### 3.2 Aprovações (Human-in-the-loop)

**Objetivo:** ser o ponto central onde o gestor revisa e autoriza toda ação irreversível que o agente gerou.

**Conceito:** por design (ADR-005), os agentes não executam ações irreversíveis sem aprovação. Esta tela é a fila de trabalho do gestor.

**Layout:**

```
┌──────────────────────────────────────────────────────────────────────────┐
│  APROVAÇÕES PENDENTES                          [Aprovar todas seguras ▼] │
│  3 pendentes  |  12 aprovadas hoje  |  0 rejeitadas                      │
│                                                                          │
│  Filtrar por: [Todas ▼]  [Todos os agentes ▼]  [Qualquer urgência ▼]    │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  🔴 URGENTE                                           há 15 minutos      │
│                                                                          │
│  EMITIR NFS-e — Bradesco Seguros                                         │
│                                                                          │
│  O agente de comissionamento consolidou as comissões de fevereiro/2026   │
│  referentes à carteira da Bradesco Seguros e gerou a nota fiscal abaixo. │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Tomador:    Bradesco Seguros S.A.                               │   │
│  │  Serviço:    Intermediação de seguros — fevereiro/2026           │   │
│  │  Valor:      R$ 4.200,00                                        │   │
│  │  ISS (5%):   R$ 210,00                                          │   │
│  │  Valor líq.: R$ 3.990,00                                        │   │
│  │  Competênc.: fevereiro/2026                                     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Histórico de comissões Bradesco:                                        │
│  Jan/26: R$ 3.800 ✅  |  Dez/25: R$ 4.100 ✅  |  Nov/25: R$ 3.950 ✅   │
│                                                                          │
│  [Ver relatório completo]          [Rejeitar e comentar]  [✅ Aprovar]  │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  🟡 NORMAL                                            há 1 hora          │
│                                                                          │
│  ESCALAR SINISTRO #2341 — Atendimento humano necessário                  │
│                                                                          │
│  O agente classificou este sinistro como CRÍTICO (colisão com danos      │
│  estruturais) e solicita handoff para o corretor.                        │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Cliente:     Maria Santos (CPF: ***.***.***-72)                 │   │
│  │  Apólice:     Porto Seguro Auto #PS-2024-88821                   │   │
│  │  Veículo:     Fiat Argo 2022 / Placa ABC-1D23                   │   │
│  │  Ocorrência:  27/02/2026 às 07:20 — Av. Paulista, 1000, SP      │   │
│  │  Tipo:        Colisão frontal — danos estruturais                │   │
│  │  Status:      Aguardando vistoria da Porto Seguro               │   │
│  │  Fotos:       3 recebidas [ver fotos]                           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Resumo da conversa com o cliente (últimas 4 mensagens):                │
│  > Maria: "Bom dia, tive um acidente agora cedo"                        │
│  > Agente: "Olá Maria! Lamento muito. Você está bem?"                   │
│  > Maria: "Sim, só o carro bateu feio. Preciso acionar o seguro."       │
│  > Agente: "Entendido. Vou abrir o sinistro. Pode tirar fotos do carro?"│
│                                                                          │
│  [Ver conversa completa]  [Assumir atendimento]  [Rejeitar]  [✅ Escalar]│
└──────────────────────────────────────────────────────────────────────────┘
```

**Estados de uma aprovação:**

| Estado | Descrição |
|---|---|
| `🔴 Urgente` | Impede continuação do fluxo do agente se não aprovado em breve |
| `🟡 Normal` | Aguarda aprovação mas o agente continua outros fluxos |
| `🟢 Informativo` | Não bloqueia — apenas notifica o gestor sobre uma ação já executada |

**Ações disponíveis:**

- **Aprovar** — libera o agente para executar a ação
- **Rejeitar e comentar** — bloqueia a ação e permite deixar instrução para o agente ajustar
- **Assumir atendimento** — para sinistros: o gestor toma o controle da conversa com o cliente
- **Aprovar todas seguras** — aprovação em lote apenas para NFS-e e relatórios (não para escaladas)

---

### 3.3 Comissionamento

**Objetivo:** dar visibilidade completa sobre comissões captadas, NFS-e emitidas e divergências detectadas.

**Sub-telas:** Resumo do Dia | Por Seguradora | Histórico | NFS-e | Divergências

#### 3.3.1 Resumo do Dia

```
┌──────────────────────────────────────────────────────────────────────────┐
│  COMISSIONAMENTO — 27 de fevereiro de 2026                               │
│  Ciclo executado às 08:12  |  Duração: 4 min 32s  |  [Executar agora]   │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  TOTAL CAPTADO   │ │  NFS-e EMITIDAS  │ │  PENDENTES       │ │  DIVERGÊNCIAS    │
│  hoje            │ │  hoje            │ │  aprovação       │ │  detectadas      │
│                  │ │                  │ │                  │ │                  │
│  R$ 14.780       │ │  3 de 4          │ │  1               │ │  1               │
│  +8% vs jan/26   │ │  R$ 10.580       │ │  R$ 4.200        │ │  R$ 320 a menor  │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  PORTAIS ACESSADOS HOJE                                                  │
│                                                                          │
│  Seguradora         Acesso    Comissão captada   NFS-e     Status       │
│  ─────────────────────────────────────────────────────────────────────  │
│  Bradesco Seguros   ✅ OK     R$ 4.200,00        ⏳ Pend.  Ag. aprova. │
│  Allianz            ✅ OK     R$ 3.850,00        ✅ Emitida R$ 3.850    │
│  HDI                ✅ OK     R$ 4.410,00        ✅ Emitida R$ 4.410    │
│  Porto Seguro       ❌ Falhou R$ —               —         ⚠ 2FA expirou│
│                                                                          │
│  [Retentar Porto Seguro]                                                 │
└──────────────────────────────────────────────────────────────────────────┘
```

#### 3.3.2 Divergências

Esta sub-tela é crítica — é o diferencial do UC-13 que detecta comissões que não vieram.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  DIVERGÊNCIAS DETECTADAS                                                 │
│  O agente identificou diferenças entre o esperado e o recebido.         │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  ⚠ Porto Seguro — fevereiro/2026                                         │
│                                                                          │
│  Comissão esperada:  R$ 5.200,00  (baseado no histórico de 6 meses)     │
│  Comissão recebida:  R$ 4.880,00                                         │
│  Diferença:          R$ 320,00 a MENOS  (−6,1%)                         │
│                                                                          │
│  Apólices com possível divergência:                                      │
│  • Apólice #PS-2024-77340 — Carlos Lima — esperado R$ 180, recebido R$ 0│
│  • Apólice #PS-2024-81200 — Teresa Melo — esperado R$ 140, recebido R$ 0│
│                                                                          │
│  Histórico Porto Seguro:                                                 │
│  ago/25: R$ 5.100  |  set/25: R$ 5.300  |  out/25: R$ 5.050            │
│  nov/25: R$ 5.200  |  dez/25: R$ 5.100  |  jan/26: R$ 5.150            │
│                                                                          │
│  [Ignorar]  [Abrir contestação]  [Ver apólices envolvidas]              │
└──────────────────────────────────────────────────────────────────────────┘
```

---

### 3.4 Sinistros

**Objetivo:** dar visibilidade sobre todos os sinistros em andamento, com triagem já feita pelo agente.

**Sub-telas:** Fila Ativa | Escalados para Mim | Histórico

#### 3.4.1 Fila Ativa

```
┌──────────────────────────────────────────────────────────────────────────┐
│  SINISTROS ATIVOS                                     [+ Registrar manual]│
│  4 em andamento  |  2 escalados para você  |  1 resolvido hoje           │
│                                                                          │
│  Filtrar: [Todos ▼]  [Todas seguradoras ▼]  [Todo tipo ▼]  [Buscar...]  │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  #    │ Severidade │ Cliente         │ Tipo       │ Seguradora │ Status  │ SLA  │
│─────────────────────────────────────────────────────────────────────────│
│  2341 │ 🔴 Crítico  │ Maria Santos    │ Colisão    │ Porto Seg  │ Escal.  │ 2d   │
│  2338 │ 🟡 Médio    │ Carlos Lima     │ Vidro      │ Allianz    │ Ag.Seg. │ 5d   │
│  2335 │ 🟢 Simples  │ Ana Oliveira    │ Assistênc. │ Bradesco   │ Resol.  │ —    │
│  2330 │ 🟡 Médio    │ Roberto Pereira │ Furto ace. │ HDI        │ Ag.Cli. │ 3d   │
└──────────────────────────────────────────────────────────────────────────┘
```

#### 3.4.2 Detalhe do Sinistro

Ao clicar em um sinistro, o gestor vê o contexto completo:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ← Voltar    SINISTRO #2341  🔴 Crítico — Colisão                       │
│  Aberto em 27/02/2026 às 09:15  |  3 dias em andamento                  │
└──────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────┐  ┌──────────────────────────────────────┐
│  DADOS DO SINISTRO             │  │  CONVERSA COM O CLIENTE              │
│                                │  │                                      │
│  Cliente: Maria Santos         │  │  27/02 07:20                         │
│  CPF: ***.***.***-72           │  │  Maria: "Bom dia, tive um acidente"  │
│                                │  │                                      │
│  Apólice: Porto Seguro Auto    │  │  27/02 07:21                         │
│  #PS-2024-88821                │  │  Agente: "Olá Maria! Você está bem?" │
│  Vencimento: 15/08/2026        │  │                                      │
│                                │  │  27/02 07:23                         │
│  Veículo: Fiat Argo 2022       │  │  Maria: "Sim, só o carro."           │
│  Placa: ABC-1D23               │  │                                      │
│                                │  │  27/02 07:25                         │
│  Ocorrência:                   │  │  Agente: "Vou abrir o sinistro."     │
│  Av. Paulista, 1000 — SP       │  │                                      │
│  27/02/2026 às 07:20           │  │  27/02 09:15                         │
│                                │  │  Agente: "Sinistro aberto na Porto.  │
│  STATUS ATUAL:                 │  │  Protocolo #PS-SIN-2026-441"         │
│  Aguardando vistoria           │  │                                      │
│  Porto Seguro — protocolo:     │  │  [Assumir conversa]                  │
│  #PS-SIN-2026-441              │  │  [Enviar mensagem como corretor]     │
│                                │  └──────────────────────────────────────┘
│  FOTOS (3)                     │
│  [📷][📷][📷]  [ver todas]     │  ┌──────────────────────────────────────┐
│                                │  │  LINHA DO TEMPO DO SINISTRO          │
│  [Contatar seguradora]         │  │                                      │
│  [Encerrar sinistro]           │  │  ✅ 09:15 Sinistro aberto na Porto   │
│  [Gerar relatório]             │  │  ✅ 09:20 Fotos enviadas             │
└────────────────────────────────┘  │  ⏳ —    Aguardando vistoria         │
                                    │  ⬜ —    Avaliação de danos          │
                                    │  ⬜ —    Proposta de indenização     │
                                    │  ⬜ —    Pagamento                   │
                                    └──────────────────────────────────────┘
```

---

### 3.5 Carteira de Clientes

**Objetivo:** acesso rápido a qualquer cliente, com visibilidade de saúde do relacionamento (aumenta progressivamente a cada versão).

#### 3.5.1 Lista de Clientes (MVP)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  CARTEIRA DE CLIENTES                          [+ Importar CSV] [+ Novo] │
│  247 clientes  |  312 apólices ativas  |  R$ 892.000 em prêmios/ano     │
│                                                                          │
│  Buscar: [_________________________]  Filtrar: [Todos ▼] [Todas apl. ▼] │
└──────────────────────────────────────────────────────────────────────────┘

│  Cliente           │ Apólices │ Sinistros │ Próx. Renov.  │ Saúde [V2]  │
│─────────────────────────────────────────────────────────────────────────│
│  Maria Santos      │ 2        │ 1 ativo   │ 15/08/2026    │ —           │
│  Carlos Lima       │ 1        │ 1 ativo   │ 03/03/2026    │ —           │
│  Ana Oliveira      │ 3        │ —         │ 10/04/2026    │ —           │
│  Roberto Pereira   │ 1        │ 1 ativo   │ 28/02/2026    │ —           │
│  Fernanda Costa    │ 2        │ —         │ 20/05/2026    │ —           │
```

**Nota MVP:** o campo "Saúde" aparece na grade mas fica vazio até o V2. A estrutura é montada desde o início para não quebrar o layout depois.

#### 3.5.2 Ficha do Cliente

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ← Voltar    CARLOS LIMA                                                 │
│  Cliente desde: março/2023  |  47 anos  |  SP                           │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  [Dados] [Apólices] [Sinistros] [Conversas] [Memória do Agente] [Notas] │
└──────────────────────────────────────────────────────────────────────────┘

─ ABA: APÓLICES ────────────────────────────────────────────────────────────

│  Apólice        │ Produto      │ Seguradora │ Prêmio     │ Vencimento  │
│─────────────────────────────────────────────────────────────────────────│
│  AL-2023-44521  │ Auto — Gol   │ Allianz    │ R$ 1.800   │ 03/03/2026  │
│                 │              │            │ ⚠ VENCE EM │ 4 DIAS      │

─ ABA: SINISTROS ────────────────────────────────────────────────────────────

│  Sinistro  │ Data       │ Tipo    │ Seguradora │ Valor    │ Status       │
│─────────────────────────────────────────────────────────────────────────│
│  #2338     │ 25/02/2026 │ Vidro   │ Allianz    │ R$ 850   │ Em andamento │
│  #1892     │ 08/10/2025 │ Guincho │ Allianz    │ R$ 320   │ Encerrado    │

─ ABA: CONVERSAS ────────────────────────────────────────────────────────────

│  Data       │ Assunto                     │ Agente      │ Duração  │
│─────────────────────────────────────────────────────────────────────────│
│  25/02/2026 │ Acionamento sinistro vidro  │ Sinistros   │ 23 msgs  │
│  15/01/2026 │ Dúvida sobre cobertura      │ Orquestrador│ 5 msgs   │
│  08/10/2025 │ Acionamento assistência     │ Sinistros   │ 18 msgs  │
│  20/08/2025 │ Renovação apólice auto      │ Orquestrador│ 12 msgs  │

─ ABA: MEMÓRIA DO AGENTE [V1+] ─────────────────────────────────────────────

  (MVP: aba visível mas com mensagem "Disponível a partir da V1 — Grafo de
  memória por cliente com histórico longitudinal completo")
```

---

### 3.6 Relatórios

**Objetivo:** visão analítica da operação para tomada de decisão do gestor.

**Sub-telas disponíveis por versão:**

| Relatório | Versão | Descrição |
|---|---|---|
| Comissões mensais | MVP | Receita por seguradora, evolução mensal, comparativo |
| Performance dos agentes | MVP | Taxa de automação, CSAT, tempo de resposta, escaladas |
| Saúde da carteira | V2 | Churn scores, oportunidades, clientes em risco |
| Ranking de seguradoras | V2 | SLA real, taxa de contestação, prazo médio por seguradora |
| Benchmarking | V3 | Comparativo da corretora com pares do mercado |

#### 3.6.1 Relatório de Comissões Mensais (MVP)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  COMISSÕES — fevereiro/2026              [Exportar PDF] [Exportar XLS]   │
│  Total do mês: R$ 52.340  |  Meta: R$ 55.000  |  Atingimento: 95,2%    │
└──────────────────────────────────────────────────────────────────────────┘

  Evolução mensal (últimos 6 meses):
  ┌─────────────────────────────────────────────────────────────────────┐
  │  55k │                                              ┌──┐            │
  │  50k │         ┌──┐                       ┌──┐     │  │  ┌──┐     │
  │  45k │  ┌──┐   │  │  ┌──┐       ┌──┐     │  │     │  │  │  │     │
  │  40k │  │  │   │  │  │  │       │  │     │  │     │  │  │  │     │
  │      └──┴──┴───┴──┴──┴──┴───────┴──┴─────┴──┴─────┴──┴──┴──┴──── │
  │      ago/25  set/25  out/25  nov/25  dez/25  jan/26  fev/26        │
  └─────────────────────────────────────────────────────────────────────┘

  Por seguradora:
  Bradesco Seguros  R$ 18.200  ██████████████████░░░  35%
  Allianz           R$ 14.800  ██████████████░░░░░░░  28%
  HDI               R$ 11.400  ███████████░░░░░░░░░░  22%
  Porto Seguro      R$  7.940  ███████░░░░░░░░░░░░░░  15%
```

#### 3.6.2 Performance dos Agentes (MVP)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  PERFORMANCE DOS AGENTES — fevereiro/2026                                │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┐  ┌────────────────────────────────────┐
│  AGENTE DE SINISTROS             │  │  AGENTE DE COMISSIONAMENTO         │
│                                  │  │                                    │
│  Atendimentos: 34                │  │  Ciclos executados: 20             │
│  Resolvidos automaticamente: 28  │  │  Taxa de sucesso: 95% (19/20)      │
│  Taxa de automação: 82%          │  │  Portais com falha: 1              │
│  Escalados para humano: 6        │  │  Comissões capturadas: 100%        │
│  Tempo méd. 1ª resposta: 0:48s   │  │  Divergências detectadas: 1        │
│  CSAT médio: 4.6/5.0             │  │  NFS-e emitidas: 38/40             │
└──────────────────────────────────┘  └────────────────────────────────────┘
```

---

### 3.7 Agentes — Status e Controle

**Objetivo:** visibilidade técnica do estado dos agentes e controle de autonomia.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  AGENTES                                                                 │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  🤖 AGENTE DE COMISSIONAMENTO                               [Executar]   │
│                                                                          │
│  Status: ✅ OCIOSO                                                       │
│  Última execução: hoje às 08:12 (4 min 32s)                             │
│  Próxima execução: amanhã às 08:00                                       │
│                                                                          │
│  Configuração:                                                           │
│  • Horário: 08:00 BRT todos os dias                                      │
│  • Portais configurados: 4 (Bradesco, Allianz, HDI, Porto Seguro)       │
│  • Limite de NFS-e sem aprovação: R$ 0 (sempre pede aprovação)          │
│  • Alertar corretor se divergência > 5%: ✅ ativo                       │
│                                                                          │
│  [Configurar]  [Ver histórico de execuções]  [Desativar temporariamente]│
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  🤖 AGENTE DE SINISTROS                                  [Testar]        │
│                                                                          │
│  Status: ✅ AGUARDANDO (pronto para atender)                             │
│  Conversas ativas: 3                                                     │
│  Última mensagem processada: há 12 minutos                              │
│                                                                          │
│  Configuração:                                                           │
│  • Canal: WhatsApp (Z-API)                                               │
│  • Severidades que escalam automaticamente: Colisão, Furto, Acidente    │
│  • Severidades resolvidas automaticamente: Assistência, Vidro, Guincho  │
│  • Tempo máximo sem resposta antes de alertar: 2 horas                  │
│                                                                          │
│  [Configurar]  [Ver conversas ativas]  [Desativar temporariamente]      │
└──────────────────────────────────────────────────────────────────────────┘
```

---

### 3.8 Configurações

**Objetivo:** centralizar todas as configurações operacionais da plataforma.

**Sub-seções:**

#### 3.8.1 Integrações — Portais das Seguradoras

```
┌──────────────────────────────────────────────────────────────────────────┐
│  PORTAIS DAS SEGURADORAS                              [+ Adicionar portal]│
└──────────────────────────────────────────────────────────────────────────┘

│  Seguradora     │ Tipo acesso │ Status      │ Último acesso  │ Ações      │
│─────────────────────────────────────────────────────────────────────────│
│  Bradesco       │ API REST    │ ✅ Ativo    │ hoje 08:12     │ [Editar]   │
│  Allianz        │ RPA (Playwright)│ ✅ Ativo │ hoje 08:09    │ [Editar]   │
│  HDI            │ RPA         │ ✅ Ativo    │ hoje 08:06     │ [Editar]   │
│  Porto Seguro   │ RPA + 2FA   │ ⚠ 2FA expirou│ ontem 08:10 │ [Reconfigurar]│

Ao clicar em [Editar] de uma seguradora RPA:
┌──────────────────────────────────────────────────────────────────────────┐
│  CONFIGURAR PORTAL — Allianz                                             │
│                                                                          │
│  Tipo de acesso: RPA (Playwright)                                        │
│  URL do portal: [https://portal.allianz.com.br/corretor]                │
│  Login: [usuario@corretora.com.br]                                      │
│  Senha: [••••••••••••]  [Mostrar]                                        │
│  2FA: Nenhum  ○  TOTP (app)  ●  E-mail  ○  SMS                         │
│  E-mail 2FA: [financeiro@corretora.com.br]                              │
│                                                                          │
│  [Testar conexão]                         [Cancelar]  [Salvar]          │
└──────────────────────────────────────────────────────────────────────────┘
```

#### 3.8.2 Configurações do WhatsApp

```
┌──────────────────────────────────────────────────────────────────────────┐
│  WHATSAPP (Z-API)                                                        │
│                                                                          │
│  Status: ✅ Conectado — +55 11 9xxxx-xxxx                               │
│  Instance ID: [abc123xyz]                                               │
│  Token: [••••••••••••••••]  [Mostrar]                                   │
│                                                                          │
│  Templates aprovados pela Meta:                                          │
│  • sinistro_abertura ✅  |  sinistro_update ✅  |  comissao_resumo ✅   │
│  • renovacao_aviso ⏳ Em análise                                         │
│                                                                          │
│  [Atualizar credenciais]  [Ver templates]  [Testar envio]               │
└──────────────────────────────────────────────────────────────────────────┘
```

#### 3.8.3 Configurações de NFS-e

```
┌──────────────────────────────────────────────────────────────────────────┐
│  NFS-e — FOCUS NFe API                                                   │
│                                                                          │
│  Status: ✅ Conectado                                                    │
│  CNPJ da corretora: [xx.xxx.xxx/0001-xx]                                │
│  Município: São Paulo — SP                                               │
│  Código do serviço: 10.05 (Intermediação de seguros)                    │
│  Alíquota ISS: 5%                                                        │
│  Série NFS-e: 1                                                          │
│                                                                          │
│  Emissão automática: ○ Sempre  ● Sempre com aprovação  ○ Nunca          │
│                                                                          │
│  [Testar emissão (sandbox)]  [Atualizar configurações]                  │
└──────────────────────────────────────────────────────────────────────────┘
```

#### 3.8.4 Equipe e Permissões

```
┌──────────────────────────────────────────────────────────────────────────┐
│  EQUIPE                                                       [+ Convidar]│
│                                                                          │
│  Nome            │ E-mail                   │ Perfil       │ Status     │
│─────────────────────────────────────────────────────────────────────────│
│  João Silva      │ joao@corretora.com.br    │ Administrador│ ✅ Ativo   │
│  Carla Mendes    │ carla@corretora.com.br   │ Corretor     │ ✅ Ativo   │
│  Paulo Rocha     │ paulo@corretora.com.br   │ Visualizador │ ✅ Ativo   │

  Perfis de acesso:
  • Administrador: acesso total, incluindo configurações e credenciais
  • Corretor: aprova ações, atende clientes, vê relatórios — sem configurações
  • Visualizador: somente leitura — sem aprovar ações ou acessar credenciais
```

---

### 3.9 Auditoria e Logs

**Objetivo:** rastreabilidade completa de todas as ações executadas pelos agentes. Também é a base para o compliance SUSEP (V1+).

```
┌──────────────────────────────────────────────────────────────────────────┐
│  AUDITORIA — LOG DE AÇÕES DOS AGENTES             [Exportar] [Filtros ▼]│
│  Período: últimos 7 dias  |  1.247 eventos registrados                  │
└──────────────────────────────────────────────────────────────────────────┘

│  Data/Hora       │ Agente          │ Ação               │ Cliente  │ Status│
│──────────────────────────────────────────────────────────────────────────│
│ 27/02 08:12:41  │ Comissionamento │ emit_nfse           │ —        │ ✅ OK │
│ 27/02 08:12:38  │ Comissionamento │ consolidate_report  │ —        │ ✅ OK │
│ 27/02 08:09:10  │ Comissionamento │ fetch_commission    │ Allianz  │ ✅ OK │
│ 27/02 08:08:03  │ Comissionamento │ handle_2fa          │ Porto Seg│ ❌ Fail│
│ 27/02 07:55:00  │ Comissionamento │ iniciar_ciclo       │ —        │ ✅ OK │
│ 26/02 23:41:22  │ Sinistros       │ relay_update_client │ Carlos L.│ ✅ OK │

Ao clicar em uma linha:
┌──────────────────────────────────────────────────────────────────────────┐
│  DETALHE DO EVENTO — 27/02 08:08:03                                      │
│                                                                          │
│  Agente: Comissionamento                                                 │
│  Ação: handle_2fa                                                        │
│  Portal: Porto Seguro                                                    │
│  Método 2FA tentado: E-mail (financeiro@corretora.com.br)               │
│  Resultado: FALHOU — timeout aguardando código por e-mail (120s)        │
│  Próximo passo: agente alertou gestor via Dashboard                     │
│                                                                          │
│  Input da ferramenta: {"portal": "porto_seguro", "method": "email"}     │
│  Output da ferramenta: {"success": false, "reason": "timeout"}         │
│                                                                          │
│  [Ver log completo do LangSmith]                                         │
└──────────────────────────────────────────────────────────────────────────┘
```

**Compliance SUSEP (V1+):**

Na V1 esta tela ganha um modo de exportação específico para auditoria SUSEP:
- Exportação de todas as conversas com clientes dos últimos 5 anos
- Registro de suitability (qual produto foi recomendado, para qual perfil, com qual justificativa)
- Relatório de atividades dos agentes no formato exigido pela regulação

---

## 4. Fluxos de Navegação

### 4.1 Fluxo: Gestor chega pela manhã

```
Home (Dashboard)
    │
    ├── Vê badge: "3 aprovações pendentes"
    │       └── Clica em [Ver fila →]
    │               └── Aprovações
    │                       ├── Revisa NFS-e Bradesco → Aprova
    │                       ├── Revisa escalada sinistro #2341 → Aprova escalada
    │                       └── Revisa relatório mensal → Aprova envio
    │
    ├── Vê alerta: "Porto Seguro — 2FA expirou"
    │       └── Clica no alerta
    │               └── Configurações > Portais > Porto Seguro
    │                       └── Reconfigurar credencial de 2FA → Testar → Salvar
    │
    └── Vê sinistro #2341 escalado na tabela
            └── Clica no sinistro
                    └── Detalhe do Sinistro #2341
                            └── Lê conversa → Clica [Assumir atendimento]
```

### 4.2 Fluxo: Novo sinistro grave chega (notificação)

```
[Notificação push/badge aparece na barra superior]
    │
    └── Clica na notificação
            └── Aprovações (item novo no topo)
                    │
                    └── Lê resumo do sinistro grave
                            ├── Aprova escalada → agente notifica cliente que corretor assumiu
                            └── Clica [Assumir conversa] → interface de chat com cliente
```

### 4.3 Fluxo: Investigar divergência de comissão

```
Home
    │
    └── Comissionamento
            │
            └── Aba: Divergências
                    │
                    └── Vê divergência Porto Seguro (R$ 320 a menos)
                            │
                            ├── Clica [Ver apólices envolvidas]
                            │       └── Ficha das apólices #PS-2024-77340 e #PS-2024-81200
                            │
                            └── Clica [Abrir contestação]
                                    └── Agente gera draft de e-mail para Porto Seguro
                                            └── Gestor revisa e aprova envio
```

### 4.4 Fluxo: Verificar saúde de um cliente específico

```
Carteira de Clientes
    │
    └── Busca por "Carlos Lima"
            │
            └── Ficha do Cliente — Carlos Lima
                    │
                    ├── Aba Apólices: vê que apólice vence em 4 dias
                    │
                    └── Aba Sinistros: vê sinistro #2338 em andamento
                            │
                            └── Clica no sinistro → Detalhe #2338
                                    └── Vê que está aguardando seguradora há 3 dias
                                            └── Clica [Contatar seguradora]
```

---

## 5. Notificações e Alertas

### 5.1 Canais de notificação

| Canal | Quando usar | Exemplo |
|---|---|---|
| **Badge na sidebar** | Contagem de itens pendentes — sempre visível | "3" no ícone de Aprovações |
| **Banner no Dashboard** | Problemas operacionais que precisam de ação hoje | "Porto Seguro — 2FA expirou" |
| **Sino (top bar)** | Histórico dos últimos eventos relevantes | Log das últimas 24h |
| **WhatsApp** | Alertas críticos fora do horário de uso da plataforma | "Sinistro crítico #2341 escalado — colisão" |
| **E-mail** | Relatórios periódicos | Resumo mensal de comissões |

### 5.2 Tipos de alerta por criticidade

| Nível | Cor | Exemplos | Ação esperada |
|---|---|---|---|
| Crítico | 🔴 Vermelho | Sinistro grave escalado, portal com falha, cliente em risco de cancelamento | Ação imediata |
| Atenção | 🟡 Amarelo | NFS-e aguardando aprovação, renovação em 7 dias, divergência de comissão | Ação no dia |
| Informativo | 🟢 Verde | Ciclo de comissionamento concluído, sinistro resolvido, cliente onboardado | Apenas conhecimento |

---

## 6. Telas por Versão — Mapa de Evolução

### MVP (Mês 3)

Telas disponíveis e completas:
- ✅ Home / Dashboard
- ✅ Aprovações
- ✅ Comissionamento (Resumo, Por Seguradora, NFS-e, Divergências)
- ✅ Sinistros (Fila, Escalados, Histórico, Detalhe)
- ✅ Carteira de Clientes (Lista, Ficha básica)
- ✅ Relatórios (Comissões mensais, Performance dos agentes)
- ✅ Agentes (Status, Configuração de autonomia)
- ✅ Configurações (Portais, WhatsApp, NFS-e, Equipe)
- ✅ Auditoria (Log de ações)

### V1 — Memória Real (Mês 6)

Adições e expansões:
- 🆕 Ficha do Cliente — Aba "Memória do Agente" (grafo de conhecimento por cliente)
- 🆕 Ficha do Cliente — Aba "Histórico de Negociação" (o que foi prometido, aceito, recusado)
- 🆕 Seção "Relacionamento Proativo" — agenda de mensagens automáticas previstas
- 🆕 Auditoria — Exportação SUSEP (retenção 5 anos, suitability)
- 🔄 Aprovações — novo tipo: "Mensagem proativa gerada pelo agente" (para revisar antes de enviar)

### V2 — Inteligência de Carteira (Mês 12)

Adições e expansões:
- 🆕 Carteira de Clientes — campo "Score de Saúde" com churn score, potencial de expansão e NPS implícito
- 🆕 Relatórios — "Saúde da Carteira" (clientes em risco, oportunidades de cross-sell)
- 🆕 Relatórios — "Ranking de Seguradoras" (SLA real, contestação, prazo médio)
- 🆕 Home — widget "Oportunidades detectadas esta semana"
- 🆕 Home — widget "Clientes em risco de churn"

### V3 — Estratégia (Ano 2)

Adições e expansões:
- 🆕 Sinistros — seção "Advocacia Inteligente" (detecta subpagamentos, gera documentação de recurso)
- 🆕 Relatórios — "Benchmarking" (comparativo com corretoras similares)
- 🆕 Carteira — "Detecção de risco" (padrões anômalos, possíveis fraudes)
- 🆕 Relatórios — "Precificação de risco" (quem merece desconto, quem está perto de cancelar)

### V4 — Plataforma (Ano 2-3)

Adições e expansões:
- 🆕 Seção "Inteligência de Mercado" (dados agregados e anonimizados da rede de corretoras)
- 🆕 Seção "Prospecção" (agente de prospecção autônomo — prospects similares à carteira atual)
- 🆕 API Dashboard — visibilidade sobre consumo da BrokerAI Intelligence API

---

## 7. Decisões de Design a Definir

| # | Decisão | Opções | Impacto |
|---|---|---|---|
| DD-01 | Framework front-end | Next.js (React) vs. Rails + Turbo/Hotwire | Velocidade de dev vs. stack unificada |
| DD-02 | Componentes de UI | Shadcn/ui vs. Tailwind puro vs. biblioteca pronta | Customização vs. velocidade |
| DD-03 | Real-time de status dos agentes | WebSocket vs. Server-Sent Events vs. polling | Complexidade vs. UX |
| DD-04 | Mobile responsivo vs. app nativo | Web responsivo vs. PWA vs. React Native | Escopo e custo |
| DD-05 | Chat inline com cliente | Embutido no detalhe do sinistro vs. tela separada | UX de gestão multi-conversa |
| DD-06 | Autenticação | Email/senha vs. SSO (Google, Microsoft) | Facilidade de onboarding |

---

## 8. Referências

- `docs/produto/casos-de-uso.md` — base dos 19 use cases que esta plataforma expõe
- `docs/produto/roadmap.md` — versões e features planejadas
- `docs/architecture.md` — arquitetura técnica que suporta a plataforma
- `CLAUDE.md` — stack, padrões e regras de implementação
- ADR-008 (a definir) — decisão de arquitetura: web app separado vs. embutido na API

---

*Documento criado em fevereiro/2026. Deve ser revisado antes de iniciar o desenvolvimento do front-end.*

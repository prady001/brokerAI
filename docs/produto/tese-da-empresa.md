# Tese da Empresa — BrokerAI

> **Versão:** 1.0
> **Data:** Fevereiro de 2026

---

## O Problema

O Brasil tem **65.000 corretoras de seguros** registradas na SUSEP. A esmagadora maioria — especialmente as 16.000 corretoras de pequeno porte com 3 a 10 funcionários — opera de forma 100% manual nos processos que mais consomem tempo e que menos exigem julgamento humano.

Todo dia, em cada uma dessas corretoras, alguém:

- Abre N abas de portais de seguradoras, digita login e senha em cada uma, resolve código de verificação, exporta planilha, cola num Google Sheets, emite nota fiscal manualmente
- Fica no meio da conversa de WhatsApp entre cliente e seguradora, copiando e colando mensagens de um lado para o outro, tentando lembrar onde parou no caso do cliente anterior

Enquanto isso, os clientes esperam. As comissões ficam para trás. E o corretor, que deveria estar construindo relacionamentos e negociando, está fazendo trabalho de escriturário.

---

## O Insight

Em 2026, **80% das seguradoras brasileiras já usam IA** — mas quase nenhuma corretora de pequeno porte usa. A tecnologia chegou nas grandes, não chegou em quem mais precisa.

O problema não é falta de produto. É que os produtos existentes (Agger, Segfy, Quiver) são sistemas de gestão — fazem o que um arquivo Excel faria, só que com interface mais bonita. Eles armazenam dados. Não agem. Não pensam. Não lembram.

A pesquisa acadêmica mais recente em sistemas de IA (Yang et al., 2026 — *Graph-based Agent Memory*) revela que a próxima fronteira dos agentes de IA não é a capacidade de raciocinar, mas a capacidade de **lembrar e acumular conhecimento ao longo do tempo**. Um agente com memória em grafo temporal não começa cada conversa do zero — ele conhece o cliente há anos, conecta eventos, detecta padrões e age antes de ser acionado.

Essa tecnologia, aplicada ao contexto da corretora de seguros, cria algo que não existe hoje: um agente que conhece cada cliente da carteira tão bem quanto um corretor experiente conhece seus 50 melhores clientes — mas aplicado a todos os 1.000.

---

## A Solução

O BrokerAI é uma plataforma de agentes de IA com **memória relacional acumulativa** projetada exclusivamente para corretoras de seguros brasileiras.

Diferente de um chatbot ou de um sistema de gestão, o BrokerAI:

1. **Age** — executa tarefas completas de ponta a ponta, sem precisar ser instruído a cada passo
2. **Lembra** — constrói um grafo de conhecimento de cada cliente que cresce a cada interação
3. **Antecipa** — detecta padrões e age antes que o problema apareça
4. **Aprende** — evolui com cada negociação, cada sinistro, cada renovação

### O que o agente faz hoje que o corretor faz manualmente

| Processo | Como era | Como fica |
|---|---|---|
| Comissionamento diário | Acessar N portais, consolidar em planilha, emitir NF | Relatório automático no WhatsApp às 08h + NFS-e emitida |
| Sinistro simples | Copia-e-cola entre cliente e seguradora no WhatsApp | Agente coleta, abre, acompanha e encerra sem intervenção |
| Acompanhamento de sinistro | Cliente liga perguntando o status | Agente proativamente informa a cada atualização |
| Renovação | Corretor tenta lembrar de ligar 30 dias antes | Agente inicia régua 60 dias antes com argumento personalizado |
| Onboarding | 3 dias de email e ligações para coletar documentos | 15 minutos via WhatsApp com OCR automático |
| Conhecimento do cliente | O corretor lembra dos 50 que falou recentemente | Agente conhece todos os 1.000 igualmente bem |

---

## Por Que Agora

Três forças convergem em 2026 que tornam esse produto possível e urgente:

**1. Tecnologia madura**
Os LLMs de última geração (Claude Sonnet) têm desempenho excepcional em português. As técnicas de graph memory (Graphiti, LangMem) saíram da academia e estão disponíveis como bibliotecas open-source estáveis. A automação de portais via Playwright é confiável o suficiente para produção.

**2. Mercado em movimento**
As seguradoras estão investindo pesado em IA — e isso pressiona as corretoras a acompanharem. Corretoras que não modernizarem o atendimento perderão espaço para as que oferecerem experiência superior ao cliente. O mercado cresceu 12,2% em 2024 e está com apetite para tecnologia.

**3. Janela competitiva**
Nenhum sistema de gestão existente para corretoras oferece agentes autônomos com memória. O Agger (líder de mercado, 16.000 clientes) foi adquirido pela Dimensa/TOTVS por R$ 260 milhões em 2025, mas ainda opera como sistema de gestão tradicional. Há uma janela de 18-24 meses antes que players maiores se movam.

---

## Modelo de Negócio

### Proposta de Valor por Segmento

| Segmento | Dor principal | Valor entregue | ROI estimado |
|---|---|---|---|
| Solocorretor | Tempo gasto em burocracia | Libera 2-3h/dia para venda | 5-10x o valor da assinatura |
| Pequena (3-10 func.) | Operação cresce mas equipe não | Escala operação sem contratar | 3-6x o valor da assinatura |
| Média (11-50 func.) | Falta visibilidade de carteira | Inteligência de portfólio | Redução de churn de clientes |

### Precificação

| Plano | Perfil | Preço/mês | Valor anual |
|---|---|---|---|
| **Starter** | Solocorretor, até 3 portais de seguradoras | R$ 497 | R$ 5.070 |
| **Pro** ⭐ | Pequena corretora, até 10 portais | R$ 997 | R$ 10.170 |
| **Business** | Média corretora, portais ilimitados | R$ 1.997 | R$ 20.370 |
| **Enterprise** | Grande corretora / rede | a partir de R$ 3.997 | negociado |

### Unit Economics (plano Pro)

| Métrica | Valor |
|---|---|
| Margem bruta estimada | ~70% |
| Churn mensal alvo | < 2% |
| LTV estimado | ~R$ 27.900 |
| CAC estimado (inside sales) | R$ 3.000-5.000 |
| LTV:CAC | ~7:1 |
| Payback do CAC | 6-9 meses |

### Projeção de ARR

| Período | Clientes | ARR |
|---|---|---|
| Ano 1 | 100-200 | R$ 1,2M - R$ 2,4M |
| Ano 2 | 300-500 | R$ 3,6M - R$ 6M |
| Ano 3 | 500-1.000 | R$ 6M - R$ 12M |

---

## Vantagem Competitiva e Defensibilidade

### Moat 1 — Dados Proprietários
Cada mês de uso gera um grafo de conhecimento do cliente da corretora. Esse grafo é impossível de exportar ou replicar. Quanto mais tempo a corretora usa, mais difícil é migrar — não por lock-in artificial, mas porque o agente literalmente "sabe mais" sobre os clientes da corretora do que qualquer sistema novo saberia.

### Moat 2 — Integrações com Portais de Seguradoras
Construir e manter o acesso automatizado (RPA + API) a dezenas de portais de seguradoras é trabalho técnico especializado que leva meses. Uma vez construído, é difícil de replicar e exige manutenção contínua (mudanças de layout, 2FA, etc.).

### Moat 3 — Efeito de Rede (V4)
A partir do momento em que múltiplas corretoras usam a plataforma, o grafo agregado (anonimizado) cria inteligência de mercado que nenhuma corretora individual teria sozinha: benchmarks de performance de seguradoras por tipo de sinistro, padrões de risco por região, taxa de resolução por produto. Quanto mais corretoras entram, mais inteligente fica para todas.

### Moat 4 — Especialização Vertical
Sistemas horizontais de IA (chatbots genéricos, CRMs com IA) não conhecem a regulação SUSEP, o modelo de comissão por ramo, os tipos de 2FA dos portais de seguradoras, os fluxos de sinistro por seguradora. Esse conhecimento de domínio está embarcado em cada prompt, cada tool e cada regra do sistema.

---

## Mercado Total Endereçável

| Segmento | Quantidade | Ticket médio anual | TAM |
|---|---|---|---|
| Solocorretores (BR) | ~40.000 | R$ 5.000 | R$ 200M |
| Pequenas corretoras (BR) | ~16.000 | R$ 10.000 | R$ 160M |
| Médias corretoras (BR) | ~6.000 | R$ 22.000 | R$ 132M |
| **Total Brasil** | **~62.000** | — | **~R$ 492M** |

SAM inicial (pequenas corretoras): **R$ 160M/ano**

---

## Visão de Longo Prazo

O BrokerAI começa como ferramenta de automação operacional — mas a visão de longo prazo é diferente:

> **Tornar-se a plataforma de inteligência do corretor de seguros brasileiro** — o sistema que une, organiza e potencializa todo o conhecimento da carteira, tornando cada corretor capaz de operar como se tivesse uma equipe de analistas e um assistente pessoal 24/7.

Nessa visão, o BrokerAI não é mais um software de automação. É a infraestrutura de inteligência sobre a qual o corretor constrói seu negócio.

A corretora que hoje gerencia 500 apólices com 5 funcionários, com o BrokerAI, gerencia 2.000 apólices com a mesma equipe — e com experiência de cliente superior.

---

## Roadmap de Versões

Ver documento completo: [`docs/produto/roadmap.md`](./roadmap.md)

| Versão | Período | Foco |
|---|---|---|
| MVP | Mês 3 | Automação operacional (comissionamento + sinistros) |
| V1 | Mês 6 | Memória real — grafo de conhecimento por cliente |
| V2 | Mês 12 | Inteligência de carteira e personalização |
| V3 | Ano 2 | Advocacia, prevenção e precificação de risco |
| V4 | Ano 2-3 | Plataforma com efeito de rede |

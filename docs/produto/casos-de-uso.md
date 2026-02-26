# Mapa de Casos de Uso — BrokerAI

> **Última atualização:** Fevereiro de 2026
> **Contexto:** Análise de todos os casos de uso possíveis para uma solução disruptiva baseada em agentes de IA com memória em grafo para corretoras de seguros no Brasil.

---

## Fundamento Teórico

Os casos de uso abaixo são fundamentados nas técnicas de **Graph-based Agent Memory** (Yang et al., arXiv:2602.05665) e no ecossistema de projetos open-source associados (Awesome-GraphMemory). A premissa central é:

> Sistemas de IA atuais têm **amnésia crônica** — cada conversa começa do zero. Um agente com **memória em grafo temporal** conhece o cliente ao longo de anos, conectando informações que nenhum humano conectaria em escala.

### Cadeia de Valor da Corretora

```
PROSPECÇÃO → COTAÇÃO → EMISSÃO → PÓS-VENDA → SINISTROS → RENOVAÇÃO
     ↑                                                          ↓
     └──────────────── COMISSIONAMENTO / GESTÃO ←──────────────┘
```

Sistemas existentes (Agger, Segfy) cobrem apenas **cotação + gestão de apólices**. O BrokerAI cobre a cadeia **inteira** com inteligência acumulativa.

---

## Bloco 1 — Inteligência do Cliente

*Técnicas: Memory Storage (Temporal KG), Memory Retrieval (Semantic + Graph-based)*

### UC-01 — Perfil Longitudinal do Cliente

O grafo acumula ao longo de anos: apólices, sinistros, reclamações, preferências de comunicação, eventos de vida (casamento, filhos, mudança de endereço), histórico de pagamentos e sensibilidade a preço. O agente nunca "esquece" e conecta informações que nenhum humano conectaria em escala.

**Impacto:** o corretor passa a conhecer 1.000 clientes tão bem quanto conhecia 50.

**Tecnologias-chave:** Graphiti (Zep), Neo4j ou equivalente, LangMem (LangChain)

---

### UC-02 — Detecção de Eventos de Vida → Novas Oportunidades

O grafo detecta padrões que indicam mudança de vida e gera alertas de oportunidade:
- Cliente mencionou "meu filho vai tirar carta" → seguro auto novo
- Sinistro com novo endereço → revisão de seguro residencial
- Seguro de vida contratado há 10+ anos → cobertura desatualizada
- Dois sinistros de assistência em 6 meses → carro velho, oportunidade de produto novo

**Impacto:** cross-sell e upsell acontecem naturalmente, sem o corretor precisar lembrar.

---

### UC-03 — Score de Saúde do Relacionamento

O grafo calcula continuamente para cada cliente:
- **Risco de churn** — sinistros não resolvidos, tempo sem contato, reclamações, renovação próxima
- **Potencial de expansão** — quantas apólices poderia ter mas ainda não tem
- **NPS implícito** — tom das mensagens, frequência de resposta, reclamações detectadas
- **Valor de vida projetado** — LTV estimado com base no histórico

**Impacto:** o corretor foca energia nos clientes certos, no momento certo.

---

## Bloco 2 — Automação de Relacionamento

*Técnicas: Memory Evolution (Reflexion, Mem-α), Personalization (PersonaMem, PrefEval)*

### UC-04 — Agente de Relacionamento Proativo

O agente não espera o cliente falar — inicia conversas no momento certo:
- 60 dias antes do vencimento: *"João, sua apólice vence em agosto. Já pesquisei 3 opções."*
- Aniversário do cliente: mensagem personalizada automática
- Pós-sinistro resolvido: *"Seu sinistro foi encerrado. Tudo certo com o carro?"*
- 1 ano sem sinistro: *"Você completou 1 ano sem acionar — isso pode te dar desconto na renovação."*
- Evento climático na cidade: *"Vi que choveu forte aí. Seu seguro residencial cobre alagamento."*

**Impacto:** o corretor mantém relacionamento ativo com toda a carteira sem esforço manual.

---

### UC-05 — Adaptação ao Perfil Emocional do Cliente

Inspirado na pesquisa da CNseg (2026) + papers de personalização. O grafo aprende:
- Esse cliente prefere mensagens curtas e diretas
- Esse cliente gosta de explicações detalhadas
- Esse cliente fica ansioso em sinistros (precisa de updates frequentes)
- Esse cliente só lê mensagens à noite

O agente adapta tom, tamanho, hora de envio e estilo automaticamente.

**Impacto:** taxa de resposta e satisfação aumentam sem o corretor mudar nada.

---

### UC-06 — Memória de Negociação

O grafo registra tudo que foi prometido, oferecido e recusado:
- *"Oferecemos 10% de desconto no ano passado. Ele não aceitou por causa da franquia alta."*
- *"Ela quase cancelou em março. O que resolveu foi incluir assistência 24h."*
- *"Esse cliente é sensível a preço mas valoriza cobertura ampla."*

Na próxima renovação, o agente usa exatamente o argumento que funcionou.

**Impacto:** taxa de renovação sobe porque cada abordagem é individualizada.

---

## Bloco 3 — Sinistros com Inteligência

*Técnicas: Multi-session Memory, Temporal Graph (Zep/TReMu), Agent-based Retrieval*

### UC-07 — Acompanhamento Autônomo de Sinistros

O agente não depende do cliente ligar para saber o que está acontecendo:
- Monitora status no portal da seguradora automaticamente (RPA)
- Informa o cliente proativamente a cada atualização
- Detecta quando prazo SLA da seguradora está sendo descumprido
- Escala para o corretor quando há risco de não pagamento

**Impacto:** o cliente não precisa ligar para saber o status — o agente corre atrás por ele.

---

### UC-08 — Advogado do Cliente no Sinistro

O agente não apenas relay informação — ele advoga ativamente:
- Detecta quando a seguradora tenta pagar menos do que o devido
- Compara o valor ofertado com casos similares na carteira histórica
- Sugere ao corretor quando vale contestar e com quais argumentos
- Gera automaticamente a documentação necessária para recurso

**Impacto:** transforma o corretor de intermediário passivo em defensor ativo do cliente.

---

### UC-09 — Prevenção de Sinistros

O grafo identifica padrões preditivos e envia alertas preventivos:
- *"Clientes nessa região tiveram 3x mais sinistros de enchente este mês"*
- *"Esse modelo de carro tem alta taxa de furto na sua carteira"*
- Alerta ao cliente: *"Sua região tem alerta de chuva forte. Evite estacionar em áreas de risco."*

**Impacto:** reduz sinistros → reduz custo para seguradora → corretor negocia melhores condições.

---

### UC-18 — Sinistro End-to-End Sem Intervenção Humana

Para sinistros simples (vidro, assistência, furto de acessório):
1. Recebe acionamento via WhatsApp
2. Coleta fotos e documentos
3. Abre sinistro no portal da seguradora (RPA)
4. Monitora até resolução
5. Confirma pagamento ou prestação do serviço
6. Fecha o loop com o cliente

Zero intervenção humana. Sinistros complexos → escalona.

**Impacto:** 80% dos sinistros tornam-se automáticos, liberando o corretor para alta complexidade.

---

## Bloco 4 — Inteligência de Portfólio

*Técnicas: Collaborative Memory, Multi-agent Systems, Cross-client Pattern Recognition*

### UC-10 — Inteligência Comparativa de Seguradoras

O grafo coletivo da carteira revela padrões invisíveis:
- *"Porto Seguro resolve sinistros de colisão em 12 dias. Bradesco leva 28."*
- *"Allianz tem a menor taxa de contestação de sinistros na sua carteira."*
- *"Essa seguradora aumentou prêmio 15% nesta região nos últimos 6 meses."*

**Impacto:** o corretor toma decisões de recomendação baseadas em evidência real, não em relacionamento comercial.

---

### UC-11 — Detecção de Padrões de Risco

O grafo detecta padrões anômalos na carteira:
- Cliente com múltiplos sinistros similares em curto período
- Padrão de sinistro que coincide com datas específicas (suspeita de fraude)
- Endereço que aparece em sinistros de múltiplos clientes diferentes

**Impacto:** protege a corretora de clientes de alto risco e melhora sua reputação com seguradoras.

---

### UC-12 — Benchmarking de Carteira

A corretora compara sua carteira com benchmarks agregados do mercado:
- *"Sua taxa de renovação é 72%. A média de corretoras similares é 81%."*
- *"Seu ticket médio de apólice auto é 8% abaixo do mercado."*
- *"Você tem concentração alta em seguro auto (78%). Corretoras similares diversificam mais."*

**Impacto:** a corretora descobre onde está perdendo dinheiro que não sabia que existia.

---

## Bloco 5 — Operação e Compliance

*Técnicas: Memory Extraction, Hierarchical Memory, Audit Trail*

### UC-13 — Comissionamento com Auditoria Inteligente

Além de automatizar o acesso aos portais, o grafo:
- Compara histórico de comissões por seguradora ao longo do tempo
- Detecta quando uma seguradora paga menos do que o contrato prevê
- Identifica apólices que deveriam gerar comissão mas não geraram
- Gera relatório de *"comissões que você deveria ter recebido e não recebeu"*

**Impacto:** corretoras recuperam dinheiro que perdiam sem saber.

---

### UC-14 — Compliance SUSEP Automático

O grafo mantém trilha de auditoria completa:
- Todas as conversas retidas por 5 anos (exigência SUSEP)
- Logs de quais recomendações foram feitas e por quê
- Documentação automática de suitability (adequação do produto ao perfil do cliente)
- Alertas de documentos vencendo (renovação de habilitação, CRLV, etc.)

**Impacto:** elimina risco de multa SUSEP e prepara a corretora para fiscalização.

---

### UC-15 — Onboarding Inteligente de Novos Clientes

O agente conduz todo o onboarding via WhatsApp:
- Coleta documentos via foto no WhatsApp
- Extrai dados via OCR (Mistral/Textract)
- Preenche proposta automaticamente
- Explica coberturas de forma personalizada ao perfil do cliente
- Cria o nó inicial no grafo com tudo que sabe sobre o cliente

**Impacto:** o que levava 3 dias de email e ligação passa a ser feito em 15 minutos.

---

## Bloco 6 — Casos de Uso Disruptivos

*Estes mudam a estrutura do negócio, não apenas automatizam tarefas existentes.*

### UC-16 — Efeito de Rede (Network Effects)

Se múltiplas corretoras usam o sistema, o grafo coletivo cria efeito de rede:
- A corretora pequena tem acesso à inteligência de mercado que antes só a grande tinha
- Padrões de sinistro por região, seguradora e produto emergem do dado agregado anonimizado
- Quanto mais corretoras usam, mais inteligente fica para todas

**Disrupção:** transforma o produto de ferramenta para plataforma — com defensibilidade crescente.

---

### UC-17 — Agente de Prospecção Autônomo

Usa dados públicos (CNPJ, LinkedIn, eventos empresariais) + grafo de clientes existentes:
- *"Seus melhores clientes são empresas de 10-50 funcionários no varejo. Encontrei 340 similares em SP."*
- O agente qualifica, aborda e agenda apresentação — o corretor entra apenas para fechar

**Disrupção:** a corretora deixa de depender de indicação e ganha motor de crescimento autônomo.

---

### UC-19 — Precificação Dinâmica de Risco

Com o grafo histórico da carteira:
- Identifica clientes com perfil de risco que pode conseguir desconto com a seguradora
- Detecta clientes pagando mais do que deveriam (oportunidade de fidelização via renegociação)
- Sugere o preço ótimo de renovação para maximizar retenção sem reduzir margem

**Disrupção:** o corretor passa a ter capacidade analítica de uma grande corretora com 5 analistas.

---

## Transformação do Modelo Operacional

| Hoje (corretor faz manualmente) | Com BrokerAI (agente faz) |
|---|---|
| Lembrar de ligar para renovar | Agente proativo 60 dias antes |
| Acompanhar sinistro por telefone | Monitoramento automático 24/7 |
| Perceber que comissão não veio | Auditoria automática diária |
| Conhecer os 50 clientes principais | Conhecer todos os 1.000 igualmente bem |
| Decidir qual seguradora indicar | Decisão baseada em dados da própria carteira |
| Onboarding manual via email | Onboarding via WhatsApp em 15 minutos |

> **O corretor deixa de ser operacional e passa a ser estratégico.**

---

## Referências

- Yang et al. (2026). *Graph-based Agent Memory: Taxonomy, Techniques, and Applications*. arXiv:2602.05665
- Awesome-GraphMemory: github.com/DEEP-PolyU/Awesome-GraphMemory
- CNseg (2026). *Levantamento de uso de IA em 26 seguradoras brasileiras*. Infomoney, 24/02/2026
- Graphiti (Zep): github.com/getzep/graphiti
- LangMem (LangChain): langchain-ai.github.io/langmem

# Reunião com Cliente — Março 2026

> **Data:** Março de 2026
> **Objetivo:** Validar o que foi construído, coletar decisões pendentes e desbloquear os próximos milestones

---

## 1. O que já está pronto

### M1 — Fundação ✅
- Infraestrutura Docker (API + PostgreSQL + Redis) configurada e funcionando
- Banco de dados criado: clientes, apólices, sinistros, conversas, renovações
- Webhook do WhatsApp configurado (aguardando número real)
- CI/CD rodando (testes automáticos a cada commit)
- CRUD de cadastro manual de clientes e apólices (`/admin/clients`, `/admin/policies`)

### M4 — Agente de Renovação ✅
- Régua de renovação automática em 4 momentos: **30, 15, 7 e 0 dias antes do vencimento**
- CRON diário às 08:00 — identifica apólices vencendo e dispara contato
- O agente coleta a intenção do cliente (quer renovar / não quer / quer cotação)
- Notifica o vendedor responsável com resumo estruturado
- 22 testes unitários passando

---

## 2. Demonstração — Fluxo do Agente de Renovação

### Como funciona na prática

```
08:00 BRT
    ↓
Sistema verifica apólices vencendo em 30, 15, 7 ou 0 dias
    ↓
Para cada apólice elegível, envia mensagem ao cliente via WhatsApp
    ↓
Cliente responde (quer renovar / não quer / quer cotação)
    ↓
Agente registra a intenção e notifica o vendedor com resumo
    ↓
Vendedor entra em contato para finalizar
```

### Mensagens que o cliente recebe (precisam de aprovação da Meta)

---

**30 dias antes do vencimento:**

> Olá, **[Nome]**! Aqui é da **[Nome da Corretora]**.
> Seu seguro do **[carro/casa/etc.]** vence em **30 dias** (**[data]**).
> Quer renovar? É só responder aqui que cuidamos de tudo pra você.

---

**15 ou 7 dias antes:**

> **[Nome]**, o seguro do **[carro/casa/etc.]** vence em **[15/7] dias**.
> Posso já verificar as condições de renovação pra você?

---

**No dia do vencimento:**

> **[Nome]**, hoje é o último dia de cobertura do seu seguro **[tipo de seguro]**.
> Para não ficar sem proteção, me avisa agora e a gente resolve rapidinho.

---

### O que o vendedor recebe (mensagens internas — sem aprovação Meta)

**Quando o cliente confirma renovação:**
```
✅ RENOVAÇÃO CONFIRMADA
Cliente: João Silva
Seguro: Honda Civic 2022 | #AP-00123 | Porto Seguro
Vigência: 15/04/2026
Cliente quer renovar. Aguardando sua ação.
```

**Quando o cliente recusa:**
```
❌ PERDA DE RENOVAÇÃO
Cliente: João Silva
Seguro: Honda Civic 2022 | #AP-00123 | Porto Seguro
Motivo: [motivo informado pelo cliente]
Ação recomendada: oferecer cotação em outra seguradora.
```

**Quando o cliente quer cotação em outra seguradora:**
```
🔄 CLIENTE QUER COTAÇÃO EM OUTRA SEGURADORA
Cliente: João Silva
Seguro: Honda Civic 2022 | #AP-00123 | Porto Seguro
Vigência: 15/04/2026
Oportunidade: cliente aberto a propostas. Entre em contato.
```

**Quando não há resposta:**
```
⚠️ SEM RESPOSTA — INTERVENÇÃO NECESSÁRIA
Cliente: João Silva
Seguro: Honda Civic 2022 | #AP-00123 | Porto Seguro
Vigência: 15/04/2026
3 tentativas de contato sem resposta.
Entre em contato diretamente para evitar perda.
```

---

## 3. Decisões que precisam sair desta reunião

### 🔴 Críticas — sem essas não colocamos nada em produção

| # | Decisão | Detalhe |
|---|---|---|
| **D-06** | **Aprovação dos 3 templates WhatsApp (acima)** | Precisam ser submetidos à Meta hoje — processo demora 3–10 dias úteis |
| **WA-01** | **Número WhatsApp Business da corretora** | Usar o número atual ou criar um dedicado para o atendimento automático? |
| **D-05** | **Cidade do CNPJ da corretora** | Para configurar emissão de NFS-e (Focus NFe) |

### 🟡 Importantes — desbloqueiam M2 (Sinistros)

| # | Decisão | Detalhe |
|---|---|---|
| **AG-01** | **Exportação do Agger** | CSV com carteira de apólices ativas. Campos necessários: nome do cliente, telefone, apólice, seguradora, vigência |
| **CR-01** | **Credenciais de 2 portais de seguradora** | Para testes de integração. Sugestão: Allianz e Azul (mais simples, sem 2FA) |
| **D-07** | **Gateway SMS para 2FA** | Porto Seguro e Tokio Marine precisam de verificação no login. Opções: Twilio, Zenvia |

### 🟢 Confirmar decisões já tomadas

| # | Decisão | Status |
|---|---|---|
| **D-01** | WhatsApp via Evolution API (open source, self-hosted) | ✅ Decidido |
| **D-02** | Infraestrutura Oracle Cloud Free Tier | ✅ Decidido |
| **D-04** | Seguradoras MVP: Porto Seguro, Allianz, Azul Seguros, Tokio Marine | ✅ Decidido — confirmar |
| **D-08** | Storage de fotos de sinistros: Cloudflare R2 (10GB gratuitos) | ✅ Decidido |

---

## 4. Perguntas sobre sinistros (M2 — próximo a implementar)

1. Hoje, quando um cliente abre um sinistro, como ele entra em contato? Por WhatsApp? Por telefone?
2. Quem acompanha o andamento no portal da seguradora? Com que frequência?
3. As atualizações do portal chegam até o cliente como hoje? (WhatsApp manual, telefone, e-mail?)
4. Além de auto e residencial, tem outros ramos relevantes para a corretora?
5. O contato com a oficina é feito pela seguradora ou pela corretora?

---

## 5. Próximos passos — o que acontece depois desta reunião

| Prazo | Ação | Responsável |
|---|---|---|
| Hoje | Submeter templates WhatsApp à Meta | Nós + cliente (aprovação dos textos) |
| Esta semana | Conectar número WhatsApp ao sistema | Cliente fornece o chip/número |
| Esta semana | Importar carteira de apólices | Cliente fornece CSV do Agger |
| Esta semana | Iniciar M2 — Agente de Sinistros | Dev |
| 3–10 dias úteis | Templates WhatsApp aprovados pela Meta | Meta |
| Mês 3 | MVP em produção — primeira corretora pagante | — |

---

## 6. Questões técnicas para o responsável pelo Agger

> *Se houver alguém de TI ou responsável pelo sistema presente:*

1. Consigo exportar a carteira completa de apólices ativas? Quais campos estão disponíveis?
2. O Agger tem alguma API ou webhook que posso usar para sincronizar dados?
3. Como o status dos sinistros é atualizado no Agger — manual ou automático?

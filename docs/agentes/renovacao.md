# Agente Auxiliar de Renovação de Apólices

## Objetivo

Eliminar o status "NÃO TRABALHADO" no relatório de renovações da corretora. O agente monitora as datas de vencimento de apólices cadastradas, inicia contato proativo com o cliente via WhatsApp antes da vigência final, coleta a intenção de renovação e notifica o vendedor responsável para fechar o negócio.

O agente **não renova a apólice** — ele prepara e qualifica o lead de renovação para o vendedor humano. A renovação formal continua sendo feita pelo corretor no portal da seguradora.

---

## Como funciona

### Fluxo principal

```
CRON diário (08:00 BRT)
    │
    ▼
Busca apólices com vigência_final em X dias
    │
    ├─ 30 dias antes → 1º contato: aviso de vencimento
    ├─ 15 dias antes → 2º contato: reforço
    └─  7 dias antes → 3º contato: urgência + notifica vendedor
         │
         ▼
Cliente responde via WhatsApp
    │
    ├─ "Quero renovar" → coleta confirmação + notifica vendedor com resumo
    ├─ "Não quero renovar" → registra perda + motivo + notifica vendedor
    ├─ "Quero cotação em outra seguradora" → registra oportunidade + notifica vendedor
    └─ Sem resposta → próximo contato conforme régua
```

### Régua de contatos

| Gatilho | Canal | Tom | Ação após resposta |
|---|---|---|---|
| 30 dias antes | WhatsApp | Informativo | Registra intenção |
| 15 dias antes | WhatsApp | Lembrete | Registra intenção |
| 7 dias antes | WhatsApp | Urgência | Notifica vendedor imediatamente |
| Dia do vencimento | WhatsApp | Alerta | Notifica vendedor + marca "em risco" |
| 3 dias após vencimento | — | — | Marca como "não trabalhado" se sem resposta |

### Estados da apólice no fluxo

```
PENDENTE → CONTATO_INICIADO → AGUARDANDO_RESPOSTA
                                    │
                   ┌────────────────┼────────────────┐
                   ▼                ▼                ▼
            CONFIRMADO         RECUSADO          SEM_RESPOSTA
            (vendedor fecha)   (perdido)         (escala para vendedor)
```

### Dados utilizados do relatório de renovações

O agente lê os seguintes campos do registro de apólice:

| Campo | Uso |
|---|---|
| `vigência_final` | Gatilho da régua de contatos |
| `cliente` | Destinatário das mensagens |
| `seguradora` + `produto` + `item` | Contexto na mensagem (ex: "seu seguro do Fiat Uno") |
| `todos_vendedores` | Quem notificar na corretora |
| `tipo_renovação` | Tom da mensagem (negócio próprio vs. novo negócio) |
| `status` | Atualizado conforme resposta do cliente |

---

## Configuração

### Variáveis de ambiente

```env
# Régua de renovação (dias antes do vencimento)
RENEWAL_ALERT_DAYS=30,15,7,0

# Horário de disparo do CRON
RENEWAL_CRON_HOUR=8
RENEWAL_CRON_TIMEZONE=America/Sao_Paulo

# Número máximo de tentativas de contato
RENEWAL_MAX_CONTACTS=4

# Dias após vencimento para marcar como "não trabalhado"
RENEWAL_OVERDUE_DAYS=3
```

### Templates de mensagem WhatsApp

Os templates precisam de aprovação prévia pela Meta. Três templates necessários:

**1. Aviso (30 dias)**
```
Olá, {nome}! Aqui é da {corretora}.
Seu seguro do {item} vence em {dias} dias ({data_vencimento}).
Quer renovar? É só responder aqui que cuidamos de tudo pra você.
```

**2. Lembrete (15 e 7 dias)**
```
{nome}, o seguro do {item} vence em {dias} dias.
Posso já verificar as condições de renovação pra você?
```

**3. Urgência (dia do vencimento)**
```
{nome}, hoje é o último dia de cobertura do seu seguro {produto}.
Para não ficar sem proteção, me avisa agora e a gente resolve rapidinho.
```

---

## Exemplos

### Exemplo 1 — cliente confirma renovação

```
Agente: Olá, Paulo! Aqui é da corretora Bernardo Seguros.
        Seu seguro do Mercedes-Benz C-300 (QIV8J81) vence em 30 dias, no dia 02/08.
        Quer renovar? É só me avisar que cuidamos de tudo.

Cliente: Sim, pode renovar.

Agente: Ótimo! Vou avisar o Bernardo agora com o resumo da sua apólice.
        Ele vai entrar em contato para confirmar os detalhes da renovação.

[Notificação interna para vendedor]:
✅ RENOVAÇÃO CONFIRMADA
Cliente: Paulo Celio Silveira Junior
Seguro: Mercedes-Benz C-300 | QIV8J81 | Mitsui
Vigência: 02/08/2025
Cliente quer renovar. Aguardando sua ação.
```

### Exemplo 2 — cliente não quer renovar

```
Agente: Olá, Juan Carlo! Seu seguro Carta Verde do Chevrolet S10 (TCQ8H88)
        vence em 15 dias. Quer renovar com a Porto Seguro?

Cliente: Não, vou cancelar.

Agente: Tudo bem! Vou registrar aqui. Se mudar de ideia, é só chamar.
        Posso te perguntar o motivo? Isso nos ajuda a melhorar.

Cliente: Tá muito caro.

[Notificação interna para vendedor]:
❌ PERDA DE RENOVAÇÃO
Cliente: Juan Carlo de Siqueira
Seguro: Carta Verde S10 | TCQ8H88 | Porto Seguro
Motivo: preço
Ação recomendada: oferecer cotação em outra seguradora.
```

### Exemplo 3 — sem resposta (escala)

```
[Após 3 tentativas sem resposta — dia do vencimento]

[Notificação interna para vendedor]:
⚠️ SEM RESPOSTA — INTERVENÇÃO NECESSÁRIA
Cliente: Romero & David Corretora de Seguros
Seguro: Toyota Yaris Sedan | FWE0H22 | Ezze Seguros
Vigência: HOJE (11/08/2025)
3 tentativas de contato sem resposta.
Entre em contato diretamente para evitar perda.
```

---

## Limitações conhecidas

- **Sem acesso a portais de seguradora no MVP:** o agente não renova a apólice automaticamente — apenas qualifica e repassa para o vendedor.
- **Templates WhatsApp limitados:** a Meta restringe o formato das mensagens de negócios iniciadas pela empresa. Respostas livres do cliente após o primeiro contato não têm restrição.
- **Dados dependem de cadastro manual:** no MVP a carteira de apólices é inserida manualmente. Inconsistências no cadastro (ex: telefone errado) travam o fluxo.
- **Um vendedor por apólice:** quando o campo `todos_vendedores` tem múltiplos nomes (ex: "BERNARDO/RITA"), o agente notifica o primeiro. Lógica de round-robin pode ser implementada em V1.
- **Sem cotação automática:** o agente não acessa seguradoras para cotar renovação — apenas sinaliza a intenção ao vendedor.

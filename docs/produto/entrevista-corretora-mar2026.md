# Entrevista com a Corretora — Março 2026

> **Objetivo:** Entender o fluxo operacional real antes de iniciar o M2 (Sinistros)
> **Responsável pelo acompanhamento de sinistros e renovações residenciais:** Lucimara

---

## 1. Fluxo de Vendas

```
Pré-cotação no Agger (CPF + CEP + placa)
        │
        ▼
Cotação em múltiplas seguradoras
        │
        ▼
Vendedor fecha a venda
```

O Agger é o sistema central de gestão. Toda pré-cotação começa nele.

---

## 2. Fluxo de Sinistros e Assistência

```
Cliente aciona o seguro
        │
        ▼
Vendedor encaminha para funcionário responsável (Lucimara)
        │
        ▼
Lucimara acompanha o andamento nos portais das seguradoras
```

O acompanhamento hoje é manual — Lucimara acessa os portais e repassa atualizações ao cliente.

---

## 3. Seguradoras

### Auto

| Categoria | Seguradoras |
|---|---|
| Principais | Zurich, Alpha, Justus, BP, Suíça |
| Parceiros recentes | Yellum, Porto, Allianz, Tokio |

**Observações:**
- Alpha tem atendimento reconhecidamente ruim — risco em integrações futuras
- **Apenas Tokio tem portal próprio para acompanhamento de sinistros**
- Para todas as demais, o acompanhamento é via ligação ou WhatsApp com a seguradora

### Residencial

- Renovações feitas uma a uma no Agger
- Sinistros fazem o cliente perder bônus
- Comissão padrão: **20%**, ajustável para aproximar do valor anterior do cliente
- Coberturas têm regras específicas (ex: vendaval exige cobertura mínima de 20% do valor do bem)

---

## 4. Impacto no Projeto

### M2 — Agente de Sinistros

A ausência de portais nas seguradoras principais **simplifica** o M2:

- O agente **não precisa fazer RPA** em portal para a maioria dos casos
- O fluxo real é: agente coleta dados → notifica Lucimara com resumo estruturado → Lucimara abre/acompanha manualmente
- RPA (Playwright) só fará sentido para **Tokio** no MVP
- A persona de escalada deve ser **Lucimara**, não um "corretor genérico"

### M4 — Agente de Renovação

- Renovações residenciais são responsabilidade de Lucimara
- O agente de renovação deve considerar as regras de bônus ao comunicar sinistros residenciais

### Seguradoras do MVP — revisão necessária

O plano original (Porto, Allianz, Azul, Tokio) não reflete as seguradoras principais da corretora. **Revisar D-04.**

---

## 5. Pendências em Aberto

| Item | Status |
|---|---|
| Exportar CSV do Agger com todas as infos necessárias (nome, telefone, apólice, seguradora, vigência) | ❓ Em dúvida — confirmar com cliente |
| Número WhatsApp para atendimento de sinistros (pessoal ou empresa) | ❓ Não definido |
| Atendimento ruim da Alpha — como afeta o fluxo operacional atual? | ❓ A aprofundar |

---

## 6. Perguntas de Follow-up Recomendadas

1. Como Lucimara recebe hoje o aviso de um sinistro novo? WhatsApp? Ligação? Sistema?
2. Para as seguradoras sem portal (Zurich, Alpha, Justus, BP, Suíça), o contato é por qual canal? WhatsApp da seguradora? Ligação? E-mail?
3. O CSV do Agger consegue exportar: nome, telefone, número da apólice, seguradora e vigência?
4. O número de WhatsApp para sinistros vai ser o mesmo da corretora ou um número dedicado?

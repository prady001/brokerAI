# Comparativo: Provedores de WhatsApp para o BrokerAI

**Data:** março/2026
**Contexto:** O IP do WSL2 foi bloqueado pelo WhatsApp para novos registros via Baileys (Evolution API local), tornando impossível emparelhar o número +5511921297395. Este documento registra a análise das alternativas avaliadas.

---

## Opções avaliadas

### Opção A — Evolution API + Railway.app
Manter a Evolution API (Baileys), mas hospedá-la em um servidor externo com IP limpo.

### Opção B — Z-API (serviço gerenciado)
Usar a Z-API, provedor brasileiro que gerencia a conexão Baileys por conta própria.

### Opção C — API Oficial do WhatsApp (Meta Cloud API)
Integrar diretamente com a API oficial homologada pela Meta.

---

## Tabela comparativa

| | Evolution API + Railway | Z-API | API Oficial (Meta) |
|---|---|---|---|
| **Custo mensal** | ~$2 (Railway) | R$97 | Gratuito até 1k conversas |
| **Setup** | 30-60 min | 15 min | 2-4h (aprovação Meta) |
| **Estabilidade** | Média (Baileys) | Média (Baileys) | Alta (infraestrutura Meta) |
| **Risco de ban** | Alto (viola ToS) | Alto (viola ToS) | Zero |
| **Número usa app normal** | ✅ | ✅ | ❌ (número dedicado) |
| **Iniciar conversa (outbound)** | ✅ livre | ✅ livre | ⚠️ só com template aprovado |
| **Suporte** | Comunidade OSS | Suporte BR pago | Meta oficial |
| **Ngrok necessário** | ✅ (para dev local) | ❌ | ❌ |

---

## Análise por critério

### Custo

- **Evolution API + Railway** é a mais barata (~$2/mês), mas exige ngrok para rotear webhooks ao ambiente local durante desenvolvimento ($0 no free ou $8/mês no plano pago).
- **Z-API** cobra R$97/mês fixo independente do volume.
- **API Oficial** é gratuita até 1.000 conversas/mês. Para uma corretora pequena com ~200 clientes ativos, o custo provavelmente fica em zero ou abaixo de R$50/mês.

### Risco de ban

Evolution API e Z-API usam o Baileys — uma biblioteca que **simula um dispositivo WhatsApp Web**, violando os Termos de Serviço da Meta. Números podem ser banidos sem aviso prévio. Para uma plataforma com dados de clientes reais de corretoras, esse risco é inaceitável em produção.

A API Oficial é homologada pela Meta. Zero risco.

### Outbound (mensagens proativas)

A API Oficial exige **templates aprovados** para iniciar conversas. Isso afeta:
- Régua de renovação (D-30, D-15, D-7) → precisa de template
- Alertas proativos ao corretor → precisa de template

Porém, quando o **cliente responde primeiro**, abre-se uma janela de 24h onde qualquer mensagem é permitida. Fluxos reativos (sinistros, onboarding pull) não têm restrição.

Os templates de renovação precisariam ser aprovados de qualquer forma para o M4 — isso antecipa um trabalho que já estava planejado.

### Número dedicado

A API Oficial exige que o número **não esteja associado a nenhum app WhatsApp**. O número +5511921297395 já é dedicado ao BrokerAI, então essa restrição não é um problema.

---

## Decisão

**API Oficial do WhatsApp (Meta Cloud API)**

**Justificativa:**
1. O número +5511921297395 já é dedicado ao BrokerAI (sem conflito com uso pessoal)
2. Custo zero para o volume esperado no MVP
3. Elimina risco de ban — crítico para uma plataforma B2B com dados de clientes reais
4. A burocracia dos templates de renovação já estava no backlog do M4
5. Infraestrutura Meta é mais estável que Baileys para uso em produção

---

## Impacto no código

A migração envolve 3 arquivos principais:

| Arquivo | Mudança |
|---|---|
| `services/notification_service.py` | Trocar chamadas Evolution API pelo cliente Meta |
| `api/routes/webhook.py` | Adaptar schema do payload (Meta vs Evolution) |
| `api/middleware/auth.py` | Trocar verificação de apikey por assinatura HMAC da Meta |
| `models/config.py` | Adicionar `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` |
| `.env` / `.env.example` | Novas variáveis, remover Evolution API |

---

## Próximos passos

1. Criar app no [Meta for Developers](https://developers.facebook.com)
2. Adicionar produto "WhatsApp Business" ao app
3. Cadastrar o número +5511921297395
4. Obter `WHATSAPP_TOKEN` e `WHATSAPP_PHONE_NUMBER_ID`
5. Adaptar `notification_service.py` e `webhook.py`
6. Cadastrar templates de renovação (D-30, D-15, D-7)

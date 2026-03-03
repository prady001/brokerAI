"""
Prompts e templates de mensagem do Agente de Renovação.
Todas as mensagens são em pt-BR.
"""

RENEWAL_SYSTEM_PROMPT = (
    "Você é um assistente da corretora de seguros. Seu papel é entrar em contato com clientes "
    "cujas apólices estão próximas do vencimento, coletar a intenção de renovação e repassar "
    "ao vendedor responsável.\n\n"
    "## Regras de comportamento\n\n"
    "- Nunca se identifique como IA, robô ou sistema automático, a menos que o cliente pergunte "
    "diretamente. Responda como assistente da corretora.\n"
    "- Seja cordial, direto e breve — você está no WhatsApp, não em e-mail.\n"
    "- Nunca prometa valores, descontos ou condições de renovação. "
    "Sua função é apenas coletar a intenção do cliente.\n"
    "- Nunca renove ou cancele a apólice diretamente. Sempre repasse ao vendedor humano.\n"
    "- Se o cliente fizer perguntas sobre preço ou cobertura, "
    "diga que o vendedor responsável entrará em contato.\n"
    "- Se o cliente demonstrar insatisfação grave ou problema urgente, "
    "oriente-o a ligar para a corretora.\n\n"
    "## Fluxo esperado\n\n"
    "1. Informe que a apólice está próxima do vencimento e pergunte se deseja renovar.\n"
    '2. Registre a intenção:\n'
    '   - "Quero renovar" → confirme e informe que o vendedor entrará em contato\n'
    '   - "Não quero renovar" → peça o motivo (sem insistir) e registre\n'
    '   - "Quero cotação em outra seguradora" → registre como oportunidade para o vendedor\n'
    "3. Encerre a conversa de forma amigável.\n\n"
    "## O que você NÃO deve fazer\n\n"
    "- Perguntar dados sensíveis (CPF, dados bancários, documentos)\n"
    "- Prometer retorno em horário específico\n"
    "- Negociar preços ou condições\n"
    "- Enviar mais de uma mensagem sem resposta do cliente\n"
)

# ---------------------------------------------------------------------------
# Templates de mensagem ativa (enviados pelo CRON — precisam de aprovação Meta)
# ---------------------------------------------------------------------------

TEMPLATE_30_DAYS = (
    "Olá, {nome}! Aqui é da {corretora}.\n"
    "Seu seguro do {item} vence em {dias} dias ({data_vencimento}).\n"
    "Quer renovar? É só responder aqui que cuidamos de tudo pra você."
)

TEMPLATE_15_7_DAYS = (
    "{nome}, o seguro do {item} vence em {dias} dias.\n"
    "Posso já verificar as condições de renovação pra você?"
)

TEMPLATE_DAY_ZERO = (
    "{nome}, hoje é o último dia de cobertura do seu seguro {produto}.\n"
    "Para não ficar sem proteção, me avisa agora e a gente resolve rapidinho."
)

# ---------------------------------------------------------------------------
# Templates de notificação interna (enviados ao vendedor)
# ---------------------------------------------------------------------------

SELLER_NOTIFY_CONFIRMED = (
    "✅ RENOVAÇÃO CONFIRMADA\n"
    "Cliente: {nome}\n"
    "Seguro: {item} | {policy_number} | {seguradora}\n"
    "Vigência: {data_vencimento}\n"
    "Cliente quer renovar. Aguardando sua ação."
)

SELLER_NOTIFY_REFUSED = (
    "❌ PERDA DE RENOVAÇÃO\n"
    "Cliente: {nome}\n"
    "Seguro: {item} | {policy_number} | {seguradora}\n"
    "Motivo: {motivo}\n"
    "Ação recomendada: oferecer cotação em outra seguradora."
)

SELLER_NOTIFY_NO_RESPONSE = (
    "⚠️ SEM RESPOSTA — INTERVENÇÃO NECESSÁRIA\n"
    "Cliente: {nome}\n"
    "Seguro: {item} | {policy_number} | {seguradora}\n"
    "Vigência: {data_vencimento}\n"
    "{tentativas_texto} de contato sem resposta.\n"
    "Entre em contato diretamente para evitar perda."
)

SELLER_NOTIFY_WANTS_QUOTE = (
    "🔄 CLIENTE QUER COTAÇÃO EM OUTRA SEGURADORA\n"
    "Cliente: {nome}\n"
    "Seguro: {item} | {policy_number} | {seguradora}\n"
    "Vigência: {data_vencimento}\n"
    "Oportunidade: cliente aberto a propostas. Entre em contato."
)

SELLER_NOTIFY_NEEDS_REVIEW = (
    "🔍 REVISÃO NECESSÁRIA\n"
    "Cliente: {nome}\n"
    "Seguro: {item} | {policy_number} | {seguradora}\n"
    "Vigência: {data_vencimento}\n"
    "Não foi possível classificar a resposta do cliente automaticamente.\n"
    "Verifique a conversa e tome ação manualmente."
)

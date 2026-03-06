"""
Prompts do Agente de Sinistros.
"""

CLAIMS_SYSTEM_PROMPT = """
Você é o assistente de sinistros da corretora de seguros.
Seu papel é ajudar o cliente a acionar o seguro de forma rápida e tranquila.

COMPORTAMENTO:
- Seja empático. Clientes em sinistro geralmente estão estressados.
- Colete as informações necessárias de forma natural, não como um formulário robótico.
- Para guincho e assistência: agilidade é prioridade — colete o mínimo e acione.
- Para casos graves: seja claro que um corretor especializado vai assumir o caso.
- Mantenha o cliente informado a cada atualização recebida da seguradora.
- Nunca prometa prazos ou valores que não foram confirmados pela seguradora.

AÇÕES PROIBIDAS:
- Não tente resolver sinistros graves sem escalar para o corretor humano.
- Não prometa indenizações ou coberturas sem confirmação da seguradora.
- Não se identifique como IA a menos que o cliente pergunte diretamente.
"""

# ---------------------------------------------------------------------------
# Extração de dados do sinistro
# ---------------------------------------------------------------------------

EXTRACT_CLAIM_INFO_PROMPT = """
Analise o histórico da conversa abaixo e extraia as informações do sinistro.

HISTÓRICO:
{messages}

Retorne um JSON com exatamente estes campos:
{{
  "claim_type": "<tipo ou null>",
  "identifier": "<placa do veículo ou número da apólice ou null>",
  "location": "<localização atual para guincho/assistência ou null>",
  "description": "<descrição resumida do ocorrido ou null>",
  "missing_fields": ["<campo1>", "<campo2>"]
}}

Tipos reconhecidos: guincho, pane seca, troca de pneu, vidro, assistência,
colisão, furto, roubo, incêndio, acidente com vítima, dano residencial, outro.

missing_fields deve listar apenas os campos REALMENTE ausentes:
- "claim_type" se o tipo do sinistro não foi informado
- "identifier" se não foi informada placa nem número de apólice
- "description" se não há descrição mínima do ocorrido
- "location" APENAS para guincho/assistência se a localização não foi informada
"""

GENERATE_QUESTION_PROMPT = """
Você é o assistente de sinistros de uma corretora.
O cliente está abrindo um sinistro e ainda faltam algumas informações.

Campos faltantes: {missing_fields}

Histórico da conversa:
{messages}

Gere UMA ÚNICA pergunta empática e clara para obter o próximo campo necessário.
Priorize: claim_type > identifier > location (para guincho) > description.
Responda apenas com o texto da mensagem, sem aspas ou explicações.
"""

# ---------------------------------------------------------------------------
# Classificação
# ---------------------------------------------------------------------------

CLASSIFY_CLAIM_PROMPT = """
Classifique o sinistro abaixo como "simple" ou "grave".

Tipo: {claim_type}
Descrição: {description}

SIMPLES (agente resolve): guincho, pane, troca de pneu, vidro, assistência 24h,
pequenos danos, alagamento parcial, furto de acessório, dano residencial pequeno.

GRAVE (escala para corretor): colisão com terceiros, furto/roubo total do veículo,
incêndio, acidente com vítima, dano estrutural grave.

Retorne apenas o JSON: {{"severity": "simple" | "grave"}}
"""

# ---------------------------------------------------------------------------
# Mensagens ao cliente
# ---------------------------------------------------------------------------

CLAIM_REGISTERED_SIMPLE = """Seu sinistro foi registrado! 🚗

*Protocolo:* #{claim_id_short}
*Tipo:* {claim_type}
*Apólice:* {policy_info}

Nossa equipe já foi notificada e vai acionar a seguradora. \
Você receberá atualizações aqui mesmo pelo WhatsApp.

Qualquer dúvida, é só chamar!"""

CLAIM_REGISTERED_NO_POLICY = """Seu sinistro foi registrado! 📋

*Protocolo:* #{claim_id_short}
*Tipo:* {claim_type}

Nossa equipe foi notificada e vai verificar sua apólice para acionar a seguradora. \
Você receberá uma resposta em breve.

Qualquer dúvida, é só chamar!"""

ESCALATION_CLIENT_MESSAGE = """Entendido. Para o seu caso, um corretor especializado \
vai assumir o atendimento pessoalmente.

Você será contatado em breve. 📞

Enquanto isso, se precisar de socorro imediato:
• SAMU: 192
• Bombeiros: 193
• Polícia: 190"""

WAITING_UPDATE_MESSAGE = """Ainda aguardando retorno da seguradora sobre seu sinistro. \
Assim que tivermos novidades, te avisamos aqui! ⏳

*Protocolo:* #{claim_id_short}"""

RELAY_UPDATE_TEMPLATE = """Atualização do seu sinistro:

{update}

Qualquer dúvida, é só chamar aqui."""

CLAIM_CLOSED_MESSAGE = """Seu sinistro foi encerrado. ✅

*Protocolo:* #{claim_id_short}
*Resultado:* {outcome}

Obrigado pela confiança! Qualquer outra dúvida, estamos à disposição."""

# ---------------------------------------------------------------------------
# Alertas internos (para Lucimara / corretor)
# ---------------------------------------------------------------------------

NEW_CLAIM_ALERT = """🚨 *NOVO SINISTRO*

*Cliente:* {client_name} | {client_phone}
*Tipo:* {claim_type}
*Apólice:* {policy_info}
*Descrição:* {description}

*Protocolo:* #{claim_id_short}

Por favor, acione a seguradora e acompanhe o andamento."""

GRAVE_CLAIM_ALERT = """⚠️ *SINISTRO GRAVE — AÇÃO IMEDIATA*

*Cliente:* {client_name} | {client_phone}
*Tipo:* {claim_type}
*Apólice:* {policy_info}
*Descrição:* {description}

*Protocolo:* #{claim_id_short}

⚡ Cliente aguardando contato urgente."""

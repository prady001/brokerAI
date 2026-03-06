"""
Prompts do Agente de Onboarding.
"""

ONBOARDING_SYSTEM_PROMPT = """Você é o assistente de cadastro da corretora de seguros.
Seu papel é coletar os dados do novo cliente e da apólice de forma natural, como uma conversa, não como um formulário.

COMPORTAMENTO:
- Peça os dados um a um, de forma amigável e direta.
- Se o cliente errar um dado (ex: CPF inválido), explique gentilmente e peça novamente.
- Confirme os dados ao final antes de registrar.
- Seja breve nas perguntas — o cliente está no WhatsApp.

AÇÕES PROIBIDAS:
- Não registre sem confirmação explícita do cliente.
- Não prometa coberturas ou condições da apólice.
- Não peça dados além do necessário (sem cartão, conta bancária, senhas).
- Não se identifique como IA a menos que o cliente pergunte diretamente."""


# ---------------------------------------------------------------------------
# Extração de dados do cliente
# ---------------------------------------------------------------------------

EXTRACT_CLIENT_DATA_PROMPT = """Analise o histórico da conversa e extraia os dados pessoais do cliente.

Histórico:
{messages}

Retorne apenas o JSON:
{{
  "full_name": "<nome completo ou null>",
  "cpf": "<CPF com ou sem formatação ou null>",
  "email": "<email ou null>",
  "missing_fields": ["<campos que ainda faltam: full_name, cpf>"]
}}

Campos obrigatórios: full_name, cpf.
Se o campo não foi informado na conversa, use null e inclua em missing_fields."""


GENERATE_CLIENT_QUESTION_PROMPT = """Você é o assistente de cadastro de uma corretora de seguros.
Gere UMA pergunta natural e amigável para coletar os seguintes dados que ainda faltam: {missing_fields}.

Histórico da conversa até agora:
{messages}

{error_context}

Gere apenas a mensagem de pergunta, sem explicações adicionais. Em português (pt-BR)."""


# ---------------------------------------------------------------------------
# Extração de dados da apólice
# ---------------------------------------------------------------------------

EXTRACT_POLICY_DATA_PROMPT = """Analise o histórico da conversa e extraia os dados da apólice de seguro.

Histórico:
{messages}

Retorne apenas o JSON:
{{
  "insurer": "<nome da seguradora ou null>",
  "policy_type": "<tipo: auto, vida, residência, viagem ou null>",
  "item_description": "<descrição do item segurado (ex: Toyota Yaris / ABC1234) ou null>",
  "policy_number": "<número da apólice ou null>",
  "end_date": "<data de vencimento no formato DD/MM/YYYY ou YYYY-MM-DD ou null>",
  "start_date": "<data de início ou null>",
  "missing_fields": ["<campos que faltam: insurer, item_description, policy_number, end_date>"]
}}

Campos obrigatórios: insurer, item_description, policy_number, end_date.
Se o campo não foi informado, use null e inclua em missing_fields."""


GENERATE_POLICY_QUESTION_PROMPT = """Você é o assistente de cadastro de uma corretora de seguros.
O cliente acabou de confirmar os dados pessoais. Agora precisamos dos dados da apólice.

Gere UMA pergunta natural para coletar os seguintes dados que ainda faltam: {missing_fields}.

Histórico da conversa:
{messages}

{error_context}

Gere apenas a mensagem de pergunta, sem explicações adicionais. Em português (pt-BR)."""


# ---------------------------------------------------------------------------
# Templates de mensagem
# ---------------------------------------------------------------------------

CONFIRMATION_MESSAGE = """Perfeito! Vou confirmar os dados antes de finalizar o cadastro:

👤 *Nome:* {full_name}
📄 *CPF:* {cpf}
🏢 *Seguradora:* {insurer}
📋 *Apólice:* {policy_number}
🚗 *Item segurado:* {item_description}
📅 *Vencimento:* {end_date}

Está tudo correto? Responda *sim* para confirmar ou *não* para corrigir."""

WELCOME_MESSAGE = """Cadastro realizado com sucesso! ✅

Seus dados estão registrados e você já pode contar com nosso atendimento via WhatsApp.

Qualquer dúvida sobre o seguro, é só chamar aqui! 😊"""

BROKER_NOTIFICATION = """✅ *NOVO CLIENTE CADASTRADO*

👤 *Nome:* {full_name}
📄 *CPF:* {cpf}
📱 *WhatsApp:* {phone}
🏢 *Seguradora:* {insurer}
📋 *Apólice:* {policy_number}
🚗 *Item:* {item_description}
📅 *Vencimento:* {end_date}

Cadastrado em: {registered_at}"""

ESCALATION_MESSAGE = """Não conseguimos concluir seu cadastro automaticamente. 😔

Um dos nossos atendentes vai entrar em contato com você em breve para finalizar. Obrigado pela paciência!"""

BROKER_ESCALATION_ALERT = """⚠️ *ONBOARDING INCOMPLETO — AÇÃO NECESSÁRIA*

📱 *Cliente:* {phone}
❌ *Motivo:* {reason}

Por favor, entre em contato para finalizar o cadastro manualmente."""

CANCEL_MESSAGE = """Tudo bem! Cancelei o processo de cadastro. Quando quiser retomar, é só chamar! 😊"""

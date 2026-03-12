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

VOCABULÁRIO ACESSÍVEL:
- Use "número do contrato" ou "número do seguro" em vez de "número da apólice".
- Use "o que está segurado" em vez de "item segurado".
- Use "nome da empresa de seguro" em vez de "seguradora" quando o cliente parecer leigo.
- O cliente pode não ter todos os dados em mãos — oriente-o a verificar o documento físico ou PDF do seguro se necessário.

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
  "cep": "<CEP com ou sem formatação ou null>",
  "address": "<endereço completo (rua, número, bairro, cidade, UF) ou null>",
  "missing_fields": ["<campos que ainda faltam: full_name, cpf, cep, address>"]
}}

Campos obrigatórios: full_name, cpf, cep, address.
Se o campo não foi informado na conversa, use null e inclua em missing_fields."""


GENERATE_CLIENT_QUESTION_PROMPT = """Você é o assistente de cadastro de uma corretora de seguros.
Gere UMA pergunta natural e amigável para coletar o seguinte dado que ainda falta: {missing_fields}.

Referência de como chamar cada campo (use linguagem natural, não o nome técnico):
- full_name → nome completo
- cpf → CPF (somente os números, sem pontos ou traços)
- cep → CEP (o CEP do seu endereço, 8 dígitos)
- address → endereço completo (rua, número, bairro, cidade e estado)

Dica: se o campo for "cep", peça o CEP. Quando o cliente informar o CEP, pergunte em seguida o endereço completo para confirmar.

Histórico da conversa até agora:
{messages}

{error_context}

Gere apenas a mensagem de pergunta, sem explicações adicionais. Em português (pt-BR)."""


# ---------------------------------------------------------------------------
# Extração de dados da apólice
# ---------------------------------------------------------------------------

EXTRACT_POLICY_DATA_PROMPT = """Analise o histórico da conversa e extraia os dados do seguro.

Histórico:
{messages}

Retorne apenas o JSON:
{{
  "has_existing_policy": <true se o cliente JÁ TEM seguro ativo, false se ainda NÃO TEM seguro, null se não foi informado>,
  "insurer": "<nome da seguradora ou null>",
  "policy_type": "<tipo: auto, vida, residência, viagem ou null>",
  "item_description": "<descrição do item segurado (ex: Toyota Yaris / ABC1234) ou null>",
  "policy_number": "<número da apólice ou null (obrigatório apenas se já tem seguro)>",
  "end_date": "<data de vencimento no formato DD/MM/YYYY ou YYYY-MM-DD ou null (obrigatório apenas se já tem seguro)>",
  "start_date": "<data de início ou null>",
  "minor_driver": <true se há menor de idade que dirige o veículo, false se não há, null se não foi perguntado ou não é seguro auto>
}}

Regras:
- Se has_existing_policy for false: policy_number e end_date NÃO são obrigatórios.
- Se policy_type não for "auto": minor_driver NÃO é obrigatório.
- Se o campo não foi informado, use null."""


GENERATE_POLICY_QUESTION_PROMPT = """Você é o assistente de cadastro de uma corretora de seguros.
Gere UMA pergunta natural para coletar o seguinte dado que ainda falta: {missing_fields}.

Referência de como chamar cada campo (use linguagem natural, não o nome técnico):
- has_existing_policy → pergunte se o cliente já tem um seguro ativo no momento ou se está buscando contratar um novo
- insurer → nome da seguradora (ex: Porto Seguro, Bradesco, Allianz)
- item_description → o que está sendo segurado (ex: modelo e placa do carro)
- policy_number → número do contrato ou apólice do seguro
- end_date → data de vencimento do seguro (DD/MM/AAAA)
- minor_driver → se há algum condutor menor de idade (abaixo de 26 anos) que dirige o veículo — isso é indispensável para calcular o seguro auto

Histórico da conversa:
{messages}

{error_context}

Gere apenas a mensagem de pergunta, sem explicações adicionais. Em português (pt-BR)."""


# ---------------------------------------------------------------------------
# Templates de mensagem
# ---------------------------------------------------------------------------

CONFIRMATION_MESSAGE_BASE = """Perfeito! Vou confirmar os dados antes de finalizar o cadastro:

👤 *Nome:* {full_name}
📄 *CPF:* {cpf}
📍 *CEP:* {cep}
🏠 *Endereço:* {address}

{policy_section}

Está tudo correto? Responda *sim* para confirmar ou *não* para corrigir."""

CONFIRMATION_POLICY_WITH = """🏢 *Seguradora:* {insurer}
📋 *Apólice:* {policy_number}
🚗 *Item segurado:* {item_description}
📅 *Vencimento:* {end_date}{minor_driver_line}"""

CONFIRMATION_POLICY_WITHOUT = """🏢 *Seguradora de interesse:* {insurer}
🚗 *Item a segurar:* {item_description}{minor_driver_line}
ℹ️ _Sem apólice ativa no momento — corretor fará contato para cotação._"""

CONFIRMATION_MINOR_DRIVER_LINE = "\n🧒 *Menor condutor:* {value}"

WELCOME_MESSAGE = """Cadastro realizado com sucesso! ✅

Seus dados estão registrados e você já pode contar com nosso atendimento via WhatsApp.

Qualquer dúvida sobre o seguro, é só chamar aqui! 😊"""

BROKER_NOTIFICATION = """✅ *NOVO CLIENTE CADASTRADO*

👤 *Nome:* {full_name}
📄 *CPF:* {cpf}
📱 *WhatsApp:* {phone}
📍 *CEP:* {cep}
🏠 *Endereço:* {address}
{policy_section}
Cadastrado em: {registered_at}"""

BROKER_NOTIFICATION_POLICY_WITH = """🏢 *Seguradora:* {insurer}
📋 *Apólice:* {policy_number}
🚗 *Item:* {item_description}
📅 *Vencimento:* {end_date}{minor_driver_line}"""

BROKER_NOTIFICATION_POLICY_WITHOUT = """⚠️ *Sem apólice ativa* — cliente quer contratar seguro
🏢 *Seguradora de interesse:* {insurer}
🚗 *Item a segurar:* {item_description}{minor_driver_line}"""

BROKER_NOTIFICATION_MINOR_DRIVER_LINE = "\n🧒 *Menor condutor:* {value}"

ESCALATION_MESSAGE = """Não conseguimos concluir seu cadastro automaticamente. 😔

Um dos nossos atendentes vai entrar em contato com você em breve para finalizar. Obrigado pela paciência!"""

BROKER_ESCALATION_ALERT = """⚠️ *ONBOARDING INCOMPLETO — AÇÃO NECESSÁRIA*

📱 *Cliente:* {phone}
❌ *Motivo:* {reason}

Por favor, entre em contato para finalizar o cadastro manualmente."""

CANCEL_MESSAGE = """Tudo bem! Cancelei o processo de cadastro. Quando quiser retomar, é só chamar! 😊"""

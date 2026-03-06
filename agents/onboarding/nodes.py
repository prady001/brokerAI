"""
Nós do grafo do Agente de Onboarding.
Cada nó recebe OnboardingState e retorna um dict com os campos atualizados.

Fluxo:
  entry_router → contact_client (push) | collect_client (pull/retomada)
               → collect_policy → confirm → handle_confirmation
               → register → welcome → notify_seller → END
"""
import json
import logging
from datetime import UTC, datetime

from langchain_core.messages import HumanMessage, SystemMessage

from agents.llm import get_llm as _get_llm_factory
from agents.onboarding.prompts import (
    BROKER_ESCALATION_ALERT,
    BROKER_NOTIFICATION,
    CANCEL_MESSAGE,
    CONFIRMATION_MESSAGE,
    ESCALATION_MESSAGE,
    EXTRACT_CLIENT_DATA_PROMPT,
    EXTRACT_POLICY_DATA_PROMPT,
    GENERATE_CLIENT_QUESTION_PROMPT,
    GENERATE_POLICY_QUESTION_PROMPT,
    ONBOARDING_SYSTEM_PROMPT,
    WELCOME_MESSAGE,
)
from models.config import settings
from services import notification_service
from services.onboarding_service import (
    create_client,
    create_policy,
    get_or_create_insurer,
    validate_cpf,
)

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3


def _get_llm():
    return _get_llm_factory(max_tokens=1024)


def _messages_to_text(messages: list[dict]) -> str:
    recent = messages[-20:]
    lines = []
    for m in recent:
        role = "Cliente" if m.get("role") == "user" else "Assistente"
        lines.append(f"{role}: {m.get('content', '')}")
    return "\n".join(lines)


def _parse_json_response(text: str) -> dict:
    """Extrai JSON de uma resposta do LLM (tolera texto antes/depois do JSON)."""
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        logger.warning("Falha ao parsear JSON da resposta LLM: %s", text[:200])
        return {}


# ---------------------------------------------------------------------------
# Roteamento de entrada
# ---------------------------------------------------------------------------

def entry_router_node(state: dict) -> dict:
    """Nó de entrada — não altera estado. Roteamento via conditional edges."""
    return {}


def route_entry(state: dict) -> str:
    status = state.get("status", "")
    push_mode = state.get("push_mode", False)

    if status in ("registered", "failed"):
        return "end"
    if status == "cancel":
        return "cancel"
    if status == "awaiting_confirmation":
        return "handle_confirmation"
    if status == "collecting_policy":
        return "collect_policy"
    if push_mode and not status:
        return "contact_client"
    return "collect_client"


# ---------------------------------------------------------------------------
# Contato proativo (modo push)
# ---------------------------------------------------------------------------

async def contact_client_node(state: dict) -> dict:
    """
    Modo push: envia mensagem proativa ao cliente e pede o nome para iniciar.
    Executado apenas uma vez, no primeiro acionamento via /cadastrar.
    """
    phone = state.get("client_phone", "")
    greeting = (
        "Olá! Sou o assistente da corretora. O seu corretor pediu pra eu "
        "fazer seu cadastro rapidinho aqui no WhatsApp. 😊\n\n"
        "Pode me confirmar seu nome completo para começarmos?"
    )
    await notification_service.send_whatsapp_message(phone, greeting)
    return {
        "messages": [{"role": "assistant", "content": greeting}],
        "status": "collecting_client",
    }


# ---------------------------------------------------------------------------
# Coleta de dados do cliente (multi-turn)
# ---------------------------------------------------------------------------

async def collect_client_node(state: dict) -> dict:
    """
    Extrai nome e CPF do cliente das mensagens da conversa.
    - Valida CPF via algoritmo de dígito verificador.
    - Se incompleto: gera pergunta, envia ao cliente e retorna (aguarda próxima msg).
    - Se completo e válido: marca client_data_complete=True para prosseguir.
    """
    llm = _get_llm()
    messages = state.get("messages", [])
    client_phone = state.get("client_phone", "")

    messages_text = _messages_to_text(messages)

    # Primeira interação em modo pull — sem mensagem anterior do assistente
    has_prior_assistant = any(m.get("role") == "assistant" for m in messages)
    first_contact_hint = (
        "Esta é a primeira mensagem do cliente. Comece com uma saudação amigável."
        if not has_prior_assistant else ""
    )

    # Extrai dados já fornecidos
    extract_prompt = EXTRACT_CLIENT_DATA_PROMPT.format(messages=messages_text)
    response = await llm.ainvoke([
        SystemMessage(content=ONBOARDING_SYSTEM_PROMPT),
        HumanMessage(content=extract_prompt),
    ])
    extracted = _parse_json_response(response.content)

    prev = state.get("client_data", {})
    client_data = {
        "full_name": extracted.get("full_name") or prev.get("full_name"),
        "cpf": extracted.get("cpf") or prev.get("cpf"),
        "email": extracted.get("email") or prev.get("email"),
    }

    missing = list(extracted.get("missing_fields", []))
    error_context = first_contact_hint

    # Valida CPF se presente
    cpf = client_data.get("cpf") or ""
    if cpf and not validate_cpf(cpf):
        client_data["cpf"] = None
        if "cpf" not in missing:
            missing.append("cpf")
        error_context = (
            "O CPF informado parece inválido. "
            "Peça que o cliente confira e informe novamente."
        )

    # Recalcula campos faltantes com base no estado consolidado
    missing = [f for f in missing if not client_data.get(f)]

    if not missing:
        return {
            "client_data": client_data,
            "client_data_complete": True,
        }

    # Gera pergunta para o campo faltante
    question_prompt = GENERATE_CLIENT_QUESTION_PROMPT.format(
        missing_fields=", ".join(missing),
        messages=messages_text,
        error_context=error_context,
    )
    q_response = await llm.ainvoke([
        SystemMessage(content=ONBOARDING_SYSTEM_PROMPT),
        HumanMessage(content=question_prompt),
    ])
    question = q_response.content.strip()

    await notification_service.send_whatsapp_message(client_phone, question)
    updated_messages = messages + [{"role": "assistant", "content": question}]

    return {
        "client_data": client_data,
        "client_data_complete": False,
        "messages": updated_messages,
        "status": "collecting_client",
    }


def route_client_collection(state: dict) -> str:
    return "complete" if state.get("client_data_complete") else "incomplete"


# ---------------------------------------------------------------------------
# Coleta de dados da apólice (multi-turn)
# ---------------------------------------------------------------------------

async def collect_policy_node(state: dict) -> dict:
    """
    Extrai dados da apólice das mensagens da conversa.
    - Campos obrigatórios: insurer, item_description, policy_number, end_date.
    - Se incompleto: gera pergunta e aguarda próxima mensagem.
    - Se completo: marca policy_data_complete=True para prosseguir.
    """
    llm = _get_llm()
    messages = state.get("messages", [])
    client_phone = state.get("client_phone", "")

    messages_text = _messages_to_text(messages)

    extract_prompt = EXTRACT_POLICY_DATA_PROMPT.format(messages=messages_text)
    response = await llm.ainvoke([
        SystemMessage(content=ONBOARDING_SYSTEM_PROMPT),
        HumanMessage(content=extract_prompt),
    ])
    extracted = _parse_json_response(response.content)

    prev = state.get("policy_data", {})
    policy_data = {
        "insurer": extracted.get("insurer") or prev.get("insurer"),
        "policy_type": extracted.get("policy_type") or prev.get("policy_type") or "auto",
        "item_description": extracted.get("item_description") or prev.get("item_description"),
        "policy_number": extracted.get("policy_number") or prev.get("policy_number"),
        "end_date": extracted.get("end_date") or prev.get("end_date"),
        "start_date": extracted.get("start_date") or prev.get("start_date"),
    }

    error_context = ""

    # Recalcula missing com base nos campos obrigatórios
    required = ["insurer", "item_description", "policy_number", "end_date"]
    missing = [f for f in required if not policy_data.get(f)]

    if not missing:
        return {
            "policy_data": policy_data,
            "policy_data_complete": True,
        }

    # Se é a primeira pergunta sobre apólice, dar contexto de transição
    has_policy_question = any(
        "apólice" in m.get("content", "").lower() or
        "seguradora" in m.get("content", "").lower()
        for m in messages if m.get("role") == "assistant"
    )
    if not has_policy_question:
        error_context = "Dados pessoais já coletados. Agora colete os dados da apólice de seguro."

    question_prompt = GENERATE_POLICY_QUESTION_PROMPT.format(
        missing_fields=", ".join(missing),
        messages=messages_text,
        error_context=error_context,
    )
    q_response = await llm.ainvoke([
        SystemMessage(content=ONBOARDING_SYSTEM_PROMPT),
        HumanMessage(content=question_prompt),
    ])
    question = q_response.content.strip()

    await notification_service.send_whatsapp_message(client_phone, question)
    updated_messages = messages + [{"role": "assistant", "content": question}]

    return {
        "policy_data": policy_data,
        "policy_data_complete": False,
        "messages": updated_messages,
        "status": "collecting_policy",
    }


def route_policy_collection(state: dict) -> str:
    return "complete" if state.get("policy_data_complete") else "incomplete"


# ---------------------------------------------------------------------------
# Confirmação dos dados
# ---------------------------------------------------------------------------

async def confirm_node(state: dict) -> dict:
    """Envia resumo dos dados coletados e pede confirmação do cliente."""
    client_phone = state.get("client_phone", "")
    client_data = state.get("client_data", {})
    policy_data = state.get("policy_data", {})

    msg = CONFIRMATION_MESSAGE.format(
        full_name=client_data.get("full_name", ""),
        cpf=client_data.get("cpf", ""),
        insurer=policy_data.get("insurer", ""),
        policy_number=policy_data.get("policy_number", ""),
        item_description=policy_data.get("item_description", ""),
        end_date=policy_data.get("end_date", ""),
    )
    await notification_service.send_whatsapp_message(client_phone, msg)

    messages = state.get("messages", [])
    return {
        "messages": messages + [{"role": "assistant", "content": msg}],
        "status": "awaiting_confirmation",
    }


async def handle_confirmation_node(state: dict) -> dict:
    """
    Verifica a resposta do cliente à confirmação dos dados.
    - "sim" / confirma → prossegue para registro
    - "não" / corrigir → volta para coleta de dados do cliente
    - Indefinido → pede esclarecimento
    """
    messages = state.get("messages", [])
    client_phone = state.get("client_phone", "")

    user_messages = [m for m in messages if m.get("role") == "user"]
    latest = user_messages[-1].get("content", "").lower().strip() if user_messages else ""

    # Palavras inteiras para evitar falsos positivos de substring (ex: "n" em "nenhum")
    words = set(latest.split())
    confirmed_words = {"sim", "confirmo", "pode", "ok", "certo", "isso", "correto", "cadastra"}
    rejected_words = {"não", "nao", "errado", "errada", "corrigir", "mudar", "alterar", "refazer"}

    if words & confirmed_words or "tudo certo" in latest:
        return {"confirmation_status": "confirmed"}

    if words & rejected_words:
        msg = "Tudo bem! Vamos recomeçar a coleta. Pode me confirmar seu nome completo?"
        await notification_service.send_whatsapp_message(client_phone, msg)
        return {
            "confirmation_status": "rejected",
            "client_data": {},
            "policy_data": {},
            "client_data_complete": False,
            "policy_data_complete": False,
            "messages": messages + [{"role": "assistant", "content": msg}],
            "status": "collecting_client",
        }

    # Resposta ambígua
    msg = "Pode confirmar: responda *sim* para cadastrar ou *não* para corrigir algum dado."
    await notification_service.send_whatsapp_message(client_phone, msg)
    return {
        "confirmation_status": "unclear",
        "messages": messages + [{"role": "assistant", "content": msg}],
    }


def route_confirmation(state: dict) -> str:
    return state.get("confirmation_status", "unclear")


# ---------------------------------------------------------------------------
# Registro no banco
# ---------------------------------------------------------------------------

async def register_node(state: dict) -> dict:
    """
    Cria o cliente e a apólice no banco de dados.
    Tenta até _MAX_RETRIES vezes internamente antes de sinalizar falha.
    """
    client_phone = state.get("client_phone", "")
    client_data = state.get("client_data", {})
    policy_data = state.get("policy_data", {})

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            # Cria / busca seguradora
            insurer_id = await get_or_create_insurer(policy_data.get("insurer", "Não informada"))

            # Cria cliente (retorna existente se CPF já cadastrado)
            client_id = await create_client(
                full_name=client_data.get("full_name", ""),
                cpf_cnpj=client_data.get("cpf", ""),
                phone_whatsapp=client_phone,
                email=client_data.get("email"),
            )

            # Cria apólice
            policy_id = await create_policy(
                client_id=client_id,
                insurer_id=insurer_id,
                policy_number=policy_data.get("policy_number", ""),
                policy_type=policy_data.get("policy_type", "auto"),
                item_description=policy_data.get("item_description", ""),
                end_date=policy_data.get("end_date", ""),
                start_date=policy_data.get("start_date"),
                seller_phone=settings.broker_notification_phone,
            )

            logger.info(
                "Onboarding concluído: client_id=%s policy_id=%s phone=%s",
                client_id, policy_id, client_phone,
            )
            return {
                "client_id": client_id,
                "policy_id": policy_id,
                "registered": True,
                "status": "registered",
            }

        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Tentativa %d/%d falhou para %s: %s", attempt + 1, _MAX_RETRIES, client_phone, exc
            )

    logger.error("Todas as tentativas falharam para %s: %s", client_phone, last_exc)
    return {"failed": True, "status": "failed"}


def route_after_register(state: dict) -> str:
    if state.get("registered"):
        return "welcome"
    return "escalate"


# ---------------------------------------------------------------------------
# Boas-vindas ao cliente
# ---------------------------------------------------------------------------

async def welcome_node(state: dict) -> dict:
    """Envia mensagem de boas-vindas ao cliente após cadastro concluído."""
    client_phone = state.get("client_phone", "")
    messages = state.get("messages", [])

    await notification_service.send_whatsapp_message(client_phone, WELCOME_MESSAGE)
    return {
        "messages": messages + [{"role": "assistant", "content": WELCOME_MESSAGE}],
    }


# ---------------------------------------------------------------------------
# Notificação do corretor
# ---------------------------------------------------------------------------

async def notify_seller_node(state: dict) -> dict:
    """Envia resumo do novo cadastro ao BROKER_NOTIFICATION_PHONE."""
    client_data = state.get("client_data", {})
    policy_data = state.get("policy_data", {})
    client_phone = state.get("client_phone", "")

    alert = BROKER_NOTIFICATION.format(
        full_name=client_data.get("full_name", ""),
        cpf=client_data.get("cpf", ""),
        phone=client_phone,
        insurer=policy_data.get("insurer", ""),
        policy_number=policy_data.get("policy_number", ""),
        item_description=policy_data.get("item_description", ""),
        end_date=policy_data.get("end_date", ""),
        registered_at=datetime.now(UTC).strftime("%d/%m/%Y às %Hh%M"),
    )
    await notification_service.send_broker_alert(alert)
    return {}


# ---------------------------------------------------------------------------
# Escalada para corretor (falha após max retries)
# ---------------------------------------------------------------------------

async def escalate_node(state: dict) -> dict:
    """Notifica corretor e informa cliente que o cadastro manual será necessário."""
    client_phone = state.get("client_phone", "")

    await notification_service.send_whatsapp_message(client_phone, ESCALATION_MESSAGE)

    alert = BROKER_ESCALATION_ALERT.format(
        phone=client_phone,
        reason="Falha no cadastro automático após múltiplas tentativas.",
    )
    await notification_service.send_broker_alert(alert)

    return {"failed": True, "status": "failed"}


# ---------------------------------------------------------------------------
# Cancelamento (comando /cancelar do corretor)
# ---------------------------------------------------------------------------

async def cancel_onboarding_node(state: dict) -> dict:
    """Cancela onboarding em andamento e notifica o cliente."""
    client_phone = state.get("client_phone", "")
    await notification_service.send_whatsapp_message(client_phone, CANCEL_MESSAGE)
    return {"failed": True, "status": "failed"}

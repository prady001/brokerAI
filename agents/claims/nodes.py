"""
Nós do grafo do Agente de Sinistros.
Cada nó recebe ClaimsState e retorna um dict com os campos atualizados.
"""
import functools
import json
import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from agents.claims.prompts import (
    CLAIM_CLOSED_MESSAGE,
    CLAIM_REGISTERED_NO_POLICY,
    CLAIM_REGISTERED_SIMPLE,
    CLAIMS_SYSTEM_PROMPT,
    CLASSIFY_CLAIM_PROMPT,
    ESCALATION_CLIENT_MESSAGE,
    EXTRACT_CLAIM_INFO_PROMPT,
    GENERATE_QUESTION_PROMPT,
    GRAVE_CLAIM_ALERT,
    NEW_CLAIM_ALERT,
    RELAY_UPDATE_TEMPLATE,
    WAITING_UPDATE_MESSAGE,
)
from models.config import settings
from services import claim_service, notification_service

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def _get_llm() -> ChatAnthropic:
    model = (
        "claude-haiku-4-5-20251001"
        if settings.environment == "development"
        else "claude-sonnet-4-6"
    )
    return ChatAnthropic(
        model=model,
        api_key=settings.anthropic_api_key,
        max_tokens=1024,
    )


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
# Roteamento de entrada — direciona pelo status atual do sinistro
# ---------------------------------------------------------------------------

def entry_router_node(state: dict) -> dict:
    """Nó de entrada — não altera estado. O roteamento ocorre nas conditional edges."""
    return {}


def route_entry(state: dict) -> str:
    """
    Roteia pelo status atual:
    - Sinistro em aberto/aguardando → check_updates (mensagem de follow-up)
    - Escalado ou fechado → end
    - Novo / coletando → collect_info
    """
    status = state.get("status", "")
    if status in ("escalated", "closed"):
        return "end"
    if status in ("waiting_insurer", "in_progress"):
        return "check_updates"
    return "collect_info"


# ---------------------------------------------------------------------------
# Coleta de informações (multi-turn)
# ---------------------------------------------------------------------------

async def collect_info_node(state: dict) -> dict:
    """
    Extrai informações do sinistro das mensagens da conversa.
    Se incompleto: gera pergunta, envia ao cliente, retorna (graph vai para END).
    Se completo: marca claim_info_complete=True para prosseguir.
    """
    llm = _get_llm()
    messages = state.get("messages", [])
    client_phone = state.get("client_phone", "")
    messages_text = _messages_to_text(messages)

    # Extrai o que já temos
    extract_prompt = EXTRACT_CLAIM_INFO_PROMPT.format(messages=messages_text)
    response = await llm.ainvoke([
        SystemMessage(content=CLAIMS_SYSTEM_PROMPT),
        HumanMessage(content=extract_prompt),
    ])
    extracted = _parse_json_response(response.content)

    prev = state.get("claim_info", {})
    claim_info = {
        "claim_type": extracted.get("claim_type") or prev.get("claim_type"),
        "identifier": extracted.get("identifier") or prev.get("identifier"),
        "location": extracted.get("location") or prev.get("location"),
        "description": extracted.get("description") or prev.get("description"),
    }

    missing = extracted.get("missing_fields", [])
    # Recalcula missing com base no estado consolidado
    missing = [f for f in missing if not claim_info.get(f)]

    if not missing:
        return {"claim_info": claim_info, "claim_info_complete": True}

    # Falta informação — gera pergunta e envia ao cliente
    question_prompt = GENERATE_QUESTION_PROMPT.format(
        missing_fields=", ".join(missing),
        messages=messages_text,
    )
    q_response = await llm.ainvoke([
        SystemMessage(content=CLAIMS_SYSTEM_PROMPT),
        HumanMessage(content=question_prompt),
    ])
    question = q_response.content.strip()

    await notification_service.send_whatsapp_message(client_phone, question)

    updated_messages = messages + [{"role": "assistant", "content": question}]
    return {
        "claim_info": claim_info,
        "claim_info_complete": False,
        "messages": updated_messages,
        "status": "collecting",
    }


def route_collection_status(state: dict) -> str:
    return "complete" if state.get("claim_info_complete") else "incomplete"


# ---------------------------------------------------------------------------
# Classificação
# ---------------------------------------------------------------------------

async def classify_node(state: dict) -> dict:
    """Classifica o sinistro em 'simple' ou 'grave' via LLM."""
    claim_info = state.get("claim_info", {})
    claim_type = claim_info.get("claim_type", "")
    description = claim_info.get("description", "")

    # Classificação rápida por regras (evita chamada LLM para casos óbvios)
    simple_types = {"guincho", "pane", "pane seca", "vidro", "assistência", "assistencia",
                    "troca de pneu", "reboque"}
    grave_types = {"colisão", "colisao", "furto", "roubo", "incêndio", "incendio",
                   "acidente com vítima", "acidente com vitima"}

    claim_type_lower = claim_type.lower()
    if any(t in claim_type_lower for t in simple_types):
        return {"severity": "simple"}
    if any(t in claim_type_lower for t in grave_types):
        return {"severity": "grave"}

    # Fallback: LLM decide
    llm = _get_llm()
    prompt = CLASSIFY_CLAIM_PROMPT.format(claim_type=claim_type, description=description)
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    data = _parse_json_response(response.content)
    severity = data.get("severity", "grave")  # default grave por segurança
    return {"severity": severity}


def route_by_severity(state: dict) -> str:
    return state.get("severity", "grave")


# ---------------------------------------------------------------------------
# Abertura do sinistro (simples)
# ---------------------------------------------------------------------------

async def open_claim_node(state: dict) -> dict:
    """
    Cria o sinistro no banco, notifica Lucimara e confirma ao cliente.
    MVP: abertura manual pela equipe após notificação — sem RPA.
    """
    client_id = state.get("client_id", "")
    client_phone = state.get("client_phone", "")
    client_name = state.get("client_name", "Cliente")
    claim_info = state.get("claim_info", {})
    claim_type = claim_info.get("claim_type", "outro")
    description = claim_info.get("description", "")
    severity = state.get("severity", "simple")

    if not client_id:
        logger.warning("open_claim_node: client_id ausente — abortando criação de sinistro")
        await notification_service.send_whatsapp_message(
            client_phone,
            "Não conseguimos identificar seu cadastro. Por favor, entre em contato "
            "diretamente com a corretora para registrar o sinistro. 📞",
        )
        return {}

    # Tenta localizar a apólice no banco pelo identificador fornecido
    policy: dict | None = None
    identifier = claim_info.get("identifier", "")
    if identifier:
        policy = await claim_service.get_policy_by_identifier(identifier, client_id)

    policy_id = policy["id"] if policy else None
    insurer_id = policy["insurer_id"] if policy else None
    policy_info = (
        (policy["item_description"] or policy["policy_number"] or "não identificada")
        if policy else "não identificada"
    )

    claim_id = await claim_service.create_claim(
        client_id=client_id,
        claim_type=claim_type,
        severity=severity,
        description=description,
        policy_id=policy_id,
        insurer_id=insurer_id,
    )
    claim_id_short = claim_id[:8].upper()

    # Alerta interno para Lucimara
    alert = NEW_CLAIM_ALERT.format(
        client_name=client_name,
        client_phone=client_phone,
        claim_type=claim_type,
        policy_info=policy_info,
        description=description or "não informada",
        claim_id_short=claim_id_short,
    )
    await notification_service.send_broker_alert(alert)

    # Confirmação ao cliente
    if policy:
        msg = CLAIM_REGISTERED_SIMPLE.format(
            claim_id_short=claim_id_short,
            claim_type=claim_type,
            policy_info=policy_info,
        )
    else:
        msg = CLAIM_REGISTERED_NO_POLICY.format(
            claim_id_short=claim_id_short,
            claim_type=claim_type,
        )
    await notification_service.send_whatsapp_message(client_phone, msg)

    messages = state.get("messages", [])
    updated_messages = messages + [{"role": "assistant", "content": msg}]

    return {
        "claim_id": claim_id,
        "policy_id": policy_id or "",
        "insurer_id": insurer_id or "",
        "status": "waiting_insurer",
        "messages": updated_messages,
    }


# ---------------------------------------------------------------------------
# Verificação de atualizações (loop de acompanhamento)
# ---------------------------------------------------------------------------

async def check_updates_node(state: dict) -> dict:
    """
    MVP: não há polling de portal. Informa ao cliente que ainda aguardamos e retorna.

    LIMITAÇÃO MVP: este nó sempre retorna update_status="no_update".
    Os caminhos "has_update" (relay_to_client) e "closed" (close_node) são
    intencionalmente inalcançáveis nesta versão — o encerramento do sinistro
    ocorre via atualização direta no banco pela equipe da corretora.

    TODO(V1): substituir pela implementação de polling via Playwright no portal
    de cada seguradora (Tokio Marine primeiro, conforme entrevista mar/2026).
    Quando implementado, este nó poderá retornar "has_update" ou "closed",
    desbloqueando relay_to_client_node e close_node.
    """
    client_phone = state.get("client_phone", "")
    claim_id = state.get("claim_id", "")
    claim_id_short = claim_id[:8].upper() if claim_id else "---"

    msg = WAITING_UPDATE_MESSAGE.format(claim_id_short=claim_id_short)
    await notification_service.send_whatsapp_message(client_phone, msg)

    messages = state.get("messages", [])
    updated_messages = messages + [{"role": "assistant", "content": msg}]

    # MVP: sempre "no_update" — ver docstring acima
    return {
        "update_status": "no_update",
        "poll_count": state.get("poll_count", 0) + 1,
        "messages": updated_messages,
    }


def route_by_update_status(state: dict) -> str:
    return state.get("update_status", "no_update")


# ---------------------------------------------------------------------------
# Relay de atualização ao cliente
# ---------------------------------------------------------------------------

async def relay_to_client_node(state: dict) -> dict:
    """Envia a atualização recebida da seguradora ao cliente."""
    client_phone = state.get("client_phone", "")
    last_update = state.get("last_update", "")

    msg = RELAY_UPDATE_TEMPLATE.format(update=last_update)
    await notification_service.send_whatsapp_message(client_phone, msg)

    messages = state.get("messages", [])
    updated_messages = messages + [{"role": "assistant", "content": msg}]

    return {"messages": updated_messages}


def route_after_relay(state: dict) -> str:
    return "closed" if state.get("closed") else "open"


# ---------------------------------------------------------------------------
# Escalada para corretor (sinistros graves)
# ---------------------------------------------------------------------------

async def escalate_node(state: dict) -> dict:
    """
    Sinistros graves: notifica Lucimara com resumo urgente e informa o cliente.
    """
    client_phone = state.get("client_phone", "")
    client_name = state.get("client_name", "Cliente")
    claim_info = state.get("claim_info", {})
    claim_type = claim_info.get("claim_type", "não identificado")
    description = claim_info.get("description", "não informada")
    claim_id = state.get("claim_id", "")

    # Cria o sinistro no banco antes de escalar (se ainda não foi criado)
    if not claim_id:
        client_id = state.get("client_id", "")
        if not client_id:
            logger.warning("escalate_node: client_id ausente — abortando criação de sinistro")
        else:
            claim_id = await claim_service.create_claim(
                client_id=client_id,
                claim_type=claim_type,
                severity="grave",
                description=description,
            )
            await claim_service.update_claim_status(claim_id, "escalated")

    claim_id_short = claim_id[:8].upper() if claim_id else "---"
    policy_info = claim_info.get("identifier") or "não identificada"

    # Alerta urgente para Lucimara
    alert = GRAVE_CLAIM_ALERT.format(
        client_name=client_name,
        client_phone=client_phone,
        claim_type=claim_type,
        policy_info=policy_info,
        description=description,
        claim_id_short=claim_id_short,
    )
    await notification_service.send_broker_alert(alert)

    # Mensagem ao cliente
    await notification_service.send_whatsapp_message(client_phone, ESCALATION_CLIENT_MESSAGE)

    messages = state.get("messages", [])
    updated_messages = messages + [
        {"role": "assistant", "content": ESCALATION_CLIENT_MESSAGE}
    ]

    return {
        "claim_id": claim_id,
        "status": "escalated",
        "escalated": True,
        "messages": updated_messages,
    }


# ---------------------------------------------------------------------------
# Encerramento do sinistro
# ---------------------------------------------------------------------------

async def close_node(state: dict) -> dict:
    """Encerra o sinistro: persiste no banco e notifica o cliente."""
    client_phone = state.get("client_phone", "")
    claim_id = state.get("claim_id", "")

    if claim_id:
        await claim_service.close_claim(claim_id)

    claim_id_short = claim_id[:8].upper() if claim_id else "---"
    msg = CLAIM_CLOSED_MESSAGE.format(
        claim_id_short=claim_id_short,
        outcome="Sinistro encerrado pela seguradora.",
    )
    await notification_service.send_whatsapp_message(client_phone, msg)

    messages = state.get("messages", [])
    updated_messages = messages + [{"role": "assistant", "content": msg}]

    return {
        "status": "closed",
        "closed": True,
        "messages": updated_messages,
    }

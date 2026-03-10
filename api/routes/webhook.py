"""
Rota de webhook WhatsApp.
Recebe eventos da Twilio e roteia para o agente adequado.

Roteamento:
- Mensagem do corretor com /cadastrar <numero> → inicia onboarding (push)
- Mensagem do corretor com /cancelar <numero>  → cancela onboarding em andamento
- Cliente com onboarding ativo                 → Agente de Onboarding (M3)
- Cliente com renovação ativa (contacted)      → Agente de Renovação (M4)
- Novo cliente sem cadastro + intenção onboarding → Agente de Onboarding (M3, pull)
- Demais mensagens                             → Agente de Sinistros / Orquestrador (M2)
"""
import logging
import re
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form, Request, Response
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.claims.graph import build_claims_graph
from agents.onboarding.graph import build_onboarding_graph
from agents.orchestrator.nodes import (
    delete_conversation_state,
    delete_onboarding_state,
    detect_intent_node,
    faq_handler_node,
    human_handoff_node,
    load_conversation_state,
    load_onboarding_state,
    save_conversation_state,
    save_onboarding_state,
)
from agents.renewal.graph import get_renewal_graph
from api.middleware.auth import verify_twilio_webhook
from models.config import settings
from models.database import Client, get_db
from services import claim_service, notification_service
from services.renewal_service import RenewalService

logger = logging.getLogger(__name__)
router = APIRouter()

_claims_graph = build_claims_graph()
_onboarding_graph = build_onboarding_graph()

_CMD_CADASTRAR = re.compile(r"^/cadastrar\s+(\d+)", re.IGNORECASE)
_CMD_CANCELAR  = re.compile(r"^/cancelar\s+(\d+)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Handler principal (Twilio envia form-urlencoded)
# ---------------------------------------------------------------------------

def _parse_twilio_phone(raw: str) -> str:
    """Converte 'whatsapp:+5511999999999' → '5511999999999'."""
    return raw.removeprefix("whatsapp:+").removeprefix("whatsapp:").lstrip("+")


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    ProfileName: str = Form("Cliente"),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_twilio_webhook),
) -> Response:
    """
    Recebe eventos da Twilio WhatsApp.
    Payload é form-urlencoded com campos From, Body e ProfileName.

    Roteamento:
    - Cliente com renovação ativa (status 'contacted') → Agente de Renovação
    - Demais mensagens → Agente de Sinistros / Orquestrador (M2)
    """
    phone = _parse_twilio_phone(From)
    text = Body.strip()
    client_name = ProfileName or "Cliente"

    if not text:
        return Response(content="", media_type="text/xml")

    logger.info("Mensagem de %s (%s): %s", phone, client_name, text[:80])
    await _route_message(phone=phone, client_name=client_name, text=text, db=db)

    # Twilio espera resposta TwiML (pode ser vazia)
    return Response(content="<Response/>", media_type="text/xml")


async def _route_message(phone: str, client_name: str, text: str, db: AsyncSession) -> None:
    """Roteia mensagem recebida para o agente adequado."""
    # ---------------------------------------------------------------------------
    # Comandos do corretor (apenas de BROKER_NOTIFICATION_PHONE)
    # ---------------------------------------------------------------------------
    if phone == settings.broker_notification_phone:
        cmd_cadastrar = _CMD_CADASTRAR.match(text.strip())
        if cmd_cadastrar:
            await _handle_broker_cadastrar(cmd_cadastrar.group(1))
            return

        cmd_cancelar = _CMD_CANCELAR.match(text.strip())
        if cmd_cancelar:
            await _handle_broker_cancelar(cmd_cancelar.group(1))
            return

    # ---------------------------------------------------------------------------
    # Onboarding ativo para este cliente? (M3)
    # ---------------------------------------------------------------------------
    onboarding_state = await load_onboarding_state(phone)
    if onboarding_state is not None:
        try:
            await _resume_onboarding(phone=phone, text=text, existing_state=onboarding_state)
        except Exception:
            logger.exception("Erro ao retomar onboarding para %s", phone)
        return

    # Verifica se há renovação ativa para o cliente (M4)
    result = await db.execute(
        sa_select(Client).where(Client.phone_whatsapp == phone)
    )
    client_row = result.scalar_one_or_none()

    if client_row is not None:
        renewal_service = RenewalService(db)
        active_renewal = await renewal_service.get_active_renewal_for_client(client_row.id)  # type: ignore[arg-type]

        if active_renewal is not None:
            logger.info(
                "Roteando para Agente de Renovação: client_id=%s renewal_id=%s",
                client_row.id,
                active_renewal.id,
            )
            try:
                renewal_graph = get_renewal_graph()
                await renewal_graph.ainvoke({
                    "mode": "whatsapp",
                    "client_response": text,
                    "renewal_id": str(active_renewal.id),
                    "_renewal_service": renewal_service,
                    "_llm": None,
                    "notifications_sent": [],
                    "errors": [],
                })
            except Exception:
                logger.exception("Erro ao processar renovação para %s", phone)
            return

    # Sem renovação ativa — roteia para Agente de Sinistros / Orquestrador (M2)
    try:
        await _handle_message(phone=phone, client_name=client_name, text=text)
    except Exception as exc:
        logger.error("Erro ao processar mensagem de %s: %s", phone, exc, exc_info=True)


# ---------------------------------------------------------------------------
# Handlers de comandos do corretor
# ---------------------------------------------------------------------------

async def _handle_broker_cadastrar(target_phone: str) -> None:
    """
    Inicia o onboarding em modo push para o número informado pelo corretor.
    Cria estado inicial no Redis e aciona o grafo.
    """
    logger.info("Comando /cadastrar para %s", target_phone)

    existing = await load_onboarding_state(target_phone)
    if existing and existing.get("status") not in ("registered", "failed", ""):
        await notification_service.send_broker_alert(
            f"⚠️ Já existe um cadastro em andamento para {target_phone}."
        )
        return

    initial_state: dict = {
        "conversation_id": str(uuid.uuid4()),
        "client_phone": target_phone,
        "push_mode": True,
        "client_data": {},
        "policy_data": {},
        "client_data_complete": False,
        "policy_data_complete": False,
        "policy_transition_done": False,
        "validation_errors": [],
        "retry_count": 0,
        "client_id": "",
        "policy_id": "",
        "registered": False,
        "failed": False,
        "messages": [],
        "status": "",
        "confirmation_status": "",
    }

    final_state = await _onboarding_graph.ainvoke(initial_state)
    await _persist_or_close_onboarding(target_phone, final_state)


async def _handle_broker_cancelar(target_phone: str) -> None:
    """
    Cancela onboarding ativo para o número informado pelo corretor.
    """
    logger.info("Comando /cancelar para %s", target_phone)

    existing = await load_onboarding_state(target_phone)
    if not existing or existing.get("status") in ("registered", "failed"):
        await notification_service.send_broker_alert(
            f"ℹ️ Nenhum cadastro ativo encontrado para {target_phone}."
        )
        return

    cancel_state = {**existing, "status": "cancel"}
    await _onboarding_graph.ainvoke(cancel_state)
    await delete_onboarding_state(target_phone)
    logger.info("Onboarding cancelado para %s", target_phone)


# ---------------------------------------------------------------------------
# Handlers do agente de onboarding (M3)
# ---------------------------------------------------------------------------

async def _resume_onboarding(phone: str, text: str, existing_state: dict) -> None:
    """Retoma onboarding ativo com a nova mensagem do cliente."""
    messages = existing_state.get("messages", [])
    messages.append({"role": "user", "content": text, "ts": datetime.now(UTC).isoformat()})
    updated_state = {**existing_state, "messages": messages}

    final_state = await _onboarding_graph.ainvoke(updated_state)
    await _persist_or_close_onboarding(phone, final_state)


async def _start_onboarding_pull(phone: str, text: str) -> None:
    """Inicia onboarding em modo pull (cliente chegou sem cadastro com intenção de cadastrar)."""
    logger.info("Iniciando onboarding pull para %s", phone)

    initial_state: dict = {
        "conversation_id": str(uuid.uuid4()),
        "client_phone": phone,
        "push_mode": False,
        "client_data": {},
        "policy_data": {},
        "client_data_complete": False,
        "policy_data_complete": False,
        "policy_transition_done": False,
        "validation_errors": [],
        "retry_count": 0,
        "client_id": "",
        "policy_id": "",
        "registered": False,
        "failed": False,
        "messages": [{"role": "user", "content": text, "ts": datetime.now(UTC).isoformat()}],
        "status": "",
        "confirmation_status": "",
    }

    final_state = await _onboarding_graph.ainvoke(initial_state)
    await _persist_or_close_onboarding(phone, final_state)


async def _persist_or_close_onboarding(phone: str, state: dict) -> None:
    """Persiste estado de onboarding no Redis ou remove se concluído/cancelado."""
    if state.get("registered") or state.get("failed"):
        await delete_onboarding_state(phone)
    else:
        await save_onboarding_state(phone, state)


async def _handle_message(phone: str, client_name: str, text: str) -> None:
    """
    Orquestra o processamento da mensagem (M2):
    1. Verifica se há conversa de sinistro ativa (Redis)
    2. Se sim: retoma o agente de sinistros com o estado carregado
    3. Se não: detecta intenção e roteia
    """
    # Lookup do cliente no banco
    client = await claim_service.get_client_by_phone(phone)
    if not client:
        # Detecta se o cliente quer se cadastrar (pull mode)
        intent_state = await detect_intent_node({"message": text, "client_phone": phone})
        if intent_state.get("intent") == "onboarding":
            await _start_onboarding_pull(phone=phone, text=text)
        else:
            logger.info("Cliente não cadastrado: %s — acionando handoff humano", phone)
            await human_handoff_node({
                "message": text,
                "client_phone": phone,
                "client_name": client_name,
            })
        return

    client_id = client["id"]
    client_db_name = client["name"]

    # Verifica conversa ativa
    active_state = await load_conversation_state(phone)

    if active_state:
        await _resume_claims_agent(
            phone=phone,
            client_id=client_id,
            client_name=client_db_name,
            text=text,
            existing_state=active_state,
        )
        return

    # Nova mensagem — detecta intenção
    intent_state = await detect_intent_node({
        "message": text,
        "client_phone": phone,
        "client_name": client_db_name,
    })
    intent = intent_state.get("intent", "unknown")
    confidence = intent_state.get("confidence", 0.0)
    logger.info("Intenção detectada para %s: %s (%.2f)", phone, intent, confidence)

    if intent == "claim":
        await _start_claims_agent(
            phone=phone,
            client_id=client_id,
            client_name=client_db_name,
            text=text,
        )
    elif intent == "onboarding":
        # Cliente já cadastrado pedindo cadastro — informa que já existe
        await notification_service.send_whatsapp_message(
            phone,
            "Olá! Seus dados já estão cadastrados em nosso sistema. "
            "Se precisar de ajuda com alguma apólice ou sinistro, é só me avisar! 😊",
        )
    elif intent == "faq":
        await faq_handler_node({
            "message": text,
            "client_phone": phone,
            "client_name": client_db_name,
        })
    else:
        await human_handoff_node({
            "message": text,
            "client_phone": phone,
            "client_name": client_db_name,
        })


async def _start_claims_agent(
    phone: str, client_id: str, client_name: str, text: str
) -> None:
    """Inicia uma nova conversa de sinistro."""
    initial_state: dict = {
        "conversation_id": str(uuid.uuid4()),
        "client_id": client_id,
        "client_phone": phone,
        "client_name": client_name,
        "messages": [{"role": "user", "content": text, "ts": datetime.now(UTC).isoformat()}],
        "status": "",
        "claim_info": {},
        "claim_info_complete": False,
        "claim_id": "",
        "policy_id": "",
        "insurer_id": "",
        "severity": "",
        "update_status": "",
        "last_update": "",
        "poll_count": 0,
        "escalated": False,
        "closed": False,
    }

    final_state = await _claims_graph.ainvoke(initial_state)
    await _persist_or_close(phone, final_state)


async def _resume_claims_agent(
    phone: str, client_id: str, client_name: str, text: str, existing_state: dict
) -> None:
    """Retoma conversa de sinistro existente com a nova mensagem."""
    messages = existing_state.get("messages", [])
    messages.append({"role": "user", "content": text, "ts": datetime.now(UTC).isoformat()})
    updated_state = {**existing_state, "messages": messages}

    final_state = await _claims_graph.ainvoke(updated_state)
    await _persist_or_close(phone, final_state)


async def _persist_or_close(phone: str, state: dict) -> None:
    """Persiste estado no Redis ou remove se o sinistro foi encerrado."""
    if state.get("closed"):
        await delete_conversation_state(phone)
    elif state.get("escalated"):
        # Mantém estado por 24h para reconhecer follow-ups pós-escalada
        await save_conversation_state(phone, state, ttl=86400)
    else:
        await save_conversation_state(phone, state)

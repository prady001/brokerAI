"""
Rota de webhook WhatsApp.
Recebe eventos do Evolution API e roteia para o agente adequado.

Roteamento:
- Cliente com renovação ativa (status 'contacted') → Agente de Renovação (M4)
- Demais mensagens → Agente de Sinistros / Orquestrador (M2)
"""
import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.claims.graph import build_claims_graph
from agents.orchestrator.nodes import (
    delete_conversation_state,
    detect_intent_node,
    faq_handler_node,
    human_handoff_node,
    load_conversation_state,
    save_conversation_state,
)
from agents.renewal.graph import get_renewal_graph
from api.middleware.auth import verify_evolution_webhook
from models.database import Client, get_db
from services import claim_service, notification_service
from services.renewal_service import RenewalService

logger = logging.getLogger(__name__)
router = APIRouter()

_claims_graph = build_claims_graph()


# ---------------------------------------------------------------------------
# Schemas do payload Evolution API
# ---------------------------------------------------------------------------

class MessageKey(BaseModel):
    remoteJid: str
    fromMe: bool
    id: str


class MessageContent(BaseModel):
    conversation: str | None = None


class MessageData(BaseModel):
    key: MessageKey
    pushName: str | None = None
    message: MessageContent | None = None
    messageType: str | None = None
    messageTimestamp: int | None = None


class EvolutionWebhookPayload(BaseModel):
    event: str
    instance: str | None = None
    data: MessageData | None = None


# ---------------------------------------------------------------------------
# Handler principal
# ---------------------------------------------------------------------------

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(
    payload: EvolutionWebhookPayload,
    _: None = Depends(verify_evolution_webhook),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Recebe eventos do Evolution API.
    Filtra apenas mensagens recebidas (messages.upsert, fromMe=false).

    Roteamento:
    - Cliente com renovação ativa (status 'contacted') → Agente de Renovação
    - Demais mensagens → Agente de Sinistros / Orquestrador (M2)
    """
    if payload.event != "messages.upsert":
        return {"status": "ignored"}

    if payload.data is None or payload.data.key.fromMe:
        return {"status": "ignored"}

    phone = payload.data.key.remoteJid.replace("@s.whatsapp.net", "")
    client_name = payload.data.pushName or "Cliente"
    text = (payload.data.message.conversation or "") if payload.data.message else ""

    if not text.strip():
        return {"status": "ignored"}

    logger.info("Mensagem de %s (%s): %s", phone, client_name, text[:80])

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
                return {"status": "routed_to_renewal", "phone": phone}
            except Exception:
                logger.exception("Erro ao processar renovação para %s", phone)
                return {"status": "error_renewal", "phone": phone}

    # Sem renovação ativa — roteia para Agente de Sinistros / Orquestrador (M2)
    try:
        await _handle_message(phone=phone, client_name=client_name, text=text)
    except Exception as exc:
        logger.error("Erro ao processar mensagem de %s: %s", phone, exc, exc_info=True)
        return {"status": "error"}

    return {"status": "received", "phone": phone}


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
        logger.info("Cliente não cadastrado: %s — enviando mensagem de boas-vindas", phone)
        await notification_service.send_whatsapp_message(
            phone,
            "Olá! Para que possamos ajudá-lo, por favor entre em contato com a corretora "
            "para cadastrar seus dados. 😊",
        )
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

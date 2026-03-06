"""
Rota de webhook WhatsApp.
Recebe eventos do Evolution API, roteia para o agente correto e persiste estado no Redis.
"""
import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from agents.claims.graph import build_claims_graph
from agents.orchestrator.nodes import (
    delete_conversation_state,
    detect_intent_node,
    faq_handler_node,
    human_handoff_node,
    load_conversation_state,
    save_conversation_state,
)
from api.middleware.auth import verify_evolution_webhook
from services import claim_service, notification_service

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
) -> dict:
    """
    Recebe eventos do Evolution API.
    Filtra apenas mensagens recebidas (messages.upsert, fromMe=false).
    Roteia para agente de sinistros ou orquestrador conforme contexto.
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

    await _handle_message(phone=phone, client_name=client_name, text=text)
    return {"status": "received", "phone": phone}


async def _handle_message(phone: str, client_name: str, text: str) -> None:
    """
    Orquestra o processamento da mensagem:
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
    """Persiste estado no Redis ou remove se o sinistro foi encerrado/escalado."""
    if state.get("closed") or state.get("escalated"):
        await delete_conversation_state(phone)
    else:
        await save_conversation_state(phone, state)

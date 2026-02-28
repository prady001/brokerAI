"""
Rota de webhook WhatsApp.
Recebe eventos do Evolution API e encaminha para o Agente Orquestrador (M2+).
"""
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.middleware.auth import verify_evolution_webhook

logger = logging.getLogger(__name__)
router = APIRouter()


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
# Handler
# ---------------------------------------------------------------------------

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(
    payload: EvolutionWebhookPayload,
    _: None = Depends(verify_evolution_webhook),
) -> dict:
    """
    Recebe eventos do Evolution API.
    Filtra apenas mensagens recebidas (messages.upsert, fromMe=false).
    Roteamento para agentes será implementado no M2.
    """
    if payload.event != "messages.upsert":
        return {"status": "ignored"}

    if payload.data is None or payload.data.key.fromMe:
        return {"status": "ignored"}

    phone = payload.data.key.remoteJid.replace("@s.whatsapp.net", "")
    name = payload.data.pushName or "Desconhecido"
    text = (payload.data.message.conversation or "") if payload.data.message else ""

    logger.info("Mensagem recebida de %s (%s): %s", phone, name, text[:80])

    return {"status": "received", "phone": phone}

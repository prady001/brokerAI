"""
Rota de webhook WhatsApp.
Recebe eventos do Evolution API e roteia para o agente adequado.
- Mensagens de clientes com renovação ativa → Agente de Renovação
- Demais mensagens → Orquestrador (M2+)
"""
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.renewal.graph import get_renewal_graph
from api.middleware.auth import verify_evolution_webhook
from models.database import Client, get_db
from services.renewal_service import RenewalService

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
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Recebe eventos do Evolution API.
    Filtra apenas mensagens recebidas (messages.upsert, fromMe=false).

    Roteamento:
    - Cliente com renovação ativa (status 'contacted') → Agente de Renovação
    - Demais mensagens → Orquestrador (implementado no M2)
    """
    if payload.event != "messages.upsert":
        return {"status": "ignored"}

    if payload.data is None or payload.data.key.fromMe:
        return {"status": "ignored"}

    phone = payload.data.key.remoteJid.replace("@s.whatsapp.net", "")
    name = payload.data.pushName or "Desconhecido"
    text = (payload.data.message.conversation or "") if payload.data.message else ""

    logger.info("Mensagem recebida de %s (%s): %s", phone, name, text[:80])

    # Tenta localizar o cliente pelo número de telefone
    result = await db.execute(
        sa_select(Client).where(Client.phone_whatsapp == phone)
    )
    client = result.scalar_one_or_none()

    if client is not None:
        # Verifica se há renovação ativa para esse cliente
        renewal_service = RenewalService(db)
        active_renewal = await renewal_service.get_active_renewal_for_client(client.id)  # type: ignore[arg-type]

        if active_renewal is not None:
            logger.info(
                "Roteando para Agente de Renovação: client_id=%s renewal_id=%s",
                client.id,
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

    # Sem roteamento específico — Orquestrador (M2+)
    return {"status": "received", "phone": phone}

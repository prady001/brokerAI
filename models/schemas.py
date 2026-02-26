"""
Schemas Pydantic para validação de request/response da API.
"""
from datetime import datetime
from typing import Any
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Webhook — Z-API (WhatsApp)
# ---------------------------------------------------------------------------

class ZApiMessage(BaseModel):
    """Mensagem recebida via webhook do Z-API."""
    phone: str
    body: str
    messageId: str
    fromMe: bool = False
    momment: int | None = None       # timestamp Unix (Z-API usa esse nome)
    type: str = "text"               # text | image | audio | document | ...
    caption: str | None = None       # legenda de mídia
    mimetype: str | None = None
    mediaUrl: str | None = None


class ZApiWebhookPayload(BaseModel):
    """Payload completo do webhook Z-API."""
    instanceId: str
    messageId: str
    phone: str
    fromMe: bool
    momment: int
    status: str
    chatName: str | None = None
    senderName: str | None = None
    senderPhoto: str | None = None
    text: ZApiMessage | None = None
    image: ZApiMessage | None = None
    audio: ZApiMessage | None = None
    document: ZApiMessage | None = None


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class CommissionCheckResponse(BaseModel):
    status: str
    message: str
    run_date: str = ""


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime = datetime.utcnow()

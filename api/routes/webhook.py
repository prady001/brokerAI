"""
Rota de webhook WhatsApp.
Recebe eventos do Z-API e encaminha para o Agente Orquestrador.
"""
from fastapi import APIRouter, Request, HTTPException
from agents.orchestrator.graph import build_orchestrator_graph

router = APIRouter()


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request) -> dict:
    """
    Recebe mensagens do Z-API via webhook.
    Valida a assinatura ZAPI_WEBHOOK_SECRET e aciona o Orquestrador.
    """
    raise NotImplementedError

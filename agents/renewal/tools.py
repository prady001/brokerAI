"""
Tools do Agente de Renovação.
Todas as tools são Pydantic-tipadas via @tool decorator do LangChain.
Dependências são passadas via RunnableConfig (configurable.renewal_service).
"""
import logging
from typing import Any, Literal
from uuid import UUID

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

import services.notification_service as ns

logger = logging.getLogger(__name__)


def _get_service(config: RunnableConfig, key: str) -> Any:
    svc = (config.get("configurable") or {}).get(key)
    if svc is None:
        raise RuntimeError(f"{key} não configurado. Passe via configurable no RunnableConfig.")
    return svc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
async def get_expiring_policies(days_ahead: list[int], config: RunnableConfig) -> list[dict]:
    """
    Busca apólices ativas com vencimento em exatamente N dias (para cada N em days_ahead).
    Retorna lista de candidatos elegíveis para contato de renovação.
    days_ahead: lista de inteiros, ex: [30, 15, 7, 0]
    """
    renewal_service = _get_service(config, "renewal_service")

    candidates = await renewal_service.get_expiring_policies(days_ahead)
    return [
        {
            "policy_id": str(c.policy_id),
            "client_id": str(c.client_id),
            "client_name": c.client_name,
            "client_phone": c.client_phone,
            "seller_phone": c.seller_phone,
            "policy_number": c.policy_number,
            "item_description": c.item_description,
            "expiry_date": c.expiry_date.isoformat(),
            "days_until_expiry": c.days_until_expiry,
            "renewal_id": str(c.renewal_id) if c.renewal_id else None,
        }
        for c in candidates
    ]


@tool
async def send_renewal_contact(
    renewal_id: str,
    client_phone: str,
    message: str,
    config: RunnableConfig,
) -> dict:
    """
    Envia mensagem de contato de renovação para o cliente via WhatsApp.
    Incrementa o contador de tentativas de contato.
    renewal_id: UUID da renovação (str)
    client_phone: número no formato 5511999999999
    message: texto da mensagem a enviar
    """
    renewal_service = _get_service(config, "renewal_service")

    try:
        success = await ns.send_whatsapp_message(client_phone, message)
    except NotImplementedError:
        logger.warning("Evolution API não configurada — simulando envio para %s", client_phone)
        success = False

    renewal = await renewal_service.register_contact_attempt(UUID(renewal_id))

    logger.info(
        "Contato de renovação enviado: renewal_id=%s contato=%s success=%s",
        renewal_id,
        renewal.contact_count,
        success,
    )
    return {
        "success": success,
        "renewal_id": renewal_id,
        "contact_count": renewal.contact_count,
        "next_contact_at": renewal.next_contact_at.isoformat() if renewal.next_contact_at else None,
    }


@tool
async def register_client_intent(
    renewal_id: str,
    intent: Literal["wants_renewal", "refused", "wants_quote"],
    config: RunnableConfig,
    notes: str | None = None,
) -> dict:
    """
    Registra a intenção do cliente em relação à renovação.
    renewal_id: UUID da renovação (str)
    intent: 'wants_renewal' | 'refused' | 'wants_quote'
    notes: observação livre do cliente (ex: motivo da recusa)
    """
    renewal_service = _get_service(config, "renewal_service")

    status_map = {
        "wants_renewal": "confirmed",
        "refused": "refused",
        "wants_quote": "contacted",
    }
    new_status = status_map[intent]
    renewal = await renewal_service.update_renewal_status(
        UUID(renewal_id), status=new_status, intent=intent, notes=notes
    )
    logger.info("Intenção registrada: renewal_id=%s intent=%s", renewal_id, intent)
    return {
        "renewal_id": renewal_id,
        "status": renewal.status,
        "intent": intent,
        "notes": notes,
    }


@tool
async def notify_seller(
    renewal_id: str,
    seller_phone: str,
    summary_message: str,
) -> dict:
    """
    Envia resumo estruturado ao vendedor responsável pela apólice.
    renewal_id: UUID da renovação (str)
    seller_phone: número do vendedor no formato 5511999999999
    summary_message: texto do resumo a enviar
    """
    try:
        success = await ns.send_whatsapp_message(seller_phone, summary_message)
    except NotImplementedError:
        logger.warning("Evolution API não configurada — notificação ao vendedor simulada")
        success = False

    logger.info(
        "Vendedor notificado: renewal_id=%s seller=%s success=%s", renewal_id, seller_phone, success
    )
    return {
        "success": success,
        "renewal_id": renewal_id,
        "seller_phone": seller_phone,
    }


@tool
async def mark_renewal_status(
    renewal_id: str,
    status: Literal["pending", "contacted", "confirmed", "refused", "no_response", "lost"],
    config: RunnableConfig,
) -> dict:
    """
    Atualiza o status de uma renovação diretamente.
    renewal_id: UUID da renovação (str)
    status: novo status
    """
    renewal_service = _get_service(config, "renewal_service")

    renewal = await renewal_service.update_renewal_status(UUID(renewal_id), status=status)
    logger.info("Status atualizado: renewal_id=%s status=%s", renewal_id, status)
    return {
        "renewal_id": renewal_id,
        "status": renewal.status,
    }

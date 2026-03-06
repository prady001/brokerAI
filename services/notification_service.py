"""
NotificationService — Envio de mensagens via WhatsApp (Evolution API).
"""
import logging

import httpx

from models.config import settings

logger = logging.getLogger(__name__)


async def send_whatsapp_message(phone: str, message: str) -> bool:
    """
    Envia mensagem de texto via Evolution API.
    phone: número no formato 5511999999999 (DDI + DDD + número, sem espaços ou símbolos).
    """
    url = (
        f"{settings.evolution_server_url}/message/sendText"
        f"/{settings.evolution_instance_name}"
    )
    headers = {
        "apikey": settings.evolution_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "number": phone,
        "textMessage": {"text": message},
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info("WhatsApp enviado para %s", phone)
            return True
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Erro HTTP ao enviar WhatsApp para %s: %s %s",
                phone,
                exc.response.status_code,
                exc.response.text[:200],
            )
            return False
        except httpx.RequestError as exc:
            logger.error("Erro de conexão ao enviar WhatsApp para %s: %s", phone, exc)
            return False


async def send_broker_alert(message: str) -> bool:
    """Envia alerta para o número da corretora (Lucimara / BROKER_NOTIFICATION_PHONE)."""
    return await send_whatsapp_message(settings.broker_notification_phone, message)


async def send_email(to: str, subject: str, body: str) -> bool:
    """Envia e-mail via SendGrid como fallback de comunicação (V1+)."""
    logger.warning("send_email não implementado — SendGrid pós-MVP. Para: %s", to)
    return False

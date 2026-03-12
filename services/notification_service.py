"""
NotificationService — Envio de mensagens via WhatsApp (Twilio).
"""
import logging

import httpx

from models.config import settings

logger = logging.getLogger(__name__)

_TWILIO_API_URL = "https://api.twilio.com/2010-04-01/Accounts"


def _whatsapp_number(phone: str) -> str:
    """Converte número armazenado (5511999999999) para formato Twilio (whatsapp:+5511999999999)."""
    if phone.startswith("whatsapp:"):
        return phone
    return f"whatsapp:+{phone}"


async def send_whatsapp_message(phone: str, message: str) -> bool:
    """
    Envia mensagem de texto via Twilio WhatsApp API.
    phone: número no formato 5511999999999 (DDI + DDD + número, sem espaços ou símbolos).
    """
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        logger.warning("Twilio não configurado — mensagem não enviada para %s", phone)
        return False

    url = f"{_TWILIO_API_URL}/{settings.twilio_account_sid}/Messages.json"
    data = {
        "From": settings.twilio_whatsapp_from,
        "To": _whatsapp_number(phone),
        "Body": message,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                url,
                data=data,
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            )
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

"""
NotificationService — Envio de mensagens via WhatsApp (Z-API) e e-mail (SendGrid).
"""
import httpx
from models.config import settings


async def send_whatsapp_message(phone: str, message: str) -> bool:
    """
    Envia mensagem de texto via Z-API para um número WhatsApp.
    phone: número no formato 5511999999999 (DDI + DDD + número).
    """
    raise NotImplementedError


async def send_broker_alert(message: str) -> bool:
    """
    Envia alerta para o número da corretora (BROKER_NOTIFICATION_PHONE).
    Usado para resumos de comissionamento, erros críticos e handoffs.
    """
    raise NotImplementedError


async def send_email(to: str, subject: str, body: str) -> bool:
    """Envia e-mail via SendGrid como fallback de comunicação."""
    raise NotImplementedError

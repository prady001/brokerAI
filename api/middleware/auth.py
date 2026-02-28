"""
Middleware de autenticação.
Valida assinaturas de webhook (Evolution API) e tokens internos (scheduler, admin).
"""
import logging

from fastapi import Header, HTTPException

from models.config import settings

logger = logging.getLogger(__name__)


async def verify_evolution_webhook(apikey: str = Header(None)) -> None:
    """Valida chamadas do Evolution API verificando o header 'apikey'."""
    if apikey != settings.evolution_api_key:
        logger.warning("Webhook recebido com apikey inválida")
        raise HTTPException(status_code=401, detail="Chave de API inválida")


async def verify_internal_token(authorization: str = Header(None)) -> None:
    """Valida token Bearer para rotas internas (scheduler, admin).
    Se internal_api_token estiver vazio, libera acesso (modo desenvolvimento).
    """
    if not settings.internal_api_token:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autorização ausente")
    token = authorization.removeprefix("Bearer ")
    if token != settings.internal_api_token:
        raise HTTPException(status_code=401, detail="Token inválido")

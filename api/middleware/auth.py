"""
Middleware de autenticação.
Valida assinaturas de webhook (Evolution API) e tokens internos (scheduler, admin).
"""
import hmac
import logging
from typing import Annotated

from fastapi import Header, HTTPException

from models.config import settings

logger = logging.getLogger(__name__)


async def verify_evolution_webhook(
    apikey: Annotated[str | None, Header()] = None,
) -> None:
    """Valida chamadas do Evolution API verificando o header 'apikey'."""
    if not apikey or not hmac.compare_digest(apikey, settings.evolution_api_key):
        logger.warning("Webhook recebido com apikey inválida")
        raise HTTPException(status_code=401, detail="Chave de API inválida")


async def verify_internal_token(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Valida token Bearer para rotas internas (scheduler, admin).
    Em ambiente de desenvolvimento sem token configurado, loga aviso e libera acesso.
    Em produção, token é obrigatório.
    """
    if not settings.internal_api_token:
        if settings.environment != "development":
            raise HTTPException(
                status_code=500,
                detail="INTERNAL_API_TOKEN não configurado em ambiente de produção",
            )
        logger.warning(
            "INTERNAL_API_TOKEN não configurado — rotas admin abertas (modo development)"
        )
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autorização ausente")
    token = authorization.removeprefix("Bearer ")
    if not hmac.compare_digest(token, settings.internal_api_token):
        raise HTTPException(status_code=401, detail="Token inválido")

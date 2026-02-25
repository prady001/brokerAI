"""
Middleware de autenticação.
Valida assinaturas de webhook (Z-API) e tokens internos (scheduler).
"""
from fastapi import HTTPException, Header
from models.config import settings


async def verify_zapi_signature(x_zapi_signature: str = Header(None)) -> None:
    """Valida a assinatura HMAC do webhook Z-API."""
    raise NotImplementedError


async def verify_internal_token(authorization: str = Header(None)) -> None:
    """Valida token Bearer para rotas internas (scheduler, admin)."""
    raise NotImplementedError

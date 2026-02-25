"""
NfseService — Emissão de NFS-e via Focus NFe API.
Abstrai a comunicação com o serviço de nota fiscal eletrônica.
"""
import httpx
from models.config import settings


async def emit_nfse(commission: dict) -> dict:
    """
    Emite uma NFS-e para a comissão informada.
    Retorna: { nfse_number: str, pdf_url: str, status: str }

    A NFS-e é emitida com:
    - Prestador: CNPJ da corretora (BROKER_CNPJ)
    - Tomador: CNPJ da seguradora
    - Serviço: intermediação de seguros
    - Valor: net_amount da comissão
    """
    raise NotImplementedError


async def check_nfse_status(nfse_reference: str) -> dict:
    """Consulta o status de uma NFS-e na Focus NFe API."""
    raise NotImplementedError


async def cancel_nfse(nfse_number: str, reason: str) -> bool:
    """Cancela uma NFS-e emitida (se o município permitir)."""
    raise NotImplementedError

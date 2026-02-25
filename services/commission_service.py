"""
CommissionService — CRUD de comissões.
Responsável por persistir e consultar dados de comissão extraídos dos portais.
"""


async def save_commission(commission: dict) -> str:
    """Salva uma comissão no banco. Retorna o UUID gerado."""
    raise NotImplementedError


async def get_commissions_by_date(date: str) -> list[dict]:
    """Retorna todas as comissões de uma data de execução."""
    raise NotImplementedError


async def mark_nfse_emitted(commission_id: str, nfse_number: str, pdf_url: str) -> bool:
    """Atualiza o status da comissão para nfse_emitted."""
    raise NotImplementedError


async def mark_nfse_failed(commission_id: str, error: str) -> bool:
    """Registra falha na emissão da NFS-e."""
    raise NotImplementedError

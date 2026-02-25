"""
ClaimService — CRUD de sinistros.
"""


async def create_claim(claim_data: dict) -> str:
    """Cria um sinistro no banco. Retorna o UUID gerado."""
    raise NotImplementedError


async def get_claim(claim_id: str) -> dict:
    """Retorna dados de um sinistro pelo ID."""
    raise NotImplementedError


async def update_claim_status(claim_id: str, status: str) -> bool:
    """Atualiza o status de um sinistro."""
    raise NotImplementedError


async def assign_to_broker(claim_id: str, user_id: str) -> bool:
    """Atribui o sinistro a um corretor humano."""
    raise NotImplementedError


async def close_claim(claim_id: str) -> bool:
    """Encerra o sinistro e registra closed_at."""
    raise NotImplementedError

"""
PolicyService — Consulta de apólices importadas do Agger.
No MVP, a carteira é carregada via importação de CSV exportado do Agger.
"""


async def import_from_csv(file_path: str) -> int:
    """
    Importa apólices de um CSV exportado do Agger.
    Retorna o número de registros importados.
    """
    raise NotImplementedError


async def get_policy_by_plate(plate: str) -> dict | None:
    """Busca apólice pela placa do veículo."""
    raise NotImplementedError


async def get_policy_by_number(policy_number: str) -> dict | None:
    """Busca apólice pelo número."""
    raise NotImplementedError


async def get_active_policies() -> list[dict]:
    """Retorna todas as apólices com status ativo."""
    raise NotImplementedError

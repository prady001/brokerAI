"""
InsurerPortalService — Seleção e invocação de adapters por seguradora.
Seleciona automaticamente ApiAdapter ou RpaAdapter com base na configuração
da seguradora (integration_type: 'api' | 'rpa').
"""
from agents.commissioning.portal_adapters.api_adapter import ApiAdapter
from agents.commissioning.portal_adapters.rpa_adapter import RpaAdapter
from agents.commissioning.portal_adapters.base import InsurerAdapter


def get_adapter(insurer: dict, credentials: dict) -> InsurerAdapter:
    """
    Retorna o adapter correto para a seguradora.
    insurer: { id, code, integration_type, two_fa_method, ... }
    """
    if insurer["integration_type"] == "api":
        return ApiAdapter(insurer["id"], credentials)
    return RpaAdapter(insurer["id"], credentials)


async def load_insurer_credentials(insurer_id: str) -> dict:
    """
    Carrega credenciais da seguradora do arquivo criptografado
    (INSURER_CREDENTIALS_PATH + INSURER_CREDENTIALS_KEY).
    Nunca retorna credenciais em logs ou histórico de LLM.
    """
    raise NotImplementedError


async def fetch_commissions(insurer: dict) -> list[dict]:
    """
    Seleciona o adapter, faz login, extrai comissões e encerra sessão.
    Centraliza tratamento de erros e logging de auditoria.
    """
    raise NotImplementedError

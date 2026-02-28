"""
Adapter para seguradoras com API REST (ex: Bradesco Seguros).
Usa httpx para chamadas autenticadas via OAuth.
"""
from agents.commissioning.portal_adapters.base import InsurerAdapter


class ApiAdapter(InsurerAdapter):

    async def login(self) -> bool:
        """Obtém token OAuth com client_id e client_secret da seguradora."""
        raise NotImplementedError

    async def fetch_commissions(self) -> list[dict]:
        """Chama endpoint de extratos de comissão da API da seguradora."""
        raise NotImplementedError

    async def logout(self) -> None:
        """Revoga token OAuth se necessário."""
        raise NotImplementedError

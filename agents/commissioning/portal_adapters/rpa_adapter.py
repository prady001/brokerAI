"""
Adapter RPA para seguradoras sem API REST.
Usa Playwright em modo headless para navegar o portal e extrair comissões.
"""
from agents.commissioning.portal_adapters.base import InsurerAdapter


class RpaAdapter(InsurerAdapter):

    async def login(self) -> bool:
        """
        Abre o portal em headless, preenche login e senha,
        e resolve 2FA se necessário (TOTP, e-mail ou SMS).
        """
        raise NotImplementedError

    async def fetch_commissions(self) -> list[dict]:
        """
        Navega até a seção de extratos de comissão,
        extrai os dados da tabela ou baixa o arquivo CSV/PDF.
        """
        raise NotImplementedError

    async def logout(self) -> None:
        """Fecha o contexto do browser."""
        raise NotImplementedError

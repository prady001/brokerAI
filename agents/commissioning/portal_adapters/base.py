"""
Classe abstrata para adapters de portais de seguradoras.
Todos os adapters devem implementar esta interface.
"""
from abc import ABC, abstractmethod


class InsurerAdapter(ABC):

    def __init__(self, insurer_id: str, credentials: dict) -> None:
        self.insurer_id = insurer_id
        self.credentials = credentials

    @abstractmethod
    async def login(self) -> bool:
        """Realiza login no portal. Retorna True se bem-sucedido."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_commissions(self) -> list[dict]:
        """Extrai dados de comissão disponíveis. Retorna lista de comissões."""
        raise NotImplementedError

    @abstractmethod
    async def logout(self) -> None:
        """Encerra a sessão no portal."""
        raise NotImplementedError

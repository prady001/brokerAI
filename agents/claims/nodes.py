"""
Nós do grafo do Agente de Sinistros.
"""
from agents.claims.tools import ClaimsState


def collect_info_node(state: ClaimsState) -> ClaimsState:
    """Coleta dados mínimos do sinistro do cliente via conversa."""
    raise NotImplementedError


def classify_node(state: ClaimsState) -> ClaimsState:
    """Classifica o sinistro em simples ou grave."""
    raise NotImplementedError


def open_claim_node(state: ClaimsState) -> ClaimsState:
    """Abre o chamado na seguradora pelo canal adequado (API ou WhatsApp)."""
    raise NotImplementedError


def relay_node(state: ClaimsState) -> ClaimsState:
    """
    Aguarda resposta da seguradora e repassa ao cliente.
    Persiste estado em Redis enquanto aguarda.
    """
    raise NotImplementedError


def escalate_node(state: ClaimsState) -> ClaimsState:
    """Notifica corretor humano e informa cliente sobre o handoff."""
    raise NotImplementedError


def close_node(state: ClaimsState) -> ClaimsState:
    """Encerra o caso e persiste histórico no PostgreSQL."""
    raise NotImplementedError

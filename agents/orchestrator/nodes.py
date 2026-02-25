"""
Nós do Agente Orquestrador.
"""


def detect_intent_node(state: dict) -> dict:
    """
    Usa LLM para classificar a intenção da mensagem:
    'claim' | 'faq' | 'unknown'
    """
    raise NotImplementedError


def faq_handler_node(state: dict) -> dict:
    """Responde dúvidas gerais usando LLM com contexto da corretora."""
    raise NotImplementedError


def human_handoff_node(state: dict) -> dict:
    """Notifica corretor humano e informa o cliente sobre o handoff."""
    raise NotImplementedError

"""
Nós do Agente Orquestrador.
"""


def load_conversation_node(state: dict) -> dict:
    """
    Verifica no Redis se existe uma conversa de sinistro ativa para o número do cliente.

    Se existe:
    - Carrega o ClaimsState do Redis
    - Define state['has_active_conversation'] = True
    - Define state['conversation_id'] com o ID da conversa existente

    Se não existe:
    - Define state['has_active_conversation'] = False

    Chave Redis: f"conversation:{client_phone}"
    """
    raise NotImplementedError


def detect_intent_node(state: dict) -> dict:
    """
    Usa LLM para classificar a intenção da mensagem em:
    'claim' | 'faq' | 'unknown'

    Popula state['intent'] e state['confidence'].
    Se confidence < 0.6, roteia para 'unknown' independente do resultado.
    """
    raise NotImplementedError


def faq_handler_node(state: dict) -> dict:
    """
    Responde dúvidas gerais usando LLM com contexto da corretora:
    cobertura, vencimento de apólice, como acionar seguro, boleto, etc.

    Não tem acesso a dados do cliente — apenas ao knowledge base da corretora.
    """
    raise NotImplementedError


def human_handoff_node(state: dict) -> dict:
    """
    Para mensagens não identificadas ou fora do escopo:
    1. Notifica o corretor humano com a mensagem original e o número do cliente
    2. Envia mensagem ao cliente informando que um corretor vai retornar em breve
    """
    raise NotImplementedError

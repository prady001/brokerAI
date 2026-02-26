"""
Nós do grafo do Agente de Sinistros.
Cada nó recebe e retorna ClaimsState.
"""
from agents.claims.tools import ClaimsState


def collect_info_node(state: ClaimsState) -> ClaimsState:
    """
    Conversa com o cliente para coletar os dados mínimos do sinistro:
    tipo, placa/apólice, localização e descrição.
    Recebe fotos e documentos e faz upload para S3.
    """
    raise NotImplementedError


def classify_node(state: ClaimsState) -> ClaimsState:
    """
    Classifica o sinistro em 'simple' ou 'grave' com base no tipo e descrição.
    Popula state['severity'].
    """
    raise NotImplementedError


def open_claim_node(state: ClaimsState) -> ClaimsState:
    """
    Abre o chamado no portal da seguradora pelo canal configurado
    (portal_chat, portal_notes ou API).
    Popula state['insurer_thread_id'], state['insurer_channel'] e state['waiting_since'].
    Informa o cliente que o chamado foi aberto e que atualizações serão enviadas.
    """
    raise NotImplementedError


def check_updates_node(state: ClaimsState) -> ClaimsState:
    """
    Verifica o portal da seguradora em busca de atualizações no chamado.
    Incrementa state['poll_count'] e atualiza state['last_polled_at'].
    Popula state['update_status']: 'has_update' | 'no_update' | 'closed'.
    Se closed: popula state['closed'] = True.
    """
    raise NotImplementedError


def relay_to_client_node(state: ClaimsState) -> ClaimsState:
    """
    Envia a atualização recebida da seguradora ao cliente via WhatsApp.
    Formata a mensagem de forma clara e empática.
    Se o chamado foi encerrado pela seguradora, atualiza state['closed'] = True.
    """
    raise NotImplementedError


def escalate_node(state: ClaimsState) -> ClaimsState:
    """
    Para sinistros graves:
    1. Notifica o corretor humano com resumo estruturado (cliente, apólice, tipo, docs)
    2. Informa o cliente que um corretor vai assumir o caso
    3. Marca state['escalated'] = True
    """
    raise NotImplementedError


def close_node(state: ClaimsState) -> ClaimsState:
    """
    Encerra o sinistro:
    1. Envia mensagem de encerramento ao cliente
    2. Persiste histórico completo no PostgreSQL via store_claim_history
    3. Remove estado do Redis
    4. Marca state['closed'] = True e state['status'] = 'closed'
    """
    raise NotImplementedError

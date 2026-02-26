"""
Nós do grafo do Agente de Comissionamento.
Cada nó recebe e retorna CommissioningState.
"""
from agents.commissioning.tools import CommissioningState


def load_insurers_node(state: CommissioningState) -> CommissioningState:
    """Carrega lista de seguradoras ativas do banco."""
    raise NotImplementedError


def fetch_commission_node(state: CommissioningState) -> CommissioningState:
    """
    Itera sobre insurers_pending, acessa cada portal e extrai comissões.
    Move seguradoras para insurers_done ou insurers_failed conforme resultado.
    """
    raise NotImplementedError


def consolidate_node(state: CommissioningState) -> CommissioningState:
    """Agrupa todas as comissões extraídas em relatório consolidado."""
    raise NotImplementedError


def emit_nfse_node(state: CommissioningState) -> CommissioningState:
    """Emite NFS-e para cada comissão em commissions via Focus NFe API."""
    raise NotImplementedError


def alert_failures_node(state: CommissioningState) -> CommissioningState:
    """
    Para cada seguradora em insurers_failed:
    1. Chama alert_missing_commission com o motivo do erro
    2. Notifica o corretor via WhatsApp sobre a falha de acesso

    Não bloqueia o fluxo — seguradoras com falha são registradas em errors
    e o relatório consolidado é enviado mesmo assim.
    """
    raise NotImplementedError


def send_summary_node(state: CommissioningState) -> CommissioningState:
    """Envia resumo diário para a corretora via WhatsApp."""
    raise NotImplementedError

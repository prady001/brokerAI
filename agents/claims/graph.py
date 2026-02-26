"""
Grafo LangGraph do Agente de Sinistros.

Padrão relay com loop de acompanhamento:
- Sinistros simples: coleta → abre na seguradora → verifica portal → relay → (loop até fechar)
- Sinistros graves: coleta → escala para humano com resumo estruturado

O nó check_updates é re-acionado periodicamente (CRON ou webhook do WhatsApp)
enquanto o sinistro estiver aberto. O estado persiste em Redis entre acionamentos.
"""
from langgraph.graph import StateGraph, END
from agents.claims.nodes import (
    collect_info_node,
    classify_node,
    open_claim_node,
    check_updates_node,
    relay_to_client_node,
    escalate_node,
    close_node,
)
from agents.claims.tools import ClaimsState


def build_claims_graph() -> StateGraph:
    graph = StateGraph(ClaimsState)

    graph.add_node("collect_info",    collect_info_node)
    graph.add_node("classify",        classify_node)
    graph.add_node("open_claim",      open_claim_node)
    graph.add_node("check_updates",   check_updates_node)
    graph.add_node("relay_to_client", relay_to_client_node)
    graph.add_node("escalate",        escalate_node)
    graph.add_node("close",           close_node)

    graph.set_entry_point("collect_info")

    graph.add_edge("collect_info", "classify")

    # Roteamento por severidade
    graph.add_conditional_edges("classify", route_by_severity, {
        "simple": "open_claim",
        "grave":  "escalate",
    })

    graph.add_edge("open_claim", "check_updates")

    # Loop de acompanhamento: verifica portal → relay → verifica se fechou → loop
    graph.add_conditional_edges("check_updates", route_by_update_status, {
        "has_update": "relay_to_client",   # nova atualização da seguradora
        "no_update":  END,                 # sem novidade — aguarda próximo ciclo (CRON)
        "closed":     "close",             # seguradora encerrou o chamado
    })

    graph.add_conditional_edges("relay_to_client", route_after_relay, {
        "closed": "close",            # seguradora confirmou encerramento
        "open":   "check_updates",    # sinistro ainda aberto → volta ao loop
    })

    graph.add_edge("escalate", END)
    graph.add_edge("close",    END)

    return graph.compile()


def route_by_severity(state: ClaimsState) -> str:
    return state.get("severity", "grave")


def route_by_update_status(state: ClaimsState) -> str:
    """
    Decide o próximo passo após verificar o portal da seguradora.
    Retorna: 'has_update' | 'no_update' | 'closed'
    """
    return state.get("update_status", "no_update")


def route_after_relay(state: ClaimsState) -> str:
    """
    Após fazer relay ao cliente, verifica se o sinistro foi encerrado.
    Retorna: 'closed' | 'open'
    """
    return "closed" if state.get("closed") else "open"

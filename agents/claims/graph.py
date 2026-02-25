"""
Grafo LangGraph do Agente de Sinistros.
Padrão relay: coleta → classifica → abre na seguradora → relay atualizações → encerra.
Sinistros graves são escalados imediatamente para humano.
"""
from langgraph.graph import StateGraph, END
from agents.claims.nodes import (
    collect_info_node,
    classify_node,
    open_claim_node,
    relay_node,
    escalate_node,
    close_node,
)
from agents.claims.tools import ClaimsState


def build_claims_graph() -> StateGraph:
    graph = StateGraph(ClaimsState)

    graph.add_node("collect_info", collect_info_node)
    graph.add_node("classify", classify_node)
    graph.add_node("open_claim", open_claim_node)
    graph.add_node("relay", relay_node)
    graph.add_node("escalate", escalate_node)
    graph.add_node("close", close_node)

    graph.set_entry_point("collect_info")

    graph.add_edge("collect_info", "classify")

    graph.add_conditional_edges("classify", route_by_severity, {
        "simple": "open_claim",
        "grave":  "escalate",
    })

    graph.add_edge("open_claim", "relay")
    graph.add_edge("relay", "close")
    graph.add_edge("escalate", END)
    graph.add_edge("close", END)

    return graph.compile()


def route_by_severity(state: ClaimsState) -> str:
    return state.get("severity", "grave")

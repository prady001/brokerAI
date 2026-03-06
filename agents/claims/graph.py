"""
Grafo LangGraph do Agente de Sinistros.

Fluxo principal (sinistro simples):
  entry_router → collect_info (multi-turn) → classify → open_claim
               → check_updates (no_update MVP) → END

Fluxo grave:
  entry_router → collect_info → classify → escalate → END

Retomada (mensagem de follow-up com sinistro já aberto):
  entry_router → check_updates → END

O estado persiste em Redis entre acionamentos do webhook.
"""
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agents.claims.nodes import (
    check_updates_node,
    classify_node,
    close_node,
    collect_info_node,
    entry_router_node,
    escalate_node,
    open_claim_node,
    relay_to_client_node,
    route_after_relay,
    route_by_severity,
    route_by_update_status,
    route_collection_status,
    route_entry,
)
from agents.claims.tools import ClaimsState


def build_claims_graph() -> CompiledStateGraph:
    graph = StateGraph(ClaimsState)

    graph.add_node("entry_router",    entry_router_node)
    graph.add_node("collect_info",    collect_info_node)
    graph.add_node("classify",        classify_node)
    graph.add_node("open_claim",      open_claim_node)
    graph.add_node("check_updates",   check_updates_node)
    graph.add_node("relay_to_client", relay_to_client_node)
    graph.add_node("escalate",        escalate_node)
    graph.add_node("close",           close_node)

    graph.set_entry_point("entry_router")

    # Roteamento de entrada pelo status atual do sinistro
    graph.add_conditional_edges("entry_router", route_entry, {
        "collect_info":   "collect_info",
        "check_updates":  "check_updates",
        "end":            END,
    })

    # collect_info: continua apenas quando todos os dados foram coletados
    graph.add_conditional_edges("collect_info", route_collection_status, {
        "complete":   "classify",
        "incomplete": END,          # envia pergunta ao cliente e aguarda próxima mensagem
    })

    # Roteamento por severidade
    graph.add_conditional_edges("classify", route_by_severity, {
        "simple": "open_claim",
        "grave":  "escalate",
    })

    graph.add_edge("open_claim", "check_updates")

    # Acompanhamento: MVP sempre retorna "no_update" (polling não implementado).
    # "has_update" e "closed" são caminhos reservados para V1 (Playwright portal).
    # Ver docstring de check_updates_node para detalhes.
    graph.add_conditional_edges("check_updates", route_by_update_status, {
        "has_update": "relay_to_client",   # TODO(V1): habilitado com polling de portal
        "no_update":  END,
        "closed":     "close",             # TODO(V1): habilitado com polling de portal
    })

    graph.add_conditional_edges("relay_to_client", route_after_relay, {
        "closed": "close",
        "open":   END,
    })

    graph.add_edge("escalate", END)
    graph.add_edge("close",    END)

    return graph.compile()

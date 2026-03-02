"""
Grafo LangGraph do Agente de Renovação.

Dois fluxos no mesmo grafo:
  - mode=cron:      check_expiring_policies → send_contacts → update_statuses
  - mode=whatsapp:  process_client_response → notify_sellers → update_statuses
"""
from typing import Literal
from typing_extensions import TypedDict

from langgraph.graph import END, StateGraph

from agents.renewal.nodes import (
    check_expiring_policies,
    notify_sellers,
    process_client_response,
    send_contacts,
    update_statuses,
)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class RenewalState(TypedDict, total=False):
    mode: Literal["cron", "whatsapp"]
    policies_to_contact: list[dict]
    contacts_sent: list[dict]
    client_response: str | None       # quando acionado por WhatsApp
    renewal_id: str | None            # quando acionado por WhatsApp
    intent: str | None
    notifications_sent: list[dict]
    errors: list[str]


# ---------------------------------------------------------------------------
# Roteador de entrada
# ---------------------------------------------------------------------------

def _route_by_mode(state: RenewalState) -> str:
    """Determina o fluxo com base no modo de acionamento."""
    return "whatsapp" if state.get("mode") == "whatsapp" else "cron"


# ---------------------------------------------------------------------------
# Grafo
# ---------------------------------------------------------------------------

def build_renewal_graph() -> StateGraph:
    graph = StateGraph(RenewalState)

    # Nós
    graph.add_node("check_expiring_policies", check_expiring_policies)
    graph.add_node("send_contacts", send_contacts)
    graph.add_node("process_client_response", process_client_response)
    graph.add_node("notify_sellers", notify_sellers)
    graph.add_node("update_statuses", update_statuses)

    # Roteamento de entrada
    graph.set_conditional_entry_point(
        _route_by_mode,
        {
            "cron": "check_expiring_policies",
            "whatsapp": "process_client_response",
        },
    )

    # Fluxo cron
    graph.add_edge("check_expiring_policies", "send_contacts")
    graph.add_edge("send_contacts", "update_statuses")

    # Fluxo whatsapp
    graph.add_edge("process_client_response", "notify_sellers")
    graph.add_edge("notify_sellers", "update_statuses")

    # Fim comum
    graph.add_edge("update_statuses", END)

    return graph


renewal_graph = build_renewal_graph().compile()

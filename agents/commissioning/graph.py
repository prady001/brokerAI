"""
Grafo LangGraph do Agente de Comissionamento.

Ciclo diário (08:00 BRT):
1. Carrega lista de seguradoras configuradas
2. Para cada seguradora: acessa portal (API, RPA ou e-mail), extrai comissões
3. Consolida relatório com todas as seguradoras
4. Emite NFS-e para cada comissão confirmada
5. Alerta sobre seguradoras com falha de acesso
6. Envia resumo consolidado via WhatsApp para a corretora
"""
from langgraph.graph import StateGraph, END
from agents.commissioning.nodes import (
    load_insurers_node,
    fetch_commission_node,
    consolidate_node,
    emit_nfse_node,
    alert_failures_node,
    send_summary_node,
)
from agents.commissioning.tools import CommissioningState


def build_commissioning_graph() -> StateGraph:
    graph = StateGraph(CommissioningState)

    graph.add_node("load_insurers",    load_insurers_node)
    graph.add_node("fetch_commission", fetch_commission_node)
    graph.add_node("consolidate",      consolidate_node)
    graph.add_node("emit_nfse",        emit_nfse_node)
    graph.add_node("alert_failures",   alert_failures_node)
    graph.add_node("send_summary",     send_summary_node)

    graph.set_entry_point("load_insurers")

    graph.add_edge("load_insurers",    "fetch_commission")
    graph.add_edge("fetch_commission", "consolidate")
    graph.add_edge("consolidate",      "emit_nfse")
    graph.add_edge("emit_nfse",        "alert_failures")  # alerta falhas antes do resumo
    graph.add_edge("alert_failures",   "send_summary")
    graph.add_edge("send_summary",     END)

    return graph.compile()

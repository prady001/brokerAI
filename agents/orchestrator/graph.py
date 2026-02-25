"""
Grafo LangGraph do Agente Orquestrador.
Roteia mensagens WhatsApp para o agente correto.
"""
from langgraph.graph import StateGraph, END
from agents.orchestrator.nodes import detect_intent_node, human_handoff_node, faq_handler_node
from agents.claims.graph import build_claims_graph


class OrchestratorState(dict):
    pass


def build_orchestrator_graph() -> StateGraph:
    graph = StateGraph(OrchestratorState)

    graph.add_node("detect_intent", detect_intent_node)
    graph.add_node("claims_agent", build_claims_graph())
    graph.add_node("faq_handler", faq_handler_node)
    graph.add_node("human_handoff", human_handoff_node)

    graph.set_entry_point("detect_intent")

    graph.add_conditional_edges("detect_intent", route_by_intent, {
        "claim":   "claims_agent",
        "faq":     "faq_handler",
        "unknown": "human_handoff",
    })

    graph.add_edge("claims_agent", END)
    graph.add_edge("faq_handler", END)
    graph.add_edge("human_handoff", END)

    return graph.compile()


def route_by_intent(state: OrchestratorState) -> str:
    return state.get("intent", "unknown")

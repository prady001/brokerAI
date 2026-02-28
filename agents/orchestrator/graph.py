"""
Grafo LangGraph do Agente Orquestrador.

Fluxo:
1. Carrega conversa ativa do Redis pelo número do cliente (se existir)
2. Se há conversa ativa → retoma o agente de sinistros com o estado existente
3. Se não há conversa ativa → detecta intenção → roteia para claims / faq / humano
"""
from typing import TypedDict

from langgraph.graph import END, StateGraph

from agents.claims.graph import build_claims_graph
from agents.orchestrator.nodes import (
    detect_intent_node,
    faq_handler_node,
    human_handoff_node,
    load_conversation_node,
)


class OrchestratorState(TypedDict):
    # Mensagem recebida
    message: str
    client_phone: str
    received_at: str

    # Conversa existente (carregada do Redis)
    conversation_id: str
    has_active_conversation: bool

    # Roteamento
    intent: str             # "claim" | "faq" | "unknown"
    confidence: float       # 0.0 - 1.0


def build_orchestrator_graph() -> StateGraph:
    graph = StateGraph(OrchestratorState)

    graph.add_node("load_conversation", load_conversation_node)
    graph.add_node("detect_intent",     detect_intent_node)
    graph.add_node("claims_agent",      build_claims_graph())
    graph.add_node("faq_handler",       faq_handler_node)
    graph.add_node("human_handoff",     human_handoff_node)

    graph.set_entry_point("load_conversation")

    # Se há conversa ativa → retoma sinistro. Se não → detecta intenção.
    graph.add_conditional_edges("load_conversation", route_by_active_conversation, {
        "active":   "claims_agent",   # retoma conversa de sinistro em andamento
        "inactive": "detect_intent",  # nova mensagem, detecta intenção
    })

    graph.add_conditional_edges("detect_intent", route_by_intent, {
        "claim":   "claims_agent",
        "faq":     "faq_handler",
        "unknown": "human_handoff",
    })

    graph.add_edge("claims_agent",  END)
    graph.add_edge("faq_handler",   END)
    graph.add_edge("human_handoff", END)

    return graph.compile()


def route_by_active_conversation(state: OrchestratorState) -> str:
    return "active" if state.get("has_active_conversation") else "inactive"


def route_by_intent(state: OrchestratorState) -> str:
    return state.get("intent", "unknown")

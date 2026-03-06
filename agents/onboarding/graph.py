"""
Grafo LangGraph do Agente de Onboarding.

Fluxo push (corretor inicia com /cadastrar):
  entry_router → contact_client → collect_client (multi-turn) → collect_policy (multi-turn)
               → confirm → handle_confirmation → register → welcome → notify_seller → END

Fluxo pull (cliente chega sem cadastro):
  entry_router → collect_client (multi-turn) → collect_policy (multi-turn)
               → confirm → handle_confirmation → register → welcome → notify_seller → END

Falha após max retries:
  register → escalate → END

Cancelamento:
  cancel_onboarding → END

O estado persiste em Redis entre acionamentos do webhook.
"""
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agents.onboarding.nodes import (
    cancel_onboarding_node,
    collect_client_node,
    collect_policy_node,
    confirm_node,
    contact_client_node,
    entry_router_node,
    escalate_node,
    handle_confirmation_node,
    notify_seller_node,
    register_node,
    route_after_register,
    route_client_collection,
    route_confirmation,
    route_entry,
    route_policy_collection,
    welcome_node,
)
from agents.onboarding.state import OnboardingState


def build_onboarding_graph() -> CompiledStateGraph:
    graph = StateGraph(OnboardingState)

    graph.add_node("entry_router",        entry_router_node)
    graph.add_node("contact_client",      contact_client_node)
    graph.add_node("collect_client",      collect_client_node)
    graph.add_node("collect_policy",      collect_policy_node)
    graph.add_node("confirm",             confirm_node)
    graph.add_node("handle_confirmation", handle_confirmation_node)
    graph.add_node("register",            register_node)
    graph.add_node("welcome",             welcome_node)
    graph.add_node("notify_seller",       notify_seller_node)
    graph.add_node("escalate",            escalate_node)
    graph.add_node("cancel_onboarding",   cancel_onboarding_node)

    graph.set_entry_point("entry_router")

    # Roteamento de entrada pelo status atual
    graph.add_conditional_edges("entry_router", route_entry, {
        "contact_client":      "contact_client",
        "collect_client":      "collect_client",
        "collect_policy":      "collect_policy",
        "handle_confirmation": "handle_confirmation",
        "cancel":              "cancel_onboarding",
        "end":                 END,
    })

    # Após contato proativo (push): coleta dados do cliente
    graph.add_edge("contact_client", END)  # aguarda resposta do cliente

    # collect_client: continua quando todos os dados pessoais estão completos
    graph.add_conditional_edges("collect_client", route_client_collection, {
        "complete":   "collect_policy",
        "incomplete": END,  # aguarda próxima mensagem
    })

    # collect_policy: continua quando todos os dados da apólice estão completos
    graph.add_conditional_edges("collect_policy", route_policy_collection, {
        "complete":   "confirm",
        "incomplete": END,  # aguarda próxima mensagem
    })

    # confirm: envia resumo e aguarda confirmação
    graph.add_edge("confirm", END)  # aguarda "sim" ou "não" do cliente

    # handle_confirmation: processa a resposta de confirmação
    graph.add_conditional_edges("handle_confirmation", route_confirmation, {
        "confirmed": "register",
        "rejected":  END,   # volta para coleta após reset do estado
        "unclear":   END,   # pede esclarecimento
    })

    # register: cria cliente e apólice no banco
    graph.add_conditional_edges("register", route_after_register, {
        "welcome":  "welcome",
        "escalate": "escalate",
    })

    # welcome → notify_seller → END (fluxo de sucesso)
    graph.add_edge("welcome",       "notify_seller")
    graph.add_edge("notify_seller", END)

    graph.add_edge("escalate",        END)
    graph.add_edge("cancel_onboarding", END)

    return graph.compile()

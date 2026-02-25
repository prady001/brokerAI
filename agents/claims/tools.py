"""
Tools e State Schema do Agente de Sinistros.
Padrão relay: recebe do cliente, repassa para seguradora, devolve ao cliente.
"""
from typing import TypedDict
from langchain_core.tools import tool


class ClaimsState(TypedDict):
    conversation_id: str
    client_id: str
    client_phone: str
    policy_id: str
    claim_id: str
    claim_type: str
    severity: str                   # "simple" | "grave"
    claim_info: dict
    insurer_channel: str
    insurer_thread_id: str
    status: str
    messages: list[dict]
    escalated: bool
    closed: bool


@tool
def classify_claim(claim_type: str, description: str) -> dict:
    """
    Classifica o sinistro em simples ou grave.
    Simples: guincho, pane, troca de pneu, vidros, pequenos danos.
    Grave: colisão com terceiros, furto/roubo, incêndio, acidente com vítima.
    Retorna: { severity: 'simple' | 'grave', auto_resolve: bool }
    """
    raise NotImplementedError


@tool
def collect_claim_info(conversation_id: str) -> dict:
    """
    Coleta dados mínimos: tipo do sinistro, localização, placa ou número da apólice.
    """
    raise NotImplementedError


@tool
def open_claim_at_insurer(claim_id: str, insurer_id: str, claim_info: dict) -> dict:
    """
    Abre chamado na seguradora via canal configurado (API ou WhatsApp relay).
    Retorna: { thread_id: str, channel: str, opened_at: str }
    """
    raise NotImplementedError


@tool
def relay_update_to_client(conversation_id: str, update: str) -> bool:
    """
    Repassa resposta ou atualização da seguradora ao cliente via WhatsApp.
    """
    raise NotImplementedError


@tool
def escalate_to_broker(claim_id: str, reason: str, summary: dict) -> bool:
    """
    Notifica corretor humano com resumo estruturado do sinistro.
    summary contém: cliente, apólice, tipo, descrição e timeline.
    """
    raise NotImplementedError


@tool
def store_claim_history(claim_id: str) -> bool:
    """
    Persiste histórico completo da conversa no PostgreSQL ao encerrar.
    """
    raise NotImplementedError

"""
Tools e State Schema do Agente de Sinistros.
Todas as tools são Pydantic-tipadas — sem free-form function calling.
"""
from typing import TypedDict
from langchain_core.tools import tool


class ClaimsState(TypedDict):
    # Identificação
    conversation_id: str
    client_id: str
    client_phone: str
    policy_id: str              # identificado pela placa ou número da apólice
    claim_id: str

    # Dados do sinistro
    claim_type: str             # tipo: guincho, vidro, colisão, furto, residencial, etc.
    severity: str               # "simple" | "grave"
    claim_info: dict            # dados coletados: localização, descrição, placa, etc.
    documents: list[str]        # URLs S3 de fotos e documentos enviados pelo cliente

    # Integração com a seguradora
    insurer_id: str             # qual seguradora
    insurer_channel: str        # "portal_chat" | "portal_notes" | "api" | "whatsapp"
    insurer_portal_url: str     # URL do portal para acompanhamento
    insurer_thread_id: str      # ID do chamado aberto na seguradora

    # Loop de acompanhamento
    update_status: str          # "has_update" | "no_update" | "closed"
    last_update: str            # último update recebido da seguradora
    poll_count: int             # quantas vezes verificou o portal sem novidade
    last_polled_at: str         # ISO datetime da última verificação
    waiting_since: str          # ISO datetime de quando o sinistro foi aberto

    # Status geral
    status: str                 # status atual do caso
    messages: list[dict]        # histórico completo de mensagens
    escalated: bool             # se foi escalado para humano
    closed: bool


@tool
def classify_claim(claim_type: str, description: str) -> dict:
    """
    Classifica o sinistro em simples ou grave.

    Simples: guincho, pane, troca de pneu, vidros, pequenos danos,
             assistência 24h, alagamento parcial, furto de acessório.
    Grave: colisão com terceiros, furto/roubo total, incêndio,
           acidente com vítima, dano estrutural grave.

    Retorna: { severity: 'simple' | 'grave', auto_resolve: bool }
    """
    raise NotImplementedError


@tool
def collect_claim_info(conversation_id: str) -> dict:
    """
    Coleta via conversa WhatsApp os dados mínimos para abrir o sinistro:
    - Tipo do sinistro
    - Placa do veículo ou número da apólice
    - Localização atual (para guincho/assistência)
    - Descrição breve do ocorrido

    Retorna os dados estruturados coletados.
    """
    raise NotImplementedError


@tool
def upload_document(conversation_id: str, media_url: str, doc_type: str) -> str:
    """
    Faz upload de foto ou documento enviado pelo cliente para o S3.

    doc_type: 'photo_damage' | 'cnh' | 'crlv' | 'bo' | 'other'
    Retorna: URL pública do arquivo no S3.
    """
    raise NotImplementedError


@tool
def open_claim_at_insurer(claim_id: str, insurer_id: str, claim_info: dict) -> dict:
    """
    Abre chamado na seguradora via canal configurado por seguradora:
    - portal_chat: abre via chat do portal (RPA)
    - portal_notes: insere nota no portal (RPA)
    - api: chamada REST à API da seguradora

    Retorna: { thread_id: str, channel: str, opened_at: str }
    """
    raise NotImplementedError


@tool
def check_insurer_portal_for_updates(claim_id: str, insurer_id: str, thread_id: str) -> dict:
    """
    Verifica o portal da seguradora em busca de novas notas, mensagens ou
    mudanças de status no chamado.

    Acessa o portal via RPA (Playwright) e lê o status atual do chamado.

    Retorna:
    {
        update_status: 'has_update' | 'no_update' | 'closed',
        update_text: str,           # conteúdo da atualização, se houver
        new_status: str,            # novo status no portal da seguradora
        checked_at: str             # ISO datetime da verificação
    }
    """
    raise NotImplementedError


@tool
def relay_update_to_client(conversation_id: str, update: str) -> bool:
    """
    Repassa atualização da seguradora ao cliente via WhatsApp.
    Formata a mensagem de forma clara e empática antes de enviar.
    """
    raise NotImplementedError


@tool
def escalate_to_broker(claim_id: str, reason: str, summary: dict) -> bool:
    """
    Notifica corretor humano com resumo estruturado do sinistro grave.

    summary contém: cliente, apólice, tipo, descrição, localização,
                    documentos recebidos e timeline da conversa.
    """
    raise NotImplementedError


@tool
def store_claim_history(claim_id: str) -> bool:
    """
    Persiste histórico completo da conversa no PostgreSQL ao encerrar.
    Migra estado do Redis para banco permanente (retenção SUSEP 5 anos).
    """
    raise NotImplementedError

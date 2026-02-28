"""
Tools e State Schema do Agente de Comissionamento.
Todas as tools são Pydantic-tipadas — sem free-form function calling.
"""
from typing import TypedDict

from langchain_core.tools import tool


class CommissioningState(TypedDict):
    run_date: str
    insurers_pending: list[str]
    insurers_done: list[str]
    insurers_failed: list[str]
    commissions: list[dict]

    # Formato e arquivos brutos por seguradora
    commission_format: str          # "pdf" | "spreadsheet" | "email" | "api"
    raw_files: list[str]            # URLs S3 dos PDFs/planilhas baixados antes do parse

    nfse_emitted: list[dict]
    nfse_failed: list[dict]
    report_sent: bool
    errors: list[dict]


@tool
def fetch_commission_data(insurer_id: str) -> dict:
    """
    Acessa o portal da seguradora e extrai dados de comissão disponíveis.
    Usa InsurerPortalService que seleciona automaticamente API ou RPA.
    Retorna: { insurer: str, commissions: list[dict], extracted_at: str }
    """
    raise NotImplementedError


@tool
def handle_2fa(insurer_id: str, method: str) -> bool:
    """
    Resolve autenticação 2FA para o portal da seguradora.
    method: 'totp' | 'email' | 'sms'
    """
    raise NotImplementedError


@tool
def consolidate_report(commissions: list[dict]) -> dict:
    """
    Agrupa comissões de todas as seguradoras em relatório único.
    Retorna: { total: str, by_insurer: list[dict], date: str }
    """
    raise NotImplementedError


@tool
def emit_nfse(commission: dict) -> dict:
    """
    Emite NFS-e via Focus NFe API para uma comissão confirmada.
    Retorna: { nfse_number: str, pdf_url: str, status: str }
    """
    raise NotImplementedError


@tool
def send_daily_summary(report: dict, nfse_results: list[dict]) -> bool:
    """
    Envia resumo consolidado do dia via WhatsApp para a corretora.
    """
    raise NotImplementedError


@tool
def alert_missing_commission(insurer_id: str, reason: str) -> bool:
    """
    Notifica corretora sobre seguradora sem dados ou com erro de acesso.
    """
    raise NotImplementedError

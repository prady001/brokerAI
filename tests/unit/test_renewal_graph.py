"""
Testes unitários para o grafo LangGraph do Agente de Renovação.
Testa os fluxos mode=cron e mode=whatsapp com mocks.
Dependências são passadas via state (_renewal_service, _llm).
"""
import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.renewal.graph import build_renewal_graph
from services.renewal_service import RenewalCandidate, RenewalDetail

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_candidate(**kwargs):
    defaults = dict(
        policy_id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        client_name="Maria Souza",
        client_phone="5511999990002",
        seller_phone="5511988880002",
        policy_number="POL-002",
        item_description="Honda Fit / DEF5678",
        expiry_date=date.today() + timedelta(days=30),
        days_until_expiry=30,
        renewal_id=None,
    )
    defaults.update(kwargs)
    return RenewalCandidate(**defaults)


def _make_renewal_mock(**kwargs):
    m = MagicMock()
    m.id = uuid.uuid4()
    m.status = kwargs.get("status", "contacted")
    m.contact_count = kwargs.get("contact_count", 1)
    m.next_contact_at = kwargs.get("next_contact_at", None)
    m.seller_phone = kwargs.get("seller_phone", "5511988880002")
    m.expiry_date = kwargs.get("expiry_date", date.today() + timedelta(days=30))
    m.intent_notes = None
    m.client_intent = None
    return m


def _make_detail(renewal_mock=None, **kwargs):
    rm = renewal_mock or _make_renewal_mock(**kwargs)
    return RenewalDetail(
        renewal=rm,
        client_name=kwargs.get("client_name", "Maria Souza"),
        client_phone=kwargs.get("client_phone", "5511999990002"),
        policy_number=kwargs.get("policy_number", "POL-002"),
        item_description=kwargs.get("item_description", "Honda Fit / DEF5678"),
        insurer_name=kwargs.get("insurer_name", "Porto Seguro"),
    )


# ---------------------------------------------------------------------------
# Fluxo cron
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cron_flow_finds_and_sends_contacts():
    """Fluxo cron: encontra apólices → envia mensagens → atualiza status."""
    candidate = _make_candidate()
    renewal_mock = _make_renewal_mock()

    mock_service = AsyncMock()
    mock_service.get_expiring_policies.return_value = [candidate]
    mock_service.get_or_create_renewal.return_value = renewal_mock
    mock_service.register_contact_attempt.return_value = renewal_mock
    mock_service.mark_overdue_renewals.return_value = []

    with patch("services.notification_service.send_whatsapp_message", new_callable=AsyncMock, return_value=True):
        graph = build_renewal_graph().compile()
        result = await graph.ainvoke({
            "mode": "cron",
            "_renewal_service": mock_service,
            "_llm": None,
            "policies_to_contact": [],
            "contacts_sent": [],
            "errors": [],
        })

    assert len(result["contacts_sent"]) == 1
    assert result["contacts_sent"][0]["client_phone"] == "5511999990002"
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_cron_flow_no_policies():
    """Fluxo cron com nenhuma apólice para contato."""
    mock_service = AsyncMock()
    mock_service.get_expiring_policies.return_value = []
    mock_service.mark_overdue_renewals.return_value = []

    graph = build_renewal_graph().compile()
    result = await graph.ainvoke({
        "mode": "cron",
        "_renewal_service": mock_service,
        "_llm": None,
        "policies_to_contact": [],
        "contacts_sent": [],
        "errors": [],
    })

    assert result["contacts_sent"] == []
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_cron_flow_simulates_when_evolution_unavailable():
    """Fluxo cron não deve lançar exceção quando Evolution API não está configurada."""
    candidate = _make_candidate()
    renewal_mock = _make_renewal_mock()

    mock_service = AsyncMock()
    mock_service.get_expiring_policies.return_value = [candidate]
    mock_service.get_or_create_renewal.return_value = renewal_mock
    mock_service.register_contact_attempt.return_value = renewal_mock
    mock_service.mark_overdue_renewals.return_value = []

    with patch("services.notification_service.send_whatsapp_message", new_callable=AsyncMock, side_effect=NotImplementedError):
        graph = build_renewal_graph().compile()
        result = await graph.ainvoke({
            "mode": "cron",
            "_renewal_service": mock_service,
            "_llm": None,
            "policies_to_contact": [],
            "contacts_sent": [],
            "errors": [],
        })

    assert len(result["contacts_sent"]) == 1
    assert result["contacts_sent"][0]["sent"] is False


# ---------------------------------------------------------------------------
# Fluxo whatsapp
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_whatsapp_flow_wants_renewal():
    """Fluxo whatsapp: cliente quer renovar → notifica vendedor → confirma."""
    renewal_id = str(uuid.uuid4())
    renewal_mock = _make_renewal_mock(status="confirmed")
    detail = _make_detail(renewal_mock=renewal_mock)

    mock_service = AsyncMock()
    mock_service.get_renewal_with_details.return_value = detail
    mock_service.update_renewal_status.return_value = renewal_mock
    mock_service.mark_overdue_renewals.return_value = []

    mock_llm = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = "wants_renewal"
    mock_llm.ainvoke.return_value = mock_response

    with patch("services.notification_service.send_whatsapp_message", new_callable=AsyncMock, return_value=True):
        graph = build_renewal_graph().compile()
        result = await graph.ainvoke({
            "mode": "whatsapp",
            "client_response": "Sim, pode renovar!",
            "renewal_id": renewal_id,
            "_renewal_service": mock_service,
            "_llm": mock_llm,
            "notifications_sent": [],
            "errors": [],
        })

    assert result["intent"] == "wants_renewal"
    assert len(result["notifications_sent"]) == 1


@pytest.mark.asyncio
async def test_whatsapp_flow_refused():
    """Fluxo whatsapp: cliente recusa → notifica vendedor."""
    renewal_id = str(uuid.uuid4())
    renewal_mock = _make_renewal_mock(status="refused")
    detail = _make_detail(renewal_mock=renewal_mock)

    mock_service = AsyncMock()
    mock_service.get_renewal_with_details.return_value = detail
    mock_service.update_renewal_status.return_value = renewal_mock
    mock_service.mark_overdue_renewals.return_value = []

    mock_llm = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = "refused"
    mock_llm.ainvoke.return_value = mock_response

    with patch("services.notification_service.send_whatsapp_message", new_callable=AsyncMock, return_value=True):
        graph = build_renewal_graph().compile()
        result = await graph.ainvoke({
            "mode": "whatsapp",
            "client_response": "Não quero mais, está muito caro.",
            "renewal_id": renewal_id,
            "_renewal_service": mock_service,
            "_llm": mock_llm,
            "notifications_sent": [],
            "errors": [],
        })

    assert result["intent"] == "refused"


@pytest.mark.asyncio
async def test_whatsapp_flow_needs_review_on_invalid_intent():
    """Fallback de intenção inválida deve ser needs_review em vez de wants_renewal."""
    renewal_id = str(uuid.uuid4())
    renewal_mock = _make_renewal_mock(status="contacted")
    detail = _make_detail(renewal_mock=renewal_mock)

    mock_service = AsyncMock()
    mock_service.get_renewal_with_details.return_value = detail
    mock_service.update_renewal_status.return_value = renewal_mock
    mock_service.mark_overdue_renewals.return_value = []

    mock_llm = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = "maybe_later"
    mock_llm.ainvoke.return_value = mock_response

    with patch("services.notification_service.send_whatsapp_message", new_callable=AsyncMock, return_value=True):
        graph = build_renewal_graph().compile()
        result = await graph.ainvoke({
            "mode": "whatsapp",
            "client_response": "Vou pensar...",
            "renewal_id": renewal_id,
            "_renewal_service": mock_service,
            "_llm": mock_llm,
            "notifications_sent": [],
            "errors": [],
        })

    assert result["intent"] == "needs_review"


@pytest.mark.asyncio
async def test_whatsapp_flow_needs_review_on_llm_error():
    """Erro no LLM deve resultar em needs_review como fallback seguro."""
    renewal_id = str(uuid.uuid4())
    renewal_mock = _make_renewal_mock(status="contacted")
    detail = _make_detail(renewal_mock=renewal_mock)

    mock_service = AsyncMock()
    mock_service.get_renewal_with_details.return_value = detail
    mock_service.update_renewal_status.return_value = renewal_mock
    mock_service.mark_overdue_renewals.return_value = []

    mock_llm = AsyncMock()
    mock_llm.ainvoke.side_effect = RuntimeError("LLM offline")

    with patch("services.notification_service.send_whatsapp_message", new_callable=AsyncMock, return_value=True):
        graph = build_renewal_graph().compile()
        result = await graph.ainvoke({
            "mode": "whatsapp",
            "client_response": "Sim quero",
            "renewal_id": renewal_id,
            "_renewal_service": mock_service,
            "_llm": mock_llm,
            "notifications_sent": [],
            "errors": [],
        })

    assert result["intent"] == "needs_review"

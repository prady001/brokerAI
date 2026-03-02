"""
Testes unitários para as tools do Agente de Renovação.
"""
import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.renewal import tools as renewal_tools
from services.renewal_service import RenewalCandidate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_renewal_mock(status="contacted", contact_count=1, next_contact_at=None):
    m = MagicMock()
    m.id = uuid.uuid4()
    m.status = status
    m.contact_count = contact_count
    m.next_contact_at = next_contact_at
    m.client_intent = None
    m.intent_notes = None
    return m


def _make_candidate(**kwargs):
    defaults = dict(
        policy_id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        client_name="João Silva",
        client_phone="5511999990001",
        seller_phone="5511988880001",
        policy_number="POL-001",
        item_description="Toyota Yaris / ABC1234",
        expiry_date=date.today() + timedelta(days=30),
        days_until_expiry=30,
        renewal_id=None,
    )
    defaults.update(kwargs)
    return RenewalCandidate(**defaults)


# ---------------------------------------------------------------------------
# get_expiring_policies
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_expiring_policies_returns_candidates():
    mock_service = AsyncMock()
    mock_service.get_expiring_policies.return_value = [_make_candidate()]

    renewal_tools.inject_services(mock_service, None)

    result = await renewal_tools.get_expiring_policies.ainvoke({"days_ahead": [30]})
    assert len(result) == 1
    assert result[0]["days_until_expiry"] == 30
    assert result[0]["client_phone"] == "5511999990001"


@pytest.mark.asyncio
async def test_get_expiring_policies_empty():
    mock_service = AsyncMock()
    mock_service.get_expiring_policies.return_value = []

    renewal_tools.inject_services(mock_service, None)

    result = await renewal_tools.get_expiring_policies.ainvoke({"days_ahead": [30]})
    assert result == []


# ---------------------------------------------------------------------------
# send_renewal_contact
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_renewal_contact_success():
    renewal_id = str(uuid.uuid4())
    mock_service = AsyncMock()
    mock_service.register_contact_attempt.return_value = _make_renewal_mock(contact_count=1)

    renewal_tools.inject_services(mock_service, object())

    with patch("services.notification_service.send_whatsapp_message", new_callable=AsyncMock, return_value=True):
        result = await renewal_tools.send_renewal_contact.ainvoke({
            "renewal_id": renewal_id,
            "client_phone": "5511999990001",
            "message": "Olá, sua apólice vence em 30 dias.",
        })

    assert result["success"] is True
    assert result["contact_count"] == 1


@pytest.mark.asyncio
async def test_send_renewal_contact_simulates_when_evolution_unavailable():
    """Deve funcionar mesmo quando Evolution API não está configurada (NotImplementedError)."""
    renewal_id = str(uuid.uuid4())
    mock_service = AsyncMock()
    mock_service.register_contact_attempt.return_value = _make_renewal_mock(contact_count=1)

    renewal_tools.inject_services(mock_service, object())

    with patch("services.notification_service.send_whatsapp_message", new_callable=AsyncMock, side_effect=NotImplementedError):
        with pytest.raises(NotImplementedError):
            await renewal_tools.send_renewal_contact.ainvoke({
                "renewal_id": renewal_id,
                "client_phone": "5511999990001",
                "message": "Teste",
            })


# ---------------------------------------------------------------------------
# register_client_intent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_client_intent_wants_renewal():
    renewal_id = str(uuid.uuid4())
    mock_service = AsyncMock()
    mock_service.update_renewal_status.return_value = _make_renewal_mock(status="confirmed")

    renewal_tools.inject_services(mock_service, None)

    result = await renewal_tools.register_client_intent.ainvoke({
        "renewal_id": renewal_id,
        "intent": "wants_renewal",
        "notes": None,
    })

    assert result["intent"] == "wants_renewal"
    mock_service.update_renewal_status.assert_called_once()
    call_kwargs = mock_service.update_renewal_status.call_args
    assert call_kwargs.kwargs["status"] == "confirmed"


@pytest.mark.asyncio
async def test_register_client_intent_refused_with_notes():
    renewal_id = str(uuid.uuid4())
    mock_service = AsyncMock()
    mock_service.update_renewal_status.return_value = _make_renewal_mock(status="refused")

    renewal_tools.inject_services(mock_service, None)

    result = await renewal_tools.register_client_intent.ainvoke({
        "renewal_id": renewal_id,
        "intent": "refused",
        "notes": "Preço muito alto",
    })

    assert result["notes"] == "Preço muito alto"
    call_kwargs = mock_service.update_renewal_status.call_args
    assert call_kwargs.kwargs["status"] == "refused"


# ---------------------------------------------------------------------------
# notify_seller
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_notify_seller_sends_message():
    renewal_id = str(uuid.uuid4())
    renewal_tools.inject_services(MagicMock(), object())

    with patch("services.notification_service.send_whatsapp_message", new_callable=AsyncMock, return_value=True):
        result = await renewal_tools.notify_seller.ainvoke({
            "renewal_id": renewal_id,
            "seller_phone": "5511988880001",
            "summary_message": "✅ RENOVAÇÃO CONFIRMADA\nCliente: João",
        })

    assert result["success"] is True
    assert result["seller_phone"] == "5511988880001"


# ---------------------------------------------------------------------------
# mark_renewal_status
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mark_renewal_status():
    renewal_id = str(uuid.uuid4())
    mock_service = AsyncMock()
    mock_service.update_renewal_status.return_value = _make_renewal_mock(status="no_response")

    renewal_tools.inject_services(mock_service, None)

    result = await renewal_tools.mark_renewal_status.ainvoke({
        "renewal_id": renewal_id,
        "status": "no_response",
    })

    assert result["status"] == "no_response"

"""
Testes unitários do Agente de Onboarding (M3).
Usa mocks para LLM e serviços externos — sem dependências de rede ou banco.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.onboarding.nodes import (
    cancel_onboarding_node,
    collect_client_node,
    collect_policy_node,
    confirm_node,
    contact_client_node,
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
from services.onboarding_service import (
    format_cpf,
    normalize_policy_type,
    validate_cpf,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_state(**kwargs) -> dict:
    """Estado mínimo válido para o agente de onboarding."""
    base: dict = {
        "conversation_id": "conv-001",
        "client_phone": "5517999990001",
        "push_mode": False,
        "client_data": {},
        "policy_data": {},
        "client_data_complete": False,
        "policy_data_complete": False,
        "validation_errors": [],
        "retry_count": 0,
        "client_id": "",
        "policy_id": "",
        "registered": False,
        "failed": False,
        "messages": [],
        "status": "",
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# validate_cpf
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cpf,expected", [
    ("529.982.247-25", True),
    ("52998224725",    True),
    ("111.111.111-11", False),   # todos iguais
    ("000.000.000-00", False),
    ("123.456.789-00", False),   # dígitos errados
    ("123",            False),   # curto demais
])
def test_validate_cpf(cpf: str, expected: bool) -> None:
    assert validate_cpf(cpf) == expected


# ---------------------------------------------------------------------------
# format_cpf
# ---------------------------------------------------------------------------

def test_format_cpf_with_digits() -> None:
    assert format_cpf("52998224725") == "529.982.247-25"


def test_format_cpf_already_formatted() -> None:
    assert format_cpf("529.982.247-25") == "529.982.247-25"


# ---------------------------------------------------------------------------
# normalize_policy_type
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("auto",       "auto"),
    ("carro",      "auto"),
    ("moto",       "auto"),
    ("vida",       "life"),
    ("residência", "home"),
    ("casa",       "home"),
    ("viagem",     "travel"),
    ("empresarial","business"),
    ("outro",      "auto"),  # fallback
])
def test_normalize_policy_type(raw: str, expected: str) -> None:
    assert normalize_policy_type(raw) == expected


# ---------------------------------------------------------------------------
# route_entry
# ---------------------------------------------------------------------------

def test_route_entry_registered() -> None:
    state = make_state(status="registered")
    assert route_entry(state) == "end"


def test_route_entry_failed() -> None:
    state = make_state(status="failed")
    assert route_entry(state) == "end"


def test_route_entry_awaiting_confirmation() -> None:
    state = make_state(status="awaiting_confirmation")
    assert route_entry(state) == "handle_confirmation"


def test_route_entry_collecting_policy() -> None:
    state = make_state(status="collecting_policy")
    assert route_entry(state) == "collect_policy"


def test_route_entry_push_new() -> None:
    state = make_state(push_mode=True, status="")
    assert route_entry(state) == "contact_client"


def test_route_entry_pull_new() -> None:
    state = make_state(push_mode=False, status="")
    assert route_entry(state) == "collect_client"


def test_route_entry_cancel() -> None:
    state = make_state(status="cancel")
    assert route_entry(state) == "cancel"


# ---------------------------------------------------------------------------
# route_client_collection / route_policy_collection
# ---------------------------------------------------------------------------

def test_route_client_collection_complete() -> None:
    assert route_client_collection(make_state(client_data_complete=True)) == "complete"


def test_route_client_collection_incomplete() -> None:
    assert route_client_collection(make_state(client_data_complete=False)) == "incomplete"


def test_route_policy_collection_complete() -> None:
    assert route_policy_collection(make_state(policy_data_complete=True)) == "complete"


def test_route_policy_collection_incomplete() -> None:
    assert route_policy_collection(make_state(policy_data_complete=False)) == "incomplete"


# ---------------------------------------------------------------------------
# route_confirmation
# ---------------------------------------------------------------------------

def test_route_confirmation_confirmed() -> None:
    assert route_confirmation({"confirmation_status": "confirmed"}) == "confirmed"


def test_route_confirmation_rejected() -> None:
    assert route_confirmation({"confirmation_status": "rejected"}) == "rejected"


def test_route_confirmation_unclear() -> None:
    assert route_confirmation({"confirmation_status": "unclear"}) == "unclear"


# ---------------------------------------------------------------------------
# route_after_register
# ---------------------------------------------------------------------------

def test_route_after_register_success() -> None:
    state = make_state(registered=True)
    assert route_after_register(state) == "welcome"


def test_route_after_register_failure() -> None:
    state = make_state(failed=True)
    assert route_after_register(state) == "escalate"


def test_route_after_register_fallback() -> None:
    state = make_state(registered=False, failed=False)
    assert route_after_register(state) == "escalate"


# ---------------------------------------------------------------------------
# contact_client_node (push mode)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_contact_client_node_sends_greeting() -> None:
    state = make_state(push_mode=True)
    with patch("agents.onboarding.nodes.notification_service") as mock_notif:
        mock_notif.send_whatsapp_message = AsyncMock()
        result = await contact_client_node(state)

    mock_notif.send_whatsapp_message.assert_awaited_once()
    assert result["status"] == "collecting_client"
    assert any(m["role"] == "assistant" for m in result["messages"])


# ---------------------------------------------------------------------------
# collect_client_node
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_collect_client_node_incomplete_asks_question() -> None:
    state = make_state(messages=[{"role": "user", "content": "Olá"}])

    llm_extract_response = MagicMock()
    llm_extract_response.content = json.dumps({
        "full_name": None,
        "cpf": None,
        "email": None,
        "missing_fields": ["full_name", "cpf"],
    })
    llm_question_response = MagicMock()
    llm_question_response.content = "Pode me dizer seu nome completo?"

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(side_effect=[llm_extract_response, llm_question_response])

    with (
        patch("agents.onboarding.nodes._get_llm", return_value=mock_llm),
        patch("agents.onboarding.nodes.notification_service") as mock_notif,
    ):
        mock_notif.send_whatsapp_message = AsyncMock()
        result = await collect_client_node(state)

    assert result["client_data_complete"] is False
    assert result["status"] == "collecting_client"
    mock_notif.send_whatsapp_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_collect_client_node_complete() -> None:
    state = make_state(messages=[
        {"role": "user", "content": "Meu nome é João Silva, CPF 529.982.247-25"},
    ])

    llm_response = MagicMock()
    llm_response.content = json.dumps({
        "full_name": "João Silva",
        "cpf": "529.982.247-25",
        "email": None,
        "missing_fields": [],
    })

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(return_value=llm_response)

    with patch("agents.onboarding.nodes._get_llm", return_value=mock_llm):
        result = await collect_client_node(state)

    assert result["client_data_complete"] is True
    assert result["client_data"]["full_name"] == "João Silva"


@pytest.mark.asyncio
async def test_collect_client_node_invalid_cpf() -> None:
    """CPF inválido deve ser descartado e o campo adicionado a missing_fields."""
    state = make_state(messages=[
        {"role": "user", "content": "João Silva, CPF 111.111.111-11"},
    ])

    llm_extract_response = MagicMock()
    llm_extract_response.content = json.dumps({
        "full_name": "João Silva",
        "cpf": "111.111.111-11",
        "email": None,
        "missing_fields": [],
    })
    llm_question_response = MagicMock()
    llm_question_response.content = "Esse CPF parece inválido. Pode conferir?"

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(side_effect=[llm_extract_response, llm_question_response])

    with (
        patch("agents.onboarding.nodes._get_llm", return_value=mock_llm),
        patch("agents.onboarding.nodes.notification_service") as mock_notif,
    ):
        mock_notif.send_whatsapp_message = AsyncMock()
        result = await collect_client_node(state)

    assert result["client_data_complete"] is False
    assert result["client_data"]["cpf"] is None


# ---------------------------------------------------------------------------
# collect_policy_node
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_collect_policy_node_complete() -> None:
    state = make_state(
        status="collecting_policy",
        client_data_complete=True,
        messages=[
            {"role": "user", "content": "Porto Seguro, apólice 12345, Toyota Yaris ABC1234, vence 31/12/2026"},
        ],
    )

    llm_response = MagicMock()
    llm_response.content = json.dumps({
        "insurer": "Porto Seguro",
        "policy_type": "auto",
        "item_description": "Toyota Yaris ABC1234",
        "policy_number": "12345",
        "end_date": "31/12/2026",
        "start_date": None,
        "missing_fields": [],
    })

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(return_value=llm_response)

    with patch("agents.onboarding.nodes._get_llm", return_value=mock_llm):
        result = await collect_policy_node(state)

    assert result["policy_data_complete"] is True
    assert result["policy_data"]["insurer"] == "Porto Seguro"
    assert result["policy_data"]["policy_number"] == "12345"


# ---------------------------------------------------------------------------
# confirm_node
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_confirm_node_sends_summary() -> None:
    state = make_state(
        client_data={"full_name": "João Silva", "cpf": "529.982.247-25"},
        policy_data={
            "insurer": "Porto Seguro",
            "policy_number": "12345",
            "item_description": "Toyota Yaris",
            "end_date": "31/12/2026",
        },
    )
    with patch("agents.onboarding.nodes.notification_service") as mock_notif:
        mock_notif.send_whatsapp_message = AsyncMock()
        result = await confirm_node(state)

    mock_notif.send_whatsapp_message.assert_awaited_once()
    assert result["status"] == "awaiting_confirmation"


# ---------------------------------------------------------------------------
# handle_confirmation_node
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("user_message,expected_status", [
    ("sim", "confirmed"),
    ("Sim!", "confirmed"),
    ("ok", "confirmed"),
    ("confirmo", "confirmed"),
    ("não", "rejected"),
    ("nao", "rejected"),
    ("corrigir", "rejected"),
])
async def test_handle_confirmation_node(user_message: str, expected_status: str) -> None:
    state = make_state(
        messages=[{"role": "user", "content": user_message}],
        status="awaiting_confirmation",
    )
    with patch("agents.onboarding.nodes.notification_service") as mock_notif:
        mock_notif.send_whatsapp_message = AsyncMock()
        result = await handle_confirmation_node(state)

    assert result["confirmation_status"] == expected_status


# ---------------------------------------------------------------------------
# register_node
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_node_success() -> None:
    state = make_state(
        client_data={"full_name": "João Silva", "cpf": "529.982.247-25"},
        policy_data={
            "insurer": "Porto Seguro",
            "policy_type": "auto",
            "item_description": "Toyota Yaris",
            "policy_number": "12345",
            "end_date": "31/12/2026",
            "start_date": None,
        },
    )

    with (
        patch("agents.onboarding.nodes.get_or_create_insurer", AsyncMock(return_value="insurer-uuid")),
        patch("agents.onboarding.nodes.create_client", AsyncMock(return_value="client-uuid")),
        patch("agents.onboarding.nodes.create_policy", AsyncMock(return_value="policy-uuid")),
    ):
        result = await register_node(state)

    assert result["registered"] is True
    assert result["client_id"] == "client-uuid"
    assert result["policy_id"] == "policy-uuid"
    assert result["status"] == "registered"


@pytest.mark.asyncio
async def test_register_node_failure_escalates_after_max_retries() -> None:
    state = make_state(
        retry_count=2,  # já está na última tentativa
        client_data={"full_name": "João", "cpf": "529.982.247-25"},
        policy_data={"insurer": "Porto", "policy_number": "X", "item_description": "Y", "end_date": "01/01/2027"},
    )

    with patch("agents.onboarding.nodes.get_or_create_insurer", AsyncMock(side_effect=Exception("DB error"))):
        result = await register_node(state)

    assert result["failed"] is True
    assert result["status"] == "failed"


# ---------------------------------------------------------------------------
# welcome_node / notify_seller_node
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_welcome_node_sends_message() -> None:
    state = make_state()
    with patch("agents.onboarding.nodes.notification_service") as mock_notif:
        mock_notif.send_whatsapp_message = AsyncMock()
        await welcome_node(state)

    mock_notif.send_whatsapp_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_notify_seller_node_sends_alert() -> None:
    state = make_state(
        client_data={"full_name": "João Silva", "cpf": "529.982.247-25"},
        policy_data={"insurer": "Porto", "policy_number": "X", "item_description": "Y", "end_date": "01/01/2027"},
    )
    with patch("agents.onboarding.nodes.notification_service") as mock_notif:
        mock_notif.send_broker_alert = AsyncMock()
        await notify_seller_node(state)

    mock_notif.send_broker_alert.assert_awaited_once()


# ---------------------------------------------------------------------------
# cancel_onboarding_node
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cancel_onboarding_node() -> None:
    state = make_state(status="collecting_client")
    with patch("agents.onboarding.nodes.notification_service") as mock_notif:
        mock_notif.send_whatsapp_message = AsyncMock()
        result = await cancel_onboarding_node(state)

    mock_notif.send_whatsapp_message.assert_awaited_once()
    assert result["failed"] is True
    assert result["status"] == "failed"

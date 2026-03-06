"""
Testes unitários do Agente de Sinistros (M2).
Usa mocks para LLM e serviços externos — sem dependências de rede ou banco.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.claims.nodes import (
    classify_node,
    collect_info_node,
    escalate_node,
    open_claim_node,
    route_collection_status,
    route_entry,
)
from services.claim_service import normalize_claim_type

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_state(**kwargs) -> dict:
    """Estado mínimo válido para o agente de sinistros."""
    base: dict = {
        "conversation_id": "conv-001",
        "client_id": "client-001",
        "client_phone": "5517999990001",
        "client_name": "João Silva",
        "messages": [],
        "status": "",
        "claim_info": {},
        "claim_info_complete": False,
        "claim_id": "",
        "policy_id": "",
        "insurer_id": "",
        "severity": "",
        "update_status": "",
        "last_update": "",
        "poll_count": 0,
        "escalated": False,
        "closed": False,
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# normalize_claim_type
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("input_type,expected", [
    ("guincho", "assistance"),
    ("Guincho", "assistance"),
    ("PANE SECA", "assistance"),
    ("vidro", "glass"),
    ("Para-brisa", "glass"),
    ("Colisão", "collision"),
    ("batida", "collision"),
    ("furto", "theft"),
    ("ROUBO", "theft"),
    ("incêndio", "fire"),
    ("outro qualquer", "other"),
])
def test_normalize_claim_type(input_type, expected):
    assert normalize_claim_type(input_type) == expected


# ---------------------------------------------------------------------------
# route_entry
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("status,expected", [
    ("", "collect_info"),
    ("collecting", "collect_info"),
    ("waiting_insurer", "check_updates"),
    ("in_progress", "check_updates"),
    ("escalated", "end"),
    ("closed", "end"),
])
def test_route_entry(status, expected):
    state = make_state(status=status)
    assert route_entry(state) == expected


# ---------------------------------------------------------------------------
# route_collection_status
# ---------------------------------------------------------------------------

def test_route_collection_complete():
    state = make_state(claim_info_complete=True)
    assert route_collection_status(state) == "complete"


def test_route_collection_incomplete():
    state = make_state(claim_info_complete=False)
    assert route_collection_status(state) == "incomplete"


# ---------------------------------------------------------------------------
# classify_node — classificação por regras (sem LLM)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("claim_type,expected_severity", [
    ("guincho", "simple"),
    ("pane", "simple"),
    ("vidro", "simple"),
    ("assistência", "simple"),
    ("colisão", "grave"),
    ("furto", "grave"),
    ("roubo", "grave"),
    ("incêndio", "grave"),
])
async def test_classify_by_rules(claim_type, expected_severity):
    state = make_state(claim_info={"claim_type": claim_type, "description": "teste"})
    result = await classify_node(state)
    assert result["severity"] == expected_severity


@pytest.mark.asyncio
async def test_classify_unknown_uses_llm():
    """Tipos não reconhecidos pelas regras devem usar o LLM (default: grave)."""
    mock_response = MagicMock()
    mock_response.content = '{"severity": "grave"}'

    with patch("agents.claims.nodes._get_llm") as mock_llm:
        llm_instance = AsyncMock()
        llm_instance.ainvoke.return_value = mock_response
        mock_llm.return_value = llm_instance

        state = make_state(claim_info={"claim_type": "dano_estranho", "description": "algo estranho"})
        result = await classify_node(state)
        assert result["severity"] == "grave"


# ---------------------------------------------------------------------------
# collect_info_node
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_collect_info_complete():
    """Quando todas as informações estão presentes, marca como completo."""
    extract_response = MagicMock()
    extract_response.content = """{
        "claim_type": "guincho",
        "identifier": "ABC1234",
        "location": "Rodovia SP-310 km 150",
        "description": "Carro parou de funcionar",
        "missing_fields": []
    }"""

    with patch("agents.claims.nodes._get_llm") as mock_llm, \
         patch("agents.claims.nodes.notification_service.send_whatsapp_message", new_callable=AsyncMock):
        llm_instance = AsyncMock()
        llm_instance.ainvoke.return_value = extract_response
        mock_llm.return_value = llm_instance

        state = make_state(messages=[
            {"role": "user", "content": "Meu carro quebrou na SP-310, preciso de guincho. Placa ABC1234"}
        ])
        result = await collect_info_node(state)

        assert result["claim_info_complete"] is True
        assert result["claim_info"]["claim_type"] == "guincho"
        assert result["claim_info"]["identifier"] == "ABC1234"


@pytest.mark.asyncio
async def test_collect_info_missing_fields_sends_question():
    """Quando falta informação, deve enviar pergunta ao cliente."""
    extract_response = MagicMock()
    extract_response.content = """{
        "claim_type": "guincho",
        "identifier": null,
        "location": null,
        "description": null,
        "missing_fields": ["identifier", "location"]
    }"""
    question_response = MagicMock()
    question_response.content = "Qual é a placa do seu veículo?"

    with patch("agents.claims.nodes._get_llm") as mock_llm, \
         patch("agents.claims.nodes.notification_service.send_whatsapp_message",
               new_callable=AsyncMock) as mock_send:
        llm_instance = AsyncMock()
        llm_instance.ainvoke.side_effect = [extract_response, question_response]
        mock_llm.return_value = llm_instance

        state = make_state(messages=[{"role": "user", "content": "preciso de guincho"}])
        result = await collect_info_node(state)

        assert result["claim_info_complete"] is False
        assert result["status"] == "collecting"
        mock_send.assert_called_once_with("5517999990001", "Qual é a placa do seu veículo?")


# ---------------------------------------------------------------------------
# open_claim_node
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_open_claim_creates_db_record_and_notifies():
    """Deve criar sinistro no banco, alertar Lucimara e confirmar ao cliente."""
    with patch("agents.claims.nodes.claim_service.get_policy_by_identifier",
               new_callable=AsyncMock, return_value=None), \
         patch("agents.claims.nodes.claim_service.create_claim",
               new_callable=AsyncMock, return_value="claim-uuid-0001") as mock_create, \
         patch("agents.claims.nodes.notification_service.send_broker_alert",
               new_callable=AsyncMock) as mock_broker, \
         patch("agents.claims.nodes.notification_service.send_whatsapp_message",
               new_callable=AsyncMock) as mock_client:

        state = make_state(
            severity="simple",
            claim_info={
                "claim_type": "guincho",
                "identifier": "ABC1234",
                "location": "Rodovia SP-310",
                "description": "Pane seca",
            },
        )
        result = await open_claim_node(state)

        mock_create.assert_called_once()
        mock_broker.assert_called_once()
        mock_client.assert_called_once()
        assert result["claim_id"] == "claim-uuid-0001"
        assert result["status"] == "waiting_insurer"


# ---------------------------------------------------------------------------
# escalate_node
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_escalate_grave_claim():
    """Sinistro grave deve notificar Lucimara com alerta urgente."""
    with patch("agents.claims.nodes.claim_service.create_claim",
               new_callable=AsyncMock, return_value="claim-grave-001") as mock_create, \
         patch("agents.claims.nodes.claim_service.update_claim_status",
               new_callable=AsyncMock), \
         patch("agents.claims.nodes.notification_service.send_broker_alert",
               new_callable=AsyncMock) as mock_broker, \
         patch("agents.claims.nodes.notification_service.send_whatsapp_message",
               new_callable=AsyncMock) as mock_client:

        state = make_state(
            claim_info={
                "claim_type": "colisão",
                "identifier": "ABC1234",
                "description": "Batida com outro carro, pessoa ferida",
            },
        )
        result = await escalate_node(state)

        mock_create.assert_called_once()
        assert "GRAVE" in mock_broker.call_args[0][0]
        assert result["escalated"] is True
        assert result["status"] == "escalated"
        mock_client.assert_called_once()

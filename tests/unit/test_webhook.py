"""
Testes unitários do webhook handler do Evolution API.
"""
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from models.config import settings

VALID_HEADERS = {"apikey": settings.evolution_api_key}

VALID_PAYLOAD: dict[str, Any] = {
    "event": "messages.upsert",
    "instance": "brokerai",
    "data": {
        "key": {
            "remoteJid": "5517999999999@s.whatsapp.net",
            "fromMe": False,
            "id": "ABC123",
        },
        "pushName": "João Silva",
        "message": {"conversation": "Preciso de ajuda com meu seguro"},
        "messageType": "conversation",
        "messageTimestamp": 1234567890,
    },
}


@pytest.mark.asyncio
async def test_webhook_ignores_own_messages(api_client: AsyncClient):
    """Mensagens enviadas por nós (fromMe=true) devem ser ignoradas."""
    key = {**VALID_PAYLOAD["data"]["key"], "fromMe": True}
    payload = {**VALID_PAYLOAD, "data": {**VALID_PAYLOAD["data"], "key": key}}
    response = await api_client.post("/webhook/whatsapp", json=payload, headers=VALID_HEADERS)
    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}


@pytest.mark.asyncio
async def test_webhook_ignores_unknown_event(api_client: AsyncClient):
    """Eventos diferentes de messages.upsert devem ser ignorados."""
    payload = {**VALID_PAYLOAD, "event": "connection.update"}
    response = await api_client.post("/webhook/whatsapp", json=payload, headers=VALID_HEADERS)
    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}


@pytest.mark.asyncio
async def test_webhook_receives_message(api_client: AsyncClient):
    """Mensagem válida deve retornar status received com o telefone."""
    with patch("api.routes.webhook._handle_message", new_callable=AsyncMock):
        response = await api_client.post("/webhook/whatsapp", json=VALID_PAYLOAD, headers=VALID_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert data["phone"] == "5517999999999"


@pytest.mark.asyncio
async def test_webhook_rejects_invalid_apikey(api_client: AsyncClient):
    """Requisições com apikey inválida devem retornar 401."""
    response = await api_client.post(
        "/webhook/whatsapp",
        json=VALID_PAYLOAD,
        headers={"apikey": "chave-errada"},
    )
    assert response.status_code == 401

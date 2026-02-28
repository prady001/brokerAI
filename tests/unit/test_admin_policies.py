"""
Testes unitários das rotas admin de clientes e apólices.
"""
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Insurer


# ---------------------------------------------------------------------------
# Fixtures auxiliares
# ---------------------------------------------------------------------------

@pytest.fixture
def client_payload() -> dict:
    return {
        "full_name": "Maria Aparecida Silva",
        "cpf_cnpj": "123.456.789-00",
        "phone_whatsapp": "5517991234567",
        "email": "maria@example.com",
    }


async def _create_insurer(db: AsyncSession) -> Insurer:
    """Cria uma seguradora de teste no banco."""
    insurer = Insurer(
        name="Porto Seguro",
        code="porto",
        integration_type="api",
    )
    db.add(insurer)
    await db.commit()
    await db.refresh(insurer)
    return insurer


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_client(api_client: AsyncClient, client_payload: dict):
    """POST /admin/clients deve criar cliente e retornar 201 com client_id."""
    response = await api_client.post("/admin/clients", json=client_payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["full_name"] == client_payload["full_name"]
    uuid.UUID(data["id"])  # valida que é UUID válido


@pytest.mark.asyncio
async def test_create_policy(
    api_client: AsyncClient,
    db_session: AsyncSession,
    client_payload: dict,
):
    """POST /admin/policies deve criar apólice e retornar 201 com policy_id."""
    insurer = await _create_insurer(db_session)

    client_resp = await api_client.post("/admin/clients", json=client_payload)
    client_id = client_resp.json()["id"]

    policy_payload = {
        "client_id": client_id,
        "insurer_id": str(insurer.id),
        "policy_number": "PORTO-2025-001",
        "type": "auto",
        "item_description": "Toyota Yaris 1.3 Flex / ABC1234",
        "start_date": "2025-08-01",
        "end_date": "2026-08-01",
        "seller_phone": "5517999999999",
    }
    response = await api_client.post("/admin/policies", json=policy_payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["policy_number"] == "PORTO-2025-001"
    assert data["item_description"] == "Toyota Yaris 1.3 Flex / ABC1234"


@pytest.mark.asyncio
async def test_list_policies(
    api_client: AsyncClient,
    db_session: AsyncSession,
    client_payload: dict,
):
    """GET /admin/policies deve retornar 200 com lista de apólices."""
    insurer = await _create_insurer(db_session)

    client_resp = await api_client.post("/admin/clients", json={**client_payload, "cpf_cnpj": "987.654.321-00"})
    client_id = client_resp.json()["id"]

    await api_client.post("/admin/policies", json={
        "client_id": client_id,
        "insurer_id": str(insurer.id),
        "policy_number": "PORTO-2025-002",
        "type": "auto",
        "end_date": "2026-09-01",
    })

    response = await api_client.get("/admin/policies")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1

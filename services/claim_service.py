"""
ClaimService — CRUD de sinistros e lookup de clientes/apólices.
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from models.database import AsyncSessionLocal, Claim, Client, Policy

# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

async def get_client_by_phone(phone: str) -> dict | None:
    """Retorna dados básicos do cliente pelo número de WhatsApp."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Client).where(Client.phone_whatsapp == phone)
        )
        client = result.scalar_one_or_none()
        if client:
            return {"id": str(client.id), "name": client.full_name}
        return None


async def get_policy_by_identifier(identifier: str, client_id: str) -> dict | None:
    """
    Busca a apólice ativa do cliente por placa ou número de apólice.
    Faz correspondência parcial e case-insensitive.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Policy).where(
                Policy.client_id == uuid.UUID(client_id),
                Policy.status == "active",
            )
        )
        policies = result.scalars().all()
        key = identifier.upper().replace("-", "").replace(" ", "")
        for policy in policies:
            pol_num = (policy.policy_number or "").upper().replace("-", "").replace(" ", "")
            desc = (policy.item_description or "").upper().replace("-", "").replace(" ", "")
            if key in pol_num or key in desc:
                return {
                    "id": str(policy.id),
                    "policy_number": policy.policy_number,
                    "insurer_id": str(policy.insurer_id) if policy.insurer_id else None,
                    "item_description": policy.item_description,
                }
        return None


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

_CLAIM_TYPE_MAP: dict[str, str] = {
    "guincho": "assistance",
    "reboque": "assistance",
    "pane": "assistance",
    "pane seca": "assistance",
    "assistencia": "assistance",
    "assistência": "assistance",
    "vidro": "glass",
    "parabrisa": "glass",
    "para-brisa": "glass",
    "colisao": "collision",
    "colisão": "collision",
    "batida": "collision",
    "acidente": "collision",
    "furto": "theft",
    "roubo": "theft",
    "incendio": "fire",
    "incêndio": "fire",
}


def normalize_claim_type(claim_type: str) -> str:
    return _CLAIM_TYPE_MAP.get(claim_type.lower().strip(), "other")


async def create_claim(
    client_id: str,
    claim_type: str,
    severity: str,
    description: str,
    policy_id: str | None = None,
    insurer_id: str | None = None,
) -> str:
    """Cria um sinistro no banco e retorna o UUID gerado como string."""
    async with AsyncSessionLocal() as session:
        claim = Claim(
            id=uuid.uuid4(),
            client_id=uuid.UUID(client_id),
            policy_id=uuid.UUID(policy_id) if policy_id else None,
            insurer_id=uuid.UUID(insurer_id) if insurer_id else None,
            type=normalize_claim_type(claim_type),
            severity=severity,
            status="open",
            description=description,
            opened_at=datetime.now(UTC),
        )
        session.add(claim)
        await session.commit()
        return str(claim.id)


async def get_claim(claim_id: str) -> dict | None:
    """Retorna dados de um sinistro pelo ID."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Claim).where(Claim.id == uuid.UUID(claim_id))
        )
        claim = result.scalar_one_or_none()
        if not claim:
            return None
        return {
            "id": str(claim.id),
            "client_id": str(claim.client_id),
            "policy_id": str(claim.policy_id) if claim.policy_id else None,
            "type": claim.type,
            "severity": claim.severity,
            "status": claim.status,
            "description": claim.description,
            "opened_at": claim.opened_at.isoformat() if claim.opened_at else None,
        }


async def update_claim_status(claim_id: str, status: str) -> bool:
    """Atualiza o status de um sinistro."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Claim).where(Claim.id == uuid.UUID(claim_id))
        )
        claim = result.scalar_one_or_none()
        if not claim:
            return False
        claim.status = status  # type: ignore[assignment]
        await session.commit()
        return True


async def close_claim(claim_id: str) -> bool:
    """Encerra o sinistro registrando closed_at."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Claim).where(Claim.id == uuid.UUID(claim_id))
        )
        claim = result.scalar_one_or_none()
        if not claim:
            return False
        claim.status = "closed"  # type: ignore[assignment]
        claim.closed_at = datetime.now(UTC)  # type: ignore[assignment]
        await session.commit()
        return True

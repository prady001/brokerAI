"""
Schemas Pydantic para validação de request/response da API.
"""
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# Admin — Clientes
# ---------------------------------------------------------------------------

class ClientCreate(BaseModel):
    full_name: str
    cpf_cnpj: str | None = None
    phone_whatsapp: str | None = None
    email: str | None = None
    birth_date: date | None = None


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    cpf_cnpj: str | None
    phone_whatsapp: str | None
    email: str | None
    birth_date: date | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Admin — Apólices
# ---------------------------------------------------------------------------

class PolicyCreate(BaseModel):
    client_id: uuid.UUID
    insurer_id: uuid.UUID
    policy_number: str
    type: Literal["auto", "life", "home", "travel", "business"] | None = None
    item_description: str | None = None
    premium_amount: Decimal | None = None
    start_date: date | None = None
    end_date: date | None = None
    seller_phone: str | None = None


class PolicyPatch(BaseModel):
    status: Literal["active", "expired", "cancelled"] | None = None
    seller_phone: str | None = None


class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    insurer_id: uuid.UUID
    policy_number: str
    type: str | None
    item_description: str | None
    status: str
    premium_amount: Decimal | None
    start_date: date | None
    end_date: date | None
    seller_phone: str | None
    created_at: datetime

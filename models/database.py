"""
Modelos SQLAlchemy e configuração do banco de dados.
Engine assíncrona via asyncpg + SQLAlchemy 2.0.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from models.config import settings

# ---------------------------------------------------------------------------
# Engine & Session
# ---------------------------------------------------------------------------

engine = create_async_engine(settings.database_url, echo=False)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    """Dependency FastAPI para sessão de banco assíncrona."""
    async with AsyncSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------

class Insurer(Base):
    __tablename__ = "insurers"

    id               = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name             = Column(String, nullable=False)
    code             = Column(String, unique=True, nullable=False)   # ex: allianz, porto, tokio
    portal_url       = Column(String)
    integration_type = Column(Enum("api", "rpa", "manual", name="integration_type"), nullable=False)
    two_fa_method    = Column(
        Enum("totp", "email", "sms", "none", name="two_fa_method"), default="none"
    )
    active           = Column(Boolean, default=True)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Client(Base):
    __tablename__ = "clients"

    id             = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name      = Column(String, nullable=False)
    cpf_cnpj       = Column(String, unique=True)   # tokenizado antes de entrar no LLM
    phone_whatsapp = Column(String)
    email          = Column(String)
    birth_date     = Column(Date)
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Policy(Base):
    __tablename__ = "policies"

    id               = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id        = Column(Uuid(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    insurer_id       = Column(Uuid(as_uuid=True), ForeignKey("insurers.id"), nullable=False)
    policy_number    = Column(String, unique=True, nullable=False)
    type             = Column(
        Enum("auto", "life", "home", "travel", "business", name="policy_type")
    )
    item_description = Column(String)       # ex: "Toyota Yaris 1.3 Flex / ABC1234"
    status           = Column(
        Enum("active", "expired", "cancelled", name="policy_status"), default="active"
    )
    premium_amount   = Column(Numeric(12, 2))
    start_date       = Column(Date)
    end_date         = Column(Date)
    seller_phone     = Column(String)       # vendedor responsável (WhatsApp)
    imported_from    = Column(String)       # 'manual' | 'agger_csv' (V1)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Claim(Base):
    __tablename__ = "claims"

    id                  = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id           = Column(Uuid(as_uuid=True), ForeignKey("policies.id"))
    client_id           = Column(Uuid(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    insurer_id          = Column(Uuid(as_uuid=True), ForeignKey("insurers.id"))
    type                = Column(
        Enum("assistance", "glass", "collision", "theft", "fire", "other", name="claim_type")
    )
    severity            = Column(Enum("simple", "grave", name="claim_severity"))
    status              = Column(
        Enum("open", "in_progress", "waiting_insurer", "escalated", "closed", name="claim_status"),
        default="open",
    )
    insurer_thread_id   = Column(String)
    insurer_channel     = Column(String)    # api | whatsapp_relay | manual
    occurrence_date     = Column(DateTime)
    occurrence_location = Column(JSON)
    description         = Column(Text)
    documents           = Column(JSON)     # lista de URLs Cloudflare R2
    opened_at           = Column(DateTime, default=datetime.utcnow)
    closed_at           = Column(DateTime)


class Renewal(Base):
    __tablename__ = "renewals"

    id              = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id       = Column(Uuid(as_uuid=True), ForeignKey("policies.id"), nullable=False)
    client_id       = Column(Uuid(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    seller_phone    = Column(String)        # vendedor a notificar
    expiry_date     = Column(Date, nullable=False)   # cópia de policy.end_date para queries rápidas
    status          = Column(
        Enum(
            "pending", "contacted", "confirmed", "refused", "no_response", "lost",
            name="renewal_status",
        ),
        default="pending",
        nullable=False,
    )
    contact_count   = Column(Integer, default=0)
    last_contact_at = Column(DateTime)
    next_contact_at = Column(DateTime)
    client_intent   = Column(String)        # wants_renewal | refused | wants_quote
    intent_notes    = Column(Text)          # motivo livre (ex: "tá muito caro")
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"

    id         = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id  = Column(Uuid(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    claim_id   = Column(Uuid(as_uuid=True), ForeignKey("claims.id"))
    renewal_id = Column(Uuid(as_uuid=True), ForeignKey("renewals.id"))
    type       = Column(
        Enum("claim", "onboarding", "renewal", "faq", "support", name="conversation_type")
    )
    status     = Column(
        Enum(
            "active", "waiting_client", "waiting_insurer", "escalated", "closed",
            name="conversation_status",
        ),
        default="active",
    )
    messages   = Column(JSON, default=list)    # histórico completo — retido 5 anos (SUSEP)
    started_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at  = Column(DateTime)


class Commission(Base):
    """Comissões extraídas dos portais. Utilizado a partir da V1 (agente de comissionamento)."""
    __tablename__ = "commissions"

    id              = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    insurer_id      = Column(Uuid(as_uuid=True), ForeignKey("insurers.id"), nullable=False)
    policy_id       = Column(Uuid(as_uuid=True), ForeignKey("policies.id"))
    client_id       = Column(Uuid(as_uuid=True), ForeignKey("clients.id"))
    reference_month = Column(String)        # competência YYYY-MM
    gross_amount    = Column(Numeric(12, 2))
    net_amount      = Column(Numeric(12, 2))
    commission_rate = Column(Numeric(5, 4))
    nfse_number     = Column(String)
    nfse_pdf_url    = Column(String)
    status          = Column(
        Enum("pending", "nfse_emitted", "nfse_failed", name="commission_status"),
        default="pending",
    )
    extracted_at    = Column(DateTime)
    nfse_emitted_at = Column(DateTime)
    created_at      = Column(DateTime, default=datetime.utcnow)

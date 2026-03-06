"""Criação inicial de todas as tabelas do MVP.

Revision ID: 0001
Revises:
Create Date: 2026-02-28
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Tipos ENUM
    # ------------------------------------------------------------------
    op.execute("CREATE TYPE integration_type AS ENUM ('api', 'rpa', 'manual')")
    op.execute("CREATE TYPE two_fa_method    AS ENUM ('totp', 'email', 'sms', 'none')")
    op.execute("CREATE TYPE policy_type      AS ENUM ('auto', 'life', 'home', 'travel', 'business')")
    op.execute("CREATE TYPE policy_status    AS ENUM ('active', 'expired', 'cancelled')")
    op.execute("CREATE TYPE claim_type       AS ENUM ('assistance', 'glass', 'collision', 'theft', 'fire', 'other')")
    op.execute("CREATE TYPE claim_severity   AS ENUM ('simple', 'grave')")
    op.execute("CREATE TYPE claim_status     AS ENUM ('open', 'in_progress', 'waiting_insurer', 'escalated', 'closed')")
    op.execute("CREATE TYPE renewal_status   AS ENUM ('pending', 'contacted', 'confirmed', 'refused', 'no_response', 'lost')")
    op.execute("CREATE TYPE conversation_type   AS ENUM ('claim', 'onboarding', 'renewal', 'faq', 'support')")
    op.execute("CREATE TYPE conversation_status AS ENUM ('active', 'waiting_client', 'waiting_insurer', 'escalated', 'closed')")
    op.execute("CREATE TYPE commission_status   AS ENUM ('pending', 'nfse_emitted', 'nfse_failed')")

    # ------------------------------------------------------------------
    # insurers
    # ------------------------------------------------------------------
    op.create_table(
        "insurers",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name",             sa.String(),  nullable=False),
        sa.Column("code",             sa.String(),  nullable=False, unique=True),
        sa.Column("portal_url",       sa.String()),
        sa.Column("integration_type", postgresql.ENUM("api", "rpa", "manual", name="integration_type", create_type=False), nullable=False),
        sa.Column("two_fa_method",    postgresql.ENUM("totp", "email", "sms", "none", name="two_fa_method", create_type=False), server_default="none"),
        sa.Column("active",           sa.Boolean(), server_default="true"),
        sa.Column("created_at",       sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at",       sa.DateTime(), server_default=sa.func.now()),
    )

    # ------------------------------------------------------------------
    # clients
    # ------------------------------------------------------------------
    op.create_table(
        "clients",
        sa.Column("id",             postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name",      sa.String(),  nullable=False),
        sa.Column("cpf_cnpj",       sa.String(),  unique=True),
        sa.Column("phone_whatsapp", sa.String()),
        sa.Column("email",          sa.String()),
        sa.Column("birth_date",     sa.Date()),
        sa.Column("created_at",     sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at",     sa.DateTime(), server_default=sa.func.now()),
    )

    # ------------------------------------------------------------------
    # policies
    # ------------------------------------------------------------------
    op.create_table(
        "policies",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("client_id",        postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"),  nullable=False),
        sa.Column("insurer_id",       postgresql.UUID(as_uuid=True), sa.ForeignKey("insurers.id"), nullable=False),
        sa.Column("policy_number",    sa.String(), nullable=False, unique=True),
        sa.Column("type",             postgresql.ENUM("auto", "life", "home", "travel", "business", name="policy_type", create_type=False)),
        sa.Column("item_description", sa.String()),
        sa.Column("status",           postgresql.ENUM("active", "expired", "cancelled", name="policy_status", create_type=False), server_default="active"),
        sa.Column("premium_amount",   sa.Numeric(12, 2)),
        sa.Column("start_date",       sa.Date()),
        sa.Column("end_date",         sa.Date()),
        sa.Column("seller_phone",     sa.String()),
        sa.Column("imported_from",    sa.String()),
        sa.Column("created_at",       sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at",       sa.DateTime(), server_default=sa.func.now()),
    )

    # ------------------------------------------------------------------
    # claims
    # ------------------------------------------------------------------
    op.create_table(
        "claims",
        sa.Column("id",                  postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("policy_id",           postgresql.UUID(as_uuid=True), sa.ForeignKey("policies.id")),
        sa.Column("client_id",           postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"),  nullable=False),
        sa.Column("insurer_id",          postgresql.UUID(as_uuid=True), sa.ForeignKey("insurers.id")),
        sa.Column("type",                postgresql.ENUM("assistance", "glass", "collision", "theft", "fire", "other", name="claim_type", create_type=False)),
        sa.Column("severity",            postgresql.ENUM("simple", "grave", name="claim_severity", create_type=False)),
        sa.Column("status",              postgresql.ENUM("open", "in_progress", "waiting_insurer", "escalated", "closed", name="claim_status", create_type=False), server_default="open"),
        sa.Column("insurer_thread_id",   sa.String()),
        sa.Column("insurer_channel",     sa.String()),
        sa.Column("occurrence_date",     sa.DateTime()),
        sa.Column("occurrence_location", postgresql.JSONB()),
        sa.Column("description",         sa.Text()),
        sa.Column("documents",           postgresql.JSONB()),
        sa.Column("opened_at",           sa.DateTime(), server_default=sa.func.now()),
        sa.Column("closed_at",           sa.DateTime()),
    )

    # ------------------------------------------------------------------
    # renewals
    # ------------------------------------------------------------------
    op.create_table(
        "renewals",
        sa.Column("id",              postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("policy_id",       postgresql.UUID(as_uuid=True), sa.ForeignKey("policies.id"), nullable=False),
        sa.Column("client_id",       postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"),  nullable=False),
        sa.Column("seller_phone",    sa.String()),
        sa.Column("expiry_date",     sa.Date(), nullable=False),
        sa.Column("status",          postgresql.ENUM("pending", "contacted", "confirmed", "refused", "no_response", "lost", name="renewal_status", create_type=False), nullable=False, server_default="pending"),
        sa.Column("contact_count",   sa.Integer(), server_default="0"),
        sa.Column("last_contact_at", sa.DateTime()),
        sa.Column("next_contact_at", sa.DateTime()),
        sa.Column("client_intent",   sa.String()),
        sa.Column("intent_notes",    sa.Text()),
        sa.Column("created_at",      sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at",      sa.DateTime(), server_default=sa.func.now()),
    )

    # ------------------------------------------------------------------
    # conversations
    # ------------------------------------------------------------------
    op.create_table(
        "conversations",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("client_id",  postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"),  nullable=False),
        sa.Column("claim_id",   postgresql.UUID(as_uuid=True), sa.ForeignKey("claims.id")),
        sa.Column("renewal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("renewals.id")),
        sa.Column("type",       postgresql.ENUM("claim", "onboarding", "renewal", "faq", "support", name="conversation_type", create_type=False)),
        sa.Column("status",     postgresql.ENUM("active", "waiting_client", "waiting_insurer", "escalated", "closed", name="conversation_status", create_type=False), server_default="active"),
        sa.Column("messages",   postgresql.JSONB(), server_default="[]"),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("closed_at",  sa.DateTime()),
    )

    # ------------------------------------------------------------------
    # commissions (V1 — agente de comissionamento)
    # ------------------------------------------------------------------
    op.create_table(
        "commissions",
        sa.Column("id",              postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("insurer_id",      postgresql.UUID(as_uuid=True), sa.ForeignKey("insurers.id"), nullable=False),
        sa.Column("policy_id",       postgresql.UUID(as_uuid=True), sa.ForeignKey("policies.id")),
        sa.Column("client_id",       postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id")),
        sa.Column("reference_month", sa.String()),
        sa.Column("gross_amount",    sa.Numeric(12, 2)),
        sa.Column("net_amount",      sa.Numeric(12, 2)),
        sa.Column("commission_rate", sa.Numeric(5, 4)),
        sa.Column("nfse_number",     sa.String()),
        sa.Column("nfse_pdf_url",    sa.String()),
        sa.Column("status",          postgresql.ENUM("pending", "nfse_emitted", "nfse_failed", name="commission_status", create_type=False), server_default="pending"),
        sa.Column("extracted_at",    sa.DateTime()),
        sa.Column("nfse_emitted_at", sa.DateTime()),
        sa.Column("created_at",      sa.DateTime(), server_default=sa.func.now()),
    )

    # ------------------------------------------------------------------
    # Índices úteis para queries frequentes
    # ------------------------------------------------------------------
    op.create_index("ix_policies_end_date",    "policies",      ["end_date"])
    op.create_index("ix_policies_client_id",   "policies",      ["client_id"])
    op.create_index("ix_renewals_expiry_date", "renewals",      ["expiry_date"])
    op.create_index("ix_renewals_status",      "renewals",      ["status"])
    op.create_index("ix_claims_client_id",     "claims",        ["client_id"])
    op.create_index("ix_claims_status",        "claims",        ["status"])
    op.create_index("ix_conversations_client", "conversations",  ["client_id"])


def downgrade() -> None:
    op.drop_table("commissions")
    op.drop_table("conversations")
    op.drop_table("renewals")
    op.drop_table("claims")
    op.drop_table("policies")
    op.drop_table("clients")
    op.drop_table("insurers")

    op.execute("DROP TYPE IF EXISTS commission_status")
    op.execute("DROP TYPE IF EXISTS conversation_status")
    op.execute("DROP TYPE IF EXISTS conversation_type")
    op.execute("DROP TYPE IF EXISTS renewal_status")
    op.execute("DROP TYPE IF EXISTS claim_status")
    op.execute("DROP TYPE IF EXISTS claim_severity")
    op.execute("DROP TYPE IF EXISTS claim_type")
    op.execute("DROP TYPE IF EXISTS policy_status")
    op.execute("DROP TYPE IF EXISTS policy_type")
    op.execute("DROP TYPE IF EXISTS two_fa_method")
    op.execute("DROP TYPE IF EXISTS integration_type")

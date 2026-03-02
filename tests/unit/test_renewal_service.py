"""
Testes unitários para RenewalService.
"""
import uuid
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

UTC = timezone.utc

import pytest
import pytest_asyncio

from models.database import Client, Insurer, Policy, Renewal
from services.renewal_service import RenewalService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def insurer(db_session):
    obj = Insurer(
        name="Allianz Seguros",
        code=f"allianz-{uuid4().hex[:8]}",  # único por teste
        integration_type="rpa",
    )
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)
    return obj


@pytest_asyncio.fixture
async def client_obj(db_session):
    obj = Client(
        full_name="João Silva",
        phone_whatsapp="5511999990001",
        cpf_cnpj=str(uuid.uuid4()),  # único por teste para evitar conflito UNIQUE
    )
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)
    return obj


@pytest_asyncio.fixture
async def policy_obj(db_session, client_obj, insurer):
    today = date.today()
    obj = Policy(
        client_id=client_obj.id,
        insurer_id=insurer.id,
        policy_number=f"POL-{uuid4().hex[:8]}",
        item_description="Toyota Yaris / ABC1234",
        status="active",
        end_date=today + timedelta(days=30),
        seller_phone="5511988880001",
    )
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)
    return obj


@pytest_asyncio.fixture
async def renewal_obj(db_session, policy_obj, client_obj):
    today = date.today()
    obj = Renewal(
        policy_id=policy_obj.id,
        client_id=client_obj.id,
        seller_phone="5511988880001",
        expiry_date=today + timedelta(days=30),
        status="pending",
        contact_count=0,
    )
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)
    return obj


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_expiring_policies_finds_policy(db_session, policy_obj, client_obj):
    """Deve encontrar apólice vencendo em 30 dias."""
    service = RenewalService(db_session)
    candidates = await service.get_expiring_policies([30])

    assert len(candidates) == 1
    assert candidates[0].policy_id == policy_obj.id
    assert candidates[0].client_phone == client_obj.phone_whatsapp
    assert candidates[0].days_until_expiry == 30


@pytest.mark.asyncio
async def test_get_expiring_policies_excludes_contacted_with_future_next_contact(
    db_session, policy_obj, client_obj, renewal_obj
):
    """Não deve retornar apólice com renovação 'contacted' cujo next_contact_at é futuro."""
    tomorrow = datetime.now(UTC) + timedelta(days=1)
    renewal_obj.status = "contacted"
    renewal_obj.next_contact_at = tomorrow
    await db_session.commit()
    await db_session.refresh(renewal_obj)

    service = RenewalService(db_session)
    candidates = await service.get_expiring_policies([30])

    # Garante que a policy específica deste teste não está nos candidatos
    # (o DB pode ter policies de outros testes — verificamos apenas a nossa)
    policy_ids = [c.policy_id for c in candidates]
    assert policy_obj.id not in policy_ids


@pytest.mark.asyncio
async def test_get_or_create_renewal_creates_new(db_session, policy_obj, client_obj):
    """Deve criar registro de renovação quando não existe."""
    service = RenewalService(db_session)
    renewal = await service.get_or_create_renewal(
        policy_id=policy_obj.id,
        client_id=client_obj.id,
        seller_phone="5511988880001",
        expiry_date=policy_obj.end_date,
    )
    assert renewal.id is not None
    assert renewal.status == "pending"
    assert renewal.contact_count == 0


@pytest.mark.asyncio
async def test_get_or_create_renewal_returns_existing(db_session, renewal_obj, policy_obj, client_obj):
    """Deve retornar renovação existente sem duplicar."""
    service = RenewalService(db_session)
    renewal = await service.get_or_create_renewal(
        policy_id=policy_obj.id,
        client_id=client_obj.id,
        seller_phone="5511988880001",
        expiry_date=policy_obj.end_date,
    )
    assert renewal.id == renewal_obj.id


@pytest.mark.asyncio
async def test_register_contact_attempt_increments_count(db_session, renewal_obj):
    """Deve incrementar contact_count e marcar status como contacted."""
    service = RenewalService(db_session)
    renewal = await service.register_contact_attempt(renewal_obj.id)

    assert renewal.contact_count == 1
    assert renewal.status == "contacted"
    assert renewal.last_contact_at is not None


@pytest.mark.asyncio
async def test_register_contact_attempt_regua_next_contact(db_session, renewal_obj):
    """Deve calcular next_contact_at conforme a régua de contatos."""
    service = RenewalService(db_session)
    expiry = renewal_obj.expiry_date

    # 1º contato → próximo em 15d antes do vencimento
    renewal = await service.register_contact_attempt(renewal_obj.id)
    expected_15d = datetime(expiry.year, expiry.month, expiry.day, 8, 0, tzinfo=UTC) - timedelta(days=15)
    assert renewal.next_contact_at is not None
    assert renewal.next_contact_at.date() == expected_15d.date()

    # 2º contato → próximo em 7d antes do vencimento
    renewal = await service.register_contact_attempt(renewal_obj.id)
    expected_7d = datetime(expiry.year, expiry.month, expiry.day, 8, 0, tzinfo=UTC) - timedelta(days=7)
    assert renewal.next_contact_at.date() == expected_7d.date()  # type: ignore[union-attr]

    # 3º contato → próximo no dia do vencimento
    renewal = await service.register_contact_attempt(renewal_obj.id)
    assert renewal.next_contact_at is not None  # type: ignore[union-attr]
    assert renewal.next_contact_at.date() == expiry  # type: ignore[union-attr]

    # 4º contato → sem próximo agendado
    renewal = await service.register_contact_attempt(renewal_obj.id)
    assert renewal.next_contact_at is None


@pytest.mark.asyncio
async def test_update_renewal_status(db_session, renewal_obj):
    """Deve atualizar status, intenção e notas."""
    service = RenewalService(db_session)
    renewal = await service.update_renewal_status(
        renewal_obj.id,
        status="confirmed",
        intent="wants_renewal",
        notes="Cliente confirmou pelo WhatsApp",
    )
    assert renewal.status == "confirmed"
    assert renewal.client_intent == "wants_renewal"
    assert renewal.intent_notes == "Cliente confirmou pelo WhatsApp"


@pytest.mark.asyncio
async def test_get_active_renewal_for_client(db_session, renewal_obj, client_obj):
    """Deve retornar renovação 'contacted' mais recente do cliente."""
    renewal_obj.status = "contacted"
    await db_session.commit()
    await db_session.refresh(renewal_obj)

    service = RenewalService(db_session)
    renewal = await service.get_active_renewal_for_client(client_obj.id)
    assert renewal is not None
    assert renewal.id == renewal_obj.id


@pytest.mark.asyncio
async def test_get_active_renewal_returns_none_when_pending(db_session, renewal_obj, client_obj):
    """Não deve retornar renovação com status 'pending' (apenas 'contacted')."""
    service = RenewalService(db_session)
    renewal = await service.get_active_renewal_for_client(client_obj.id)
    assert renewal is None

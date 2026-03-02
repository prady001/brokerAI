"""
RenewalService — Lógica de renovação de apólices.
Gerencia a régua de contatos, criação de registros de renovação e atualização de status.
"""
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

UTC = timezone.utc
from typing import Literal
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Client, Policy, Renewal

logger = logging.getLogger(__name__)

RenewalStatus = Literal["pending", "contacted", "confirmed", "refused", "no_response", "lost"]
ClientIntent = Literal["wants_renewal", "refused", "wants_quote"]


@dataclass
class RenewalCandidate:
    """Apólice elegível para contato de renovação."""
    policy_id: UUID
    client_id: UUID
    client_name: str
    client_phone: str
    seller_phone: str | None
    policy_number: str
    item_description: str | None
    expiry_date: date
    days_until_expiry: int
    renewal_id: UUID | None  # None se ainda não tem registro de renovação


class RenewalService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_expiring_policies(self, days_ahead: list[int]) -> list[RenewalCandidate]:
        """
        Busca apólices ativas com end_date em exatamente N dias (para cada N em days_ahead).
        Retorna apenas apólices sem renovação em status 'pending' ou 'contacted'.
        """
        today = date.today()
        candidates: list[RenewalCandidate] = []

        for days in days_ahead:
            target_date = today + timedelta(days=days)

            # Busca apólices ativas vencendo na data alvo
            result = await self.db.execute(
                select(Policy, Client)
                .join(Client, Policy.client_id == Client.id)
                .where(
                    and_(
                        Policy.end_date == target_date,
                        Policy.status == "active",
                        Client.phone_whatsapp.isnot(None),
                    )
                )
            )
            rows = result.all()

            for policy, client in rows:
                # Verifica se já existe renovação ativa para essa apólice
                existing = await self.db.execute(
                    select(Renewal).where(
                        and_(
                            Renewal.policy_id == policy.id,
                            Renewal.status.in_(["pending", "contacted"]),
                        )
                    )
                )
                existing_renewal = existing.scalar_one_or_none()

                # Pula se já foi contatado nesse ciclo (contacted)
                if existing_renewal and existing_renewal.status == "contacted":
                    # Só recontata se next_contact_at <= hoje
                    if (
                        existing_renewal.next_contact_at is not None
                        and existing_renewal.next_contact_at.date() > today
                    ):
                        continue

                candidates.append(
                    RenewalCandidate(
                        policy_id=policy.id,
                        client_id=client.id,
                        client_name=client.full_name,
                        client_phone=client.phone_whatsapp,  # type: ignore[arg-type]
                        seller_phone=policy.seller_phone,
                        policy_number=policy.policy_number,
                        item_description=policy.item_description,
                        expiry_date=policy.end_date,  # type: ignore[arg-type]
                        days_until_expiry=days,
                        renewal_id=existing_renewal.id if existing_renewal else None,
                    )
                )

        return candidates

    async def get_or_create_renewal(
        self,
        policy_id: UUID,
        client_id: UUID,
        seller_phone: str | None,
        expiry_date: date,
    ) -> Renewal:
        """Cria registro de renovação se não existir."""
        result = await self.db.execute(
            select(Renewal).where(
                and_(
                    Renewal.policy_id == policy_id,
                    Renewal.status.in_(["pending", "contacted"]),
                )
            )
        )
        renewal = result.scalar_one_or_none()

        if renewal is None:
            renewal = Renewal(
                policy_id=policy_id,
                client_id=client_id,
                seller_phone=seller_phone,
                expiry_date=expiry_date,
                status="pending",
                contact_count=0,
            )
            self.db.add(renewal)
            await self.db.commit()
            await self.db.refresh(renewal)
            logger.info("Renovação criada: policy_id=%s", policy_id)

        return renewal

    async def update_renewal_status(
        self,
        renewal_id: UUID,
        status: RenewalStatus,
        intent: ClientIntent | None = None,
        notes: str | None = None,
    ) -> Renewal:
        """Atualiza status (e intenção opcional) de uma renovação."""
        result = await self.db.execute(select(Renewal).where(Renewal.id == renewal_id))
        renewal = result.scalar_one()

        renewal.status = status  # type: ignore[assignment]
        if intent is not None:
            renewal.client_intent = intent
        if notes is not None:
            renewal.intent_notes = notes

        await self.db.commit()
        await self.db.refresh(renewal)
        return renewal

    async def register_contact_attempt(self, renewal_id: UUID) -> Renewal:
        """
        Incrementa contact_count, atualiza last_contact_at e calcula next_contact_at.

        Régua:
          1º contato (30d antes) → próximo 15d antes do vencimento
          2º contato (15d antes) → próximo 7d antes do vencimento
          3º contato (7d antes)  → próximo no dia do vencimento
          4º contato (dia 0)     → marcar no_response após 3 dias sem resposta
        """
        result = await self.db.execute(select(Renewal).where(Renewal.id == renewal_id))
        renewal = result.scalar_one()

        now = datetime.now(UTC)
        renewal.contact_count = (renewal.contact_count or 0) + 1
        renewal.last_contact_at = now
        renewal.status = "contacted"  # type: ignore[assignment]

        expiry = renewal.expiry_date
        if expiry is not None:
            expiry_dt = datetime(expiry.year, expiry.month, expiry.day, 8, 0, tzinfo=UTC)
            count = renewal.contact_count

            if count == 1:
                # Após 1º contato (30d): próximo em 15d antes
                renewal.next_contact_at = expiry_dt - timedelta(days=15)
            elif count == 2:
                # Após 2º contato (15d): próximo em 7d antes
                renewal.next_contact_at = expiry_dt - timedelta(days=7)
            elif count == 3:
                # Após 3º contato (7d): próximo no dia do vencimento
                renewal.next_contact_at = expiry_dt
            else:
                # Após 4º contato (dia 0): sem próximo agendado — aguarda resposta ou no_response
                renewal.next_contact_at = None

        await self.db.commit()
        await self.db.refresh(renewal)
        logger.info(
            "Tentativa de contato registrada: renewal_id=%s contato=%s",
            renewal_id,
            renewal.contact_count,
        )
        return renewal

    async def get_renewal_by_id(self, renewal_id: UUID) -> Renewal | None:
        """Busca renovação pelo ID."""
        result = await self.db.execute(select(Renewal).where(Renewal.id == renewal_id))
        return result.scalar_one_or_none()

    async def get_active_renewal_for_client(self, client_id: UUID) -> Renewal | None:
        """
        Busca renovação ativa (status 'contacted') para um cliente.
        Usado ao receber resposta do cliente via WhatsApp.
        """
        result = await self.db.execute(
            select(Renewal).where(
                and_(
                    Renewal.client_id == client_id,
                    Renewal.status == "contacted",
                )
            )
            .order_by(Renewal.last_contact_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

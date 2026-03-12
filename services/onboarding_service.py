"""
OnboardingService — criação de clientes e apólices via fluxo de onboarding.
"""
import re
import uuid
from datetime import datetime

from sqlalchemy import select

from models.database import AsyncSessionLocal, Client, Insurer, Policy

# ---------------------------------------------------------------------------
# CPF validation
# ---------------------------------------------------------------------------

def validate_cpf(cpf: str) -> bool:
    """Valida CPF brasileiro pelo algoritmo de dígito verificador."""
    digits = re.sub(r"\D", "", cpf)
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    # Primeiro dígito verificador
    total = sum(int(d) * (10 - i) for i, d in enumerate(digits[:9]))
    first = (total * 10 % 11) % 10
    if first != int(digits[9]):
        return False
    # Segundo dígito verificador
    total = sum(int(d) * (11 - i) for i, d in enumerate(digits[:10]))
    second = (total * 10 % 11) % 10
    return second == int(digits[10])


def format_cpf(cpf: str) -> str:
    """Normaliza CPF para formato xxx.xxx.xxx-xx."""
    digits = re.sub(r"\D", "", cpf)
    if len(digits) == 11:
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
    return cpf


# ---------------------------------------------------------------------------
# Policy type mapping
# ---------------------------------------------------------------------------

_POLICY_TYPE_MAP: dict[str, str] = {
    "auto": "auto",
    "automóvel": "auto",
    "automovel": "auto",
    "carro": "auto",
    "moto": "auto",
    "motocicleta": "auto",
    "vida": "life",
    "life": "life",
    "residência": "home",
    "residencia": "home",
    "casa": "home",
    "home": "home",
    "viagem": "travel",
    "travel": "travel",
    "empresarial": "business",
    "business": "business",
}


def normalize_policy_type(raw: str) -> str:
    return _POLICY_TYPE_MAP.get(raw.lower().strip(), "auto")


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

async def get_or_create_insurer(name: str) -> str:
    """
    Busca seguradora por nome (correspondência parcial, case-insensitive).
    Se não existir, cria um registro mínimo com integration_type='manual'.
    Retorna o UUID como string.

    Nota: carrega todas as seguradoras ativas em memória para o match bidirecional.
    Aceitável no MVP (dezenas de registros); revisar se a tabela crescer.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Insurer).where(Insurer.active.is_(True)))
        insurers = result.scalars().all()
        name_lower = name.lower().strip()
        for ins in insurers:
            if name_lower in ins.name.lower() or ins.name.lower() in name_lower:
                return str(ins.id)

        # Cria seguradora nova (MVP — será refinada pelo corretor depois)
        code = re.sub(r"\s+", "_", name_lower)[:30]
        new_insurer = Insurer(
            id=uuid.uuid4(),
            name=name.strip().title(),
            code=code,
            integration_type="manual",
            two_fa_method="none",
            active=True,
        )
        session.add(new_insurer)
        await session.commit()
        return str(new_insurer.id)


async def get_client_by_cpf(cpf: str) -> dict | None:
    """Retorna dados básicos do cliente pelo CPF (ignora formatação)."""
    formatted = format_cpf(cpf)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Client).where(Client.cpf_cnpj == formatted)
        )
        client = result.scalar_one_or_none()
        if client:
            return {"id": str(client.id), "name": client.full_name}
    return None


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

async def create_client(
    full_name: str,
    cpf_cnpj: str,
    phone_whatsapp: str,
    email: str | None = None,
    cep: str | None = None,
    address: str | None = None,
) -> str:
    """
    Cria o cliente no banco.
    Se já existir um cliente com o mesmo CPF, retorna o ID existente.
    Retorna o UUID como string.
    """
    existing = await get_client_by_cpf(cpf_cnpj)
    if existing:
        return existing["id"]

    async with AsyncSessionLocal() as session:
        client = Client(
            id=uuid.uuid4(),
            full_name=full_name.strip().title(),
            cpf_cnpj=format_cpf(cpf_cnpj),
            phone_whatsapp=phone_whatsapp,
            email=email,
            cep=cep,
            address=address,
        )
        session.add(client)
        await session.commit()
        return str(client.id)


async def create_policy(
    client_id: str,
    insurer_id: str,
    policy_number: str,
    policy_type: str,
    item_description: str,
    end_date: str,
    start_date: str | None = None,
    seller_phone: str | None = None,
    minor_driver: bool | None = None,
) -> str:
    """
    Cria a apólice no banco vinculada ao cliente.
    end_date e start_date no formato YYYY-MM-DD ou DD/MM/YYYY.
    Retorna o UUID como string.
    """
    from datetime import date

    def parse_date(raw: str) -> date | None:
        if not raw:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
        return None

    end = parse_date(end_date)
    start = parse_date(start_date) if start_date else date.today()

    async with AsyncSessionLocal() as session:
        policy = Policy(
            id=uuid.uuid4(),
            client_id=uuid.UUID(client_id),
            insurer_id=uuid.UUID(insurer_id),
            policy_number=policy_number.strip(),
            type=normalize_policy_type(policy_type),
            item_description=item_description.strip(),
            status="active",
            start_date=start,
            end_date=end,
            seller_phone=seller_phone,
            minor_driver=minor_driver,
            imported_from="manual",
        )
        session.add(policy)
        await session.commit()
        return str(policy.id)

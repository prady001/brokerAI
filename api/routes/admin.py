"""
Rotas de administração — cadastro manual de clientes e apólices.
Protegidas por token interno. Usadas pelo corretor para importar carteira no MVP.
"""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.middleware.auth import verify_internal_token
from models.database import Client, Policy, get_db
from models.schemas import (
    ClientCreate,
    ClientResponse,
    PolicyCreate,
    PolicyPatch,
    PolicyResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", dependencies=[Depends(verify_internal_token)])


# ---------------------------------------------------------------------------
# Clientes
# ---------------------------------------------------------------------------

@router.post("/clients", response_model=ClientResponse, status_code=201)
async def create_client(body: ClientCreate, db: AsyncSession = Depends(get_db)) -> Client:
    """Cadastra um novo cliente manualmente."""
    client = Client(**body.model_dump())
    db.add(client)
    await db.commit()
    await db.refresh(client)
    logger.info("Cliente cadastrado: %s (%s)", client.full_name, client.id)
    return client


@router.get("/clients", response_model=list[ClientResponse])
async def list_clients(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[Client]:
    """Lista clientes cadastrados com paginação."""
    result = await db.execute(select(Client).offset(skip).limit(limit))
    return list(result.scalars().all())


@router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(client_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Client:
    """Busca cliente por ID."""
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client


# ---------------------------------------------------------------------------
# Apólices
# ---------------------------------------------------------------------------

@router.post("/policies", response_model=PolicyResponse, status_code=201)
async def create_policy(body: PolicyCreate, db: AsyncSession = Depends(get_db)) -> Policy:
    """Cadastra uma nova apólice manualmente."""
    policy = Policy(**body.model_dump(), imported_from="manual")
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    logger.info("Apólice cadastrada: %s (%s)", policy.policy_number, policy.id)
    return policy


@router.get("/policies", response_model=list[PolicyResponse])
async def list_policies(
    client_id: uuid.UUID | None = None,
    status: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[Policy]:
    """Lista apólices com filtros opcionais por cliente e status."""
    query = select(Policy)
    if client_id:
        query = query.where(Policy.client_id == client_id)
    if status:
        query = query.where(Policy.status == status)
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


@router.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Policy:
    """Busca apólice por ID."""
    policy = await db.get(Policy, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Apólice não encontrada")
    return policy


@router.patch("/policies/{policy_id}", response_model=PolicyResponse)
async def patch_policy(
    policy_id: uuid.UUID,
    body: PolicyPatch,
    db: AsyncSession = Depends(get_db),
) -> Policy:
    """Atualiza status ou vendedor responsável de uma apólice."""
    policy = await db.get(Policy, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Apólice não encontrada")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(policy, field, value)
    await db.commit()
    await db.refresh(policy)
    return policy

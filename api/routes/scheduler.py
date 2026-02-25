"""
Rota de acionamento manual do scheduler.
Permite disparar o ciclo de comissionamento fora do horário do CRON (ex: testes).
"""
from fastapi import APIRouter, Depends
from api.middleware.auth import verify_internal_token
from services.scheduler_service import run_commission_check

router = APIRouter()


@router.post("/scheduler/commission-check")
async def trigger_commission_check(_: None = Depends(verify_internal_token)) -> dict:
    """
    Aciona manualmente o ciclo de comissionamento.
    Requer token interno (não exposto ao público).
    """
    await run_commission_check()
    return {"status": "ok", "message": "Ciclo de comissionamento iniciado"}

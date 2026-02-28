"""
Rota de acionamento manual do scheduler.
Permite disparar a verificação de renovações fora do horário do CRON (ex: testes).
"""
from fastapi import APIRouter, Depends
from api.middleware.auth import verify_internal_token
from services.scheduler_service import run_renewal_check

router = APIRouter()


@router.post("/scheduler/renewal-check")
async def trigger_renewal_check(_: None = Depends(verify_internal_token)) -> dict:
    """
    Aciona manualmente a verificação de renovações.
    Requer token interno (não exposto ao público).
    """
    await run_renewal_check()
    return {"status": "ok", "message": "Verificação de renovações iniciada"}

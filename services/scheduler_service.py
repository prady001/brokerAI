"""
SchedulerService — CRON jobs via APScheduler.
Dispara o ciclo de comissionamento diariamente às 08:00 BRT.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from models.config import settings


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        run_commission_check,
        trigger=CronTrigger(
            hour=settings.commission_cron_hour,
            timezone=settings.commission_cron_timezone,
        ),
        id="commission_check",
        name="Ciclo diário de comissionamento",
        replace_existing=True,
    )

    return scheduler


async def run_commission_check() -> None:
    """
    Executa o ciclo completo do Agente de Comissionamento.
    Acionado pelo CRON e também disponível via POST /scheduler/commission-check.
    """
    raise NotImplementedError

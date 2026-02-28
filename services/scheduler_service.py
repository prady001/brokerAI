"""
SchedulerService — CRON jobs via APScheduler.
Dispara a verificação de renovações diariamente às 08:00 BRT.
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from models.config import settings

logger = logging.getLogger(__name__)


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        run_renewal_check,
        trigger=CronTrigger(
            hour=settings.renewal_cron_hour,
            timezone=settings.renewal_cron_timezone,
        ),
        id="renewal_check",
        name="Verificação diária de renovações",
        replace_existing=True,
    )

    return scheduler


async def run_renewal_check() -> None:
    """
    Executa a verificação de apólices próximas do vencimento.
    Acionado pelo CRON e também disponível via POST /scheduler/renewal-check.
    Implementação completa no M4 (Agente de Renovação).
    """
    logger.info("Verificação de renovações iniciada")


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def _main() -> None:
        sched = create_scheduler()
        sched.start()
        logger.info("Scheduler iniciado. Pressione Ctrl+C para encerrar.")
        try:
            while True:
                await asyncio.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            sched.shutdown()
            logger.info("Scheduler encerrado.")

    asyncio.run(_main())

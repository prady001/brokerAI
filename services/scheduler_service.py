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
    """
    from agents.renewal.graph import renewal_graph
    from agents.renewal.nodes import inject_node_dependencies
    from models.database import AsyncSessionLocal
    from services.renewal_service import RenewalService

    logger.info("Verificação de renovações iniciada")

    async with AsyncSessionLocal() as db:
        renewal_service = RenewalService(db)
        inject_node_dependencies(renewal_service, llm=None)

        result = await renewal_graph.ainvoke({
            "mode": "cron",
            "policies_to_contact": [],
            "contacts_sent": [],
            "errors": [],
        })

    contacts_sent = len(result.get("contacts_sent", []))
    errors = result.get("errors", [])

    if errors:
        logger.warning("Verificação de renovações concluída com erros: %s", errors)
    else:
        logger.info("Verificação de renovações concluída: %d contatos enviados", contacts_sent)


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

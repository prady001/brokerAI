"""
FastAPI app principal do brokerAI.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import admin, scheduler, webhook
from services.scheduler_service import create_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialização
    scheduler = create_scheduler()
    scheduler.start()
    yield
    # Encerramento
    scheduler.shutdown()


app = FastAPI(
    title="brokerAI",
    description="Agentes de IA para corretora de seguros",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(webhook.router)
app.include_router(scheduler.router)
app.include_router(admin.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

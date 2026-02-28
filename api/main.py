"""
FastAPI app principal do brokerAI.
"""
from fastapi import FastAPI

from api.routes import admin, scheduler, webhook

app = FastAPI(
    title="brokerAI",
    description="Agentes de IA para corretora de seguros",
    version="0.1.0",
)

app.include_router(webhook.router)
app.include_router(scheduler.router)
app.include_router(admin.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

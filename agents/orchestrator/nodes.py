"""
Nós do Agente Orquestrador.
Gerencia estado de conversa no Redis e roteamento de intenções via LLM.
"""
import json
import logging

import redis.asyncio as aioredis
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from agents.orchestrator.prompts import INTENT_DETECTION_PROMPT
from models.config import settings
from services import notification_service

logger = logging.getLogger(__name__)

_CONVERSATION_TTL = 60 * 60 * 24 * 30  # 30 dias em segundos

_redis_client: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def _get_llm() -> ChatAnthropic:
    model = (
        "claude-haiku-4-5-20251001"
        if settings.environment == "development"
        else "claude-sonnet-4-6"
    )
    return ChatAnthropic(
        model=model,
        api_key=settings.anthropic_api_key,
        max_tokens=256,
    )


def _conversation_key(phone: str) -> str:
    return f"claim_conversation:{phone}"


# ---------------------------------------------------------------------------
# Gestão de estado no Redis
# ---------------------------------------------------------------------------

async def load_conversation_state(phone: str) -> dict | None:
    """Carrega estado de conversa ativa do Redis. Retorna None se não existir."""
    redis = _get_redis()
    raw = await redis.get(_conversation_key(phone))
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Estado corrompido no Redis para %s — removendo", phone)
        await redis.delete(_conversation_key(phone))
        return None


async def save_conversation_state(phone: str, state: dict) -> None:
    """Persiste o estado da conversa no Redis com TTL de 30 dias."""
    redis = _get_redis()
    await redis.set(_conversation_key(phone), json.dumps(state), ex=_CONVERSATION_TTL)


async def delete_conversation_state(phone: str) -> None:
    """Remove o estado da conversa (sinistro encerrado ou escalado)."""
    redis = _get_redis()
    await redis.delete(_conversation_key(phone))


# ---------------------------------------------------------------------------
# Nós do grafo do orquestrador
# ---------------------------------------------------------------------------

async def load_conversation_node(state: dict) -> dict:
    """
    Verifica no Redis se existe conversa de sinistro ativa para o número do cliente.
    Popula has_active_conversation e, se existir, carrega o ClaimsState.
    """
    phone = state.get("client_phone", "")
    conversation_state = await load_conversation_state(phone)
    if conversation_state:
        return {
            "has_active_conversation": True,
            "conversation_id": conversation_state.get("conversation_id", ""),
            "claims_state": conversation_state,
        }
    return {"has_active_conversation": False}


async def detect_intent_node(state: dict) -> dict:
    """
    Usa LLM para classificar a intenção da mensagem do cliente.
    Popula state['intent'] e state['confidence'].
    """
    message = state.get("message", "")
    llm = _get_llm()
    prompt = INTENT_DETECTION_PROMPT.format(message=message)
    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        raw = response.content.strip()
        start = raw.index("{")
        end = raw.rindex("}") + 1
        data = json.loads(raw[start:end])
        intent = data.get("intent", "unknown")
        confidence = float(data.get("confidence", 0.0))
        if confidence < 0.6:
            intent = "unknown"
        return {"intent": intent, "confidence": confidence}
    except Exception as exc:
        logger.error("Falha ao detectar intenção: %s", exc)
        return {"intent": "unknown", "confidence": 0.0}


async def faq_handler_node(state: dict) -> dict:
    """
    Responde dúvidas gerais sobre seguro com LLM.
    Não acessa dados do cliente — apenas knowledge base da corretora.
    """
    message = state.get("message", "")
    phone = state.get("client_phone", "")

    llm = _get_llm()
    system = (
        "Você é o assistente de uma corretora de seguros brasileira. "
        "Responda dúvidas gerais sobre seguros de forma clara e educada. "
        "Não acesse dados pessoais do cliente. "
        "Para questões específicas de apólice, peça ao cliente que informe "
        "seu nome ou número de apólice para ser atendido por um corretor. "
        "Responda sempre em português (pt-BR)."
    )
    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=message),
    ])
    answer = response.content.strip()
    await notification_service.send_whatsapp_message(phone, answer)
    return {}


async def human_handoff_node(state: dict) -> dict:
    """
    Para mensagens fora do escopo:
    1. Notifica o corretor com a mensagem original
    2. Informa o cliente que um corretor retornará em breve
    """
    message = state.get("message", "")
    phone = state.get("client_phone", "")
    client_name = state.get("client_name", "Cliente")

    # Alerta para a corretora
    alert = (
        f"📨 *MENSAGEM SEM INTENÇÃO IDENTIFICADA*\n\n"
        f"*Cliente:* {client_name} | {phone}\n"
        f"*Mensagem:* {message}\n\n"
        f"Por favor, entre em contato para atendê-lo."
    )
    await notification_service.send_broker_alert(alert)

    # Resposta ao cliente
    response_msg = (
        "Olá! Recebi sua mensagem. Um dos nossos atendentes "
        "vai retornar para você em breve. 😊"
    )
    await notification_service.send_whatsapp_message(phone, response_msg)
    return {}

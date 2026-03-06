"""
Factory de LLM — suporta Anthropic (Claude) e Google Gemini.
Controlado pela variável LLM_PROVIDER no .env.

Uso:
    from agents.llm import get_llm
    llm = get_llm(max_tokens=1024)
"""
import functools

from langchain_core.language_models.chat_models import BaseChatModel

from models.config import settings

# Modelos Google equivalentes por tier
_GOOGLE_MODELS = {
    "development": "gemini-2.5-flash",
    "production": "gemini-2.5-flash",
}

# Tokens mínimos para modelos thinking (thinking consome parte do budget)
_GOOGLE_MIN_TOKENS = 1024

# Modelos Anthropic por tier
_ANTHROPIC_MODELS = {
    "development": "claude-haiku-4-5-20251001",
    "production": "claude-sonnet-4-6",
}


@functools.lru_cache(maxsize=None)
def get_llm(max_tokens: int = 1024) -> BaseChatModel:
    env = settings.environment if settings.environment in ("development", "production") else "development"

    if settings.llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=_GOOGLE_MODELS[env],
            google_api_key=settings.google_api_key,
            max_output_tokens=max(max_tokens, _GOOGLE_MIN_TOKENS),
            thinking_budget=0,  # desabilita thinking — output previsível e rápido
        )

    # default: anthropic
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=_ANTHROPIC_MODELS[env],
        api_key=settings.anthropic_api_key,
        max_tokens=max_tokens,
    )

"""
Configurações do projeto carregadas via pydantic-settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # LLM
    llm_provider: str = "anthropic"  # "anthropic" | "google"
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # WhatsApp (Evolution API — self-hosted)
    evolution_server_url: str = "http://localhost:8080"
    evolution_api_key: str
    evolution_instance_name: str = "brokerai"

    # Banco de dados
    database_url: str
    postgres_db: str = "insurance_agents"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    redis_url: str

    # Storage (Cloudflare R2 — compatível com S3)
    cloudflare_r2_account_id: str = ""
    cloudflare_r2_access_key_id: str = ""
    cloudflare_r2_secret_access_key: str = ""
    cloudflare_r2_bucket: str = "brokerai-documents"
    cloudflare_r2_endpoint: str = ""

    # Token interno para rotas admin/scheduler
    internal_api_token: str = ""

    # Notificações
    broker_notification_phone: str
    broker_notification_email: str
    broker_name: str = "sua corretora"

    # Agente de renovação (CRON)
    renewal_cron_hour: int = 8
    renewal_cron_timezone: str = "America/Sao_Paulo"
    renewal_alert_days: str = "30,15,7,0"   # dias antes do vencimento
    renewal_max_contacts: int = 4
    renewal_overdue_days: int = 3

    # Observabilidade
    langchain_api_key: str = ""
    langchain_tracing_v2: bool = True
    sentry_dsn: str = ""

    # Ambiente
    environment: str = "development"

    # ---------------------------------------------------------------------------
    # V1+ — Graph Memory (Graphiti + Neo4j)
    # ---------------------------------------------------------------------------
    graph_memory_enabled: bool = False
    graphiti_api_key: str = ""
    graphiti_api_url: str = "http://localhost:8001"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    langmem_enabled: bool = False


settings = Settings()  # type: ignore[call-arg]

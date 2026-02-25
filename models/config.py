"""
Configurações do projeto carregadas via pydantic-settings.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    anthropic_api_key: str

    # WhatsApp
    zapi_instance_id: str
    zapi_token: str
    zapi_webhook_secret: str

    # Banco de dados
    database_url: str
    redis_url: str

    # AWS
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = ""

    # NFS-e
    focus_nfe_api_key: str
    focus_nfe_base_url: str = "https://producao.focusnfe.com.br"
    broker_cnpj: str
    broker_city_code: str

    # 2FA / SMS Gateway
    sms_gateway_provider: str = ""
    sms_gateway_api_key: str = ""
    sms_gateway_from_number: str = ""

    # 2FA / Email IMAP
    imap_host: str = ""
    imap_port: int = 993
    imap_user: str = ""
    imap_password: str = ""

    # Credenciais de seguradoras
    insurer_credentials_path: str = "./config/insurers.json.enc"
    insurer_credentials_key: str

    # Notificações
    sendgrid_api_key: str = ""
    broker_notification_phone: str
    broker_notification_email: str

    # Schedule
    commission_cron_hour: int = 8
    commission_cron_timezone: str = "America/Sao_Paulo"

    # Observabilidade
    langchain_api_key: str = ""
    langchain_tracing_v2: bool = True
    sentry_dsn: str = ""

    # Ambiente
    environment: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

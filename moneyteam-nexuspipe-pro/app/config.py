from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MONEYTEAM / NexusPipe Pro"
    version: str = "4.4.0"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite:///./data/app.db"
    storage_dir: str = "./storage"
    max_upload_mb: int = 100

    # Safety defaults — live execution is OFF by design.
    trading_mode: str = "paper"
    financial_mode: str = "sandbox"
    allow_live_execution: bool = False
    require_human_approval: bool = True
    live_approval_token: str = ""
    admin_token: str = ""
    require_auth: bool = True

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_live: bool = False

    coinbase_api_key: str = ""
    coinbase_api_secret: str = ""
    coinbase_live: bool = False

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    enable_openai: bool = False

    # Local LLM (Ollama) — offline-first: disabled until explicitly turned on.
    local_llm_enabled: bool = False
    local_llm_url: str = "http://127.0.0.1:11434"
    local_llm_model: str = "llama3.2"

    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    trusted_hosts: str = "localhost,127.0.0.1"
    rate_limit_per_minute: int = 60
    provider_timeout_seconds: float = 20.0
    provider_max_retries: int = 3
    webhook_replay_seconds: int = 300
    backup_required: bool = False
    monitoring_enabled: bool = False
    sentry_dsn: str = ""
    kill_switch: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_list(self):
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

    @property
    def trusted_hosts_list(self):
        return [x.strip() for x in self.trusted_hosts.split(",") if x.strip()]

    @field_validator("financial_mode")
    @classmethod
    def financial_mode_valid(cls, v):
        if v not in {"sandbox", "live"}:
            raise ValueError("FINANCIAL_MODE must be sandbox or live")
        return v

    @field_validator("trading_mode")
    @classmethod
    def trading_mode_valid(cls, v):
        if v not in {"paper", "live"}:
            raise ValueError("TRADING_MODE must be paper or live")
        return v


@lru_cache
def get_settings():
    return Settings()

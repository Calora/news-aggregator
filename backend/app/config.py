from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = f"sqlite:///{(BACKEND_DIR / 'news_aggregator.db').as_posix()}"
DEFAULT_ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    database_url: str = DEFAULT_DATABASE_URL
    update_interval_hours: int = 4

    # HTTP proxy for external APIs (e.g., Gmail)
    http_proxy: str = ""

    # Gmail API OAuth
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_refresh_token: str = ""

    email_accounts: str = ""

    # Feishu (Lark) API
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_folder_token: str = ""
    feishu_material_doc_id: str = ""
    feishu_topic_doc_id: str = ""

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        sqlite_prefix = "sqlite:///"
        if not value.startswith(sqlite_prefix):
            return value
        database_path = value[len(sqlite_prefix):]
        if database_path.startswith(":memory:"):
            return value
        path = Path(database_path)
        if path.is_absolute():
            return value
        return f"{sqlite_prefix}{(BACKEND_DIR / path).resolve().as_posix()}"

    @property
    def parsed_email_accounts(self) -> list[dict]:
        """Parse EMAIL_ACCOUNTS env var into list of dicts.
        Format: email:auth_code:imap_server:imap_port,...
        Special: email:gmail_api::: uses Gmail API instead of IMAP
        """
        if not self.email_accounts:
            return []
        accounts = []
        for item in self.email_accounts.split(","):
            item = item.strip()
            if not item:
                continue
            parts = item.split(":")
            if len(parts) >= 4:
                accounts.append({
                    "email": parts[0],
                    "auth_code": parts[1],
                    "imap_server": parts[2],
                    "imap_port": int(parts[3]) if parts[3].isdigit() else 0,
                })
        return accounts

    model_config = {"env_file": DEFAULT_ENV_FILE, "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

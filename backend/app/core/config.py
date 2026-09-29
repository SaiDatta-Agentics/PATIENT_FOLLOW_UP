from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "SaiDatta Patient Follow-Up Agent"
    APP_VERSION: str = "3.0.1"
    SECRET_KEY: str = "change-me-in-production-use-keyvault"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    DATABASE_URL: str = "sqlite+aiosqlite:///./followup.db"
    DEMO_MODE: bool = True
    AUTO_FOLLOWUP_ENABLED: bool = True
    FOLLOWUP_POLL_SECONDS: int = 15
    RETRY_HOURS: int = 24
    CLINIC_ACCESS_CODE: str = "CLINIC-DEMO"

    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_KEY: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4.1-mini"
    AZURE_OPENAI_API_VERSION: str = "2024-10-21"

    AZURE_COMMUNICATION_CONNECTION_STRING: Optional[str] = None
    AZURE_SMS_FROM_NUMBER: Optional[str] = None
    AZURE_CALLER_ID: Optional[str] = None
    AZURE_CALL_CALLBACK_URL: Optional[str] = None

    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_STORAGE_CONTAINER: str = "patient-files"

    CLINIC_NAME: str = "SaiDatta Dental Clinic"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

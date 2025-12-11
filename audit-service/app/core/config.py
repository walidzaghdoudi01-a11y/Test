import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://audituser:auditpass@localhost:5432/auditdb"
    )
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    CORS_ORIGINS: List[str] = ["*"]
    
    # Security settings
    ENABLE_SIGNATURES: bool = False
    SIGNATURE_SECRET: str = os.getenv("SIGNATURE_SECRET", "change-me-in-production")
    
    # Retention settings
    DEFAULT_RETENTION_DAYS: int = 2555
    ARCHIVE_ENABLED: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings()

"""Configuration settings and data source registry."""

from typing import Any, Dict, List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class DataSource(BaseSettings):
    """Configuration for a data source."""

    model_config = SettingsConfigDict(env_prefix="")

    name: str
    type: str
    enabled: bool = True
    config: Dict[str, Any] = {}


class DataSourceRegistry(BaseSettings):
    """Registry of configured data sources."""

    sources: List[DataSource] = []

    def get_enabled_sources(self) -> List[DataSource]:
        """Get all enabled data sources."""
        return [source for source in self.sources if source.enabled]

    def get_source_by_name(self, name: str) -> Optional[DataSource]:
        """Get a data source by name."""
        for source in self.sources:
            if source.name == name:
                return source
        return None


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    app_name: str = "Threat Intelligence Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # Storage Configuration
    timeseries_db_url: str = "file:///var/lib/ti-platform/timeseries"
    document_db_url: str = "file:///var/lib/ti-platform/documents"

    # Data Sources Registry
    data_sources: DataSourceRegistry = DataSourceRegistry()


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the application settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset the settings instance (useful for testing)."""
    global _settings
    _settings = None

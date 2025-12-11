"""Tests for configuration management."""

from libs.config import DataSource, DataSourceRegistry, Settings, get_settings


class TestDataSourceRegistry:
    """Tests for DataSourceRegistry."""

    def test_registry_creation(self):
        """Test creating a data source registry."""
        registry = DataSourceRegistry()
        assert registry.sources == []

    def test_add_sources(self):
        """Test adding sources to registry."""
        source1 = DataSource(name="feed1", type="external", enabled=True)
        source2 = DataSource(name="feed2", type="external", enabled=False)

        registry = DataSourceRegistry(sources=[source1, source2])
        assert len(registry.sources) == 2

    def test_get_enabled_sources(self):
        """Test getting only enabled sources."""
        source1 = DataSource(name="feed1", type="external", enabled=True)
        source2 = DataSource(name="feed2", type="external", enabled=False)
        source3 = DataSource(name="feed3", type="internal", enabled=True)

        registry = DataSourceRegistry(sources=[source1, source2, source3])
        enabled = registry.get_enabled_sources()

        assert len(enabled) == 2
        assert enabled[0].name == "feed1"
        assert enabled[1].name == "feed3"

    def test_get_source_by_name(self):
        """Test retrieving a source by name."""
        source = DataSource(name="my-feed", type="external")
        registry = DataSourceRegistry(sources=[source])

        found = registry.get_source_by_name("my-feed")
        assert found is not None
        assert found.name == "my-feed"

    def test_get_nonexistent_source(self):
        """Test retrieving a nonexistent source."""
        registry = DataSourceRegistry()
        found = registry.get_source_by_name("nonexistent")
        assert found is None


class TestSettings:
    """Tests for Settings."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()
        assert settings.app_name == "Threat Intelligence Platform"
        assert settings.api_port == 8000
        assert settings.debug is False

    def test_settings_from_env(self, monkeypatch):
        """Test loading settings from environment variables."""
        monkeypatch.setenv("APP_NAME", "Custom TI Platform")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("API_PORT", "9000")

        settings = Settings()
        assert settings.app_name == "Custom TI Platform"
        assert settings.debug is True
        assert settings.api_port == 9000


class TestGetSettings:
    """Tests for get_settings singleton."""

    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        from libs.config import reset_settings

        reset_settings()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

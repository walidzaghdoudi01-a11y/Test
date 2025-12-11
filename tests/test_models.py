"""Tests for core domain models."""

from datetime import datetime

from libs.core.models import (
    Asset,
    AssetType,
    Indicator,
    IndicatorType,
    SeverityLevel,
    ThreatEvent,
)


class TestAsset:
    """Tests for the Asset model."""

    def test_asset_creation(self):
        """Test creating an asset."""
        asset = Asset(id="asset-1", name="Server 1", asset_type=AssetType.SERVER)
        assert asset.id == "asset-1"
        assert asset.name == "Server 1"
        assert asset.asset_type == AssetType.SERVER
        assert asset.created_at is not None

    def test_asset_with_metadata(self):
        """Test asset with custom metadata."""
        metadata = {"ip": "192.168.1.1", "os": "Linux"}
        asset = Asset(
            id="asset-2",
            name="Server 2",
            asset_type=AssetType.SERVER,
            metadata=metadata,
        )
        assert asset.metadata == metadata


class TestIndicator:
    """Tests for the Indicator model."""

    def test_indicator_creation(self):
        """Test creating an indicator."""
        indicator = Indicator(
            id="ind-1",
            indicator_type=IndicatorType.IP_ADDRESS,
            value="192.168.1.100",
            source="external-feed",
        )
        assert indicator.id == "ind-1"
        assert indicator.indicator_type == IndicatorType.IP_ADDRESS
        assert indicator.value == "192.168.1.100"
        assert indicator.confidence == 1.0

    def test_indicator_confidence_validation(self):
        """Test confidence score validation."""
        indicator = Indicator(
            id="ind-2",
            indicator_type=IndicatorType.DOMAIN,
            value="malicious.com",
            source="feed",
            confidence=0.85,
        )
        assert indicator.confidence == 0.85


class TestThreatEvent:
    """Tests for the ThreatEvent model."""

    def test_event_creation(self):
        """Test creating a threat event."""
        event = ThreatEvent(
            id="event-1",
            title="Suspicious Activity Detected",
            severity=SeverityLevel.HIGH,
            detected_at=datetime.utcnow(),
        )
        assert event.id == "event-1"
        assert event.title == "Suspicious Activity Detected"
        assert event.severity == SeverityLevel.HIGH

    def test_event_with_assets_and_indicators(self):
        """Test event with related assets and indicators."""
        event = ThreatEvent(
            id="event-2",
            title="Malware Detected",
            severity=SeverityLevel.CRITICAL,
            detected_at=datetime.utcnow(),
            asset_ids=["asset-1", "asset-2"],
            indicator_ids=["ind-1", "ind-2"],
        )
        assert event.asset_ids == ["asset-1", "asset-2"]
        assert event.indicator_ids == ["ind-1", "ind-2"]

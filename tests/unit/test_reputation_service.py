import pytest

from services.reputation_lookup.feeds import FeedAggregator, MockThreatFeed
from services.reputation_lookup.models import ReputationScore
from services.reputation_lookup.service import ReputationLookupService


@pytest.fixture
def reputation_service():
    """Create reputation service for testing"""
    feeds = [MockThreatFeed(name="TestFeed", latency_ms=10)]
    aggregator = FeedAggregator(feeds)
    return ReputationLookupService(feed_aggregator=aggregator, cache=None)


@pytest.mark.asyncio
async def test_lookup_malicious_ip(reputation_service):
    """Test lookup of known malicious IP"""
    result = await reputation_service.lookup_ip("192.168.1.100", use_cache=False)
    
    assert result.ip_address == "192.168.1.100"
    assert result.overall_score == ReputationScore.MALICIOUS
    assert result.risk_score > 80
    assert len(result.sources) > 0
    assert not result.cached


@pytest.mark.asyncio
async def test_lookup_clean_ip(reputation_service):
    """Test lookup of clean IP"""
    result = await reputation_service.lookup_ip("8.8.8.8", use_cache=False)
    
    assert result.ip_address == "8.8.8.8"
    assert result.overall_score == ReputationScore.CLEAN
    assert result.risk_score < 30
    assert len(result.sources) > 0


@pytest.mark.asyncio
async def test_lookup_malicious_domain(reputation_service):
    """Test lookup of known malicious domain"""
    result = await reputation_service.lookup_domain("malicious-site.evil", use_cache=False)
    
    assert result.domain == "malicious-site.evil"
    assert result.overall_score == ReputationScore.MALICIOUS
    assert result.risk_score > 80
    assert len(result.sources) > 0


@pytest.mark.asyncio
async def test_lookup_clean_domain(reputation_service):
    """Test lookup of clean domain"""
    result = await reputation_service.lookup_domain("google.com", use_cache=False)
    
    assert result.domain == "google.com"
    assert result.overall_score == ReputationScore.CLEAN
    assert result.risk_score < 30


@pytest.mark.asyncio
async def test_invalid_ip_address(reputation_service):
    """Test validation of invalid IP address"""
    with pytest.raises(ValueError, match="Invalid IP address"):
        await reputation_service.lookup_ip("invalid.ip.address")


@pytest.mark.asyncio
async def test_invalid_domain(reputation_service):
    """Test validation of invalid domain"""
    with pytest.raises(ValueError, match="Invalid domain"):
        await reputation_service.lookup_domain("invalid domain with spaces")


def test_ip_validation():
    """Test IP address validation"""
    assert ReputationLookupService._is_valid_ip("192.168.1.1")
    assert ReputationLookupService._is_valid_ip("8.8.8.8")
    assert not ReputationLookupService._is_valid_ip("256.1.1.1")
    assert not ReputationLookupService._is_valid_ip("not.an.ip")
    assert not ReputationLookupService._is_valid_ip("192.168.1")


def test_domain_validation():
    """Test domain validation"""
    assert ReputationLookupService._is_valid_domain("example.com")
    assert ReputationLookupService._is_valid_domain("sub.domain.example.org")
    assert not ReputationLookupService._is_valid_domain("invalid domain")
    assert not ReputationLookupService._is_valid_domain("no-tld")
    assert not ReputationLookupService._is_valid_domain("-invalid.com")

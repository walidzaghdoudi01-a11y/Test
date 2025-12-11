import asyncio
import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List

from services.reputation_lookup.models import (
    ReputationScore,
    ReputationSource,
    ThreatCategory,
)


class ReputationFeed(ABC):
    """Base class for reputation feeds"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def lookup_ip(self, ip_address: str) -> ReputationSource:
        """Lookup IP address reputation"""
        pass

    @abstractmethod
    async def lookup_domain(self, domain: str) -> ReputationSource:
        """Lookup domain reputation"""
        pass


class MockThreatFeed(ReputationFeed):
    """Mock threat intelligence feed for testing"""

    KNOWN_BAD_IPS = {
        "192.168.1.100": (ReputationScore.MALICIOUS, [ThreatCategory.MALWARE], 0.95),
        "10.0.0.50": (ReputationScore.SUSPICIOUS, [ThreatCategory.SCANNING], 0.75),
        "203.0.113.10": (ReputationScore.MALICIOUS, [ThreatCategory.C2], 0.98),
        "198.51.100.20": (ReputationScore.SUSPICIOUS, [ThreatCategory.BOTNET], 0.70),
    }

    KNOWN_BAD_DOMAINS = {
        "malicious-site.evil": (
            ReputationScore.MALICIOUS,
            [ThreatCategory.PHISHING],
            0.99,
        ),
        "suspicious-domain.net": (
            ReputationScore.SUSPICIOUS,
            [ThreatCategory.SPAM],
            0.65,
        ),
        "c2-server.bad": (ReputationScore.MALICIOUS, [ThreatCategory.C2], 0.97),
        "cryptominer.xyz": (
            ReputationScore.MALICIOUS,
            [ThreatCategory.CRYPTOCURRENCY],
            0.85,
        ),
    }

    def __init__(self, name: str = "MockThreatFeed", latency_ms: int = 100):
        super().__init__(name)
        self.latency_ms = latency_ms

    async def lookup_ip(self, ip_address: str) -> ReputationSource:
        await asyncio.sleep(self.latency_ms / 1000.0)

        if ip_address in self.KNOWN_BAD_IPS:
            score, categories, confidence = self.KNOWN_BAD_IPS[ip_address]
            last_seen = datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        else:
            score = ReputationScore.CLEAN
            categories = []
            confidence = 0.9
            last_seen = None

        return ReputationSource(
            name=self.name,
            score=score,
            categories=categories,
            confidence=confidence,
            last_seen=last_seen,
            metadata={"source_type": "mock", "ip": ip_address},
        )

    async def lookup_domain(self, domain: str) -> ReputationSource:
        await asyncio.sleep(self.latency_ms / 1000.0)

        if domain in self.KNOWN_BAD_DOMAINS:
            score, categories, confidence = self.KNOWN_BAD_DOMAINS[domain]
            last_seen = datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        else:
            score = ReputationScore.CLEAN
            categories = []
            confidence = 0.85
            last_seen = None

        return ReputationSource(
            name=self.name,
            score=score,
            categories=categories,
            confidence=confidence,
            last_seen=last_seen,
            metadata={"source_type": "mock", "domain": domain},
        )


class AbuseIPDBFeed(ReputationFeed):
    """Mock AbuseIPDB feed"""

    def __init__(self):
        super().__init__("AbuseIPDB")

    async def lookup_ip(self, ip_address: str) -> ReputationSource:
        await asyncio.sleep(0.15)

        abuse_score = random.randint(0, 100)
        if abuse_score > 80:
            score = ReputationScore.MALICIOUS
            confidence = 0.95
            categories = [ThreatCategory.SCANNING, ThreatCategory.BOTNET]
        elif abuse_score > 40:
            score = ReputationScore.SUSPICIOUS
            confidence = 0.75
            categories = [ThreatCategory.SCANNING]
        else:
            score = ReputationScore.CLEAN
            confidence = 0.90
            categories = []

        return ReputationSource(
            name=self.name,
            score=score,
            categories=categories,
            confidence=confidence,
            last_seen=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            if score != ReputationScore.CLEAN
            else None,
            metadata={"abuse_score": str(abuse_score)},
        )

    async def lookup_domain(self, domain: str) -> ReputationSource:
        return ReputationSource(
            name=self.name,
            score=ReputationScore.UNKNOWN,
            categories=[],
            confidence=0.0,
            metadata={"error": "Domain lookup not supported"},
        )


class VirusTotalFeed(ReputationFeed):
    """Mock VirusTotal feed"""

    def __init__(self):
        super().__init__("VirusTotal")

    async def lookup_ip(self, ip_address: str) -> ReputationSource:
        await asyncio.sleep(0.2)

        detections = random.randint(0, 70)
        if detections > 10:
            score = ReputationScore.MALICIOUS
            confidence = 0.98
            categories = [ThreatCategory.MALWARE, ThreatCategory.C2]
        elif detections > 3:
            score = ReputationScore.SUSPICIOUS
            confidence = 0.70
            categories = [ThreatCategory.OTHER]
        else:
            score = ReputationScore.CLEAN
            confidence = 0.85
            categories = []

        return ReputationSource(
            name=self.name,
            score=score,
            categories=categories,
            confidence=confidence,
            last_seen=datetime.utcnow() - timedelta(hours=random.randint(0, 168))
            if score != ReputationScore.CLEAN
            else None,
            metadata={"detections": f"{detections}/70", "total_votes": "65"},
        )

    async def lookup_domain(self, domain: str) -> ReputationSource:
        await asyncio.sleep(0.25)

        detections = random.randint(0, 80)
        if detections > 15:
            score = ReputationScore.MALICIOUS
            confidence = 0.97
            categories = [ThreatCategory.PHISHING, ThreatCategory.MALWARE]
        elif detections > 5:
            score = ReputationScore.SUSPICIOUS
            confidence = 0.65
            categories = [ThreatCategory.PHISHING]
        else:
            score = ReputationScore.CLEAN
            confidence = 0.88
            categories = []

        return ReputationSource(
            name=self.name,
            score=score,
            categories=categories,
            confidence=confidence,
            last_seen=datetime.utcnow() - timedelta(hours=random.randint(0, 168))
            if score != ReputationScore.CLEAN
            else None,
            metadata={"detections": f"{detections}/80", "total_votes": "78"},
        )


class FeedAggregator:
    """Aggregates results from multiple reputation feeds"""

    def __init__(self, feeds: List[ReputationFeed]):
        self.feeds = feeds

    async def lookup_ip(self, ip_address: str) -> List[ReputationSource]:
        """Query all feeds for IP reputation"""
        tasks = [feed.lookup_ip(ip_address) for feed in self.feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        sources = []
        for result in results:
            if isinstance(result, Exception):
                continue
            sources.append(result)

        return sources

    async def lookup_domain(self, domain: str) -> List[ReputationSource]:
        """Query all feeds for domain reputation"""
        tasks = [feed.lookup_domain(domain) for feed in self.feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        sources = []
        for result in results:
            if isinstance(result, Exception):
                continue
            sources.append(result)

        return sources

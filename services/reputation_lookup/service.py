import re
from datetime import datetime
from typing import List, Optional

from services.reputation_lookup.cache import ReputationCache
from services.reputation_lookup.feeds import FeedAggregator
from services.reputation_lookup.models import (
    DomainReputationResponse,
    IPReputationResponse,
    ReputationScore,
    ReputationSource,
    ThreatCategory,
)


class ReputationLookupService:
    """Service for looking up IP and domain reputation"""

    def __init__(self, feed_aggregator: FeedAggregator, cache: Optional[ReputationCache] = None):
        self.feed_aggregator = feed_aggregator
        self.cache = cache

    @staticmethod
    def _is_valid_ip(ip_address: str) -> bool:
        """Validate IP address format"""
        pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if not re.match(pattern, ip_address):
            return False

        parts = ip_address.split(".")
        return all(0 <= int(part) <= 255 for part in parts)

    @staticmethod
    def _is_valid_domain(domain: str) -> bool:
        """Validate domain format"""
        pattern = r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        return bool(re.match(pattern, domain))

    @staticmethod
    def _aggregate_score(sources: List[ReputationSource]) -> ReputationScore:
        """Aggregate reputation scores from multiple sources"""
        if not sources:
            return ReputationScore.UNKNOWN

        malicious_count = sum(1 for s in sources if s.score == ReputationScore.MALICIOUS)
        suspicious_count = sum(1 for s in sources if s.score == ReputationScore.SUSPICIOUS)

        if malicious_count >= 1:
            return ReputationScore.MALICIOUS
        elif suspicious_count >= 1:
            return ReputationScore.SUSPICIOUS
        else:
            return ReputationScore.CLEAN

    @staticmethod
    def _calculate_risk_score(sources: List[ReputationSource]) -> float:
        """Calculate overall risk score 0-100"""
        if not sources:
            return 0.0

        score_map = {
            ReputationScore.CLEAN: 0,
            ReputationScore.SUSPICIOUS: 50,
            ReputationScore.MALICIOUS: 100,
            ReputationScore.UNKNOWN: 25,
        }

        weighted_sum = 0.0
        total_confidence = 0.0

        for source in sources:
            base_score = score_map.get(source.score, 0)
            weighted_sum += base_score * source.confidence
            total_confidence += source.confidence

        if total_confidence == 0:
            return 0.0

        return round(weighted_sum / total_confidence, 2)

    @staticmethod
    def _aggregate_categories(sources: List[ReputationSource]) -> List[ThreatCategory]:
        """Aggregate threat categories from all sources"""
        categories_set = set()
        for source in sources:
            categories_set.update(source.categories)
        return list(categories_set)

    async def lookup_ip(self, ip_address: str, use_cache: bool = True) -> IPReputationResponse:
        """Lookup IP address reputation"""
        if not self._is_valid_ip(ip_address):
            raise ValueError(f"Invalid IP address: {ip_address}")

        if use_cache and self.cache:
            cached = await self.cache.get_ip(ip_address)
            if cached:
                return cached

        sources = await self.feed_aggregator.lookup_ip(ip_address)
        overall_score = self._aggregate_score(sources)
        risk_score = self._calculate_risk_score(sources)
        categories = self._aggregate_categories(sources)

        first_seen = min(
            (s.last_seen for s in sources if s.last_seen), default=None
        )
        last_seen = max(
            (s.last_seen for s in sources if s.last_seen), default=None
        )

        response = IPReputationResponse(
            ip_address=ip_address,
            overall_score=overall_score,
            risk_score=risk_score,
            sources=sources,
            categories=categories,
            first_seen=first_seen,
            last_seen=last_seen,
            cached=False,
            queried_at=datetime.utcnow(),
        )

        if self.cache:
            await self.cache.set_ip(ip_address, response)

        return response

    async def lookup_domain(
        self, domain: str, use_cache: bool = True
    ) -> DomainReputationResponse:
        """Lookup domain reputation"""
        if not self._is_valid_domain(domain):
            raise ValueError(f"Invalid domain: {domain}")

        if use_cache and self.cache:
            cached = await self.cache.get_domain(domain)
            if cached:
                return cached

        sources = await self.feed_aggregator.lookup_domain(domain)
        overall_score = self._aggregate_score(sources)
        risk_score = self._calculate_risk_score(sources)
        categories = self._aggregate_categories(sources)

        first_seen = min(
            (s.last_seen for s in sources if s.last_seen), default=None
        )
        last_seen = max(
            (s.last_seen for s in sources if s.last_seen), default=None
        )

        response = DomainReputationResponse(
            domain=domain,
            overall_score=overall_score,
            risk_score=risk_score,
            sources=sources,
            categories=categories,
            first_seen=first_seen,
            last_seen=last_seen,
            cached=False,
            queried_at=datetime.utcnow(),
        )

        if self.cache:
            await self.cache.set_domain(domain, response)

        return response

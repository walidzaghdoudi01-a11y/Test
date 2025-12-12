import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.monitoring.api import router as monitoring_router
from services.monitoring.api import set_streaming_processor
from services.monitoring.notifier import (
    MockEmailNotifier,
    MockWebhookNotifier,
    NotificationManager,
)
from services.monitoring.processor import StreamingProcessor
from services.reputation_lookup.api import router as reputation_router
from services.reputation_lookup.api import set_reputation_service
from services.reputation_lookup.cache import ReputationCache
from services.reputation_lookup.feeds import (
    AbuseIPDBFeed,
    FeedAggregator,
    MockThreatFeed,
    VirusTotalFeed,
)
from services.reputation_lookup.service import ReputationLookupService


streaming_processor_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global streaming_processor_task
    
    cache = ReputationCache(redis_url="redis://localhost:6379", ttl_seconds=3600)
    try:
        await cache.connect()
        print("Connected to Redis cache")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}. Running without cache.")
        cache = None
    
    feeds = [
        MockThreatFeed(name="MockThreatFeed", latency_ms=50),
        AbuseIPDBFeed(),
        VirusTotalFeed(),
    ]
    feed_aggregator = FeedAggregator(feeds)
    
    reputation_service = ReputationLookupService(
        feed_aggregator=feed_aggregator,
        cache=cache,
    )
    set_reputation_service(reputation_service)
    
    notification_manager = NotificationManager()
    notification_manager.add_notifier("email", MockEmailNotifier())
    notification_manager.add_notifier("webhook", MockWebhookNotifier())
    
    processor = StreamingProcessor(
        notification_manager=notification_manager,
        alert_threshold=10,
        window_seconds=60,
    )
    set_streaming_processor(processor)
    
    streaming_processor_task = asyncio.create_task(processor.start())
    print("Started streaming processor")
    
    yield
    
    await processor.stop()
    if streaming_processor_task:
        streaming_processor_task.cancel()
        try:
            await streaming_processor_task
        except asyncio.CancelledError:
            pass
    
    if cache:
        await cache.disconnect()
    
    print("Shutdown complete")


app = FastAPI(
    title="Threat Intelligence Monitoring & Reputation Service",
    description="Real-time threat monitoring with streaming processor and reputation lookup APIs",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(monitoring_router)
app.include_router(reputation_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Threat Intelligence Monitoring & Reputation Service",
        "version": "1.0.0",
        "endpoints": {
            "monitoring": "/api/v1/monitoring",
            "reputation": "/api/v1/reputation",
            "health": "/api/v1/monitoring/health",
            "metrics": "/api/v1/monitoring/metrics",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health():
    """Simple health check"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

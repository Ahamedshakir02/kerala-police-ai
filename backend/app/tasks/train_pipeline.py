"""
Celery Task — Async FIR Training Pipeline
Triggered by /api/firs/{id}/train endpoint when Redis is configured.
"""

from celery import Celery
import asyncio
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "kpai_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, name="train_fir", max_retries=3)
def train_fir_task(self, fir_id: str):
    """
    Celery task wrapper for the async FIR ingestion pipeline.
    Creates a new event loop per task execution.
    """
    try:
        from app.core.database import AsyncSessionLocal
        from app.services.training_service import ingest_fir

        async def _run():
            async with AsyncSessionLocal() as db:
                return await ingest_fir(fir_id, db)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(_run())
        loop.close()

        if not success:
            raise RuntimeError(f"Ingestion returned False for FIR {fir_id}")

        logger.info(f"✅ Celery: FIR {fir_id} training complete")
        return {"fir_id": fir_id, "status": "success"}

    except Exception as exc:
        logger.error(f"❌ Celery task failed for FIR {fir_id}: {exc}")
        raise self.retry(exc=exc, countdown=30)

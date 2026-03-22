"""
Training / Ingestion Service
Orchestrates the FIR ingestion pipeline:
  1. Extract text from PDF (if applicable)
  2. Run NLP: entities + IPC sections
  3. Generate embedding
  4. Upsert into ChromaDB
  5. Update FIR record in PostgreSQL
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.fir import FIR, FIRStatus
from app.services.nlp_service import get_nlp_service
from app.services.embedding_service import get_embedding_service
from app.services.chroma_service import get_chroma_service

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract plain text from PDF bytes using pdfplumber."""
    try:
        import pdfplumber
        import io
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages).strip()
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return ""


async def ingest_fir(fir_id: str, db: AsyncSession) -> bool:
    """
    Full pipeline: NLP → embed → ChromaDB upsert → DB update.
    Called inline (sync) or via Celery task.
    """
    try:
        result = await db.execute(select(FIR).where(FIR.id == UUID(fir_id)))
        fir = result.scalar_one_or_none()
        if not fir:
            logger.error(f"FIR {fir_id} not found")
            return False

        nlp = get_nlp_service()
        embed_svc = get_embedding_service()
        chroma = get_chroma_service()

        # Step 1: NLP
        entities = nlp.extract_entities(fir.raw_text)
        ipc_sections = nlp.suggest_ipc_sections(fir.raw_text, entities)
        section_nums = [s["section"] for s in ipc_sections]
        category = nlp.get_crime_category(section_nums)
        risk = nlp.get_risk_level(section_nums)
        mo = nlp.detect_mo_pattern(fir.raw_text, section_nums)
        summary = nlp.generate_summary(fir.raw_text, entities, ipc_sections)

        # Step 2: Embed
        vector = embed_svc.embed(fir.raw_text)

        # Step 3: ChromaDB upsert
        embedded_id = None
        if vector:
            metadata = {
                "case_number": fir.case_number,
                "district": fir.district,
                "police_station": fir.police_station,
                "crime_category": category,
                "risk_level": risk,
                "mo_pattern": mo or "",
                "date_registered": str(fir.date_registered),
            }
            success = chroma.upsert_fir(str(fir.id), vector, metadata)
            if success:
                embedded_id = str(fir.id)
                logger.info(f"✅ FIR {fir.case_number} indexed in ChromaDB")

        # Step 4: Update DB
        fir.extracted_entities = entities
        fir.ipc_sections = ipc_sections
        fir.crime_category = category
        fir.risk_level = risk
        fir.mo_pattern = mo
        fir.ai_summary = summary
        fir.status = FIRStatus.INDEXED if embedded_id else FIRStatus.ANALYSED
        fir.embedding_id = embedded_id
        fir.indexed_at = datetime.now(timezone.utc)

        await db.commit()
        logger.info(f"✅ FIR {fir.case_number} ingestion complete (risk: {risk}, IPC: {section_nums})")
        return True

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ FIR ingestion failed for {fir_id}: {e}", exc_info=True)
        return False

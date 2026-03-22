"""Analysis API — Real-time NLP FIR Analysis & Semantic Similarity Search"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_officer
from app.models.officer import Officer
from app.models.fir import FIR
from app.schemas.schemas import AnalysisRequest, AnalysisResponse, SimilarFIR
from app.services.nlp_service import get_nlp_service
from app.services.embedding_service import get_embedding_service
from app.services.chroma_service import get_chroma_service

router = APIRouter()


@router.post("/analyze-fir", response_model=AnalysisResponse)
async def analyze_fir(
    req: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer),
):
    """
    Full real-time NLP analysis of FIR text:
      - Named Entity Recognition (complainant, accused, location, weapon…)
      - IPC Section classification with confidence scores
      - Risk level assessment
      - MO pattern detection
      - Semantic similarity search against indexed FIRs in ChromaDB
    """
    nlp = get_nlp_service()
    embed_svc = get_embedding_service()
    chroma = get_chroma_service()

    # 1. Extract entities
    entities = nlp.extract_entities(req.text)

    # 2. Classify IPC sections
    ipc_sections = nlp.suggest_ipc_sections(req.text, entities)
    section_nums = [s["section"] for s in ipc_sections]

    # 3. Meta analysis
    category = nlp.get_crime_category(section_nums)
    risk = nlp.get_risk_level(section_nums)
    mo = nlp.detect_mo_pattern(req.text, section_nums)
    summary = nlp.generate_summary(req.text, entities, ipc_sections)
    next_steps = nlp.generate_next_steps(ipc_sections, risk)

    # 4. Semantic similarity via ChromaDB
    similar_firs = []
    vector = embed_svc.embed(req.text)
    if vector and chroma.is_available:
        hits = chroma.search_similar(vector, k=5)
        for hit in hits:
            fir_id = hit["id"]
            meta = hit["metadata"]
            # Fetch a snippet from DB if case exists
            try:
                db_result = await db.execute(select(FIR).where(FIR.id == uuid.UUID(fir_id)))
                db_fir = db_result.scalar_one_or_none()
                snippet = (db_fir.raw_text[:200] + "…") if db_fir else meta.get("case_number", "")
            except Exception:
                snippet = meta.get("case_number", "")

            similar_firs.append(SimilarFIR(
                fir_id=fir_id,
                case_number=meta.get("case_number", "Unknown"),
                district=meta.get("district", "Unknown"),
                crime_category=meta.get("crime_category"),
                similarity_score=hit["similarity"],
                snippet=snippet,
            ))

    return AnalysisResponse(
        entities=entities,
        ipc_sections=ipc_sections,
        crime_category=category,
        risk_level=risk,
        mo_pattern=mo,
        ai_summary=summary,
        similar_firs=similar_firs,
        next_steps=next_steps,
    )


@router.get("/similar/{fir_id}", response_model=list)
async def get_similar_firs(
    fir_id: str,
    k: int = 5,
    db: AsyncSession = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer),
):
    """Find semantically similar FIRs for an already-indexed FIR."""
    result = await db.execute(select(FIR).where(FIR.id == uuid.UUID(fir_id)))
    fir = result.scalar_one_or_none()
    if not fir:
        raise HTTPException(status_code=404, detail="FIR not found")
    if not fir.embedding_id:
        raise HTTPException(status_code=400, detail="FIR has not been indexed yet. Run /train first.")

    embed_svc = get_embedding_service()
    chroma = get_chroma_service()

    vector = embed_svc.embed(fir.raw_text)
    if not vector:
        return []

    hits = chroma.search_similar(vector, k=k, exclude_ids=[fir_id])
    return hits

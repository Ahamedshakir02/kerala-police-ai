"""FIR Management API — Upload, List, Retrieve, Train"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_officer
from app.models.fir import FIR, FIRStatus, RiskLevel
from app.models.officer import Officer
from app.schemas.schemas import FIRCreate, FIROut, FIRListItem
from app.services.training_service import ingest_fir, extract_text_from_pdf

router = APIRouter()


@router.post("/upload", response_model=FIROut, status_code=201)
async def upload_fir(
    background_tasks: BackgroundTasks,
    case_number: str = Form(...),
    district: str = Form(...),
    police_station: str = Form(...),
    original_language: str = Form("en"),
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer),
):
    """
    Upload a FIR as a PDF or raw text.
    Triggers the NLP ingestion pipeline in the background.
    """
    # Resolve text
    raw_text = ""
    if file and file.filename:
        pdf_bytes = await file.read()
        if file.filename.lower().endswith(".pdf"):
            raw_text = extract_text_from_pdf(pdf_bytes)
        else:
            raw_text = pdf_bytes.decode("utf-8", errors="replace")
    elif text:
        raw_text = text.strip()

    if not raw_text or len(raw_text) < 20:
        raise HTTPException(status_code=400, detail="FIR text is too short or could not be extracted from PDF")

    # Check for duplicate case number
    existing = await db.execute(select(FIR).where(FIR.case_number == case_number))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"FIR with case number '{case_number}' already exists")

    fir = FIR(
        id=uuid.uuid4(),
        case_number=case_number,
        district=district,
        police_station=police_station,
        original_language=original_language,
        raw_text=raw_text,
        officer_id=current_officer.id,
        status=FIRStatus.PENDING,
    )
    db.add(fir)
    await db.commit()
    await db.refresh(fir)

    # Queue ingestion in the background
    background_tasks.add_task(ingest_fir, str(fir.id), db)

    return FIROut.model_validate(fir)


@router.post("/{fir_id}/train")
async def train_fir(
    fir_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer),
):
    """Re-run the ingestion pipeline on an existing FIR."""
    result = await db.execute(select(FIR).where(FIR.id == uuid.UUID(fir_id)))
    fir = result.scalar_one_or_none()
    if not fir:
        raise HTTPException(status_code=404, detail="FIR not found")

    background_tasks.add_task(ingest_fir, fir_id, db)
    return {"message": f"Training pipeline started for FIR {fir.case_number}", "fir_id": fir_id}


@router.get("/", response_model=List[FIRListItem])
async def list_firs(
    skip: int = 0,
    limit: int = 50,
    district: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer),
):
    query = select(FIR).offset(skip).limit(limit).order_by(FIR.date_registered.desc())
    if district:
        query = query.where(FIR.district == district)
    if risk_level:
        query = query.where(FIR.risk_level == risk_level)
    if status:
        query = query.where(FIR.status == status)

    result = await db.execute(query)
    return [FIRListItem.model_validate(f) for f in result.scalars().all()]


@router.get("/{fir_id}", response_model=FIROut)
async def get_fir(
    fir_id: str,
    db: AsyncSession = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer),
):
    result = await db.execute(select(FIR).where(FIR.id == uuid.UUID(fir_id)))
    fir = result.scalar_one_or_none()
    if not fir:
        raise HTTPException(status_code=404, detail="FIR not found")
    return FIROut.model_validate(fir)

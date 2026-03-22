"""Bhashini Translation Proxy API"""

from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_officer
from app.models.officer import Officer
from app.schemas.schemas import TranslationRequest, TranslationResponse
from app.services.bhashini_service import get_bhashini_service

router = APIRouter()


@router.post("/translate", response_model=TranslationResponse)
async def translate(
    req: TranslationRequest,
    current_officer: Officer = Depends(get_current_officer),
):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    svc = get_bhashini_service()
    result = await svc.translate(
        text=req.text,
        source_language=req.source_language,
        target_language=req.target_language,
    )
    return TranslationResponse(**result)

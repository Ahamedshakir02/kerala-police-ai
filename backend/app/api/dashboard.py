"""Dashboard API — Live Stats & Intelligence Feed"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case as sa_case

from app.core.database import get_db
from app.core.security import get_current_officer
from app.models.officer import Officer
from app.models.fir import FIR, FIRStatus, RiskLevel
from app.models.case import Case, CaseStatus
from app.schemas.schemas import DashboardStats
from app.services.chroma_service import get_chroma_service
from datetime import datetime, timezone, timedelta

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer),
):
    # Total FIRs
    total_result = await db.execute(select(func.count(FIR.id)))
    total_firs = total_result.scalar() or 0

    # Indexed FIRs
    indexed_result = await db.execute(
        select(func.count(FIR.id)).where(FIR.status == FIRStatus.INDEXED)
    )
    indexed_firs = indexed_result.scalar() or 0

    # Case counts
    open_result = await db.execute(
        select(func.count(Case.id)).where(Case.status == CaseStatus.OPEN)
    )
    open_cases = open_result.scalar() or 0

    closed_result = await db.execute(
        select(func.count(Case.id)).where(Case.status == CaseStatus.CLOSED)
    )
    closed_cases = closed_result.scalar() or 0

    # High risk FIRs
    high_risk_result = await db.execute(
        select(func.count(FIR.id)).where(FIR.risk_level.in_(["high", "critical"]))
    )
    high_risk_firs = high_risk_result.scalar() or 0

    # Distinct MO patterns detected
    patterns_result = await db.execute(
        select(func.count(func.distinct(FIR.mo_pattern))).where(FIR.mo_pattern.isnot(None))
    )
    patterns_detected = patterns_result.scalar() or 0

    # FIRs today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.count(FIR.id)).where(FIR.date_registered >= today_start)
    )
    firs_today = today_result.scalar() or 0

    # District breakdown
    district_result = await db.execute(
        select(FIR.district, func.count(FIR.id)).group_by(FIR.district)
    )
    district_breakdown = {row[0]: row[1] for row in district_result.all() if row[0]}

    return DashboardStats(
        total_firs=total_firs,
        indexed_firs=indexed_firs,
        open_cases=open_cases,
        closed_cases=closed_cases,
        high_risk_firs=high_risk_firs,
        patterns_detected=patterns_detected,
        firs_today=firs_today,
        district_breakdown=district_breakdown,
    )


@router.get("/chroma-stats")
async def chroma_stats(current_officer: Officer = Depends(get_current_officer)):
    chroma = get_chroma_service()
    return chroma.get_stats()

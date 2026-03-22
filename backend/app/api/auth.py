"""Auth API — Officer Login & JWT Token"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    verify_password, create_access_token,
    get_password_hash, get_current_officer,
)
from app.models.officer import Officer, OfficerRole
from app.schemas.schemas import LoginRequest, TokenResponse, OfficerCreate, OfficerOut
from app.core.config import settings

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Officer).where(Officer.badge_number == req.badge_number))
    officer = result.scalar_one_or_none()

    if not officer or not verify_password(req.password, officer.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid badge number or password",
        )
    if not officer.is_active:
        raise HTTPException(status_code=403, detail="Officer account is deactivated")

    token = create_access_token(
        {"sub": officer.badge_number, "role": officer.role.value},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(access_token=token, officer=OfficerOut.model_validate(officer))


@router.get("/me", response_model=OfficerOut)
async def get_me(current_officer: Officer = Depends(get_current_officer)):
    return OfficerOut.model_validate(current_officer)


@router.post("/register", response_model=OfficerOut, status_code=201)
async def register_officer(data: OfficerCreate, db: AsyncSession = Depends(get_db)):
    """Register a new officer. In production, restrict to ADMIN role."""
    existing = await db.execute(select(Officer).where(Officer.badge_number == data.badge_number))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Officer with this badge number already exists")

    officer = Officer(
        badge_number=data.badge_number,
        name=data.name,
        station=data.station,
        district=data.district,
        role=data.role,
        phone=data.phone,
        hashed_password=get_password_hash(data.password),
    )
    db.add(officer)
    await db.commit()
    await db.refresh(officer)
    return OfficerOut.model_validate(officer)


@router.post("/seed-demo", status_code=201)
async def seed_demo_officer(db: AsyncSession = Depends(get_db)):
    """Seed a demo officer for testing. Only works in development mode."""
    if settings.is_production:
        raise HTTPException(status_code=403, detail="Not allowed in production")

    demo_accounts = [
        {
            "badge_number": "KP001",
            "name": "Sub Inspector Rajan Kumar",
            "station": "Thiruvananthapuram East",
            "district": "Thiruvananthapuram",
            "role": OfficerRole.SUB_INSPECTOR,
            "password": "test1234",
        },
        {
            "badge_number": "KP002",
            "name": "Inspector Priya Menon",
            "station": "Ernakulam Central",
            "district": "Ernakulam",
            "role": OfficerRole.INSPECTOR,
            "password": "test1234",
        },
    ]

    created = []
    for acc in demo_accounts:
        existing = await db.execute(select(Officer).where(Officer.badge_number == acc["badge_number"]))
        if existing.scalar_one_or_none():
            continue
        officer = Officer(
            badge_number=acc["badge_number"],
            name=acc["name"],
            station=acc["station"],
            district=acc["district"],
            role=acc["role"],
            hashed_password=get_password_hash(acc["password"]),
        )
        db.add(officer)
        created.append(acc["badge_number"])

    await db.commit()
    return {"message": f"Seeded demo officers: {created or 'already exist'}", "credentials": "password: test1234"}

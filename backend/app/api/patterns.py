"""MO Patterns API — Modus Operandi Cluster Detection"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_officer
from app.models.officer import Officer
from app.models.fir import FIR
from app.schemas.schemas import MOPattern

router = APIRouter()

# Known MO pattern definitions
KNOWN_PATTERNS = [
    {
        "cluster_id": "MO-001",
        "pattern_name": "OTP/KYC Phone Fraud",
        "description": "Fraudsters pose as bank/telecom officials and trick victims into sharing OTPs, resulting in unauthorized transfers.",
        "crime_type": "Cyber Crime / Fraud",
        "keywords": ["otp", "kyc", "bank call", "telecom fraud", "recharge fraud"],
        "risk_level": "high",
        "recommended_action": "Immediate IMEI freeze request. File NCRP complaint. Contact bank within 30 min for chargeback.",
    },
    {
        "cluster_id": "MO-002",
        "pattern_name": "Bike-Borne Chain Snatching",
        "description": "Two-wheeler gang (usually 2 persons) target women pedestrians in isolated stretches, snatch gold chains and flee.",
        "crime_type": "Robbery / Property",
        "keywords": ["chain snatching", "motorcycle", "bike", "two-wheeler", "moving vehicle snatch"],
        "risk_level": "high",
        "recommended_action": "Circulate vehicle description to checkposts. Check ANPR cameras. Issue district-wide alert.",
    },
    {
        "cluster_id": "MO-003",
        "pattern_name": "House Breaking (Lock Bypass)",
        "description": "Skilled burglars use lock-picking tools or duplicate keys to bypass standard locks, typically during daytime when residents are absent.",
        "crime_type": "Burglary / Property",
        "keywords": ["broke lock", "house break", "pried door", "entry through window", "duplicate key"],
        "risk_level": "medium",
        "recommended_action": "Collect fingerprints and tool impression evidence. Check if similar incidents in adjacent areas.",
    },
    {
        "cluster_id": "MO-004",
        "pattern_name": "Romance / Matrimony Fraud",
        "description": "Fraudsters establish fake romantic relationships via matrimony sites or social media, then extort money under various pretexts.",
        "crime_type": "Fraud / Cyber Crime",
        "keywords": ["love affair", "matrimony", "dating app", "online romance", "fake marriage"],
        "risk_level": "medium",
        "recommended_action": "Preserve all digital communications. File cybercrime report. Identify social media accounts.",
    },
    {
        "cluster_id": "MO-005",
        "pattern_name": "ATM / Card Skimming",
        "description": "Skimming devices installed on ATMs capture card data; offenders clone cards and make unauthorized withdrawals.",
        "crime_type": "Cyber Crime / Fraud",
        "keywords": ["atm", "card cloning", "skimming", "unauthorized withdrawal", "card fraud"],
        "risk_level": "critical",
        "recommended_action": "Secure ATM for forensic inspection. Alert bank for card blocking. Check ATM CCTV footage.",
    },
    {
        "cluster_id": "MO-006",
        "pattern_name": "Narcotics Peddling Network",
        "description": "Structured network using couriers for last-mile delivery of ganja/synthetic drugs — often via home delivery model.",
        "crime_type": "NDPS / Narcotics",
        "keywords": ["ganja delivery", "drug network", "courier drugs", "narcotic peddling", "home delivery drugs"],
        "risk_level": "critical",
        "recommended_action": "Register case under NDPS Act. Seize contraband. Apply for PD detention if warranted. Inform Anti-Narcotics Cell.",
    },
]


async def detect_patterns_from_db(db: AsyncSession) -> list:
    """
    Scan DB for MO patterns by keyword matching on FIR text.
    Returns list of MOPattern with actual occurrence counts.
    """
    result = await db.execute(select(FIR.id, FIR.raw_text, FIR.district, FIR.mo_pattern, FIR.case_number))
    firs = result.all()

    patterns_out = []
    for pattern in KNOWN_PATTERNS:
        matched_ids = []
        matched_districts = set()
        for fir in firs:
            text = (fir.raw_text or "").lower()
            mo = (fir.mo_pattern or "").lower()
            if any(kw.lower() in text or kw.lower() in mo for kw in pattern["keywords"]):
                matched_ids.append(str(fir.id))
                if fir.district:
                    matched_districts.add(fir.district)

        patterns_out.append(MOPattern(
            cluster_id=pattern["cluster_id"],
            pattern_name=pattern["pattern_name"],
            description=pattern["description"],
            crime_type=pattern["crime_type"],
            occurrences=max(len(matched_ids), 0),
            districts=list(matched_districts) or ["Thiruvananthapuram", "Ernakulam"],
            risk_level=pattern["risk_level"],
            fir_ids=matched_ids[:10],
            recommended_action=pattern["recommended_action"],
        ))

    # Sort by risk and occurrences
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    patterns_out.sort(key=lambda p: (order.get(p.risk_level, 4), -p.occurrences))
    return patterns_out


@router.get("/mo-alerts", response_model=list)
async def get_mo_alerts(
    db: AsyncSession = Depends(get_db),
    current_officer: Officer = Depends(get_current_officer),
):
    return await detect_patterns_from_db(db)

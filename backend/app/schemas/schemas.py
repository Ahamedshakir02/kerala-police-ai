from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.officer import OfficerRole


# ── Officer ────────────────────────────────────────────────────────
class OfficerBase(BaseModel):
    badge_number: str
    name: str
    station: str
    district: str
    role: OfficerRole = OfficerRole.SUB_INSPECTOR
    phone: Optional[str] = None


class OfficerCreate(OfficerBase):
    password: str


class OfficerOut(OfficerBase):
    id: UUID
    is_active: bool

    model_config = {"from_attributes": True}


# ── Auth ───────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    badge_number: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    officer: OfficerOut


# ── FIR ───────────────────────────────────────────────────────────
class FIRCreate(BaseModel):
    case_number: str
    district: str
    police_station: str
    date_of_incident: Optional[datetime] = None
    raw_text: str
    original_language: str = "en"


class IPCSection(BaseModel):
    section: str
    title: str
    description: str
    punishment: str
    confidence: float


class ExtractedEntities(BaseModel):
    complainant: Optional[str] = None
    accused: List[str] = []
    location: Optional[str] = None
    date_time: Optional[str] = None
    weapon: Optional[str] = None
    property_stolen: Optional[str] = None
    witnesses: List[str] = []
    vehicle: Optional[str] = None


class FIROut(BaseModel):
    id: UUID
    case_number: str
    district: str
    police_station: str
    date_of_incident: Optional[datetime]
    date_registered: datetime
    raw_text: str
    original_language: str
    extracted_entities: Dict[str, Any]
    ipc_sections: List[Dict[str, Any]]
    crime_category: Optional[str]
    risk_level: str
    mo_pattern: Optional[str]
    status: str
    ai_summary: Optional[str]

    model_config = {"from_attributes": True}


class FIRListItem(BaseModel):
    id: UUID
    case_number: str
    district: str
    police_station: str
    date_registered: datetime
    crime_category: Optional[str]
    risk_level: str
    status: str

    model_config = {"from_attributes": True}


# ── Analysis ───────────────────────────────────────────────────────
class AnalysisRequest(BaseModel):
    text: str = Field(..., min_length=20, description="FIR text to analyse")
    language: str = "en"


class SimilarFIR(BaseModel):
    fir_id: str
    case_number: str
    district: str
    crime_category: Optional[str]
    similarity_score: float
    snippet: str


class AnalysisResponse(BaseModel):
    entities: Dict[str, Any]
    ipc_sections: List[Dict[str, Any]]
    crime_category: str
    risk_level: str
    mo_pattern: Optional[str]
    ai_summary: str
    similar_firs: List[SimilarFIR]
    next_steps: List[str]


# ── Legal ──────────────────────────────────────────────────────────
class LegalSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None  # "ipc", "crpc", "judgment", "sop"


class LegalSearchResponse(BaseModel):
    query: str
    answer: str
    sections: List[Dict[str, Any]]
    citations: List[str]
    confidence: float


# ── Bhashini ──────────────────────────────────────────────────────
class TranslationRequest(BaseModel):
    text: str
    source_language: str = "en"   # ISO 639-1 code
    target_language: str = "ml"


class TranslationResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    model_used: str


# ── Dashboard ─────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_firs: int
    indexed_firs: int
    open_cases: int
    closed_cases: int
    high_risk_firs: int
    patterns_detected: int
    firs_today: int
    district_breakdown: Dict[str, int]


# ── Patterns ──────────────────────────────────────────────────────
class MOPattern(BaseModel):
    cluster_id: str
    pattern_name: str
    description: str
    crime_type: str
    occurrences: int
    districts: List[str]
    risk_level: str
    fir_ids: List[str]
    recommended_action: str

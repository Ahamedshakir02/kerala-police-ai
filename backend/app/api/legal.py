"""Legal Guidance API — IPC/CrPC keyword search and AI legal assistant"""

from fastapi import APIRouter, Depends
from app.core.security import get_current_officer
from app.models.officer import Officer
from app.schemas.schemas import LegalSearchRequest, LegalSearchResponse
from app.services.nlp_service import IPC_KNOWLEDGE_BASE

router = APIRouter()

# ── Extended Legal Knowledge Base ──────────────────────────────────────────────
CRPC_KNOWLEDGE = [
    {
        "section": "41 CrPC",
        "title": "Power to Arrest Without Warrant",
        "answer": "Under Section 41 CrPC, a police officer may, without court order, arrest when a person commits a cognizable offence in presence of the officer, or there exists reasonable suspicion.",
        "keywords": ["arrest without warrant", "arrest power", "when can police arrest", "cognizable arrest"],
        "category": "crpc",
        "citation": "Section 41, Code of Criminal Procedure, 1973",
    },
    {
        "section": "57 CrPC",
        "title": "Person Arrested Not to be Detained More than 24 Hours",
        "answer": "No person arrested shall be detained in custody for more than 24 hours without a magistrate's order. Article 22 of the Constitution reinforces this right.",
        "keywords": ["24 hour rule", "custody limit", "detention period", "produce before magistrate", "detention without warrant"],
        "category": "crpc",
        "citation": "Section 57 CrPC, Article 22 Constitution of India",
    },
    {
        "section": "154 CrPC",
        "title": "First Information Report (FIR)",
        "answer": "Section 154 mandates that every information relating to a cognizable offence must be recorded in writing and read over to the informant. A copy must be given to the informant free of cost.",
        "keywords": ["fir registration", "first information report", "how to file fir", "fir mandatory", "cognizable offence report"],
        "category": "crpc",
        "citation": "Section 154, Code of Criminal Procedure, 1973",
    },
    {
        "section": "161 CrPC",
        "title": "Examination of Witnesses by Police",
        "answer": "Any police officer investigating a cognizable case may examine any person acquainted with the facts and circumstances of the case. Statements made under 161 are not admissible as evidence but can be used for contradiction.",
        "keywords": ["witness statement", "161 statement", "police examination", "witness examination", "recording statement"],
        "category": "crpc",
        "citation": "Section 161, Code of Criminal Procedure, 1973",
    },
    {
        "section": "167 CrPC",
        "title": "Procedure When Investigation Cannot Be Completed in 24 Hours",
        "answer": "If investigation cannot be completed within 24 hours, the accused must be produced before a magistrate who may authorize detention (police custody up to 15 days, judicial custody thereafter). Bail applies after 60/90 days if charge sheet not filed.",
        "keywords": ["remand", "police custody", "judicial custody", "detention beyond 24 hours", "bail 90 days", "default bail", "167 crpc"],
        "category": "crpc",
        "citation": "Section 167 CrPC; Hussainara Khatoon v. State of Bihar AIR 1979 SC 1360",
    },
    {
        "section": "173 CrPC",
        "title": "Charge Sheet / Final Report",
        "answer": "On completion of investigation, the police officer shall forward a report (charge sheet) to the Magistrate in the prescribed format. The report must include names of parties, nature of information, names of witnesses, and whether accused is arrested/bailed.",
        "keywords": ["charge sheet", "final report", "173 crpc", "police report", "challan", "when to file charge sheet"],
        "category": "crpc",
        "citation": "Section 173, Code of Criminal Procedure, 1973",
    },
    {
        "section": "436A CrPC",
        "title": "Maximum Period of Detention While Awaiting Trial",
        "answer": "A person who has served half the maximum imprisonment period for an offence other than those punishable with death shall be released on personal bond with or without sureties.",
        "keywords": ["half sentence bail", "undertrial bail", "436a bail", "long custody bail"],
        "category": "crpc",
        "citation": "Section 436A, Code of Criminal Procedure, 1973",
    },
]

JUDGMENT_KNOWLEDGE = [
    {
        "section": "D.K. Basu v. State of West Bengal (1997)",
        "title": "Guidelines for Arrest and Detention",
        "answer": "The Supreme Court laid down mandatory guidelines for arrest: officer must identify himself, prepare memo of arrest, inform of grounds of arrest, allow legal representation, and medical examination every 48 hours.",
        "keywords": ["dk basu", "arrest guidelines", "custody rights", "arrest procedure", "rights of arrested"],
        "category": "judgment",
        "citation": "D.K. Basu v. State of West Bengal, AIR 1997 SC 610",
    },
    {
        "section": "Lalita Kumari v. Govt. of UP (2013)",
        "title": "Mandatory FIR Registration",
        "answer": "Constitution Bench held that registration of FIR is mandatory under Section 154 CrPC if the information discloses a cognizable offence. Police cannot conduct preliminary inquiry before registering FIR for cognizable offences.",
        "keywords": ["mandatory fir", "lalita kumari", "refuse to file fir", "fir registration mandatory", "police must register fir"],
        "category": "judgment",
        "citation": "Lalita Kumari v. Govt. of Uttar Pradesh, (2013) 4 SCC 1",
    },
    {
        "section": "Arnesh Kumar v. State of Bihar (2014)",
        "title": "Arrest Guidelines for Sec 498A IPC",
        "answer": "Supreme Court held that police must not automatically arrest in Sec 498A (matrimonial cruelty) cases. A checklist must be completed before arrest. Magistrate must apply mind before granting remand.",
        "keywords": ["498a arrest", "arnesh kumar", "domestic violence arrest", "matrimonial dispute arrest"],
        "category": "judgment",
        "citation": "Arnesh Kumar v. State of Bihar, (2014) 8 SCC 273",
    },
]

SOP_KNOWLEDGE = [
    {
        "section": "BPR&D SOP — Crime Scene Management",
        "title": "First Responding Officer Duties",
        "answer": "First officer at scene must: (1) Ensure safety, (2) Cordon off scene, (3) Preserve evidence, (4) Record time of arrival, (5) Identify witnesses, (6) Photograph/video before any movement, (7) Maintain scene register. No evidence must be disturbed before FSL arrives.",
        "keywords": ["crime scene", "first responder", "scene preservation", "fsl", "scene cordon", "evidence preservation"],
        "category": "sop",
        "citation": "BPR&D Standard Operating Procedures for Crime Scene Management",
    },
    {
        "section": "Kerala Police SOP — CCTNS Data Entry",
        "title": "CCTNS FIR Entry Requirements",
        "answer": "FIR must be entered in CCTNS within 24 hours of registration. All fields including IPC sections, complainant details, and location must be filled. District CCTNS coordinator must be informed of any technical issues.",
        "keywords": ["cctns", "cctns entry", "fir entry system", "cctns registration", "digital fir"],
        "category": "sop",
        "citation": "Kerala Police CCTNS Implementation Manual, 2019",
    },
]

ALL_LEGAL = IPC_KNOWLEDGE_BASE + CRPC_KNOWLEDGE + JUDGMENT_KNOWLEDGE + SOP_KNOWLEDGE


def search_legal_kb(query: str, category: str = None) -> list:
    query_lower = query.lower()
    results = []
    for item in ALL_LEGAL:
        if category and item.get("category") != category and not item.get("section", "").lower().startswith(category):
            continue
        score = 0
        for kw in item.get("keywords", []):
            if kw.lower() in query_lower:
                score += 1
        if query_lower in item.get("title", "").lower():
            score += 3
        if score > 0:
            results.append((score, item))
    results.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in results[:5]]


@router.post("/search", response_model=LegalSearchResponse)
async def legal_search(
    req: LegalSearchRequest,
    current_officer: Officer = Depends(get_current_officer),
):
    results = search_legal_kb(req.query, req.category)

    if not results:
        answer = (
            f"No direct match found for '{req.query}' in the legal knowledge base. "
            "Please consult the latest Kerala Police Legal Handbook or contact the District Legal Cell. "
            "You may also refer to the Ministry of Law & Justice portal at https://legislative.gov.in"
        )
        return LegalSearchResponse(
            query=req.query, answer=answer, sections=[], citations=[], confidence=0.0
        )

    top = results[0]
    all_sections = [
        {"section": r["section"], "title": r["title"], "description": r.get("answer", r.get("description", ""))}
        for r in results
    ]
    citations = list({r.get("citation", "") for r in results if r.get("citation")})

    answer = top.get("answer", top.get("description", "Please refer to the relevant legal text."))
    if len(results) > 1:
        related = ", ".join([r["section"] for r in results[1:4]])
        answer += f"\n\n**Related:** {related}"

    confidence = min(0.95, 0.5 + len(results) * 0.1)

    return LegalSearchResponse(
        query=req.query,
        answer=answer,
        sections=all_sections,
        citations=citations,
        confidence=round(confidence, 2),
    )

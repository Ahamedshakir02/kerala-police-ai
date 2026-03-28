"""Legal Guidance API â€” IPC/CrPC keyword search and AI legal assistant"""

from fastapi import APIRouter, Depends
from app.core.security import get_current_officer
from app.models.officer import Officer
from app.schemas.schemas import LegalSearchRequest, LegalSearchResponse, LegalChatResponse
from app.services.nlp_service import IPC_KNOWLEDGE_BASE
from app.services.gemini_service import get_gemini_service

router = APIRouter()

# â”€â”€ Extended Legal Knowledge Base â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

MOTOR_ACT_KNOWLEDGE = [
    {
        "section": "185 MVA",
        "title": "Driving Under Influence of Alcohol/Drugs",
        "answer": "Section 185 of the Motor Vehicles Act provides punishment for driving under influence. Penalty: First offence â€” imprisonment up to 6 months and/or fine up to â‚¹10,000. Second offence within 3 years â€” imprisonment up to 2 years and/or fine up to â‚¹15,000. Breathalyzer test can be conducted by a traffic officer.",
        "keywords": ["drunk driving", "drunken driving", "driving under influence", "alcohol limit", "breathalyzer", "drink and drive", "dui"],
        "category": "motor",
        "citation": "Section 185, Motor Vehicles Act, 1988 (Amended 2019)",
    },
    {
        "section": "184 MVA",
        "title": "Dangerous Driving",
        "answer": "Driving dangerously or at reckless speed on a public road. Penalty: First offence â€” imprisonment up to 6 months and/or fine up to â‚¹5,000. Second offence â€” imprisonment up to 2 years and/or fine up to â‚¹10,000.",
        "keywords": ["dangerous driving", "reckless driving", "over-speeding accident", "negligent driving"],
        "category": "motor",
        "citation": "Section 184, Motor Vehicles Act, 1988",
    },
    {
        "section": "304A IPC / 106 BNS",
        "title": "Causing Death by Negligence (Motor Accident)",
        "answer": "Whoever causes death of any person by doing any rash or negligent act not amounting to culpable homicide. In motor accident fatalities, Section 304A IPC (now 106 BNS) is typically invoked along with 279 IPC (rash driving). Punishment: Imprisonment up to 2 years + Fine.",
        "keywords": ["accident death", "motor accident fatality", "rash driving death", "hit and run death", "road accident kill", "vehicle accident killing"],
        "category": "motor",
        "citation": "Section 304A IPC / Section 106 BNS 2023",
    },
    {
        "section": "279 IPC / 281 BNS",
        "title": "Rash Driving or Riding on Public Way",
        "answer": "Whoever drives any vehicle or rides on any public way in a manner so rash or negligent as to endanger human life. Punishment: Imprisonment up to 6 months or Fine up to â‚¹1000, or Both. Often charged alongside 304A in fatal accidents.",
        "keywords": ["rash driving", "negligent driving", "speeding", "overspeeding", "road accident", "atv accident", "two wheeler rash"],
        "category": "motor",
        "citation": "Section 279 IPC / Section 281 BNS 2023",
    },
    {
        "section": "132 MVA",
        "title": "Driving Without Licence",
        "answer": "Section 132 read with Section 181 MVA â€” Driving a motor vehicle without a valid driving licence. Penalty: Fine up to â‚¹5,000 (first offence, under 2019 amendment). Imprisonment up to 3 months or fine may also apply.",
        "keywords": ["no licence", "driving without license", "unlicensed driver", "driving licence offence"],
        "category": "motor",
        "citation": "Section 132 read with Section 181, Motor Vehicles Act, 1988 (Amended 2019)",
    },
    {
        "section": "161 MVA",
        "title": "Hit and Run â€” Compensation",
        "answer": "Under the Solatium Fund Scheme, victims of hit-and-run accidents (where the offending vehicle is unknown) are entitled to compensation: â‚¹2 lakh for death, â‚¹50,000 for grievous hurt. Police must file a specific Form 1A report to the Claims Tribunal.",
        "keywords": ["hit and run", "vehicle fled", "unknown vehicle accident", "solatium fund", "compensation accident"],
        "category": "motor",
        "citation": "Section 161, Motor Vehicles Act, 1988; Solatium Fund Scheme",
    },
]

BNS_KNOWLEDGE = [
    {
        "section": "103 BNS",
        "title": "Murder (BNS 2023 â€” replaces IPC 302)",
        "answer": "Section 103 of Bharatiya Nyaya Sanhita 2023 replaces IPC Section 302. Punishment for murder remains death or life imprisonment with fine. The BNS came into force on 1 July 2024. All new FIRs from 1 July 2024 must cite BNS sections.",
        "keywords": ["bns murder", "bns 103", "bharatiya nyaya sanhita murder", "new criminal law murder"],
        "category": "bns",
        "citation": "Section 103, Bharatiya Nyaya Sanhita, 2023 (effective 1 July 2024)",
    },
    {
        "section": "309 BNS",
        "title": "Theft (BNS 2023 â€” replaces IPC 379)",
        "answer": "Section 309 BNS replaces IPC 379. Punishment remains imprisonment up to 3 years + Fine. The procedure under BNSS 2023 (replaces CrPC) applies for all new cases from 1 July 2024.",
        "keywords": ["bns theft", "bns 309", "new law theft", "bharatiya nyaya sanhita theft"],
        "category": "bns",
        "citation": "Section 309, Bharatiya Nyaya Sanhita, 2023",
    },
    {
        "section": "316 BNS",
        "title": "Cheating (BNS 2023 â€” replaces IPC 420)",
        "answer": "Section 316 BNS replaces IPC Section 420. Fraud, cheating, and dishonest inducement remains punishable with imprisonment up to 7 years + Fine.",
        "keywords": ["bns cheating", "bns 316", "new law fraud", "bharatiya nyaya sanhita fraud"],
        "category": "bns",
        "citation": "Section 316, Bharatiya Nyaya Sanhita, 2023",
    },
    {
        "section": "BNSS Overview",
        "title": "Bharatiya Nagarik Suraksha Sanhita 2023 (BNSS) â€” replaces CrPC",
        "answer": "The Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023 replaced the Code of Criminal Procedure (CrPC) 1973 with effect from 1 July 2024. Key changes: (1) Trials to be concluded within 3 years, (2) Video-conference trials allowed, (3) Maximum police custody extended to 60 days for serious offences, (4) e-FIR facility, (5) Zero FIR allowed and to be transferred within 15 days.",
        "keywords": ["bnss", "new crpc", "replacement crpc", "2024 criminal procedure", "new criminal laws", "bharatiya nagarik suraksha sanhita"],
        "category": "bns",
        "citation": "Bharatiya Nagarik Suraksha Sanhita, 2023 (effective 1 July 2024)",
    },
    {
        "section": "175 BNSS",
        "title": "Zero FIR (BNSS)",
        "answer": "Under BNSS 2023, Section 175 codifies Zero FIR â€” an FIR registered at any police station regardless of jurisdiction. It must be transferred to the jurisdictionally correct police station within 15 days. This was previously only case law (established by courts).",
        "keywords": ["zero fir", "zero fir bnss", "fir without jurisdiction", "any station fir", "inter-district fir"],
        "category": "bns",
        "citation": "Section 175, Bharatiya Nagarik Suraksha Sanhita, 2023",
    },
]

POCSO_KNOWLEDGE = [
    {
        "section": "4 POCSO",
        "title": "Penetrative Sexual Assault on Child (POCSO)",
        "answer": "Section 4 POCSO provides punishment for penetrative sexual assault. Minimum 20 years imprisonment, may extend to life imprisonment and fine. Victim must be below 18 years. Investigation must be completed within 30 days. Trial to be completed within one year in Special Court.",
        "keywords": ["pocso", "child sexual abuse", "assault on child", "minor raped", "sexual assault child", "pocso case"],
        "category": "pocso",
        "citation": "Section 4, Protection of Children from Sexual Offences Act, 2012 (Amended 2019)",
    },
    {
        "section": "8 POCSO",
        "title": "Sexual Assault (Non-Penetrative) on Child",
        "answer": "Sexual assault (non-penetrative) of a child under POCSO. Punishment: Minimum 3 years, up to 5 years, with fine. Child is defined as below 18 years. Reporting obligation: Any person aware of a POCSO offence MUST report to police or face imprisonment up to 6 months.",
        "keywords": ["pocso sexual assault", "groping child", "touching child inappropriately", "minor molestation", "child groping"],
        "category": "pocso",
        "citation": "Section 8, Protection of Children from Sexual Offences Act, 2012",
    },
    {
        "section": "21 POCSO",
        "title": "Mandatory Reporting Obligation (POCSO)",
        "answer": "Under Section 21 POCSO, failure to report knowledge of sexual offence against a child is an offence. Punishment: Imprisonment up to 6 months or Fine. This applies to all citizens and institutions, including hospitals, schools, and NGOs.",
        "keywords": ["pocso mandatory reporting", "failure report child abuse", "doctor report pocso", "school report abuse"],
        "category": "pocso",
        "citation": "Section 21, Protection of Children from Sexual Offences Act, 2012",
    },
]

DOMESTIC_VIOLENCE_KNOWLEDGE = [
    {
        "section": "DV Act 2005",
        "title": "Protection of Women from Domestic Violence Act 2005",
        "answer": "The Protection of Women from Domestic Violence Act 2005 provides protection orders, residence orders, and monetary relief. Aggrieved woman can approach Protection Officer or court. Domestic violence includes physical, verbal, emotional, sexual, and economic abuse. Court can issue protection order within 3 working days of application. Violation of protection order is a criminal offence.",
        "keywords": ["domestic violence act", "dv act", "protection order", "residence order", "domestic abuse woman", "spouse violence"],
        "category": "domestic_violence",
        "citation": "Protection of Women from Domestic Violence Act, 2005",
    },
    {
        "section": "498A IPC / 85 BNS",
        "title": "Cruelty by Husband or Relatives (Dowry Harassment)",
        "answer": "Section 498A IPC (now 85 BNS) â€” Husband or relative subjecting woman to cruelty. This covers dowry harassment, physical abuse by in-laws. Punishment: Imprisonment up to 3 years + Fine. It is a cognizable, non-bailable offence. Arnesh Kumar guidelines mandate that police must not automatically arrest without applying the checklist from the Supreme Court.",
        "keywords": ["dowry", "dowry demand", "498a", "cruelty husband", "wife beating husband", "in-laws harassment", "matrimonial cruelty", "bns 85"],
        "category": "domestic_violence",
        "citation": "Section 498A IPC / Section 85 BNS 2023; Arnesh Kumar v. Bihar (2014)",
    },
]

ALL_LEGAL = (
    IPC_KNOWLEDGE_BASE
    + CRPC_KNOWLEDGE
    + JUDGMENT_KNOWLEDGE
    + MOTOR_ACT_KNOWLEDGE
    + BNS_KNOWLEDGE
    + POCSO_KNOWLEDGE
    + DOMESTIC_VIOLENCE_KNOWLEDGE
)



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


@router.post("/chat", response_model=LegalChatResponse)
async def legal_chat(
    req: LegalSearchRequest,
    current_officer: Officer = Depends(get_current_officer),
):
    """
    AI-powered legal chat using Google Gemini with RAG.
    Falls back to keyword search if Gemini is unavailable.
    """
    gemini = get_gemini_service()

    # Try Gemini LLM first
    if gemini.is_available:
        result = await gemini.chat(req.query, ALL_LEGAL)
        if result:
            return LegalChatResponse(
                query=req.query,
                answer=result["answer"],
                sections=result["sections"],
                citations=result["citations"],
                confidence=result["confidence"],
                is_fallback=False,
                source="gemini",
            )

    # Fallback to keyword search
    results = search_legal_kb(req.query, req.category)

    if not results:
        return LegalChatResponse(
            query=req.query,
            answer=(
                f"No direct match found for '{req.query}' in the legal knowledge base. "
                "Please consult the latest Kerala Police Legal Handbook or contact the District Legal Cell."
            ),
            sections=[],
            citations=[],
            confidence=0.0,
            is_fallback=True,
            source="keyword_search",
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

    return LegalChatResponse(
        query=req.query,
        answer=answer,
        sections=all_sections,
        citations=citations,
        confidence=round(confidence, 2),
        is_fallback=True,
        source="keyword_search",
    )

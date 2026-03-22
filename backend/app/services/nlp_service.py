"""
NLP Service — spaCy NER + IPC Section Rule Engine
Extracts entities from FIR text and suggests relevant IPC sections.
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# ── IPC Knowledge Base ─────────────────────────────────────────────────────────
IPC_KNOWLEDGE_BASE = [
    {
        "section": "302",
        "title": "Murder",
        "description": "Punishment for murder. Whoever commits murder shall be punished with death or imprisonment for life.",
        "punishment": "Death or Life Imprisonment + Fine",
        "keywords": ["murder", "killed", "death", "shoot", "stab", "strangled", "homicide", "dead body", "body found", "gunshot"],
        "bailable": False,
    },
    {
        "section": "304",
        "title": "Culpable Homicide Not Amounting to Murder",
        "description": "Punishment for culpable homicide not amounting to murder.",
        "punishment": "Imprisonment up to 10 years or Life + Fine",
        "keywords": ["culpable homicide", "accidental death", "rash driving death", "grievous hurt leading to death"],
        "bailable": False,
    },
    {
        "section": "307",
        "title": "Attempt to Murder",
        "description": "Whoever does any act with such intention or knowledge that if he by that act caused death he would be guilty of murder.",
        "punishment": "Imprisonment up to 10 years + Fine (Life if hurt caused)",
        "keywords": ["attempt to murder", "tried to kill", "attacked with weapon", "fired gun", "assault with intent to kill"],
        "bailable": False,
    },
    {
        "section": "354",
        "title": "Assault or Criminal Force on Women",
        "description": "Assault or criminal force to a woman with intent to outrage her modesty.",
        "punishment": "Imprisonment 1–5 years + Fine",
        "keywords": ["molestation", "outrage modesty", "assault woman", "touched inappropriately", "eve teasing", "groped"],
        "bailable": False,
    },
    {
        "section": "376",
        "title": "Rape",
        "description": "A man is said to commit rape with a woman against her will, without her consent.",
        "punishment": "Rigorous Imprisonment not less than 7 years, may extend to Life",
        "keywords": ["rape", "sexual assault", "sexually assaulted", "non-consensual", "violated"],
        "bailable": False,
    },
    {
        "section": "379",
        "title": "Theft",
        "description": "Whoever, intending to take dishonestly any moveable property out of the possession of any person without that person's consent.",
        "punishment": "Imprisonment up to 3 years + Fine",
        "keywords": ["theft", "stolen", "stole", "pickpocket", "shoplifting", "took without consent", "missing items", "burglary"],
        "bailable": True,
    },
    {
        "section": "380",
        "title": "Theft in Dwelling House",
        "description": "Whoever commits theft in any building, tent or vessel used as a human dwelling.",
        "punishment": "Imprisonment up to 7 years + Fine",
        "keywords": ["house theft", "broke into house", "stole from home", "residential theft", "entered home and stole"],
        "bailable": False,
    },
    {
        "section": "392",
        "title": "Robbery",
        "description": "Whoever commits robbery shall be punished with rigorous imprisonment.",
        "punishment": "Rigorous Imprisonment up to 10 years + Fine",
        "keywords": ["robbery", "snatched", "robbed", "chain snatching", "bag snatched", "mugged", "hold up"],
        "bailable": False,
    },
    {
        "section": "395",
        "title": "Dacoity",
        "description": "Robbery by five or more persons jointly.",
        "punishment": "Life Imprisonment or Rigorous Imprisonment up to 10 years + Fine",
        "keywords": ["dacoity", "gang robbery", "five persons robbery", "armed gang", "looted by group"],
        "bailable": False,
    },
    {
        "section": "420",
        "title": "Cheating and Dishonestly Inducing Delivery of Property",
        "description": "Cheating and dishonestly inducing delivery of property.",
        "punishment": "Imprisonment up to 7 years + Fine",
        "keywords": ["fraud", "cheating", "cheated", "scam", "deceived", "false promise", "money fraud", "online fraud", "cyber fraud"],
        "bailable": False,
    },
    {
        "section": "406",
        "title": "Criminal Breach of Trust",
        "description": "Punishment for criminal breach of trust.",
        "punishment": "Imprisonment up to 3 years, or Fine, or Both",
        "keywords": ["breach of trust", "misappropriated", "entrusted money", "embezzlement", "taken entrusted property"],
        "bailable": False,
    },
    {
        "section": "436",
        "title": "Mischief by Fire",
        "description": "Whoever commits mischief by fire or any explosive substance with intent to destroy a house.",
        "punishment": "Life Imprisonment or Rigorous Imprisonment up to 10 years + Fine",
        "keywords": ["arson", "set fire", "burned house", "fire to building", "torched", "set ablaze"],
        "bailable": False,
    },
    {
        "section": "323",
        "title": "Voluntarily Causing Hurt",
        "description": "Whoever, except in the case provided for by section 334, voluntarily causes hurt.",
        "punishment": "Imprisonment up to 1 year + Fine up to ₹1000, or Both",
        "keywords": ["assault", "beat", "hit", "injured", "slapped", "punched", "hurt", "attacked"],
        "bailable": True,
    },
    {
        "section": "324",
        "title": "Voluntarily Causing Hurt by Dangerous Weapons",
        "description": "Voluntarily causing hurt by means of any instrument for shooting, stabbing or cutting.",
        "punishment": "Imprisonment up to 3 years + Fine, or Both",
        "keywords": ["knife attack", "cut with weapon", "stabbed", "razor attack", "iron rod", "hurt with weapon"],
        "bailable": False,
    },
    {
        "section": "498A",
        "title": "Husband or Relative Subjecting Woman to Cruelty",
        "description": "Whoever, being the husband or the relative of the husband of a woman, subjects such woman to cruelty.",
        "punishment": "Imprisonment up to 3 years + Fine",
        "keywords": ["domestic violence", "dowry harassment", "cruelty by husband", "marital abuse", "dowry demand", "wife beating"],
        "bailable": False,
    },
    {
        "section": "304B",
        "title": "Dowry Death",
        "description": "Where death of a woman is caused by burns or bodily injury within 7 years of marriage in connection with dowry demand.",
        "punishment": "Imprisonment not less than 7 years, may extend to Life",
        "keywords": ["dowry death", "bride burning", "woman died after marriage", "dowry demand death"],
        "bailable": False,
    },
    {
        "section": "363",
        "title": "Kidnapping",
        "description": "Whoever kidnaps any person from India or from lawful guardianship.",
        "punishment": "Imprisonment up to 7 years + Fine",
        "keywords": ["kidnapping", "kidnapped", "abducted", "missing child", "taken away", "went missing forcibly"],
        "bailable": False,
    },
    {
        "section": "366",
        "title": "Kidnapping/Abduction of Woman",
        "description": "Kidnapping, abducting or inducing woman to compel her marriage.",
        "punishment": "Imprisonment up to 10 years + Fine",
        "keywords": ["abduction of woman", "kidnapped girl", "eloped forcibly", "woman abducted"],
        "bailable": False,
    },
    {
        "section": "506",
        "title": "Criminal Intimidation",
        "description": "Whoever commits the offence of criminal intimidation shall be punished.",
        "punishment": "Imprisonment up to 2 years + Fine, or Both",
        "keywords": ["threat", "threatened", "intimidation", "threatening message", "death threat", "blackmail"],
        "bailable": True,
    },
    {
        "section": "509",
        "title": "Word / Gesture Intended to Insult Modesty of Woman",
        "description": "Whoever, intending to insult the modesty of any woman, utters any word or makes any sound.",
        "punishment": "Simple Imprisonment up to 3 years + Fine",
        "keywords": ["verbal harassment", "obscene gesture", "indecent remark", "catcalling", "sexual comments at woman"],
        "bailable": True,
    },
    # IT Act sections
    {
        "section": "66 IT Act",
        "title": "Computer Related Offence (IT Act)",
        "description": "If any person dishonestly or fraudulently does any act referred to in section 43 IT Act.",
        "punishment": "Imprisonment up to 3 years + Fine up to ₹5 Lakhs, or Both",
        "keywords": ["hacking", "cyber crime", "computer fraud", "phishing", "data theft", "online scam", "social media fraud", "otp fraud", "upi fraud"],
        "bailable": True,
    },
    {
        "section": "67 IT Act",
        "title": "Publishing Obscene Material in Electronic Form (IT Act)",
        "description": "Whoever publishes or transmits in the electronic form, any material which is lascivious or appeals to the prurient interest.",
        "punishment": "First: Imprisonment up to 3 years + Fine up to ₹5 Lakhs. Subsequent: up to 5 years",
        "keywords": ["obscene video", "morphed photo", "revenge porn", "objectionable content shared online", "obscene whatsapp message"],
        "bailable": False,
    },
    # NDPS Act
    {
        "section": "20 NDPS Act",
        "title": "Punishment for Contravention (Cannabis) — NDPS Act",
        "description": "Punishment for contravention of provisions relating to cannabis plant and cannabis.",
        "punishment": "Rigorous Imprisonment up to 10 years + Fine up to ₹1 Lakh (for commercial quantity: up to 20 years)",
        "keywords": ["ganja", "cannabis", "marijuana", "bhang", "drug possession", "narcotics"],
        "bailable": False,
    },
    {
        "section": "22 NDPS Act",
        "title": "Punishment for Contravention of Provisions Relating to Psychotropic Substances — NDPS Act",
        "description": "Punishment for contravention in relation to psychotropic substances.",
        "punishment": "Rigorous Imprisonment up to 10 years + Fine (commercial: up to 20 years)",
        "keywords": ["mdma", "ecstasy", "psychotropic", "prescription drug abuse", "tramadol abuse", "drug trafficking"],
        "bailable": False,
    },
]

# ── Crime Category Map ─────────────────────────────────────────────
CRIME_CATEGORIES = {
    "violent": ["302", "304", "307", "323", "324", "354", "376"],
    "property": ["379", "380", "392", "395", "406", "420", "436"],
    "domestic": ["498A", "304B", "363", "366"],
    "cyber": ["66 IT Act", "67 IT Act", "420"],
    "narcotics": ["20 NDPS Act", "22 NDPS Act"],
    "public_order": ["506", "509"],
}


def _get_category(sections: List[str]) -> str:
    for cat, sec_list in CRIME_CATEGORIES.items():
        for s in sections:
            if s in sec_list:
                return cat.replace("_", " ").title()
    return "General"


def _get_risk(sections: List[str]) -> str:
    critical = {"302", "376", "395", "304B"}
    high = {"307", "304", "380", "392", "363", "366", "498A"}
    medium = {"354", "420", "406", "436", "66 IT Act", "20 NDPS Act", "22 NDPS Act"}
    if any(s in critical for s in sections):
        return "critical"
    if any(s in high for s in sections):
        return "high"
    if any(s in medium for s in sections):
        return "medium"
    return "low"


def _detect_mo_pattern(text: str, sections: List[str]) -> Optional[str]:
    text_lower = text.lower()
    if any(w in text_lower for w in ["atm", "card cloning", "skimming"]):
        return "ATM/Card Skimming"
    if any(w in text_lower for w in ["otp", "kyc", "bank call", "telecom fraud"]):
        return "OTP/KYC Phone Fraud"
    if any(w in text_lower for w in ["motorcycle", "bike", "chain snatching", "moving vehicle"]):
        return "Mobile Snatching (Bike-borne)"
    if any(w in text_lower for w in ["broke lock", "pried door", "entry through window", "house break"]):
        return "House Breaking (Lock Bypass)"
    if "379" in sections and any(w in text_lower for w in ["market", "bus", "crowd", "busy area"]):
        return "Pickpocketing in Public Space"
    if any(w in text_lower for w in ["love affair", "matrimony", "dating app", "online romance"]):
        return "Romance/Matrimony Fraud"
    return None


class NLPService:
    """
    spaCy-based NER + rule-based IPC section classifier.
    Falls back to regex patterns if spaCy model is unavailable.
    """

    def __init__(self):
        self._nlp = None
        self._load_spacy()

    def _load_spacy(self):
        try:
            import spacy
            self._nlp = spacy.load("en_core_web_sm")
            logger.info("✅ spaCy en_core_web_sm loaded")
        except Exception as e:
            logger.warning(f"⚠️ spaCy not available, using regex fallback: {e}")
            self._nlp = None

    def extract_entities(self, text: str) -> Dict[str, Any]:
        entities: Dict[str, Any] = {
            "complainant": None,
            "accused": [],
            "location": None,
            "date_time": None,
            "weapon": None,
            "property_stolen": None,
            "witnesses": [],
            "vehicle": None,
        }

        if self._nlp:
            doc = self._nlp(text)
            persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
            places = [ent.text for ent in doc.ents if ent.label_ in ("GPE", "LOC", "FAC")]
            dates = [ent.text for ent in doc.ents if ent.label_ in ("DATE", "TIME")]
            if persons:
                entities["complainant"] = persons[0]
                entities["accused"] = persons[1:4]
            if places:
                entities["location"] = ", ".join(places[:2])
            if dates:
                entities["date_time"] = dates[0]

        # Regex fallbacks & augmentations
        complainant_match = re.search(
            r"(?:complainant|reported by|filed by|stated by|name of complainant)[:\s]+([A-Z][a-z]+(?: [A-Z][a-z]+)*)",
            text, re.IGNORECASE
        )
        if complainant_match and not entities["complainant"]:
            entities["complainant"] = complainant_match.group(1)

        accused_match = re.search(
            r"(?:accused|suspect|perpetrator|alleged offender|named accused)[:\s]+([A-Z][a-z]+(?: [A-Z][a-z]+)*)",
            text, re.IGNORECASE
        )
        if accused_match and not entities["accused"]:
            entities["accused"] = [accused_match.group(1)]

        # Weapon detection
        weapons = ["knife", "gun", "pistol", "rifle", "rod", "axe", "sword", "stone", "sickle", "country bomb", "explosives"]
        found_weapons = [w for w in weapons if re.search(rf'\b{w}\b', text, re.IGNORECASE)]
        if found_weapons:
            entities["weapon"] = ", ".join(found_weapons[:3])

        # Vehicle detection
        vehicle_match = re.search(
            r'\b([A-Z]{2}[\s-]?\d{1,2}[\s-]?[A-Z]{1,2}[\s-]?\d{4})\b|'
            r'(?:motorcycle|bike|car|van|auto|tempo|truck|lorry)',
            text, re.IGNORECASE
        )
        if vehicle_match:
            entities["vehicle"] = vehicle_match.group(0)

        # Property stolen
        property_match = re.search(
            r'(?:stole|stolen|theft of|robbed of|took away)[^.]*?(₹[\d,]+|Rs\.?\s*[\d,]+|cash|gold|mobile|laptop|jewel\w*)',
            text, re.IGNORECASE
        )
        if property_match:
            entities["property_stolen"] = property_match.group(1)

        return entities

    def suggest_ipc_sections(self, text: str, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        text_lower = text.lower()
        matches = []

        for ipc in IPC_KNOWLEDGE_BASE:
            score = 0.0
            keyword_hits = 0
            for kw in ipc["keywords"]:
                if kw.lower() in text_lower:
                    keyword_hits += 1
            if keyword_hits == 0:
                continue
            score = min(0.95, 0.4 + (keyword_hits / len(ipc["keywords"])) * 0.55)
            matches.append({
                "section": ipc["section"],
                "title": ipc["title"],
                "description": ipc["description"],
                "punishment": ipc["punishment"],
                "confidence": round(score, 2),
                "bailable": ipc["bailable"],
            })

        # Sort by confidence desc, cap at 5 suggestions
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        return matches[:5]

    def get_crime_category(self, sections: List[str]) -> str:
        return _get_category(sections)

    def get_risk_level(self, sections: List[str]) -> str:
        return _get_risk(sections)

    def detect_mo_pattern(self, text: str, sections: List[str]) -> Optional[str]:
        return _detect_mo_pattern(text, sections)

    def generate_summary(self, text: str, entities: Dict, sections: List[Dict]) -> str:
        complainant = entities.get("complainant") or "the complainant"
        location = entities.get("location") or "the reported location"
        ipc_list = ", ".join([f"IPC {s['section']} ({s['title']})" for s in sections[:3]]) or "relevant IPC sections"
        return (
            f"FIR filed by {complainant} regarding an incident at {location}. "
            f"AI analysis suggests applicable sections: {ipc_list}. "
            f"Weapon: {entities.get('weapon') or 'Not reported'}. "
            f"Property: {entities.get('property_stolen') or 'Not specified'}. "
            f"Immediate investigation and evidence collection recommended."
        )

    def generate_next_steps(self, sections: List[Dict], risk_level: str) -> List[str]:
        steps = []
        section_nums = [s["section"] for s in sections]

        if risk_level in ("critical", "high"):
            steps.append("Immediate FIR registration and senior officer notification")
            steps.append("Secure the crime scene and preserve forensic evidence")

        if any(s in section_nums for s in ["302", "307"]):
            steps.extend([
                "Inform DySP / SP immediately",
                "Arrange post-mortem / medical examination",
                "Record dying declaration if victim is alive",
                "Collect CCTV footage from surrounding areas",
            ])

        if any(s in section_nums for s in ["379", "380", "392", "395"]):
            steps.extend([
                "Record complainant's statement under Sec 161 CrPC",
                "Check nearby CCTV footage and ATM cameras",
                "Verify suspect's antecedents in CCTNS",
                "Circulate vehicle description to checkposts",
            ])

        if any(s in section_nums for s in ["66 IT Act", "420"]):
            steps.extend([
                "File NCRP (National Cybercrime Reporting Portal) complaint",
                "Preserve digital evidence: screenshots, transaction IDs",
                "Contact bank for transaction hold within 24 hours",
                "Identify IP address / phone number through IMEI report",
            ])

        if any(s in section_nums for s in ["376", "354"]):
            steps.extend([
                "Arrange medical examination within 24 hours",
                "Record victim's statement in a private setting",
                "Assign a female officer",
                "Ensure victim's privacy and sensitivity protocol",
            ])

        if not steps:
            steps.append("Register FIR and investigate per standard SOP")
            steps.append("Record all witness statements under Sec 161 CrPC")

        return steps[:6]


_nlp_service_instance: Optional[NLPService] = None


def get_nlp_service() -> NLPService:
    global _nlp_service_instance
    if _nlp_service_instance is None:
        _nlp_service_instance = NLPService()
    return _nlp_service_instance

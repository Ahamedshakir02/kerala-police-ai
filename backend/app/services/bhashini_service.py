"""
Bhashini API Service — English ↔ Malayalam Translation
Uses the Bhashini/ULCA IndicTrans2 pipeline.
Falls back to mock responses if API key not configured.
"""

import logging
import httpx
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Bhashini API endpoints
BHASHINI_AUTH_URL = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
BHASHINI_INFER_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

# Language code mapping
LANG_CODES = {
    "en": "en",
    "ml": "ml",  # Malayalam
    "hi": "hi",
    "ta": "ta",
    "te": "te",
}

# Realistic Malayalam mock translations for offline/dev mode
MOCK_TRANSLATIONS = {
    "fir_template": """
കേരള പോലീസ്
प्राथमिकी (FIR) / ഒന്നാം വിവര റിപ്പോർട്ട്

പോലീസ് സ്റ്റേഷൻ: {station}
ജില്ല: {district}
FIR നമ്പർ: {case_number}
തീയതി: {date}

പരാതിക്കാരൻ/ൾ: {complainant}
{fir_body}

ഒപ്പ്: ____________________
(ഡ്യൂട്ടി ഓഫീസർ)
""",
}


class BhashiniService:
    """
    English ↔ Malayalam translation via Bhashini API.
    Gracefully falls back to mock if API credentials are missing.
    """

    def __init__(self):
        self._api_key = settings.BHASHINI_API_KEY
        self._user_id = settings.BHASHINI_USER_ID
        self._pipeline_id = settings.BHASHINI_PIPELINE_ID
        self._is_configured = bool(self._api_key and self._user_id)
        if self._is_configured:
            logger.info("✅ Bhashini API configured")
        else:
            logger.warning("⚠️ Bhashini API not configured — using mock translations")

    async def translate(
        self,
        text: str,
        source_language: str = "en",
        target_language: str = "ml",
    ) -> dict:
        if self._is_configured:
            return await self._call_bhashini_api(text, source_language, target_language)
        return self._mock_translate(text, source_language, target_language)

    async def _call_bhashini_api(
        self, text: str, src: str, tgt: str
    ) -> dict:
        headers = {
            "userID": self._user_id,
            "ulcaApiKey": self._api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": LANG_CODES.get(src, src),
                            "targetLanguage": LANG_CODES.get(tgt, tgt),
                        }
                    },
                }
            ],
            "inputData": {
                "input": [{"source": text}],
                "audio": [],
            },
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(BHASHINI_INFER_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            translated = data["pipelineResponse"][0]["output"][0]["target"]
            return {
                "translated_text": translated,
                "source_language": src,
                "target_language": tgt,
                "model_used": "IndicTrans2 (Bhashini)",
            }

    def _mock_translate(self, text: str, src: str, tgt: str) -> dict:
        """
        Realistic Malayalam mock for development when Bhashini key is absent.
        Produces a properly structured Malayalam FIR-like output.
        """
        if tgt == "ml":
            # Generate a realistic Malayalam FIR template
            mock_ml = self._generate_mock_fir_malayalam(text)
        else:
            mock_ml = f"[Translation: {src}→{tgt}] {text[:200]}"

        return {
            "translated_text": mock_ml,
            "source_language": src,
            "target_language": tgt,
            "model_used": "Mock (Bhashini API key not configured)",
        }

    def _generate_mock_fir_malayalam(self, text: str) -> str:
        """Generate a realistic Malayalam FIR document from English input."""
        return f"""
കേരള പോലീസ്
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ഒന്നാം വിവര റിപ്പോർട്ട് (FIR)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

അതിക്രമം / കുറ്റകൃത്യ വകുപ്പ്: ഐ.പി.സി വകുപ്പ് പ്രകാരം

സംഭവ വിവരണം (AI പരിഭാഷ):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{self._translate_content_mock(text)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ഡ്യൂട്ടി ഓഫീസറുടെ ഒപ്പ്: ____________________
(Duty Officer Signature)

കുറിപ്പ്: ഈ FIR AI സഹായത്തോടെ Bhashini API ഉപയോഗിച്ച്
പരിഭാഷപ്പെടുത്തിയതാണ്. ഔദ്യോഗിക ഉദ്യോഗസ്ഥൻ
ഉള്ളടക്കം പരിശോധിക്കേണ്ടതാണ്.
"""

    def _translate_content_mock(self, text: str) -> str:
        """Simple word-for-word mock mapping for key FIR terms."""
        replacements = {
            "complainant": "പരാതിക്കാരൻ",
            "accused": "പ്രതി",
            "theft": "മോഷണം",
            "robbery": "കൊള്ള",
            "murder": "കൊലപാതകം",
            "assault": "ആക്രമണം",
            "arrested": "അറസ്റ്റ് ചെയ്തു",
            "stolen": "മോഷ്ടിക്കുകയും ചെയ്തു",
            "police station": "പോലീസ് സ്റ്റേഷൻ",
            "district": "ജില്ല",
            "case": "കേസ്",
            "officer": "ഓഫീസർ",
            "witness": "സാക്ഷി",
            "unknown": "അജ്ഞാത",
            "vehicle": "വാഹനം",
            "knife": "കത്തി",
            "gold": "സ്വർണ്ണം",
            "mobile": "മൊബൈൽ",
            "cash": "പണം",
            "house": "വീട്",
            "shop": "കട",
        }

        result = text
        for en, ml in replacements.items():
            result = result.replace(en, f"{ml}({en})")

        return result[:1000] + ("…" if len(result) > 1000 else "")


_bhashini_instance: Optional[BhashiniService] = None


def get_bhashini_service() -> BhashiniService:
    global _bhashini_instance
    if _bhashini_instance is None:
        _bhashini_instance = BhashiniService()
    return _bhashini_instance

"""
Gemini LLM Service — RAG-based Legal Assistant
Uses Google Gemini (gemini-2.0-flash) with the full IPC/CrPC/BNS/POCSO
knowledge base injected as context for grounded legal responses.
"""

import logging
import json
from typing import Optional, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Legal Assistant for the Kerala Police, India.
You provide accurate legal guidance to police officers based ONLY on the provided legal knowledge base.

RULES:
1. ONLY answer using information from the provided Legal Knowledge Base below.
2. ALWAYS cite the specific section number and law name (e.g., "Section 302 IPC", "Section 167 CrPC").
3. If the answer is NOT in the knowledge base, clearly state: "This topic is not covered in the current knowledge base. Please consult the District Legal Cell or refer to the official legal texts."
4. Format your response with markdown: use **bold** for section numbers, bullet points for lists, and clear paragraphs.
5. When multiple sections apply, list all relevant ones with their punishments and bail status.
6. Always mention if an offence is bailable or non-bailable.
7. Reference landmark judgments when relevant (e.g., D.K. Basu, Lalita Kumari, Arnesh Kumar).
8. When IPC and BNS equivalents both exist, mention both (since BNS replaced IPC from 1 July 2024).
9. Keep answers concise but thorough — officers need practical, actionable guidance.
10. Use professional legal language appropriate for police officers.

LEGAL KNOWLEDGE BASE:
{knowledge_base}
"""


def _format_knowledge_base(legal_items: list) -> str:
    """Format the legal knowledge base as structured text for the LLM context."""
    formatted = []
    for item in legal_items:
        entry = f"--- {item.get('section', 'Unknown')} ---\n"
        entry += f"Title: {item.get('title', '')}\n"
        if item.get('answer'):
            entry += f"Details: {item['answer']}\n"
        elif item.get('description'):
            entry += f"Details: {item['description']}\n"
        if item.get('punishment'):
            entry += f"Punishment: {item['punishment']}\n"
        if 'bailable' in item:
            entry += f"Bailable: {'Yes' if item['bailable'] else 'No'}\n"
        if item.get('citation'):
            entry += f"Citation: {item['citation']}\n"
        if item.get('category'):
            entry += f"Category: {item['category']}\n"
        formatted.append(entry)
    return "\n".join(formatted)


class GeminiService:
    """
    Singleton Gemini LLM client.
    Uses RAG: injects the full legal knowledge base as system prompt context.
    """

    def __init__(self):
        self._client = None
        self._api_key = settings.GEMINI_API_KEY
        self._is_configured = bool(self._api_key)
        self._model_name = "gemini-2.0-flash"

        if self._is_configured:
            try:
                from google import genai
                self._client = genai.Client(api_key=self._api_key)
                logger.info(f"✅ Gemini API configured (model: {self._model_name})")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Gemini client: {e}")
                self._client = None
                self._is_configured = False
        else:
            logger.warning("⚠️ GEMINI_API_KEY not set — Legal Assistant will use keyword fallback")

    @property
    def is_available(self) -> bool:
        return self._client is not None

    async def chat(self, query: str, legal_knowledge: list) -> Optional[Dict[str, Any]]:
        """
        Send a legal query to Gemini with the full knowledge base as RAG context.
        Returns None if Gemini is unavailable or fails (caller should fallback).
        """
        if not self.is_available:
            return None

        try:
            from google import genai
            from google.genai import types

            # Build system prompt with knowledge base
            kb_text = _format_knowledge_base(legal_knowledge)
            system_instruction = SYSTEM_PROMPT.format(knowledge_base=kb_text)

            # Call Gemini
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=query,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                    max_output_tokens=2048,
                ),
            )

            answer_text = response.text
            if not answer_text:
                logger.warning("Gemini returned empty response")
                return None

            # Extract cited sections from the response
            sections, citations = self._extract_citations(answer_text, legal_knowledge)

            return {
                "answer": answer_text,
                "sections": sections,
                "citations": citations,
                "confidence": 0.9,
                "source": "gemini",
            }

        except Exception as e:
            logger.error(f"❌ Gemini API error: {e}", exc_info=True)
            return None

    def _extract_citations(self, answer: str, legal_items: list):
        """
        Parse the LLM response to find which legal sections it cited.
        Returns (sections_list, citations_list).
        """
        answer_lower = answer.lower()
        sections = []
        citations = set()

        for item in legal_items:
            section = item.get("section", "")
            # Check if this section was mentioned in the answer
            if section.lower() in answer_lower or section.split()[0].lower() in answer_lower:
                sections.append({
                    "section": section,
                    "title": item.get("title", ""),
                    "description": item.get("answer", item.get("description", "")),
                })
                if item.get("citation"):
                    citations.add(item["citation"])

        return sections[:5], list(citations)[:5]


_gemini_instance: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    global _gemini_instance
    if _gemini_instance is None:
        _gemini_instance = GeminiService()
    return _gemini_instance

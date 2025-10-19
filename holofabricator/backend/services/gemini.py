"""Gemini client wrapper for analysis and chat interactions."""

from __future__ import annotations

import json
from typing import Any, Dict

import google.generativeai as genai
from PIL import Image

from ..models import AnalysisResponse, ChatResponse


class GeminiNotConfigured(RuntimeError):
    """Raised when Gemini API interactions are attempted without configuration."""


class GeminiClient:
    """Thin wrapper around Gemini model usage."""

    def __init__(self, api_key: str | None) -> None:
        if api_key:
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel("gemini-2.5-pro")
        else:
            self._model = None

    @property
    def configured(self) -> bool:
        return self._model is not None

    def _require_model(self) -> None:
        if self._model is None:
            raise GeminiNotConfigured("Gemini API key not configured.")

    def analyse_image(self, image: Image.Image) -> AnalysisResponse:
        """Analyse an object image and return a structured response."""
        self._require_model()

        prompt = """
        Analyse this object as an expert engineer. Provide detailed technical analysis.

        Return a JSON response with this exact structure:
        {
            "object_name": "Specific name of the object",
            "category": "Category (e.g., mechanical, electronic, tool, automotive)",
            "description": "Detailed technical description",
            "parts": [
                {"name": "Part name", "function": "What this part does", "material": "Likely material", "location": "Where on object"}
            ],
            "materials": ["List of probable materials"],
            "dimensions": {"width_mm": value, "height_mm": value, "depth_mm": value},
            "confidence": 0.0-1.0
        }
        """

        response = self._model.generate_content([prompt, image])
        payload = self._extract_json(response.text)

        # Ensure optional keys exist
        payload.setdefault("parts", [])
        payload.setdefault("materials", [])
        payload.setdefault("dimensions", None)
        payload.setdefault("confidence", 0.0)

        analysis = AnalysisResponse(**payload)
        return analysis

    def answer_question(self, analysis: AnalysisResponse, image: Image.Image, question: str) -> ChatResponse:
        """Generate an answer using the existing analysis context."""
        self._require_model()

        prompt = f"""
        You are an expert engineer analysing this object: {analysis.object_name}.
        Previous analysis:
        {analysis.json(indent=2)}

        User question: {question}

        Provide:
        1. A clear, detailed answer
        2. List which parts are relevant (by name from the parts list)

        Return JSON:
        {{
            "answer": "Your detailed answer here",
            "highlighted_parts": ["part1", "part2"]
        }}
        """

        response = self._model.generate_content([prompt, image])
        payload = self._extract_json(response.text)
        payload.setdefault("highlighted_parts", [])

        return ChatResponse(**payload)

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        """Extract JSON payload from Gemini output."""
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            json_str = text.split("```")[1].split("```")[0]
        else:
            json_str = text

        return json.loads(json_str.strip())

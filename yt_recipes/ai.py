"""AI-powered recipe extraction using Groq API."""

import json
import logging
import re

import httpx
from pydantic import BaseModel, Field

from .config import Settings

logger = logging.getLogger("yt_recipes")


class Recipe(BaseModel):
    """Recipe data model."""

    name: str
    icon: str = "🍽️"
    servings: str
    prep_time: str
    cook_time: str
    total_time: str
    difficulty: str
    ingredients: list[str]
    instructions: list[str]
    notes: list[str] = Field(default_factory=list)


class RecipeExtractionResponse(BaseModel):
    """Response model for recipe extraction."""

    recipes: list[Recipe]


class RecipeExtractorError(Exception):
    """Base exception for recipe extraction errors."""

    pass


class RecipeExtractor:
    """Extract recipes from video transcripts using Groq AI."""

    # Language-specific system prompts
    LANGUAGE_PROMPTS = {
        "es": "español",
        "en": "English",
        "fr": "français",
        "de": "Deutsch",
        "it": "italiano",
        "pt": "português",
    }

    def __init__(self, settings: Settings):
        """
        Initialize recipe extractor.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.client = httpx.Client(timeout=60.0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def extract(self, transcript: str, language: str = "es") -> list[Recipe]:
        """
        Extract recipes from transcript using Groq AI.

        Args:
            transcript: Video transcript text
            language: Target language code (es, en, fr, de, it, pt)

        Returns:
            list of extracted recipes

        Raises:
            RecipeExtractorError: If extraction fails
        """
        system_prompt = self._build_system_prompt(language)

        payload = {
            "model": self.settings.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Extract all recipes from this transcript:\n\n{transcript}"
                    ),
                },
            ],
            "temperature": 0.2,
            "max_tokens": 8000,
        }

        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        logger.debug(f"Sending transcript to Groq API (language: {language})")

        try:
            response = self.client.post(
                self.settings.groq_api_url, json=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise RecipeExtractorError(f"Groq API request failed: {e}") from e

        # Parse response
        try:
            content = data["choices"][0]["message"]["content"]
            recipes = self._parse_response(content)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise RecipeExtractorError(f"Failed to parse Groq response: {e}") from e

        logger.info(f"Extracted {len(recipes)} recipe(s)")
        return recipes

    def _build_system_prompt(self, language: str) -> str:
        """
        Build system prompt for recipe extraction.

        Args:
            language: Target language code

        Returns:
            System prompt text
        """
        target_language = self.LANGUAGE_PROMPTS.get(language, "español")

        # Build translation instruction
        if language != "en":
            translation_text = (
                f"2. Translate them to {target_language} if they are in another language"
            )
        else:
            translation_text = (
                "2. Keep them in the original language if already in English, "
                "otherwise translate to English"
            )

        return f"""
You are an expert culinary instructor who extracts detailed, professional recipes from
video transcripts. Your task:

1. Identify ALL food recipes mentioned in the transcript
{translation_text}
3. Extract COMPLETE details including:
   - Exact ingredient quantities (never omit amounts)
   - Precise cooking temperatures and times
   - Detailed step-by-step instructions
   - Important tips, warnings, and variations
4. Return ONLY valid JSON with no additional text
5. If no recipes found, return empty array

IMPORTANT:
- Be thorough with measurements and times
- Include every ingredient mentioned
- Break complex steps into smaller, clear actions
- Add helpful notes about technique or substitutions
- Specify equipment when relevant (air fryer, oven, etc.)

Return format:
{{
  "recipes": [
    {{
      "name": "Recipe Name in {target_language}",
      "icon": "appropriate emoji (🍕🍝🥘🍖🥗🍰🧁🍪🥐🌮🍜🍛🥟🍱)",
      "servings": "number or range",
      "prep_time": "X minutes",
      "cook_time": "X minutes",
      "total_time": "X minutes",
      "difficulty": "Easy/Medium/Hard",
      "ingredients": ["quantity + ingredient with details"],
      "instructions": ["detailed step with specific technique"],
      "notes": ["tip, variation, or important observation"]
    }}
  ]
}}"""

    def _parse_response(self, content: str) -> list[Recipe]:
        """
        Parse AI response and extract recipes.

        Args:
            content: AI response content

        Returns:
            List of Recipe objects
        """
        # Remove markdown code blocks if present
        cleaned_content = content.strip()
        if cleaned_content.startswith("```"):
            cleaned_content = re.sub(r"^```(?:json)?\n?", "", cleaned_content)
            cleaned_content = re.sub(r"\n?```$", "", cleaned_content)

        # Parse JSON
        try:
            parsed_data = json.loads(cleaned_content.strip())
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse JSON. Content preview: {cleaned_content[:200]}"
            )
            raise RecipeExtractorError(f"Invalid JSON response from AI: {e}") from e

        # Validate with Pydantic
        try:
            response = RecipeExtractionResponse(**parsed_data)
        except Exception as e:
            raise RecipeExtractorError(f"Invalid recipe data structure: {e}") from e

        return response.recipes


def extract_recipes(
    transcript: str, settings: Settings, language: str = "es"
) -> list[Recipe]:
    """
    Convenience function to extract recipes.

    Args:
        transcript: Video transcript
        settings: Application settings
        language: Target language code

    Returns:
        List of recipes
    """
    with RecipeExtractor(settings) as extractor:
        return extractor.extract(transcript, language)

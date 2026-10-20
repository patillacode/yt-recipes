"""AI-powered recipe extraction using Groq API."""

import json
import logging
import re
from typing import Literal, get_args

import httpx
from pydantic import BaseModel, Field

from .config import Settings

logger = logging.getLogger("yt_recipes")


Dificultad = Literal["fácil", "media", "difícil"]
Categoria = Literal[
    "aperitivo",
    "carne",
    "pollo",
    "pescado",
    "huevos",
    "verduras",
    "pasta",
    "arroz",
    "sandwich",
    "patatas",
    "postre",
]
Electrodomestico = Literal["air-fryer", "horno", "fuego", "ninguno"]


class Recipe(BaseModel):
    """Recipe data model."""

    nombre: str
    raciones: str
    tiempo_total: int
    dificultad: Dificultad
    categoria: list[Categoria] = Field(min_length=1)
    electrodomestico: Electrodomestico
    ingredientes: list[str]
    pasos: list[str]
    notas: list[str] = Field(default_factory=list)
    original: str | None = None


class RecipeExtractionResponse(BaseModel):
    """Response model for recipe extraction."""

    recipes: list[Recipe]


SYSTEM_PROMPT = f"""
Eres un instructor de cocina experto que extrae recetas detalladas de transcripciones
de vídeos. Tu tarea:

1. Identifica TODAS las recetas de comida mencionadas en la transcripción.
2. Tradúcelas al español si están en otro idioma.
3. Extrae los detalles COMPLETOS: cantidades exactas de cada ingrediente (nunca omitas
   cantidades), temperaturas y tiempos precisos, pasos detallados, y consejos,
   advertencias y variantes como notas.
4. Devuelve SOLO JSON válido, sin texto adicional. Si no hay recetas, devuelve
   {{"recipes": []}}.

Formato:
{{
  "recipes": [
    {{
      "nombre": "Nombre completo y descriptivo, p. ej. Sándwich de atún y queso",
      "raciones": "número o rango, p. ej. \\"4\\" o \\"4-6\\"",
      "tiempo_total": entero en minutos (preparación + cocción, máximo si es rango),
      "dificultad": una de {list(get_args(Dificultad))},
      "categoria": lista con TODAS las que encajen, de {list(get_args(Categoria))},
      "electrodomestico": uno de {list(get_args(Electrodomestico))},
      "ingredientes": ["cantidad + ingrediente"],
      "pasos": ["paso detallado con técnica, temperatura y tiempo"],
      "notas": ["consejo, variante u observación importante"]
    }}
  ]
}}

El nombre va en minúscula salvo la primera letra y los nombres propios (Oreo, Brás).
"categoria" incluye TODAS las que encajen: por el ingrediente principal y por el formato
(postre para dulces, aperitivo para picoteo, sandwich para bocadillos y panes rellenos);
p. ej. un sándwich de atún es ["sandwich", "pescado"]. "electrodomestico" es
el aparato principal de cocción: air-fryer, horno, fuego (sartén, cazuela, vitro) o
ninguno (sin cocción). Usa exactamente los valores de las listas.
"""


class RecipeExtractorError(Exception):
    """Base exception for recipe extraction errors."""

    pass


class RecipeExtractor:
    """Extract recipes from video transcripts using Groq AI."""

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

    def extract(self, transcript: str) -> list[Recipe]:
        """
        Extract recipes from transcript using Groq AI.

        Args:
            transcript: Video transcript text

        Returns:
            list of extracted recipes

        Raises:
            RecipeExtractorError: If extraction fails
        """
        payload = {
            "model": self.settings.groq_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Extrae todas las recetas de esta transcripción:\n\n{transcript}"
                    ),
                },
            ],
            "temperature": 0.2,
            "max_tokens": 8000,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        logger.debug("Sending transcript to Groq API")

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


def extract_recipes(transcript: str, settings: Settings) -> list[Recipe]:
    """
    Convenience function to extract recipes.

    Args:
        transcript: Video transcript
        settings: Application settings

    Returns:
        List of recipes
    """
    with RecipeExtractor(settings) as extractor:
        return extractor.extract(transcript)

"""Configuration management using Pydantic Settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # RapidAPI Configuration
    rapidapi_key: str = Field(..., description="RapidAPI key for YouTube transcript API")

    # Groq API Configuration
    groq_api_key: str = Field(..., description="Groq API key for AI recipe extraction")

    # Obsidian vault folder where recipes are written
    recipes_dir: Path = Field(
        default=Path("~/syncthing/obsidian/recetas").expanduser(),
        description="Directory for recipe notes",
    )

    # API Endpoints
    rapidapi_host: str = Field(
        default="youtube-transcript3.p.rapidapi.com",
        description="RapidAPI transcript host",
    )
    groq_api_url: str = Field(
        default="https://api.groq.com/openai/v1/chat/completions",
        description="Groq API endpoint",
    )
    groq_model: str = Field(
        default="openai/gpt-oss-120b", description="Groq model to use"
    )


def get_settings() -> Settings:
    """Load and return application settings."""
    return Settings()

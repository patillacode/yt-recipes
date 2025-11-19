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

    # Docmost Configuration
    docmost_url: str = Field(
        default="https://docmost.patilla.es", description="Docmost instance URL"
    )
    docmost_email: str = Field(..., description="Docmost account email")
    docmost_password: str = Field(..., description="Docmost account password")
    docmost_space_id: str = Field(
        default="0199bdd6-b113-7a3d-a72a-d4001253ba70", description="Docmost space ID"
    )
    docmost_parent_page_id: str = Field(
        default="0199fd11-45e0-7004-b322-30922f3f470a",
        description="Parent page ID for recipes",
    )

    # Application Settings
    default_language: str = Field(
        default="es", description="Default language for recipes"
    )
    export_dir: Path = Field(
        default=Path("./recipes"), description="Directory for exported recipes"
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
        default="llama-3.3-70b-versatile", description="Groq model to use"
    )


def get_settings() -> Settings:
    """Load and return application settings."""
    return Settings()

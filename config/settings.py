"""
Configuration Management for The Soundtrack of Your Life

This module provides centralized, type-safe configuration using Pydantic Settings.
All settings can be overridden via environment variables or .env file.

Cross-platform compatible: Windows, Linux, macOS
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from platformdirs import user_data_dir, user_cache_dir


class Settings(BaseSettings):
    """Application configuration with environment variable override support."""

    # =========================================================================
    # APPLICATION SETTINGS
    # =========================================================================
    app_name: str = Field(
        default="The Soundtrack of Your Life",
        description="Application display name"
    )
    app_env: str = Field(
        default="development",
        description="Environment: development, production, testing"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )

    # =========================================================================
    # LLM CONFIGURATION
    # =========================================================================
    llm_provider: str = Field(
        default="ollama",
        description="LLM provider: ollama, openai, anthropic"
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL"
    )
    ollama_model: str = Field(
        default="qwen2.5:3b",
        description="Ollama model name"
    )
    llm_timeout: int = Field(
        default=180,
        ge=30,
        le=600,
        description="LLM request timeout in seconds"
    )
    llm_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="LLM temperature for response randomness"
    )
    llm_max_tokens: int = Field(
        default=1000,
        ge=100,
        le=8000,
        description="Maximum tokens in LLM response"
    )
    enable_llm_explanations: bool = Field(
        default=False,
        description="Use a second Ollama call for explanations; disabled for faster local responses"
    )

    # =========================================================================
    # EMBEDDING CONFIGURATION
    # =========================================================================
    embedding_provider: str = Field(
        default="sentence-transformers",
        description="Embedding provider"
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model identifier"
    )
    embedding_device: str = Field(
        default="cpu",
        description="Device for embeddings: cpu, cuda, mps"
    )

    # =========================================================================
    # VECTOR DATABASE CONFIGURATION
    # =========================================================================
    vector_store: str = Field(
        default="chroma",
        description="Vector store type: chroma"
    )
    vector_db_path: Optional[str] = Field(
        default=None,
        description="Custom vector DB path (optional)"
    )
    collection_name: str = Field(
        default="music_knowledge",
        description="ChromaDB collection name"
    )
    retrieval_top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of top results to retrieve"
    )

    # =========================================================================
    # RECOMMENDATION ENGINE SETTINGS
    # =========================================================================
    max_recommendations: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of track recommendations"
    )
    max_memory_length: int = Field(
        default=5000,
        ge=100,
        le=10000,
        description="Maximum character length for memory input"
    )

    # Scoring weights
    weight_mood: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Weight for mood matching in scoring"
    )
    weight_genre: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description="Weight for genre matching in scoring"
    )
    weight_language: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Weight for language compatibility in scoring"
    )
    weight_instrument: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Weight for instrument matching in scoring"
    )
    weight_theme: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Weight for theme matching in scoring"
    )
    weight_audio: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Weight for tempo and energy compatibility"
    )
    weight_personal: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Weight for future preference signals"
    )

    # =========================================================================
    # OPTIONAL FEATURES
    # =========================================================================
    enable_external_music_lookup: bool = Field(
        default=False,
        description="Enable bounded iTunes/Spotify metadata enrichment"
    )
    spotify_client_id: Optional[str] = Field(default=None, description="Optional Spotify client ID")
    spotify_client_secret: Optional[str] = Field(default=None, description="Optional Spotify client secret")
    enable_memory_vault: bool = Field(
        default=True,
        description="Enable memory vault persistence"
    )

    # =========================================================================
    # DATA STORAGE
    # =========================================================================
    app_data_dir: Optional[str] = Field(
        default=None,
        description="Custom app data directory (optional)"
    )
    db_name: str = Field(
        default="memories.db",
        description="SQLite database filename"
    )

    # =========================================================================
    # PYDANTIC CONFIGURATION
    # =========================================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # =========================================================================
    # VALIDATORS
    # =========================================================================
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @field_validator("weight_mood", "weight_genre", "weight_instrument", "weight_theme")
    @classmethod
    def validate_weights(cls, v: float) -> float:
        """Validate that weights are between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Weight must be between 0 and 1, got {v}")
        return v

    # =========================================================================
    # COMPUTED PROPERTIES
    # =========================================================================
    @property
    def data_dir(self) -> Path:
        """Get the application data directory (platform-aware)."""
        if self.app_data_dir:
            return Path(self.app_data_dir)
        return Path(user_data_dir(self.app_name, appauthor=False))

    @property
    def cache_dir(self) -> Path:
        """Get the application cache directory (platform-aware)."""
        return Path(user_cache_dir(self.app_name, appauthor=False))

    @property
    def db_path(self) -> Path:
        """Get the full database file path."""
        return self.data_dir / self.db_name

    @property
    def vector_db_dir(self) -> Path:
        """Get the vector database directory."""
        if self.vector_db_path:
            return Path(self.vector_db_path)
        return self.data_dir / "chroma_db"

    @property
    def total_weight(self) -> float:
        """Calculate total configured scoring weight."""
        return sum((
            self.weight_mood, self.weight_genre, self.weight_language,
            self.weight_instrument, self.weight_theme, self.weight_audio,
            self.weight_personal,
        ))

    def validate_weights_sum(self) -> bool:
        """Check if weights approximately sum to 1.0."""
        return abs(self.total_weight - 1.0) < 0.01

    def ensure_directories(self) -> None:
        """Create necessary application directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.vector_db_dir.mkdir(parents=True, exist_ok=True)

    def display_summary(self) -> str:
        """Generate a configuration summary for display."""
        return f"""
{'='*70}
  {self.app_name:^66}  
{'='*70}

ENVIRONMENT: {self.app_env}
LOG LEVEL: {self.log_level}

LLM CONFIGURATION:
  Provider: {self.llm_provider}
  Model: {self.ollama_model}
  Base URL: {self.ollama_base_url}
  Timeout: {self.llm_timeout}s
  Temperature: {self.llm_temperature}

EMBEDDING CONFIGURATION:
  Provider: {self.embedding_provider}
  Model: {self.embedding_model}
  Device: {self.embedding_device}

VECTOR DATABASE:
  Type: {self.vector_store}
  Path: {self.vector_db_dir}
  Collection: {self.collection_name}
  Top-K: {self.retrieval_top_k}

RECOMMENDATION ENGINE:
  Max Recommendations: {self.max_recommendations}
  Scoring Weights: Mood={self.weight_mood}, Genre={self.weight_genre}, Instrument={self.weight_instrument}, Theme={self.weight_theme}
  Total Weight: {self.total_weight:.2f}

STORAGE:
  Data Directory: {self.data_dir}
  Database: {self.db_path}

FEATURES:
  Memory Vault: {'Enabled' if self.enable_memory_vault else 'Disabled'}
  External Music Lookup: {'Enabled' if self.enable_external_music_lookup else 'Disabled'}
"""


# =============================================================================
# GLOBAL SETTINGS INSTANCE
# =============================================================================
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
        # Ensure directories exist
        _settings.ensure_directories()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment/config files."""
    global _settings
    _settings = Settings()
    _settings.ensure_directories()
    return _settings

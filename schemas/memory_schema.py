"""
Pydantic Schemas for Memory Analysis and Music Recommendations

Defines structured data models for LLM output validation and data consistency.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class MemoryAnalysis(BaseModel):
    """Structured output from LLM memory analysis.
    
    This schema ensures the LLM provides comprehensive emotional and musical
    analysis of user memories in a consistent, validated format.
    """

    # =========================================================================
    # MEMORY UNDERSTANDING
    # =========================================================================
    memory_title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Generated title summarizing the memory"
    )
    
    summary: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Brief summary of the memory's essence"
    )

    # =========================================================================
    # EMOTIONAL ANALYSIS
    # =========================================================================
    primary_emotions: List[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Main emotions present in the memory"
    )
    
    secondary_emotions: List[str] = Field(
        default_factory=list,
        max_length=5,
        description="Subtle or underlying emotions"
    )
    
    emotional_intensity: int = Field(
        ...,
        ge=1,
        le=10,
        description="Intensity of emotions on scale 1-10"
    )

    # =========================================================================
    # CONTEXTUAL UNDERSTANDING
    # =========================================================================
    themes: List[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Key themes (e.g., friendship, achievement, farewell)"
    )
    
    context: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Contextual elements (e.g., college, family, celebration)"
    )

    # =========================================================================
    # MUSICAL CHARACTERISTICS
    # =========================================================================
    genres: List[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Recommended music genres"
    )
    
    instruments: List[str] = Field(
        ...,
        min_length=1,
        max_length=8,
        description="Instruments that would match the mood"
    )
    
    tempo: str = Field(
        ...,
        description="Tempo description (e.g., slow, moderate, fast, variable)"
    )
    
    energy: str = Field(
        ...,
        description="Energy level (e.g., low, moderate, high, dynamic)"
    )
    
    atmosphere: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Overall musical atmosphere and mood"
    )
    
    musical_description: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="Detailed description of suitable musical characteristics"
    )
    language: Optional[str] = Field(default=None, max_length=80)
    requested_music_language: Optional[str] = Field(default=None, max_length=80)
    cultural_context: List[str] = Field(default_factory=list, max_length=10)

    # =========================================================================
    # VALIDATORS
    # =========================================================================
    @field_validator('cultural_context', mode='before')
    @classmethod
    def normalize_cultural_context(cls, value: Any) -> List[str]:
        """Accept a single model-generated sentence or a list of references."""
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        return value

    @field_validator('primary_emotions', 'secondary_emotions', 'themes', 'context', 'genres', 'instruments')
    @classmethod
    def validate_list_items(cls, v: List[str]) -> List[str]:
        """Ensure list items are non-empty and properly formatted."""
        cleaned = [item.strip() for item in v if item.strip()]
        if not cleaned and v:  # Only raise if original list was non-empty
            raise ValueError("List items cannot be empty strings")
        return cleaned

    @field_validator('tempo')
    @classmethod
    def validate_tempo(cls, v: str) -> str:
        """Validate tempo is a reasonable value."""
        v_clean = v.strip().lower()
        if len(v_clean) < 3:
            raise ValueError("Tempo description too short")
        return v.strip()

    @field_validator('energy')
    @classmethod
    def validate_energy(cls, v: str) -> str:
        """Validate energy level description."""
        v_clean = v.strip().lower()
        if len(v_clean) < 3:
            raise ValueError("Energy description too short")
        return v.strip()

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "memory_title": "Last Day at College with Friends",
                "summary": "A bittersweet farewell moment filled with happiness and nostalgia as college ends.",
                "primary_emotions": ["nostalgia", "happiness", "sadness"],
                "secondary_emotions": ["gratitude", "hope"],
                "emotional_intensity": 7,
                "themes": ["friendship", "farewell", "life transitions", "memories"],
                "context": ["college", "youth", "coming of age"],
                "genres": ["indie folk", "acoustic pop", "soft rock"],
                "instruments": ["acoustic guitar", "piano", "strings", "light percussion"],
                "tempo": "moderate",
                "energy": "low to moderate",
                "atmosphere": "warm, reflective, bittersweet with a touch of hope",
                "musical_description": "Gentle acoustic melodies with warm instrumentation that balances uplifting elements with reflective, introspective moments. The music should feel like a warm embrace while acknowledging the bittersweetness of change."
            }
        }


class TrackRecommendation(BaseModel):
    """Individual music track recommendation."""
    
    track_id: str = Field(
        ...,
        description="Unique track identifier"
    )
    
    track_name: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Track title"
    )
    
    artist: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Artist name"
    )
    
    genre_tags: List[str] = Field(
        default_factory=list,
        description="Genre tags from catalogue"
    )
    
    mood_tags: List[str] = Field(
        default_factory=list,
        description="Mood/theme tags from catalogue"
    )
    
    instrument_tags: List[str] = Field(
        default_factory=list,
        description="Instrument tags from catalogue"
    )
    
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score (0-1)"
    )
    
    explanation: str = Field(
        ...,
        min_length=20,
        max_length=1000,
        description="Explanation of why this track matches the memory"
    )
    
    source: str = Field(
        default="MTG-Jamendo",
        description="Data source"
    )
    
    preview_url: Optional[str] = Field(
        default=None,
        description="Optional preview URL (if available and permitted)"
    )
    listening_url: Optional[str] = Field(default=None)
    album: Optional[str] = Field(default=None)
    language: Optional[str] = Field(default=None)
    artwork_url: Optional[str] = Field(default=None)
    availability_status: str = Field(default="metadata_only")
    metadata_enrichment: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "track_id": "12345",
                "track_name": "Memories Fade",
                "artist": "Acoustic Dreamers",
                "genre_tags": ["indie", "folk", "acoustic"],
                "mood_tags": ["nostalgic", "bittersweet", "reflective"],
                "instrument_tags": ["guitar", "piano"],
                "relevance_score": 0.92,
                "explanation": "This track perfectly captures the bittersweet nostalgia of your memory through gentle acoustic guitar and reflective piano melodies.",
                "source": "MTG-Jamendo",
                "preview_url": None
            }
        }


class SoundtrackResult(BaseModel):
    """Complete soundtrack generation result."""
    
    memory_analysis: MemoryAnalysis = Field(
        ...,
        description="Analyzed memory with emotions and musical characteristics"
    )
    
    recommendations: List[TrackRecommendation] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Recommended tracks"
    )
    
    overall_explanation: str = Field(
        ...,
        min_length=50,
        max_length=2000,
        description="Overall explanation of the soundtrack selection"
    )
    
    retrieved_knowledge_summary: Optional[List[str]] = Field(
        default=None,
        description="Summary of retrieved RAG context (for transparency)"
    )
    
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of generation"
    )


class SavedMemory(BaseModel):
    """Saved memory in the personal vault."""
    
    id: Optional[int] = Field(
        default=None,
        description="Database ID (auto-generated)"
    )
    
    story: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Original memory story"
    )
    
    memory_title: str = Field(
        ...,
        description="Generated title"
    )
    
    summary: str = Field(
        ...,
        description="Memory summary"
    )
    
    emotions: List[str] = Field(
        ...,
        description="All emotions (primary + secondary)"
    )
    
    themes: List[str] = Field(
        ...,
        description="Themes identified"
    )
    
    musical_attributes: Dict[str, Any] = Field(
        ...,
        description="Musical characteristics (genres, instruments, tempo, etc.)"
    )
    
    recommendations: List[Dict[str, Any]] = Field(
        ...,
        description="Track recommendations as dicts"
    )
    
    explanation: str = Field(
        ...,
        description="Overall soundtrack explanation"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Save timestamp"
    )

    class Config:
        """Pydantic configuration."""
        from_attributes = True

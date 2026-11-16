# Low-Level Design (LLD)
## The Soundtrack of Your Life

---

## 1. Module-Level Design

### 1.1 config/settings.py

**Purpose:** Centralized configuration management

**Class:** `Settings(BaseSettings)`

**Key Attributes:**
```python
# LLM Configuration
ollama_base_url: str = "http://localhost:11434"
ollama_model: str = "qwen2.5:3b"
llm_temperature: float = 0.3
llm_max_tokens: int = 2000

# Embedding Configuration
embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
embedding_device: str = "cpu"

# RAG Configuration
vector_db_dir: Path
collection_name: str = "music_knowledge"
retrieval_top_k: int = 5

# Recommendation Weights
weight_mood: float = 0.40
weight_genre: float = 0.30
weight_instrument: float = 0.20
weight_theme: float = 0.10

# Database
db_path: Path
```

**Methods:**
- `ensure_directories()`: Create required directories
- `model_post_init()`: Initialize platformdirs paths

**Design Decisions:**
- Uses Pydantic for validation
- Environment variable override via .env
- Platform-specific paths (Windows/Linux/macOS)
- Singleton pattern via `@lru_cache`

---

### 1.2 schemas/memory_schema.py

**Purpose:** Data validation and type safety

**Classes:**

#### MemoryAnalysis
```python
class MemoryAnalysis(BaseModel):
    memory_title: str
    summary: str
    primary_emotions: List[str]
    secondary_emotions: List[str]
    emotional_intensity: int  # 1-10
    themes: List[str]
    context: List[str]
    genres: List[str]
    instruments: List[str]
    tempo: str  # slow/moderate/fast
    energy: str  # very low/low/moderate/high/very high
    atmosphere: str
    musical_description: str
    retrieval_query: str
```

#### TrackRecommendation
```python
class TrackRecommendation(BaseModel):
    track_id: str
    track_name: str
    artist: str
    genre_tags: List[str]
    mood_tags: List[str]
    instrument_tags: List[str]
    relevance_score: float  # 0.0-1.0
    explanation: str
    source: str
```

#### SoundtrackResult
```python
class SoundtrackResult(BaseModel):
    memory_analysis: MemoryAnalysis
    recommendations: List[TrackRecommendation]
    overall_explanation: str
    retrieved_knowledge_summary: Optional[List[str]]
```

**Design Decisions:**
- Strict type validation
- Prevents LLM hallucination via schema
- Serialization ready (JSON export)

---

### 1.3 modules/memory_analyzer.py

**Purpose:** LLM-based memory analysis

**Class:** `MemoryAnalyzer`

**Key Methods:**

```python
def analyze_memory(
    self, 
    story: str,
    max_retries: int = 3
) -> Optional[MemoryAnalysis]:
    """Analyze memory with LLM and return structured output."""
```

**Algorithm:**
1. Build structured prompt with JSON schema
2. Call Ollama LLM
3. Extract JSON from response (handle markdown fences)
4. Parse and validate with Pydantic
5. Retry on failure (up to max_retries)
6. Return MemoryAnalysis object or None

**Prompt Engineering:**
```python
prompt = f"""
Analyze this personal memory and extract emotional and musical characteristics.

MEMORY:
{story}

Provide analysis as JSON matching this schema:
{MemoryAnalysis.model_json_schema()}

RULES:
- primary_emotions: 2-4 most dominant
- secondary_emotions: 1-3 supporting
- emotional_intensity: 1 (very mild) to 10 (extremely intense)
...
"""
```

**Error Handling:**
- Retry logic for transient failures
- Graceful degradation (returns None)
- Logs all errors for debugging

---

### 1.4 modules/rag_engine.py

**Purpose:** Semantic retrieval from knowledge base

**Class:** `RAGEngine`

**Key Methods:**

```python
def initialize(self) -> None:
    """Initialize embedding model and ChromaDB."""

def embed_text(self, text: str) -> List[float]:
    """Generate embedding for text."""

def retrieve(
    self, 
    query: str, 
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """Retrieve relevant documents."""
```

**Embedding Process:**
1. Load SentenceTransformer model
2. Tokenize and encode query
3. Return 384-dimensional vector

**Retrieval Process:**
1. Embed query text
2. ChromaDB cosine similarity search
3. Return top-K results with metadata
4. Calculate relevance scores (1 - distance)

**Design Decisions:**
- Lazy initialization (avoid slow startup)
- Persistent storage (no rebuilds)
- CPU-friendly model (all-MiniLM-L6-v2)
- Metadata filtering support

---

### 1.5 modules/recommendation_engine.py

**Purpose:** Score and rank tracks

**Class:** `RecommendationEngine`

**Key Methods:**

```python
def generate_recommendations(
    self,
    analysis: MemoryAnalysis,
    retrieved_context: Optional[List[Dict]] = None,
    max_recommendations: int = None
) -> List[TrackRecommendation]:
    """Generate ranked recommendations."""
```

**Scoring Algorithm:**

```python
def _score_track(
    self,
    track: Dict[str, Any],
    analysis: MemoryAnalysis
) -> float:
    # Calculate component scores
    mood_score = jaccard_similarity(
        analysis.primary_emotions + analysis.secondary_emotions,
        track['mood_tags']
    )
    
    genre_score = jaccard_similarity(
        analysis.genres,
        track['genre_tags']
    )
    
    instrument_score = jaccard_similarity(
        analysis.instruments,
        track['instrument_tags']
    )
    
    theme_score = jaccard_similarity(
        analysis.context + analysis.themes,
        track['mood_tags'] + track['genre_tags']
    )
    
    # Weighted combination
    final_score = (
        0.40 * mood_score +
        0.30 * genre_score +
        0.20 * instrument_score +
        0.10 * theme_score
    )
    
    return final_score
```

**Jaccard Similarity:**
```python
def jaccard_similarity(set_a, set_b):
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0
```

**Design Decisions:**
- Tag normalization (lowercase)
- Configurable weights
- Duplicate filtering
- Minimum relevance threshold

---

### 1.6 modules/memory_vault.py

**Purpose:** SQLite persistence layer

**Class:** `MemoryVault`

**Key Methods:**

```python
def save_memory(
    self,
    story: str,
    soundtrack_result: SoundtrackResult
) -> Optional[int]:
    """Save memory to database."""

def get_all_memories(self, limit: int = 100) -> List[Dict]:
    """Retrieve all memories."""

def search_memories(self, query: str) -> List[Dict]:
    """Full-text search."""

def filter_by_emotion(self, emotion: str) -> List[Dict]:
    """Filter by emotion tag."""

def delete_memory(self, memory_id: int) -> bool:
    """Delete memory."""
```

**Database Schema:**
```sql
CREATE TABLE memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story TEXT NOT NULL,
    memory_title TEXT NOT NULL,
    summary TEXT NOT NULL,
    emotions TEXT NOT NULL,              -- JSON array
    themes TEXT NOT NULL,                -- JSON array
    musical_attributes TEXT NOT NULL,    -- JSON object
    recommendations TEXT NOT NULL,       -- JSON array
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_created_at ON memories(created_at DESC);
CREATE INDEX idx_memory_title ON memories(memory_title);
```

**Design Decisions:**
- JSON for complex fields (flexibility)
- Parameterized queries (SQL injection prevention)
- Indexes for performance
- Auto-incrementing primary key

---

## 2. Data Structures

### 2.1 Knowledge Base Document
```python
{
    'id': str,  # UUID
    'text': str,  # Document content
    'metadata': {
        'category': str,  # emotion/genre/instrument/context
        'topic': str,     # Nostalgia, Indie Folk, etc.
        'source': str     # Filename
    }
}
```

### 2.2 Track Metadata
```python
{
    'track_id': str,
    'track_name': str,
    'artist': str,
    'genre_tags': List[str],
    'mood_tags': List[str],
    'instrument_tags': List[str],
    'tempo': str,  # slow/moderate/fast
    'energy': str  # very low/low/moderate/high/very high
}
```

### 2.3 Retrieved Document
```python
{
    'id': str,
    'text': str,
    'metadata': Dict[str, Any],
    'distance': float,  # 0.0-2.0 (cosine distance)
    'relevance_score': float  # 0.0-1.0 (1 - distance/2)
}
```

---

## 3. Algorithms

### 3.1 Memory Analysis Pipeline
```
INPUT: story (string)

1. Validate input (length, non-empty)
2. Construct LLM prompt with JSON schema
3. Call Ollama API
4. Extract JSON from markdown response:
   - Remove ```json and ``` fences
   - Strip whitespace
5. Parse JSON
6. Validate with Pydantic schema
7. Retry if fails (up to 3 times)
8. Return MemoryAnalysis or None

OUTPUT: MemoryAnalysis object
```

### 3.2 RAG Retrieval Algorithm
```
INPUT: query (string), top_k (int)

1. Embed query using SentenceTransformer:
   - Tokenize text
   - Generate 384-dim vector
2. ChromaDB similarity search:
   - Calculate cosine similarity
   - Rank by distance (ascending)
   - Return top-K results
3. Enrich results:
   - Add relevance_score = 1 - (distance / 2)
   - Include metadata
4. Return list of documents

OUTPUT: List[Dict] with text, metadata, relevance
```

### 3.3 Track Scoring Algorithm
```
INPUT: track (dict), analysis (MemoryAnalysis)

1. Extract search tags:
   - all_emotions = primary + secondary
   - all_themes = themes + context

2. Calculate component scores (Jaccard):
   mood_score = jaccard(
       all_emotions + themes,
       track['mood_tags']
   )
   
   genre_score = jaccard(
       analysis.genres,
       track['genre_tags']
   )
   
   instrument_score = jaccard(
       analysis.instruments,
       track['instrument_tags']
   )
   
   theme_score = jaccard(
       context + themes,
       mood_tags + genre_tags
   )

3. Weighted combination:
   final = 0.40*mood + 0.30*genre + 0.20*instrument + 0.10*theme

4. Return final score (0.0-1.0)

OUTPUT: float (relevance score)
```

---

## 4. Error Handling Strategy

### 4.1 LLM Errors
- **Connection Failure:** Retry with exponential backoff
- **Invalid JSON:** Retry with clearer prompt
- **Schema Violation:** Log and return None
- **Timeout:** Increase timeout, retry

### 4.2 Database Errors
- **Lock Contention:** Retry with delay
- **Corruption:** Provide rebuild instructions
- **Disk Full:** Clear error message

### 4.3 RAG Errors
- **Model Download Failure:** Retry, check internet
- **Empty Collection:** Prompt to build knowledge base
- **Embedding Failure:** Log and skip document

---

## 5. Performance Optimizations

### 5.1 Lazy Loading
- Load embedding model only when needed
- Defer ChromaDB initialization
- Cache loaded models in memory

### 5.2 Batch Processing
- Embed multiple documents at once
- Batch ChromaDB inserts (10 docs/batch)
- Process tracks in chunks

### 5.3 Caching
- Settings singleton (`@lru_cache`)
- Embedding model kept in memory
- ChromaDB persistent storage

### 5.4 Indexing
- SQLite indexes on created_at, memory_title
- ChromaDB HNSW index for vectors

---

## 6. Security Considerations

### 6.1 Input Validation
- Max memory length (5000 chars)
- Pydantic schema validation
- SQL parameterized queries

### 6.2 Data Privacy
- No external API calls
- Local-only storage
- No telemetry or tracking

### 6.3 File System
- Platform-specific secure paths
- User-only permissions
- No world-readable files

---

## 7. Testing Strategy

### 7.1 Unit Tests
- Config loading and validation
- Pydantic schema validation
- Scoring algorithms
- Database operations

### 7.2 Integration Tests
- Ollama connectivity
- RAG retrieval pipeline
- End-to-end memory analysis

### 7.3 Portability Tests
- Cross-platform path handling
- Environment variable loading
- Script execution

---

**Document Version:** 1.0  
**Last Updated:** November 2024  
**Author:** AI Solutions Architect Internship Assessment

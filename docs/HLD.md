# High-Level Design (HLD)
## The Soundtrack of Your Life

---

## 1. System Overview

### 1.1 Purpose
The Soundtrack of Your Life is an AI-powered application that analyzes personal memories, understands their emotional context, and recommends music that captures those feelings using advanced AI techniques including LLMs, RAG, and semantic search.

### 1.2 Key Objectives
- Demonstrate practical implementation of modern AI technologies
- Provide genuine emotional intelligence through LLM analysis
- Implement authentic RAG (not simulated retrieval)
- Ensure 100% local execution (privacy-first)
- Maintain cross-platform compatibility
- Enable easy configuration and deployment

---

## 2. System Architecture

### 2.1 Architectural Style
**Modular Monolithic Architecture**

- Single-process application
- Clear module boundaries
- No microservices complexity
- Local-first design
- Stateless request handling (except database)

### 2.2 High-Level Component Diagram

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃          USER LAYER                 ┃
┃   (Web Browser / Streamlit UI)     ┃
┗━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┛
                   │
                   v
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃    PRESENTATION LAYER            ┃
┃    (app.py - Streamlit)          ┃
┃  - Page routing                  ┃
┃  - User input handling           ┃
┃  - Results display               ┃
┗━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┛
                   │
    ┌────────────┴───────────┐
    │                            │
    v                            v
┏━━━━━━━━━━━━━┓      ┏━━━━━━━━━━━━━┓
┃  BUSINESS    ┃      ┃ PERSISTENCE ┃
┃   LOGIC      ┃      ┃    LAYER    ┃
┃             ┃      ┃             ┃
┃ - Memory    ┃      ┃ - Memory    ┃
┃   Analysis  ┃      ┃   Vault     ┃
┃ - RAG       ┃      ┃ - SQLite    ┃
┃   Engine    ┃      ┃   Database  ┃
┃ - Music     ┃      ┃             ┃
┃   Catalogue ┃      ┗━━━━━━━━━━━━━┛
┃ - Recommend ┃
┃   Engine    ┃
┃ - Explain   ┃
┃   Generator ┃
┗━━━━━━┳━━━━━━┛
       │
    ┌──┴──┐
    │     │
    v     v
┏━━━━━┓ ┏━━━━━━━┓
┃ LLM ┃ ┃ VECTOR ┃
┃     ┃ ┃   DB   ┃
┃Olla-┃ ┃Chroma-┃
┃ ma  ┃ ┃  DB   ┃
┗━━━━━┛ ┗━━━━━━━┛
```

---

## 3. Core Components

### 3.1 Memory Analysis Engine
**Responsibility:** Understand and extract emotional meaning from memories

**Key Features:**
- LLM-based natural language understanding
- Structured JSON output (Pydantic validated)
- Emotion detection (primary + secondary)
- Theme and context extraction
- Musical characteristic derivation

**Technology:**
- Ollama (local LLM runtime)
- Qwen 2.5 3B Instruct (language model)
- Pydantic (schema validation)

**Input:** Raw memory text
**Output:** MemoryAnalysis object

### 3.2 RAG (Retrieval-Augmented Generation) Engine
**Responsibility:** Retrieve relevant music knowledge to inform recommendations

**Key Features:**
- Semantic text embedding
- Vector similarity search
- Metadata filtering
- Top-K retrieval
- Persistent vector storage

**Technology:**
- Sentence Transformers (all-MiniLM-L6-v2)
- ChromaDB (vector database)
- Cosine similarity ranking

**Input:** Retrieval query (emotions + themes + musical attributes)
**Output:** Relevant knowledge documents

### 3.3 Music Catalogue
**Responsibility:** Manage track metadata and provide search capabilities

**Key Features:**
- Track metadata storage
- Tag-based filtering
- Multi-criteria search
- Catalogue statistics

**Technology:**
- Pandas (data processing)
- In-memory storage
- Optional: MTG-Jamendo dataset integration

**Input:** Search criteria (genres, moods, instruments)
**Output:** Candidate tracks

### 3.4 Recommendation Engine
**Responsibility:** Score and rank tracks based on memory analysis

**Key Features:**
- Weighted multi-criteria scoring
- Configurable scoring weights
- Tag overlap calculation
- Duplicate removal
- Top-N selection

**Scoring Formula:**
```
Final Score = 
  0.40 × Mood Match +
  0.30 × Genre Match +
  0.20 × Instrument Match +
  0.10 × Theme Match
```

**Input:** Memory analysis + Retrieved knowledge + Music catalogue
**Output:** Ranked track recommendations

### 3.5 Explanation Generator
**Responsibility:** Create natural language explanations for recommendations

**Key Features:**
- LLM-powered explanation generation
- Grounding in retrieved knowledge
- Per-track explanations
- Overall soundtrack narrative

**Technology:**
- Ollama (local LLM)
- Prompt engineering

**Input:** Memory + Analysis + Tracks + RAG context
**Output:** Human-friendly explanations

### 3.6 Personal Memory Vault
**Responsibility:** Persist and manage saved memories

**Key Features:**
- SQLite-based persistence
- CRUD operations
- Full-text search
- Emotion/theme filtering
- JSON serialization for complex fields

**Technology:**
- SQLite (embedded database)
- Parameterized queries (SQL injection prevention)

**Schema:**
```sql
CREATE TABLE memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story TEXT NOT NULL,
    memory_title TEXT NOT NULL,
    summary TEXT NOT NULL,
    emotions TEXT NOT NULL,  -- JSON array
    themes TEXT NOT NULL,    -- JSON array
    musical_attributes TEXT, -- JSON object
    recommendations TEXT,    -- JSON array
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Data Flow

### 4.1 Memory-to-Music Flow

```
1. User Input
   ↓
2. Memory Analyzer → Ollama LLM
   ↓
3. Structured Analysis (Pydantic validation)
   ↓
4. Retrieval Query Generation
   ↓
5. RAG Engine → Sentence Transformers → ChromaDB
   ↓
6. Retrieved Music Knowledge
   ↓
7. Music Catalogue Search
   ↓
8. Recommendation Engine (Scoring & Ranking)
   ↓
9. Explanation Generator → Ollama LLM
   ↓
10. Final Soundtrack Result
   ↓
11. Display to User
   ↓
12. Optional: Save to Vault → SQLite
```

### 4.2 Memory Vault Flow

```
Browse:
  User → UI → MemoryVault.get_all_memories() → SQLite → Display

Search:
  User → Query → MemoryVault.search_memories() → SQLite LIKE → Results

Filter:
  User → Emotion/Theme ∙2 MemoryVault.filter_by_X() → Filter → Results

Delete:
  User → Confirm → MemoryVault.delete_memory() → SQLite DELETE
```

---

## 5. Technology Stack

### 5.1 Core Technologies

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|----------|
| Frontend | Streamlit | 1.67+ | Web UI |
| Backend | Python | 3.11+ | Application logic |
| LLM Runtime | Ollama | Latest | Local LLM serving |
| Language Model | Qwen 2.5 | 3B Instruct | Memory analysis |
| Embeddings | Sentence-Transformers | 2.2+ | Text vectorization |
| Embedding Model | all-MiniLM-L6-v2 | - | 384-dim embeddings |
| Vector DB | ChromaDB | 0.4+ | Semantic search |
| Database | SQLite | 3.x | Persistence |
| Validation | Pydantic | 2.0+ | Data schemas |
| Config | pydantic-settings | 2.0+ | Configuration |
| Data Processing | Pandas | 2.0+ | Metadata handling |

### 5.2 Infrastructure

**Development:**
- Git (version control)
- pytest (testing)
- Virtual environment (isolation)

**Deployment:**
- Cross-platform (Windows, Linux, macOS)
- No containers required
- Single-command setup
- Local execution only

---

## 6. Non-Functional Requirements

### 6.1 Performance
- **Memory Analysis:** < 10 seconds (CPU-only)
- **RAG Retrieval:** < 2 seconds
- **Recommendation:** < 1 second
- **Total Processing:** < 15 seconds per memory

### 6.2 Scalability
- **Knowledge Base:** Supports 1K+ documents
- **Music Catalogue:** Supports 50K+ tracks
- **Memory Vault:** Supports 10K+ saved memories
- **Concurrent Users:** Single-user application

### 6.3 Security
- **Local Execution:** No data leaves the machine
- **SQL Injection:** Parameterized queries
- **Input Validation:** Pydantic schemas
- **Config Security:** .env excluded from Git

### 6.4 Portability
- **OS Support:** Windows, Linux, macOS
- **Hardware:** CPU-only minimum, GPU optional
- **Dependencies:** Minimal, well-documented
- **Configuration:** Environment-based

### 6.5 Maintainability
- **Modularity:** Clear separation of concerns
- **Documentation:** Comprehensive README + docs
- **Testing:** Unit and integration tests
- **Code Quality:** Type hints, docstrings

---

## 7. Deployment Architecture

### 7.1 Development Environment
```
Developer Machine
│
├── Python 3.11+ Runtime
├── Virtual Environment (.venv)
├── Ollama Service (localhost:11434)
├── Application Code
├── ChromaDB (local filesystem)
└── SQLite Database (local filesystem)
```

### 7.2 Production Environment
```
User Machine
│
├── Python 3.11+ Runtime
├── Ollama Service (installed locally)
├── Application (cloned from GitHub)
├── Virtual Environment (created during setup)
├── ChromaDB (platform-specific app data dir)
└── SQLite Database (platform-specific app data dir)
```

**Platform-Specific Paths:**
- Windows: `%LOCALAPPDATA%\The Soundtrack of Your Life`
- Linux: `~/.local/share/soundtrack-of-your-life`
- macOS: `~/Library/Application Support/The Soundtrack of Your Life`

---

## 8. Future Enhancements

### 8.1 Short-term
1. **MTG-Jamendo Integration:** Full dataset (55K tracks)
2. **iTunes API:** Preview links and additional metadata
3. **Advanced Filtering:** More search criteria
4. **Batch Processing:** Analyze multiple memories

### 8.2 Long-term
1. **Spotify Integration:** Direct playlist creation
2. **Multi-modal Input:** Image analysis for context
3. **Collaborative Filtering:** User preference learning
4. **Fine-tuned Models:** Custom emotion-music embeddings
5. **Mobile App:** iOS/Android support
6. **Multi-user:** Authentication and user management

---

## 9. Risk Analysis

### 9.1 Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM hallucination | Medium | Pydantic validation, retry logic |
| Slow CPU performance | Medium | Progress indicators, GPU support |
| Model incompatibility | Low | Version pinning, testing |
| ChromaDB corruption | Low | Rebuild script, backups |
| SQLite lock contention | Low | Single-user design |

### 9.2 Operational Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Ollama not installed | High | Setup script checks, clear errors |
| Memory overflow | Low | Input length limits |
| Disk space shortage | Low | Compressed models, cleanup tools |
| Platform incompatibility | Low | Cross-platform testing |

---

## 10. Success Criteria

✅ **Functional:**
- Memory analysis produces structured output
- RAG retrieves relevant knowledge
- Recommendations match emotional tone
- Memory vault persists data correctly

✅ **Technical:**
- < 15 second total processing time
- Works on CPU-only systems
- Cross-platform compatibility
- No external API dependencies

✅ **Usability:**
- One-command setup
- Intuitive UI
- Clear error messages
- Comprehensive documentation

---

**Document Version:** 1.0  
**Last Updated:** November 2024  
**Author:** AI Solutions Architect Internship Assessment

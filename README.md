# 🎵 The Soundtrack of Your Life

**AI-Powered Personal Memory Analysis and Music Recommendation System**

> *Your memories. Your emotions. Your music.*


![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

---

## 📖 Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Testing](#testing)
- [Configuration](#configuration)
- [Known Limitations](#known-limitations)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## 🌟 Overview

The Soundtrack of Your Life is an AI-powered application that understands personal memories, identifies their emotional meaning, and recommends music that captures those feelings. Using advanced techniques like Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), and semantic search, this system provides personalized music recommendations based on the emotional depth of your experiences.

This project demonstrates practical implementation of:
- **Local LLM Integration** (Ollama + Qwen 2.5 3B)
- **RAG (Retrieval-Augmented Generation)**
- **Vector Databases** (ChromaDB)
- **Text Embeddings** (Sentence Transformers)
- **Structured LLM Outputs** (Pydantic)
- **Full-Stack Development** (React/Vite + FastAPI, with Streamlit fallback)

> **Current setup:** Use [`docs/LOCAL_RUNBOOK.md`](docs/LOCAL_RUNBOOK.md) for the accurate Windows installation, dependency setup, Ollama configuration, FastAPI startup, React startup, Streamlit fallback, live browser voice input, optional local Whisper fallback, testing, and troubleshooting instructions. See [`PERFORMANCE.md`](PERFORMANCE.md) for the CPU latency fast path.
    ??? CLONE_SETUP.md              # Fresh-clone Windows setup
    ??? LOCAL_RUNBOOK.md            # Current local runbook

---

## 🎯 Problem Statement

**Can AI understand the emotional depth of personal memories and recommend music that captures those feelings?**

For example, if you describe:
> "It was my last day at college. I was sitting with my friends, remembering all the memories we created together. I was happy, but somewhere inside I knew I would miss those days."

The system should:
1. Understand emotions: **Nostalgia, Happiness, Sadness, Gratitude**
2. Identify themes: **Friendship, Farewell, College, Life Transitions**
3. Derive musical characteristics: **Indie folk, Acoustic pop, Piano, Guitar**
4. Recommend actual tracks that match these elements
5. Explain why each track fits your memory

---

## ✨ Features

### 🎭 Memory-to-Music Analysis
- **Emotion Detection**: Identifies primary and secondary emotions with intensity scoring
- **Theme Extraction**: Recognizes life contexts, events, and relationships
- **Musical Mapping**: Translates emotions into genres, instruments, tempo, and atmosphere
- **RAG-Powered Insights**: Retrieves relevant music knowledge to inform recommendations
- **Intelligent Ranking**: Scores tracks using configurable weighted matching
- **Natural Explanations**: Generates empathetic explanations for each recommendation

### 💾 Personal Memory Vault
- **Persistent Storage**: Save analyzed memories with their soundtracks (SQLite)
- **Search & Filter**: Find memories by keywords, emotions, or themes
- **Browse History**: Revisit past memories and their recommended music
- **Delete with Confirmation**: Manage your personal memory collection

### 🔒 Privacy & Portability
- **100% Local Execution**: No cloud APIs, all processing on your machine
- **Cross-Platform**: Windows, Linux, macOS compatible
- **CPU-Only Support**: No GPU required (optional GPU acceleration)
- **Configurable**: Easy customization via environment variables

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Primary frontend** | React + TypeScript + Vite | Memory composer, voice capture, vault, preferences, refinement |
| **Fallback frontend** | Streamlit | Local fallback/admin UI |
| **API** | FastAPI + Uvicorn | REST service and OpenAPI docs |
| **Backend services** | Python 3.11+ | Shared soundtrack orchestration |
| **LLM** | Ollama (Qwen 2.5 3B) | Memory analysis & explanations |
| **Embeddings** | all-MiniLM-L6-v2 | Text vectorization |
| **Vector DB** | ChromaDB | Semantic search |
| **Database** | SQLite | Memory, feedback, and preferences |
| **Validation** | Pydantic | Structured request and response schemas |
| **Config** | pydantic-settings | Centralized configuration |
| **Optional speech** | faster-whisper | Local CPU transcription |

---

## 🏗️ Architecture

### High-Level System Design

```
USER
 ↓
STREAMLIT FRONTEND
 ↓
PYTHON BACKEND
 ↓
┌────────────────────┬─────────────────────┐
│                    │                     │
MEMORY ANALYSIS    PERSONAL MEMORY VAULT
│                    │
OLLAMA LLM         SQLite DATABASE
│
STRUCTURED OUTPUT
│
RAG RETRIEVAL ENGINE
│
┌──────────────┬──────────────┐
│              │              │
EMBEDDINGS   CHROMADB    MUSIC KNOWLEDGE
│              │              │
└──────────────┴──────────────┘
         │
RECOMMENDATION ENGINE
         │
MUSIC CATALOGUE → RANKING → EXPLANATION
         │
FINAL SOUNDTRACK RESULTS
```

### RAG Workflow

```
1. User Memory → 2. LLM Analysis → 3. Emotion/Theme Extraction
                           ↓
              4. Generate Retrieval Query
                           ↓
              5. Embed Query (Sentence Transformers)
                           ↓
              6. ChromaDB Vector Search
                           ↓
              7. Retrieve Music Knowledge
                           ↓
    8. Combine Analysis + Retrieved Context
                           ↓
         9. Score & Rank Tracks
                           ↓
        10. Generate Explanations
```

---

## 📥 Installation

### Prerequisites

- **Python 3.11 or higher** (3.12 recommended)
- **Git**
- **Ollama** ([Download](https://ollama.com/download))
- **8GB+ RAM** (recommended)
- **2GB+ free disk space**

### Windows Setup

```powershell
# 1. Clone the repository
git clone <repository-url>
cd "The Soundtrack of Your Life"

# 2. Run automated setup
.\scripts\setup_windows.ps1

# 3. Build knowledge base (one-time)
python scripts/build_knowledge_base.py

# 4. Run the application
.\scripts\run_windows.ps1
```

### Linux/macOS Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd "The Soundtrack of Your Life"

# 2. Run automated setup
chmod +x scripts/setup_unix.sh scripts/run_unix.sh
./scripts/setup_unix.sh

# 3. Build knowledge base (one-time)
python scripts/build_knowledge_base.py

# 4. Run the application
./scripts/run_unix.sh
```

### Manual Installation

```bash
# 1. Install Ollama
# Windows: Download from https://ollama.com/download/windows
# Linux: curl -fsSL https://ollama.com/install.sh | sh
# macOS: brew install ollama

# 2. Pull the LLM model
ollama pull qwen2.5:3b

# 3. Create virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Linux/macOS:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
# Edit .env if needed

# 6. Build knowledge base
python scripts/build_knowledge_base.py

# 7. Run application
streamlit run app.py
```

---

## 🚀 Usage

### Creating Your Soundtrack

1. **Launch the application**
   ```bash
   streamlit run app.py
   ```

2. **Navigate to "Create Soundtrack"**

3. **Enter a personal memory** (example):
   ```
   I was sitting near a lake early in the morning, enjoying the 
   silence and fresh air. The world felt peaceful and calm.
   ```

4. **Click "Generate Soundtrack"**

5. **View Results**:
   - Memory analysis (emotions, themes, musical direction)
   - Recommended tracks with explanations
   - RAG transparency (how AI selected tracks)

6. **Save to Memory Vault** (optional)

### Managing Memory Vault

1. **Navigate to "Memory Vault"**
2. **Browse** saved memories
3. **Search** by keywords
4. **Filter** by emotion or theme
5. **View** detailed memory analysis and soundtrack
6. **Delete** memories (with confirmation)

---

## 📁 Project Structure

```
The Soundtrack of Your Life/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── .env.example                    # Configuration template
├── .gitignore                      # Git ignore rules
│
├── config/
│   └── settings.py                 # Centralized configuration
│
├── schemas/
│   └── memory_schema.py            # Pydantic data models
│
├── modules/
│   ├── memory_analyzer.py          # LLM-based memory analysis
│   ├── rag_engine.py               # RAG retrieval system
│   ├── music_catalogue.py          # Track metadata management
│   ├── recommendation_engine.py    # Scoring & ranking
│   ├── explanation_generator.py    # LLM explanations
│   ├── memory_vault.py             # SQLite persistence
│   └── health_check.py             # Startup diagnostics
│
├── data/
│   ├── knowledge_base/
│   │   ├── emotions/               # Emotion documents (6)
│   │   ├── genres/                 # Genre documents (4)
│   │   ├── instruments/            # Instrument documents (3)
│   │   └── contexts/               # Context documents (5)
│   └── music_metadata/             # Music catalogue data
│
├── scripts/
│   ├── build_knowledge_base.py     # ChromaDB ingestion
│   ├── prepare_music_catalogue.py  # MTG-Jamendo processor
│   ├── setup_windows.ps1           # Windows setup
│   ├── run_windows.ps1             # Windows launcher
│   ├── setup_unix.sh               # Linux/macOS setup
│   └── run_unix.sh                 # Linux/macOS launcher
│
├── tests/
│   ├── test_config.py              # Configuration tests
│   ├── test_ollama.py              # Integration tests
│   ├── test_memory_analyzer.py     # Memory analyzer tests
│   ├── test_rag_engine.py          # RAG tests
│   ├── test_recommendation_engine.py
│   ├── test_memory_vault.py
│   └── test_portability.py
│
└── docs/
```

---

## 🔍 How It Works

### 1. Memory Analysis

**Input:** User's personal memory text

**Process:**
- Ollama LLM analyzes the narrative
- Extracts structured JSON output
- Pydantic validates the response

**Output:**
```json
{
  "memory_title": "Peaceful Morning by the Lake",
  "primary_emotions": ["peace", "calm"],
  "themes": ["nature", "solitude", "reflection"],
  "genres": ["ambient", "classical"],
  "instruments": ["piano", "strings"],
  "tempo": "slow",
  "atmosphere": "serene and contemplative"
}
```

### 2. RAG Retrieval

**Input:** Emotions, themes, musical characteristics

**Process:**
- Generate semantic query
- Embed query using Sentence Transformers
- ChromaDB vector similarity search
- Retrieve top-K relevant knowledge chunks

**Output:** Music knowledge documents (emotions, genres, instruments, contexts)

### 3. Recommendation

**Input:** Memory analysis + Retrieved knowledge + Music catalogue

**Process:**
- Filter candidate tracks by tags
- Score each track using weighted formula:
  ```
  Score = 0.4×Mood + 0.3×Genre + 0.2×Instrument + 0.1×Theme
  ```
- Rank by relevance score
- Select top N tracks

**Output:** Ranked list of tracks with scores

### 4. Explanation Generation

**Input:** Original memory + Analysis + Selected tracks + RAG context

**Process:**
- LLM generates natural language explanation
- Explains emotional and musical connections
- Grounds explanations in retrieved knowledge

**Output:** Human-friendly soundtrack story

---

## 🧪 Testing

### Run All Tests

```bash
# Configuration tests
python tests/test_config.py

# Integration tests (Ollama + RAG)
python tests/test_ollama.py

# Unit tests
pytest tests/ -v
```

### Test Scenarios

**Scenario 1: Nostalgia**
```
Memory: "My final day at college with my friends. I was happy but sad that everything was ending."
Expected: Nostalgia, friendship, farewell, mixed emotions
```

**Scenario 2: Achievement**
```
Memory: "I finally received my first job offer after months of preparation. I felt proud and relieved."
Expected: Achievement, pride, excitement, relief
```

**Scenario 3: Peace**
```
Memory: "I was sitting near a lake early in the morning, enjoying the silence and fresh air."
Expected: Peace, calmness, reflection
```

---

## ⚙️ Configuration

Edit `.env` file to customize:

```ini
# LLM Configuration
OLLAMA_MODEL=qwen2.5:3b          # Change model
LLM_TEMPERATURE=0.3              # Creativity (0-1)
LLM_MAX_TOKENS=2000              # Response length

# Embedding Configuration
EMBEDDING_DEVICE=cpu             # cpu, cuda, mps

# RAG Configuration
RETRIEVAL_TOP_K=5                # Documents to retrieve

# Recommendation Weights
WEIGHT_MOOD=0.40
WEIGHT_GENRE=0.30
WEIGHT_INSTRUMENT=0.20
WEIGHT_THEME=0.10

# Features
ENABLE_MEMORY_VAULT=true
ENABLE_EXTERNAL_MUSIC_LOOKUP=false
```

---

## ⚠️ Known Limitations

1. **Sample Music Catalogue**: Currently uses 10 sample tracks. For production, integrate MTG-Jamendo dataset.
2. **CPU Performance**: Embedding generation may be slow on older CPUs (GPU recommended for large datasets).
3. **LLM Accuracy**: Results depend on Ollama model quality and prompt engineering.
4. **Language Support**: Currently optimized for English text.
5. **No Audio Playback**: Only provides track metadata, not actual audio streaming.

---

## 🚀 Future Improvements

### Short-term
- [ ] Integrate full MTG-Jamendo dataset (55K+ tracks)
- [ ] Add Spotify/Apple Music API integration for previews
- [ ] Support multiple languages
- [ ] Add emotion history visualization
- [ ] Export playlists to Spotify/Apple Music

### Long-term
- [ ] Fine-tune embedding model on music-emotion data
- [ ] Add collaborative filtering
- [ ] Support image uploads (analyze photos for context)
- [ ] Multi-user support with authentication
- [ ] Mobile app (React Native)
- [ ] Voice input for memories

---

## 📊 Performance

**Hardware Requirements:**

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 8 GB | 16 GB+ |
| CPU | Dual-core 2.0 GHz | Quad-core 3.0 GHz+ |
| GPU | Not required | Optional (CUDA/MPS) |
| Storage | 2 GB | 5 GB+ |

**Typical Processing Times** (Intel i5, 16GB RAM, CPU-only):
- Memory analysis: 3-8 seconds
- RAG retrieval: 0.5-2 seconds
- Recommendation: 0.1-0.5 seconds
- Explanation generation: 2-5 seconds
- **Total: 6-15 seconds per memory**

---

## 📄 License

MIT License - feel free to use this project for learning and development.

---

## 🙏 Acknowledgments

- **Ollama** - Local LLM runtime
- **Sentence Transformers** - Embedding models
- **ChromaDB** - Vector database
- **Streamlit** - Web framework
- **MTG-Jamendo** - Music dataset
- **Qwen Team** - Language model

---

## 📞 Contact

For questions, issues, or contributions, please open an issue on GitHub.

---

**Made with ❤️ for AI Solutions Architect Internship Assessment**

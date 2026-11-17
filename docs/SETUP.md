# Detailed Setup Guide
## The Soundtrack of Your Life

> For the current React/Vite + FastAPI + Streamlit workflow, use [`LOCAL_RUNBOOK.md`](LOCAL_RUNBOOK.md). This document contains legacy platform notes retained for reference.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Knowledge Base Setup](#knowledge-base-setup)
5. [Running the Application](#running-the-application)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Configuration](#advanced-configuration)

---

## 1. System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10+, Ubuntu 20.04+, macOS 11+ |
| **CPU** | Dual-core 2.0 GHz+ |
| **RAM** | 8 GB |
| **Storage** | 2 GB free space |
| **Python** | 3.11, 3.12, or 3.13 |
| **Internet** | Required for initial setup only |

### Recommended Requirements

| Component | Requirement |
|-----------|-------------|
| **CPU** | Quad-core 3.0 GHz+ |
| **RAM** | 16 GB+ |
| **GPU** | Optional (CUDA/MPS for faster embeddings) |
| **Storage** | 5 GB+ free space |

---

## 2. Installation

### 2.1 Install Python

#### Windows
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer, **check "Add Python to PATH"**
3. Verify: `python --version`

#### Linux
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

#### macOS
```bash
brew install python@3.11
```

### 2.2 Install Ollama

#### Windows
1. Download: [https://ollama.com/download/windows](https://ollama.com/download/windows)
2. Run installer
3. Open PowerShell and verify: `ollama --version`

#### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### macOS
```bash
brew install ollama
```

### 2.3 Pull LLM Model

```bash
ollama pull qwen2.5:3b
```

**Expected download:** ~2 GB

**Verify:**
```bash
ollama list
```

You should see `qwen2.5:3b` in the list.

### 2.4 Clone Repository

```bash
git clone <repository-url>
cd "The Soundtrack of Your Life"
```

### 2.5 Automated Setup

#### Windows
```powershell
.\scripts\setup_windows.ps1
```

#### Linux/macOS
```bash
chmod +x scripts/setup_unix.sh
./scripts/setup_unix.sh
```

**What the setup script does:**
1. Checks Python version
2. Checks Ollama installation
3. Creates virtual environment
4. Installs Python dependencies
5. Creates `.env` configuration file
6. Sets up application directories

---

## 3. Configuration

### 3.1 Environment Variables

The `.env` file contains all configurable settings.

**Location:** Project root directory

**Default values:**
```ini
# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2000

# Embedding Configuration  
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu  # or cuda, mps

# RAG Configuration
COLLECTION_NAME=music_knowledge
RETRIEVAL_TOP_K=5

# Recommendation Weights (must sum to 1.0)
WEIGHT_MOOD=0.40
WEIGHT_GENRE=0.30
WEIGHT_INSTRUMENT=0.20
WEIGHT_THEME=0.10

# Features
MAX_RECOMMENDATIONS=10
MAX_MEMORY_LENGTH=5000
ENABLE_MEMORY_VAULT=true
```

### 3.2 Customization Examples

**Use GPU for faster embeddings (NVIDIA):**
```ini
EMBEDDING_DEVICE=cuda
```

**Use GPU for Mac (Apple Silicon):**
```ini
EMBEDDING_DEVICE=mps
```

**Change LLM creativity:**
```ini
LLM_TEMPERATURE=0.7  # More creative (0.0-1.0)
```

**Adjust recommendation weights:**
```ini
WEIGHT_MOOD=0.50      # Prioritize mood matching
WEIGHT_GENRE=0.25
WEIGHT_INSTRUMENT=0.15
WEIGHT_THEME=0.10
```

---

## 4. Knowledge Base Setup

### 4.1 Initial Build

**Important:** The knowledge base must be built once before using the application.

```bash
python scripts/build_knowledge_base.py
```

**Expected output:**
```
[INFO] Loaded 18 documents
[INFO] Created 36 chunks from 18 documents
[INFO] Generating embeddings and adding to ChromaDB...
[INFO] Progress: 36/36 chunks processed
[SUCCESS] Knowledge base ingestion complete!
[INFO] Documents: 36
```

**Time required:** 2-5 minutes (first run, downloads embedding model)

### 4.2 Rebuild Knowledge Base

If you modify knowledge documents or encounter issues:

```bash
python scripts/build_knowledge_base.py --rebuild
```

### 4.3 Knowledge Base Location

**Windows:**
```
C:\Users\<username>\AppData\Local\The Soundtrack of Your Life\chroma_db
```

**Linux:**
```
~/.local/share/soundtrack-of-your-life/chroma_db
```

**macOS:**
```
~/Library/Application Support/The Soundtrack of Your Life/chroma_db
```

---

## 5. Running the Application

### 5.1 Automated Launch

#### Windows
```powershell
.\scripts\run_windows.ps1
```

#### Linux/macOS
```bash
./scripts/run_unix.sh
```

**What the run script does:**
1. Activates virtual environment
2. Checks Ollama status
3. Verifies knowledge base
4. Runs health check
5. Launches Streamlit app

### 5.2 Manual Launch

```bash
# Activate virtual environment
# Windows:
.venv\Scripts\activate

# Linux/macOS:
source .venv/bin/activate

# Run application
streamlit run app.py
```

### 5.3 Accessing the Application

The app will automatically open in your default browser at:
```
http://localhost:8501
```

If it doesn't open automatically, click the link in the terminal.

### 5.4 Stopping the Application

Press `Ctrl+C` in the terminal running Streamlit.

---

## 6. Troubleshooting

### 6.1 Ollama Not Running

**Error:**
```
[ERROR] Ollama not accessible at http://localhost:11434
```

**Solution:**

**Windows:**
- Ollama should start automatically
- If not, launch "Ollama" from Start Menu

**Linux:**
```bash
ollama serve &
```

**macOS:**
```bash
ollama serve &
```

### 6.2 Model Not Found

**Error:**
```
[ERROR] Model 'qwen2.5:3b' not found
```

**Solution:**
```bash
ollama pull qwen2.5:3b
```

### 6.3 Knowledge Base Not Built

**Warning:**
```
[WARNING] Knowledge base not found
```

**Solution:**
```bash
python scripts/build_knowledge_base.py
```

### 6.4 Python Version Issues

**Error:**
```
[ERROR] Python 3.11+ required
```

**Solution:**
- Install Python 3.11, 3.12, or 3.13
- Update PATH to use correct version
- Recreate virtual environment:
  ```bash
  rm -rf .venv
  python3.11 -m venv .venv
  ```

### 6.5 ChromaDB Import Error

**Error:**
```
ModuleNotFoundError: No module named 'chromadb'
```

**Solution:**
```bash
# Activate virtual environment first
pip install chromadb --no-deps
pip install sentence-transformers
```

### 6.6 Slow Performance

**Issue:** Analysis takes > 30 seconds

**Solutions:**
1. **Use GPU acceleration:**
   ```ini
   # In .env
   EMBEDDING_DEVICE=cuda  # or mps for Mac
   ```

2. **Reduce knowledge base size:**
   - Remove unnecessary documents from `data/knowledge_base/`
   - Rebuild knowledge base

3. **Use smaller model:**
   ```ini
   OLLAMA_MODEL=qwen2.5:1.5b  # Faster but less accurate
   ```

### 6.7 Memory Vault Database Locked

**Error:**
```
atabase is locked
```

**Solution:**
1. Close any other instances of the app
2. Delete lock file:
   ```bash
   # Location varies by OS (see section 4.3)
   rm memories.db-wal
   rm memories.db-shm
   ```

### 6.8 PowerShell Execution Policy (Windows)

**Error:**
```
File cannot be loaded because running scripts is disabled
```

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 7. Advanced Configuration

### 7.1 Using Different LLM Models

**Available Ollama models:**
- `qwen2.5:3b` (default, balanced)
- `qwen2.5:1.5b` (faster, less accurate)
- `qwen2.5:7b` (more accurate, slower)
- `llama3.2:3b` (alternative)

**Change model:**
1. Pull new model: `ollama pull qwen2.5:7b`
2. Update `.env`:
   ```ini
   OLLAMA_MODEL=qwen2.5:7b
   ```
3. Restart application

### 7.2 Using Different Embedding Models

**Alternatives:**
- `sentence-transformers/paraphrase-MiniLM-L6-v2` (similar size)
- `sentence-transformers/all-mpnet-base-v2` (larger, better)
- `BAAI/bge-small-en-v1.5` (optimized for retrieval)

**Change model:**
1. Update `.env`:
   ```ini
   EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
   ```
2. Rebuild knowledge base:
   ```bash
   python scripts/build_knowledge_base.py --rebuild
   ```

### 7.3 Custom Knowledge Base

**Add new documents:**

1. Create text file in appropriate category:
   ```
   data/knowledge_base/emotions/hope.txt
   data/knowledge_base/genres/jazz.txt
   data/knowledge_base/instruments/saxophone.txt
   data/knowledge_base/contexts/childhood.txt
   ```

2. Write content (see existing files for format)

3. Rebuild knowledge base:
   ```bash
   python scripts/build_knowledge_base.py --rebuild
   ```

### 7.4 External Music Catalogue (MTG-Jamendo)

**To use real music dataset (55K+ tracks):**

1. Download MTG-Jamendo dataset
2. Place CSV in `data/music_metadata/`
3. The app will automatically use it instead of sample data

### 7.5 Running on Remote Server

**For remote access:**

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

**Access from another machine:**
```
http://<server-ip>:8501
```

**Security warning:** Use firewall rules or SSH tunneling for production.

---

## 8. Health Check

**Run anytime to verify system health:**

```bash
python modules/health_check.py
```

**Example output:**
```
======================================================================
SYSTEM HEALTH CHECK
======================================================================

Platform: Windows 11
Python: 3.14.7

[OK]     Python Version
[OK]     Streamlit
[OK]     Ollama Connectivity
[OK]     Embedding Model Package
[OK]     ChromaDB Package
[OK]     Configured LLM Model
[OK]     Knowledge Base
[OK]     Database Access

SUMMARY: 8/8 checks passed
[SUCCESS] System is ready!
```

---

## 9. Uninstallation

### 9.1 Remove Application

```bash
# Delete project directory
cd ..
rm -rf "The Soundtrack of Your Life"
```

### 9.2 Remove Application Data

**Windows:**
```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\The Soundtrack of Your Life"
```

**Linux:**
```bash
rm -rf ~/.local/share/soundtrack-of-your-life
```

**macOS:**
```bash
rm -rf ~/Library/Application\ Support/The\ Soundtrack\ of\ Your\ Life
```

### 9.3 Uninstall Ollama (Optional)

**Windows:** Uninstall via Settings > Apps

**Linux:**
```bash
sudo systemctl stop ollama
sudo systemctl disable ollama
sudo rm /usr/local/bin/ollama
sudo rm -rf /usr/share/ollama
```

**macOS:**
```bash
brew uninstall ollama
```

---

## 10. Getting Help

### Documentation
- **README.md** - Project overview
- **HLD.md** - High-level architecture
- **LLD.md** - Technical implementation details

### Common Issues
- Check [Troubleshooting](#6-troubleshooting) section above
- Run health check: `python modules/health_check.py`
- Check logs in terminal output

### Support
- Open an issue on GitHub
- Check existing issues for solutions

---

**Document Version:** 1.0  
**Last Updated:** November 2024  
**Author:** AI Solutions Architect Internship Assessment

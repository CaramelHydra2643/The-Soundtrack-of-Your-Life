# The Soundtrack of Your Life - Fresh Clone Setup

This guide explains how to install and run the complete application on Windows 10/11.

The current product is the React/Vite frontend backed by FastAPI. Use the React client for the application workflow.

## 1. Prerequisites

Install:

- Git
- Python 3.11-3.14
- Node.js 20 or newer, including npm
- Ollama
- 8 GB RAM minimum; 16 GB recommended
- At least 5 GB free disk space for packages, models, and local indexes

No NVIDIA GPU is required. CPU inference is supported and is the default for this project.

Recommended downloads:

- Ollama: <https://ollama.com/download/windows>
- Node.js: <https://nodejs.org/>
- Git: <https://git-scm.com/download/win>

## 2. Clone the repository

Open PowerShell:

```powershell
git clone <repository-url>
cd "The Soundtrack of Your Life"
```

Replace `<repository-url>` with the repository URL. Confirm that the folder contains `api.py`, `frontend`, `requirements.txt`, and `scripts`.

## 3. Create the Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Install CPU-only PyTorch first. This avoids CUDA assumptions on Intel integrated graphics:

```powershell
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch
python -m pip install -r requirements.txt
```

## 4. Install frontend packages

```powershell
npm.cmd --prefix frontend install
```

## 5. Create local configuration

```powershell
Copy-Item .env.example .env
```

The default CPU/local configuration is:

```ini
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
EMBEDDING_DEVICE=cpu
ENABLE_LLM_EXPLANATIONS=false
ENABLE_EXTERNAL_MUSIC_LOOKUP=false
```

### Optional Spotify and Apple/iTunes enrichment

Apple iTunes Search works without credentials. Spotify requires a Spotify Developer Dashboard application using the Web API.

Add credentials only to `.env`:

```ini
ENABLE_EXTERNAL_MUSIC_LOOKUP=true
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

Never commit `.env`, paste the secret into source code, or share it publicly. Keep `.env.example` blank.

## 6. Prepare Ollama

Pull the configured model:

```powershell
ollama pull qwen2.5:3b
ollama list
```

If Ollama is not already running, use a separate terminal:

```powershell
ollama serve
```

## 7. Build the conceptual RAG index

Run once after installation:

```powershell
.\.venv\Scripts\python.exe scripts\build_knowledge_base.py
```

This downloads the Sentence Transformers model on first use and creates the `music_knowledge` ChromaDB collection.

After changing files under `data\knowledge_base`, rebuild with:

```powershell
.\.venv\Scripts\python.exe scripts\build_knowledge_base.py --rebuild
```

## 8. Import real music metadata

Generated catalogue files are intentionally ignored by Git. A fresh clone must import the datasets locally before it can recommend real catalogue tracks.

### MTG-Jamendo

Official dataset repository: <https://github.com/MTG/jamendo-dataset>

Clone it outside this repository, then obtain the MTG-Jamendo dataset separately, then run:

```powershell
.\.venv\Scripts\python.exe scripts\ingest_mtg_jamendo.py `
  "C:\path\to\mtg-jamendo-dataset" `
  --output data\music_metadata\mtg_jamendo_catalogue.json
```

This imports metadata, tags, licence provenance, and legitimate Jamendo links. It does not download the large audio archive.

### Free Music Archive

Official repository: <https://github.com/mdeff/fma>

Official metadata archive: <https://os.unil.cloud.switch.ch/fma/fma_metadata.zip>

Download and extract the official FMA metadata archive. Then run:

```powershell
.\.venv\Scripts\python.exe scripts\ingest_fma.py `
  "C:\path\to\fma" `
  --output data\music_metadata\fma_catalogue.json
```

Optional FMA Echo Nest features:

```powershell
.\.venv\Scripts\python.exe scripts\ingest_fma_features.py `
  "C:\path\to\fma\data\fma_metadata\echonest.csv" `
  --output data\music_metadata\fma_audio_features.json
```

### DEAM

DEAM download page: <https://cvml.unige.ch/databases/DEAM/>

Download the DEAM annotations and precomputed features. DEAM is used for emotion calibration, not as the main recommendation catalogue:

```powershell
.\.venv\Scripts\python.exe scripts\ingest_deam.py `
  data\emotion_annotations\deam `
  --output data\emotion_annotations\deam_song_emotions.json
```

DEAM audio is optional. Do not download the huge MTG-Jamendo or FMA audio archives unless you have a specific licensed local-audio requirement.

## 9. Build catalogue indexes

After importing catalogue metadata:

```powershell
.\.venv\Scripts\python.exe scripts\build_catalogue_db.py
```

Build the semantic track index in resumable CPU batches:

```powershell
.\.venv\Scripts\python.exe scripts\build_track_index.py `
  --limit 5000 `
  --batch-size 128 `
  --resume
```

Repeat until the progress manifest is complete:

```text
data\cache\music_tracks_progress.json
```

This can take a long time on CPU. Do not run it during recommendation requests.

## 10. Start the application

Use two PowerShell terminals from the repository root.

### Terminal 1 - FastAPI backend

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Check health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

OpenAPI documentation:

```text
http://127.0.0.1:8000/docs
```

### Terminal 2 - React frontend

```powershell
npm.cmd --prefix frontend run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173
```

The Vite proxy forwards `/api/*` requests to FastAPI on port 8000.

## 11. Optional local voice transcription

The browser Web Speech API is the fast voice path, but it may use a browser/vendor service. For local post-upload transcription, install:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install "faster-whisper>=1.0.0,<2.0.0"
```

FFmpeg may be required for some audio formats. Install it separately and ensure `ffmpeg.exe` is on `PATH`.

The application does not retain temporary uploaded audio after transcription.

## 12. Verify the setup

```powershell
.\.venv\Scripts\python.exe -m compileall -q .
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd --prefix frontend run build
```

The optional Ollama integration test requires Ollama and the configured model:

```powershell
$env:RUN_LOCAL_INTEGRATION = "1"
.\.venv\Scripts\python.exe -m pytest -m integration tests\test_ollama.py -q
```

## 13. First-use workflow

1. Open the React URL.
2. Choose **Type** or **Voice**.
3. Enter or speak a memory in the single memory field.
4. Click **Create my soundtrack**.
5. Wait for Ollama analysis and recommendation ranking.
6. Review recommendations, artwork, previews, and official provider links where available.
7. Use **Refine** to adjust mood, energy, language, or genre.
8. Save the complete soundtrack to **Memory Vault**.
9. Open a saved card and choose **View soundtrack** to expand its tracks.
10. Open Spotify/Apple links or play an available iTunes preview.
11. Open Preferences to save languages, genres, exclusions, explicit-content settings, and diversity.

## 14. Common troubleshooting

### The frontend shows an old version

Stop all Vite processes, start only one frontend server, then use `Ctrl+Shift+R`.

### API requests fail

Confirm FastAPI is running at `http://127.0.0.1:8000` and check `/api/health`.

### Ollama connection error

Run `ollama serve`, then confirm `ollama list` contains `qwen2.5:3b`.

### First request is slow

The first request loads Ollama, Sentence Transformers, ChromaDB, and catalogue data. Later requests reuse the loaded services.

### No real tracks appear after cloning

Generated catalogue files are not committed. Run the MTG-Jamendo and/or FMA ingestion commands and rebuild the SQLite catalogue index.

### No Spotify or Apple artwork/preview appears

Not every open-catalogue track has a confident Apple or Spotify match. Confirm external lookup is enabled and Spotify credentials are present. The application does not fabricate missing artwork, previews, or links.

### Port already in use

Stop the existing process or select another port and update the Vite proxy configuration.

## 15. Data and secret safety

Never commit:

- `.env`
- Spotify client secrets
- SQLite databases
- ChromaDB data
- Generated catalogue files
- Model caches
- Audio recordings
- Personal memories or exports

The repository `.gitignore` already excludes these local artifacts.

# Local setup and runbook

This is the authoritative setup guide for the current implementation.

The repository contains two local web clients:

- **React/Vite client:** recommended product experience at `http://localhost:5173`
- **Streamlit client:** fallback/admin experience at `http://localhost:8501`

Both clients use the same FastAPI service at `http://localhost:8000`.

## 1. Requirements

### Windows 11 / Windows 10

- Python 3.11–3.14
- Node.js 20+ and npm
- Git
- 8 GB RAM minimum; 16 GB recommended
- 5 GB free disk space for Python packages and local models
- Ollama for memory analysis and explanations
- Optional: FFmpeg and `faster-whisper` for local speech transcription

No NVIDIA GPU is required. CPU mode is the default.

## 2. First-time installation

Open PowerShell in the repository root:

```powershell
cd "C:\path\to\The Soundtrack of Your Life"
```

Create and activate the Python environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip

# Intel/integrated-graphics and CPU setup: install CPU-only PyTorch first.
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch
python -m pip install -r requirements.txt
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Create local configuration:

```powershell
Copy-Item .env.example .env
```

Install Ollama from <https://ollama.com/download/windows>, then pull the default CPU-friendly model:

```powershell
ollama pull qwen2.5:3b
```

Verify Ollama:

```powershell
ollama list
```

Install the React client dependencies:

```powershell
npm.cmd --prefix frontend install
```

The `npm.cmd` form avoids PowerShell execution-policy issues on some Windows installations.

## 3. Build the local knowledge base

The first RAG build downloads the embedding model and creates a local ChromaDB collection:

```powershell
.\.venv\Scripts\python.exe scripts\build_knowledge_base.py
```

Rebuild after changing files under `data\knowledge_base`:

```powershell
.\.venv\Scripts\python.exe scripts\build_knowledge_base.py --rebuild
```

The vector store and SQLite database are stored under the platform data directory configured by `APP_DATA_DIR`, or the default `platformdirs` location.

## 4. Import the cloned MTG-Jamendo metadata

The provided MTG-Jamendo clone can be converted without downloading the 508 GB audio archive:

```powershell
.\.venv\Scripts\python.exe scripts\ingest_mtg_jamendo.py `
  "C:\Users\madsaich\Documents\mtg-jamendo-dataset" `
  --output data\music_metadata\mtg_jamendo_catalogue.json
```

This imports the cloned `raw.meta.tsv` and `raw_30s_cleantags_50artists.tsv` files. The verified import currently produces the track count reported by the script, preserves Jamendo listening URLs, maps genre/instrument/mood tags, and labels licence provenance as `See dataset audio_licenses.txt`.

The application will load the normalized JSON catalogue on the next start. It will no longer use demo fixtures while this file is present.

This step imports metadata and legitimate external listening links only. It does not download or redistribute audio.

## 5. Import FMA metadata

The FMA metadata archive is approximately 342 MiB and contains track metadata, genre hierarchy, and precomputed features. The much larger FMA audio archives are not required for metadata-based recommendations.

After extracting `fma_metadata.zip` under the cloned FMA repository, run:

```powershell
.\.venv\Scripts\python.exe scripts\ingest_fma.py `
  "C:\Users\madsaich\Documents\fma" `
  --output data\music_metadata\fma_catalogue.json
```

The current adapter imports:

- Track title
- Artist
- Album
- Language code
- Genre hierarchy
- Per-track licence
- Source provenance

It marks FMA records as `metadata_only` unless an authorized listening or preview URL is separately verified.

The catalogue loader merges `mtg_jamendo_catalogue.json` and `fma_catalogue.json` on the next application start.

## 6. Start the complete application

Use three PowerShell windows, all from the repository root.

### Terminal 1 — FastAPI

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Check the service:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Expected response:

```json
{"status":"ok","mode":"local"}
```

API documentation is available at <http://127.0.0.1:8000/docs>.

### Terminal 2 — React/Vite client

```powershell
npm.cmd --prefix frontend run dev -- --host 127.0.0.1
```

Open <http://127.0.0.1:5173>.

The Vite proxy forwards `/api/*` requests to FastAPI on port 8000.

### Terminal 3 — Streamlit fallback

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Open <http://127.0.0.1:8501>.

Stop any server with `Ctrl+C` in its terminal.

## 5. Optional local voice transcription

The browser recorder works without a cloud service. Transcription requires the optional `faster-whisper` package and a local model download.

Install the optional package inside `.venv`:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install "faster-whisper>=1.0.0,<2.0.0"
```

If FFmpeg is required by the selected audio format, install it from <https://ffmpeg.org/download.html> and ensure `ffmpeg.exe` is on `PATH`.

The speech endpoint is:

```text
POST http://127.0.0.1:8000/api/speech/transcribe
```

The React client records locally, uploads only after the user selects transcription, displays the returned transcript for editing, and does not retain the temporary server-side audio file.

## 7. Import DEAM emotion annotations and features

After extracting the downloaded DEAM archives into the project data directories, normalize the song-level valence/arousal annotations:

```powershell
.\.venv\Scripts\python.exe scripts\ingest_deam.py `
  data\emotion_annotations\deam `
  --output data\emotion_annotations\deam_song_emotions.json
```

The verified annotation import contains 1,802 songs. The openSMILE feature archive remains under `data\audio_features\deam\features` for future audio/emotion calibration. It is not copied into the track catalogue and it does not replace MTG-Jamendo/FMA tracks.

## 8. Enrich a bounded catalogue batch with MusicBrainz

MusicBrainz JSON/PostgreSQL dumps are not required. Use the read API for a small verified batch with local response caching:

```powershell
.\.venv\Scripts\python.exe scripts\enrich_musicbrainz.py `
  data\music_metadata\mtg_jamendo_catalogue.json `
  --limit 100 `
  --output data\music_metadata\musicbrainz_enriched.json `
  --cache data\cache\musicbrainz `
  --user-agent "TheSoundtrackOfYourLife/0.1"
```

The adapter enforces a request interval, caches raw responses, scores artist/title matches, rejects uncertain matches, and preserves MusicBrainz IDs. Do not enrich all 163,124 records through the API at once; start with a small batch or enrich selected recommendations.

## 9. Configuration

Copy `.env.example` to `.env` and adjust values when needed:

```ini
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
EMBEDDING_DEVICE=cpu
RETRIEVAL_TOP_K=5
MAX_RECOMMENDATIONS=5
MAX_MEMORY_LENGTH=5000
APP_DATA_DIR=
DB_NAME=memories.db
```

Keep `EMBEDDING_DEVICE=cpu` on Intel integrated graphics or machines without CUDA. Do not set `cuda` unless a compatible NVIDIA installation is available.

Never commit `.env`, personal memories, SQLite databases, ChromaDB files, or audio recordings.

## 7. Verification commands

Python checks:

```powershell
.\.venv\Scripts\python.exe -m compileall -q .
.\.venv\Scripts\python.exe -m pytest -q
```

React build:

```powershell
npm.cmd --prefix frontend run build
```

The Ollama integration test is intentionally skipped by default. Run it only when Ollama and the configured model are available:

```powershell
$env:RUN_LOCAL_INTEGRATION = "1"
.\.venv\Scripts\python.exe -m pytest -m integration tests\test_ollama.py -q
```

## 8. Troubleshooting

### NumPy tries to compile from source on Windows

Python 3.14 cannot use the old NumPy 1.26 constraint because that release has no compatible Python 3.14 wheel. The current requirements use NumPy 2.x wheels.

If an older checkout still contains `numpy<2.0.0`, update the repository first, then recreate the environment:

```powershell
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Do not install Visual Studio merely to compile NumPy for this project.

### `npm` is not recognized or PowerShell blocks npm scripts

Use `npm.cmd` instead of `npm`:

```powershell
npm.cmd --prefix frontend install
npm.cmd --prefix frontend run dev -- --host 127.0.0.1
```

### FastAPI returns 503 for soundtrack generation

Check that Ollama is running and the model exists:

```powershell
ollama list
ollama pull qwen2.5:3b
```

Then restart FastAPI.

### Recommendations are empty

Build the knowledge base and confirm the catalogue is available:

```powershell
.\.venv\Scripts\python.exe scripts\build_knowledge_base.py
```

When no approved catalogue file exists, the application uses clearly labelled metadata-only demo fixtures. These are not authorized playback tracks.

### ChromaDB or embedding startup is slow

The first start downloads `all-MiniLM-L6-v2`. Later starts reuse the local model and vector store. Keep the application on CPU mode unless a complete GPU stack is intentionally configured.

### Speech transcription returns 503

This means `faster-whisper` is not installed or its model cannot initialize. Install the optional package, verify FFmpeg, or continue with typed memories.

### Existing port is busy

Find and stop the process using the port, or select another port:

```powershell
python -m uvicorn api:app --host 127.0.0.1 --port 8001
npm.cmd --prefix frontend run dev -- --host 127.0.0.1 --port 5174
```

If changing the backend port, update the Vite proxy in `frontend\vite.config.ts`.

## 9. Data and privacy

- Memories are stored locally in SQLite only after the user saves a soundtrack.
- Feedback and preferences are stored locally.
- `/api/export` returns a JSON export of local user data.
- `DELETE /api/data` deletes memories, feedback, and preferences.
- Local audio recordings are written to a temporary file only during transcription and then removed.
- The default workflow does not require paid cloud APIs.
- Track metadata, artwork, previews, and listening links remain separate capabilities; metadata-only records must not be treated as playable audio.

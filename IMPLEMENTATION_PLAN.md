# Prioritized implementation plan

## Contract

**Input:** a user memory of 10–5,000 characters, optionally corrected after analysis.

**Output:** a validated `SoundtrackResult` containing memory analysis, ranked and diverse catalogue tracks, grounded explanations, and retrieval transparency.

**Failure states:** empty/short input, unavailable local LLM, unavailable vector store, invalid model output, empty catalogue, and database failures must produce actionable messages rather than stack traces.

**Success criteria:** deterministic ranking works without a model, RAG context can change ranking, dynamic text is safely rendered, tracks never claim unavailable playback, and saved memories remain queryable.

## Phase 1 — stabilization (current)

- [x] Audit repository and record honest baseline.
- [x] Normalize track metadata and add a provenance-preserving demo fallback.
- [x] Make recommendation weights match the brief and renormalize missing signals.
- [x] Make RAG context influence scoring with transparent topic/tag boosts.
- [x] Fix Chroma distance normalization for cosine, L2, and unknown metrics.
- [x] Make Ollama configuration and structured-output retries reliable.
- [x] Replace unsafe HTML interpolation in the UI.
- [x] Add deterministic core tests and isolate external integration tests.

## Phase 2 — product surface

- [x] Extract shared `SoundtrackService` orchestration and expose initial FastAPI contracts.
- [x] Refresh the existing Streamlit soundtrack/results surface with safer native components.
- [x] Add feedback persistence (`like`, `dislike`, `save`, `skip`) and export/delete-all controls.
- [x] Add optional local speech transcription endpoint with CPU-safe faster-whisper integration.
- [x] Add local preferences controls and API contracts.
- [x] Add Streamlit microphone capture with post-upload transcript review.
- [x] Apply saved preferences and feedback to recommendation ranking.
- [x] Add React browser MediaRecorder UI and React Memory Vault/Preferences views.
- [x] Add bounded conversational recommendation refinement across FastAPI and React.

## Phase 3 — service seam

- [x] Extract `SoundtrackService` orchestration from the Streamlit entry point.
- [x] Expose that service through FastAPI request/response schemas.
- [x] Add a Vite/React client using the same contracts; keep Streamlit available as a local fallback during migration.
- [x] Add browser smoke coverage for the React shell and microphone controls.
- [ ] Add full API-backed browser integration tests and wire microphone capture to speech in a running environment.

## Phase 4 — data expansion

- [x] Add a dedicated MTG-Jamendo clone adapter with licence and URL provenance.
- [x] Import the cloned MTG-Jamendo metadata/tag catalogue without downloading audio.
- [x] Add FMA metadata adapter and merge MTG-Jamendo/FMA catalogue sources.
- [x] Add cached, rate-limited MusicBrainz API enrichment for bounded batches.
- [x] Add enrichment fields to the primary catalogue and a separate music-track Chroma collection.
- [ ] Complete full 163,124-track index build.
- [x] Import verified FMA Echo Nest audio features for 13,129 tracks and use numeric audio compatibility.
- [ ] Add verified DEAM joins where an explicit cross-dataset identity exists.
- [x] Import DEAM valence/arousal annotations and retain openSMILE features for calibration.
- [ ] Add audio-feature extraction/mapping into track ranking.
- [ ] Add multilingual catalogue normalization and optional local speech recognition.
- [ ] Add batch ingestion diagnostics, deduplication reports, and retrieval evaluation fixtures.

## Quality gates per phase

- `python -m compileall -q .`
- `python -m pytest -q`
- Manual Streamlit smoke test with Ollama unavailable (fallback path).
- Manual browser accessibility/responsive review when the UI is running.
- No raw memory text in logs or unsafe HTML rendering.

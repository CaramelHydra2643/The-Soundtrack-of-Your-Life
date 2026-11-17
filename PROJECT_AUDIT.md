# Project audit

**Audit date:** 17 November 2026

## Executive summary

The repository is a local-first Streamlit prototype with a useful modular Python core. It is not yet the FastAPI/React platform described by the brief, and several "production ready" claims in the legacy documentation are inaccurate. The fastest safe path for the one-week milestone is to stabilize the existing core, make the local workflow resilient without Ollama/Chroma, expand the normalized catalogue contract, and refresh the Streamlit experience. A later migration can place the same services behind FastAPI and a React client without rewriting the domain logic.

## What is implemented

- Pydantic settings, memory analysis prompt, JSON extraction, and schema validation.
- ChromaDB/Sentence Transformers ingestion and retrieval scripts.
- SQLite-backed Memory Vault with parameterized queries, search, filters, and deletion.
- Weighted tag-based recommendation scoring and LLM/fallback explanations.
- Curated knowledge documents covering emotions, genres, instruments, and contexts.
- Streamlit create-soundtrack and vault screens.

## Findings and risks

| Area | Finding | Priority | Decision |
|---|---|---:|---|
| UI | Streamlit UI uses unsafe HTML interpolation for user/track text and has no responsive design system, voice input, feedback, or preference views. | High | Replace unsafe dynamic HTML and redesign the existing UI in a cinematic, accessible Streamlit style first. |
| LLM | Ollama calls use the global client and do not pass `ollama_base_url`; invalid JSON and schema errors are not retried consistently. Long inputs are silently truncated. | High | Use a configured client, explicit validation, bounded retries, and user-visible length errors. |
| RAG | Chroma distance is converted as `1 - distance` regardless of collection metric. Retrieved context is accepted by the recommender but does not affect ranking. | High | Normalize cosine/L2 distances defensively and derive small, explainable RAG signal boosts from retrieved topics/text. |
| Catalogue | No committed catalogue records are present; the app silently falls back to ten fictional sample tracks and labels recommendations as “Sample Catalogue”. | High | Add a clearly labelled, provenance-preserving seed catalogue with nullable metadata and no fabricated playback claims. |
| Dependencies | `sentence-transformers` and `chromadb` were commented out despite imports being mandatory. | High | Make runtime dependencies explicit and CPU-safe. |
| Persistence | SQLite persistence is functional but uses repeated connection boilerplate, has no feedback/preferences tables, and no export method. | Medium | Preserve the vault API and add feedback/export in focused increments. |
| Tests | Pytest passes four configuration tests, but emits deprecated Pydantic and test-return warnings. The Ollama test is an import-time integration script and should not be collected as a unit test. | Medium | Add deterministic unit tests and make external integrations opt-in. |
| Docs | README/HLD/LLD/PROJECT_COMPLETE claim a completed production system, 18 docs, 36 chunks, and a full catalogue without verifiable local data. | High | Replace completion claims with current architecture, limitations, and reproducible commands. |
| Privacy | Local storage is used, but raw memories can be sent to the local Ollama service and are displayed with unsafe HTML. | Medium | Keep processing local by default, never log raw memories, and render dynamic text through Streamlit primitives. |

## Baseline verification

- `python -m pytest -q`: **4 passed**, with 8 warnings (Pydantic deprecations and pytest test functions returning booleans).
- `python -m compileall -q .`: **passed**.
- The existing end-to-end Ollama test was not run as part of the unit baseline because it requires a live model and performs work at import time.

## Target for this iteration

1. Stabilize configuration, schemas, catalogue normalization, RAG scoring, and recommendation ranking.
2. Add deterministic tests for recommendation/RAG influence, missing metadata, deduplication, and vault export.
3. Redesign the Streamlit surface with accessible native components and explicit loading/error/empty states.
4. Document the honest local setup, catalogue provenance, and next-step FastAPI/React migration seam.

## Deferred deliberately

FastAPI/React, faster-whisper, authentication, cloud deployment, and broad external catalogue ingestion are deferred until the current local workflow is stable. They require new dependency and operational surfaces and should consume the existing service modules rather than duplicate business logic.

# Performance and latency

## Current fast path

The default soundtrack request uses one Ollama call for structured memory analysis. Overall explanations are deterministic by default so a second LLM request is not required.

```text
FastAPI validation
  → cached SoundtrackService
  → one Ollama analysis call
  → one shared Sentence Transformer model
  → bounded RAG/track retrieval
  → candidate ranking and MMR diversity
  → deterministic grounded explanation
```

## CPU configuration

Recommended `.env` values:

```ini
EMBEDDING_DEVICE=cpu
LLM_MAX_TOKENS=1000
ENABLE_LLM_EXPLANATIONS=false
```

Set `ENABLE_LLM_EXPLANATIONS=true` only when a slower, second Ollama explanation is preferred.

## Instrumentation

The service logs stage timings without logging raw memory text:

- `soundtrack_stage=analysis`
- `soundtrack_stage=knowledge_retrieval`
- `soundtrack_stage=ranking`

The first request can be slower because Ollama, Sentence Transformers, ChromaDB, and the catalogue are initialized. FastAPI caches the expensive service for subsequent requests.

## Retrieval performance

- Track embeddings are precomputed by `scripts/build_track_index.py`.
- The service reuses the RAG embedding model for track queries.
- The `music_tracks` collection returns a bounded candidate pool.
- If the vector index is unavailable, the service falls back to the normalized catalogue.
- The full 163,124-track index is resumable with `--offset` and `--limit`; it is not built during a user request.

## Honest limitations

CPU-only Ollama inference remains the largest variable latency source. Enabling LLM explanations adds another model request. Browser speech recognition may use the browser provider; typed input avoids that path.

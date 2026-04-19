# 📄 `app/services/gemma_with_RAG_services.py` — Gemma + RAG (Disabled)

> **Back to:** [APP_DOCUMENTATION.md](../../APP_DOCUMENTATION.md)

---

## Overview

`gemma_with_RAG_services.py` was a **local on-device RAG system** combining:

- **Gemma 3 1B IT** quantized model (`google/gemma-3-1b-it-qat-q4_0-unquantized`) running locally via HuggingFace Transformers
- **E5 Multilingual embeddings** for retrieval
- **ChromaDB** as a vector store

> ⚠️ **This entire file is currently commented out.** The `GemmaWithRAGServices` class is disabled and not used in the running application.

---

## Why It Was Disabled

Running a local LLM requires:
- A GPU (CUDA) or slow CPU inference
- ~2-4 GB of model weights
- HuggingFace `transformers`, `accelerate`, `torch` dependencies

These requirements were too heavy for the cloud deployment. The project uses **Groq's hosted LLM API** instead.

---

## Original Architecture (When Active)

```
User Query
    │
    ▼
E5 embedding → ChromaDB retrieval (top-K docs)
    │
    ▼
Context assembled from retrieved docs
    │
    ▼
Gemma 3 local model generates answer
(GPU if available, CPU fallback)
    │
    ▼
Response
```

---

## Original Class: `GemmaWithRAGServices` (Commented Out)

| Method | Description |
|---|---|
| `__init__()` | Loads E5 embeddings, ChromaDB, and Gemma model (heavy startup) |
| `add_json(json_path)` | Ingests Q&A JSON into ChromaDB (same format as E5RAGSystem) |
| `retrieve(query, top_k=5)` | Semantic similarity search in ChromaDB |
| `generate_text(prompt, retrieved, max_tokens, temperature)` | Generates answer from Gemma using retrieved context |
| `chat(query, top_k, show_context)` | Combined pipeline |

---

## GPU/CPU Detection

The system auto-detects hardware:
```python
if torch.cuda.is_available():
    self.device = "cuda"
    self.dtype = torch.bfloat16  # or float16
else:
    self.device = "cpu"
    self.dtype = torch.float32
    # Warning: CPU inference will be slow
```

---

## Model Used

| Setting | Value |
|---|---|
| Model ID | `google/gemma-3-1b-it-qat-q4_0-unquantized` |
| Cache dir | `/home/rospc/tanishq/RaithaMithra_v2/.../model` (Linux path) |
| Max new tokens | 200 |
| Temperature | 0.6 |

---

## How to Re-enable

1. Uncomment the entire file.
2. Install dependencies:
   ```bash
   pip install transformers accelerate torch sentence-transformers chromadb
   ```
3. Update the `cache_dir` path in the constructor to your local model directory.
4. In `conversation_nodes.py`, uncomment:
   ```python
   from services.gemma_with_RAG_services import get_gemma_with_RAG_service
   self.gemma_with_rag_service = get_gemma_with_RAG_service()
   ```
5. Call `service.add_json(...)` once to pre-populate the vector store.

---

## Difference vs `rag_e5_groq.py`

| Feature | `rag_e5_groq.py` | `gemma_with_RAG_services.py` |
|---|---|---|
| LLM | Groq API (llama-3.3-70b) | Local Gemma 3 1B |
| Network required | ✅ Yes | ❌ No (fully offline) |
| Speed | Fast (API) | Slow without GPU |
| Cost | Per-API-call | Free (local compute) |
| Embeddings | E5 Multilingual | E5 Multilingual |
| Vector DB | ChromaDB | ChromaDB |

---

## Related Files

| File | Role |
|---|---|
| [services/rag_e5_groq.py](rag_e5_groq.md) | Alternative RAG with cloud LLM (also disabled) |
| [services/groq_service.py](groq_service.md) | Active LLM service being used instead |
| `model/` | Local model cache directory |
| `rag/final_clean_merged_dataset.json` | Knowledge base for ingestion |

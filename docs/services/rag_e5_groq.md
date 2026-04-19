# 📄 `app/services/rag_e5_groq.py` — E5 RAG System (Disabled)

> **Back to:** [APP_DOCUMENTATION.md](../../APP_DOCUMENTATION.md)

---

## Overview

`rag_e5_groq.py` was a **Retrieval-Augmented Generation (RAG)** system combining:

- **E5 Multilingual Large Instruct** (`intfloat/multilingual-e5-large-instruct`) for embeddings
- **ChromaDB** as a persistent vector store
- **Groq LLM** (`llama-3.3-70b-versatile`) for answer generation

> ⚠️ **This entire file is currently commented out.** The `E5RAGSystem` class and all its methods are disabled and not used in the running application.

---

## Why It Was Disabled

The E5 model requires downloading a large sentence-transformers model (~1.3 GB). This dependency was too heavy for the current deployment setup. The project switched to the direct Groq LLM approach (with conversation history as context) instead of full RAG.

---

## Original Architecture (When Active)

```
User Query
    │
    ▼
E5 embedding of query
    │
    ▼
ChromaDB cosine similarity search
    │
    ▼
Top-K relevant Q&A documents retrieved
    │
    ▼
Groq LLM generates answer from context
    │
    ▼
Response
```

---

## Original Class: `E5RAGSystem` (Commented Out)

| Method | Description |
|---|---|
| `add_json(json_path)` | Ingests Q&A JSON file (like `sugar_cane.json`) into ChromaDB |
| `retrieve(query, top_k=5)` | Embeds query, searches ChromaDB for similar documents |
| `generate_response(query, retrieved)` | Prompts Groq strictly to answer only from context |
| `chat(query, top_k, show_context)` | Combined retrieve + generate pipeline |

---

## Data Format Expected

The system expected JSON files with Q&A pairs:
```json
[
    {"id": "sc_001", "question": "ಕಬ್ಬು ಎಷ್ಟು ಆಳ ನೆಡಬೇಕು?", "answer": "15-20 ಸೆಂ.ಮೀ ಆಳ..."},
    {"id": "sc_002", "question": "...", "answer": "..."}
]
```

The dataset `rag/final_clean_merged_dataset.json` (573 KB) was the primary knowledge base.

---

## How to Re-enable

1. Uncomment the entire file.
2. Install dependencies:
   ```bash
   pip install sentence-transformers chromadb
   ```
3. In `groq_service.py`, uncomment:
   ```python
   from services.rag_e5_groq import get_e5_rag_service
   self.rag_service = get_e5_rag_service()
   context = self.rag_service.retrieve(query=prompt, top_k=5)
   context = "\n\n".join(context["documents"])
   ```
4. Pre-populate the ChromaDB by running:
   ```python
   service = get_e5_rag_service()
   service.add_json("rag/final_clean_merged_dataset.json")
   ```

---

## Related Files

| File | Role |
|---|---|
| [services/gemma_with_RAG_services.py](gemma_with_rag_services.md) | Alternative RAG using local Gemma model (also disabled) |
| [services/groq_service.py](groq_service.md) | Had commented-out RAG integration hooks |
| `rag/final_clean_merged_dataset.json` | The Q&A knowledge base this system was designed for |
| `chroma_db_e6/` | Persistent ChromaDB storage directory |

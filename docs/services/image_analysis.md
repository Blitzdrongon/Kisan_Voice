# 📄 `app/services/image_anylsis.py` — Gemini Image Analysis Service

> **Back to:** [APP_DOCUMENTATION.md](../../APP_DOCUMENTATION.md)

---

## Overview

`image_anylsis.py` (note: typo in filename — "analysis" is misspelled) implements **AI-powered image understanding** using **Google Gemini 2.5 Flash** vision model. It supports multiple API keys with round-robin load balancing and routes images through a 3-step analysis pipeline.

---

## Class: `image_analysis`

### Initialization

- Reads `GOOGLE_IMAGE_KEYS` (comma-separated) from settings.
- Initializes with first key; rotates on failure.
- Loads `system_prompt` from `prompt.prompts` (currently unused in actual calls).

---

## 3-Step Image Analysis Pipeline

```
Image File Input
      │
      ▼
classify_image()      → "disease" | "identification" | "none"
      │
      ├─ "disease"        → disease_analysis()
      ├─ "identification" → identification_image()
      └─ "none"           → describe_image()
```

---

## Methods

### `analyze_image(image_path, prompt, model, language) → str`

**Main entry point.** Called by `_handle_image_analysis()` in `conversation_nodes.py`.

**Steps:**
1. Validates file exists.
2. Reads and base64-encodes image.
3. Detects MIME type from extension.
4. Calls `classify_image()` first to route correctly.
5. Delegates to the appropriate sub-analyzer.

```python
result = await image_analysis_service.analyze_image(
    image_path="/path/to/crop.jpg",
    language="kn"
)
```

---

### `classify_image(mime_type, image_base64, language) → str`

Single-word classification using Gemini.

**Prompt:**
```
You are an AI expert in agriculture. Classify this input into one of three categories:
1. disease – plant shows disease symptoms
2. identification – identify plant species
3. none – unrelated or unrecognizable

Just return a single word: disease, identification, or none.
```

**Returns:** `"disease"`, `"identification"`, or `"none"`

---

### `disease_analysis(mime_type, image_base64, language) → str`

Detailed crop disease analysis.

**Output format (in detected language):**
1. Detected Disease
2. Affected Crop
3. Symptoms Observed
4. Recommended Treatment Plan
5. Prevention Tips
6. Severity Level

Token limit: ~300 tokens.

---

### `identification_image(mime_type, image_base64, language) → str`

Plant species identification by a "botanist expert".

**Output format:**
1. Common Name
2. Scientific Name
3. Family
4. Key Identifying Features
5. Possible Uses
6. Native Region
7. Additional Notes

Token limit: ~300 tokens.

---

### `describe_image(mime_type, image_base64, language) → str`

Generic image description for unrecognized or general images.

Token limit: ~300 tokens.

---

## Load Balancing

Same pattern as Gemini TTS:
- `_rotate_key()` — switches to next key in round-robin.
- `_safe_api_call(func, *args)` — retries all keys before raising `RuntimeError`.

---

## Supported Image Formats

| Extension | MIME Type |
|---|---|
| `.jpg`, `.jpeg` | `image/jpeg` |
| `.png` | `image/png` |
| `.gif` | `image/gif` |
| `.webp` | `image/webp` |
| (default) | `image/jpeg` |

---

## Global Instance

```python
Image_analysis = image_analysis()

def get_image_analysis() -> image_analysis:
    return Image_analysis
```

---

## Note on Filename Typo

The file is named `image_anylsis.py` (typo). When importing:
```python
from services.image_anylsis import get_image_analysis  # Note: typo preserved
```

---

## Related Files

| File | Role |
|---|---|
| [core/config.py](../core/config.md) | Provides `GOOGLE_IMAGE_KEYS` |
| [prompt/prompts.py](../prompt/prompts.md) | System prompt templates (imported but not actively used) |
| [nodes/conversation_nodes.py](../nodes/conversation_nodes.md) | Calls `analyze_image()` in `_handle_image_analysis()` |
| [services/groq_service.py](groq_service.md) | Alternative vision analysis via Groq |

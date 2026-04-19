# 📄 `app/prompt/prompts.py` — System Prompt Templates

> **Back to:** [APP_DOCUMENTATION.md](../../APP_DOCUMENTATION.md)

---

## Overview

`prompts.py` defines a `prompt` class containing system prompt templates for the image analysis pipeline. These prompts were designed to be loaded by `image_anylsis.py` to classify, analyze disease, identify plants, or describe images.

> ⚠️ **Currently not actively used.** The `image_anylsis.py` file imports `get_system_prompt()` but the actual prompts used in `classify_image()`, `disease_analysis()`, etc. are **hardcoded inline** in `image_anylsis.py`. These `prompt` class methods are available for future refactoring.

---

## Class: `prompt`

All methods are `async` static-style methods (no `self`).

### `classify_prompt() → str`

Returns the agricultural image classification prompt:
```
You are an AI expert in agriculture. Classify this input into one of three categories:
1. disease – plant shows disease symptoms
2. identification – identify plant species
3. none – unrelated or unrecognizable

Just return a single word: disease, identification, or none.
```

---

### `diesase_prompt() → str` *(typo: "disease")*

Returns the crop disease analysis prompt:
```
You are an expert in crop health. Analyze this plant image and provide:
1. Detected Disease
2. Affected Crop
3. Symptoms Observed
4. Recommended Treatment Plan
5. Prevention Tips
6. Severity Level
If unrecognizable, respond: "Could not recognize the crop or disease."
```

---

### `identification_prompt() → str`

Returns the plant identification prompt:
```
You are a botanist and plant taxonomy expert. Analyze this plant image and provide:
1. Common Name
2. Scientific Name
3. Family
4. Key Identifying Features
5. Possible Uses
6. Native Region
7. Additional Notes
If identification is unclear, respond: "Could not identify the plant species."
```

---

### `describe_prompt() → str`

Returns a generic describe prompt (currently same content as disease prompt — likely a copy-paste placeholder).

---

## Global Instance

```python
system_prompt = prompt()

def get_system_prompt() -> prompt:
    return system_prompt
```

---

## How to Clean This Up

The intended design was for `image_anylsis.py` to call methods like `self.prompt.classify_prompt()` instead of hardcoding prompts. To restore this:

1. In `image_anylsis.py`, uncomment the calls:
   ```python
   prompt = self.prompt.classify_prompt()
   prompt = self.prompt.diesase_prompt()
   prompt = self.prompt.identification_prompt()
   prompt = self.prompt.describe_prompt()
   ```
2. Remove the hardcoded inline prompt strings from each method.

---

## Related Files

| File | Role |
|---|---|
| [services/image_anylsis.py](../services/image_analysis.md) | Imports this but uses inline prompts instead |

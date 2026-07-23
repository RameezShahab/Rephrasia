---
title: Rephrasia — AI-Powered Text Processing API
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---


# Rephrasia - AI-Powered Text Processing API

A Flask-based API for text paraphrasing, translation, chat, and more.

## Features

- **Paraphrasing**: Generate multiple paraphrased versions using `humarin/chatgpt_paraphraser_on_T5_base`
- **Translation**: Bidirectional English ↔ Urdu translation using `facebook/nllb-200-distilled-600M`
- **Chat**: Global AI Copilot powered by the blazing-fast Groq API (`llama-3.1-8b-instant`)
- **OCR (Image to Text)**: Extract text from images and process it
- **Batch Processing**: Process multiple texts in one request
- **Text-to-Speech**: Convert text to audio (Urdu/English)
- **Export**: Save results as PDF or DOCX

## System Requirements

- Python 3.9+
- 8GB+ RAM recommended (for models)
- 5GB+ disk space for model weights
- **Tesseract OCR** installed (for image-to-text)
  - Windows: Download from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
  - Install to `C:\Program Files\Tesseract-OCR\`
  - Or adjust path in `ocr.py`

## Installation

```bash
# Clone the repository
cd Rephrasia

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Run the Flask server
python app.py

# Server starts at http://127.0.0.1:5000
```

## API Endpoints

### 1. Paraphrasing

**Single Text:**
```bash
POST /api/rephrase
Content-Type: application/json

{
  "text": "Education shapes society."
}
```

**Batch Processing:**
```bash
POST /api/batch/rephrase
Content-Type: application/json

{
  "texts": ["Text 1", "Text 2", "Text 3"]
}
```

### 2. Translation

**Single Translation:**
```bash
POST /api/translate
Content-Type: application/json

{
  "text": "Hello world",
  "language": "urdu"  # or "english"
}
```

**Batch Translation:**
```bash
POST /api/batch/translate
Content-Type: application/json

{
  "texts": ["Hello", "Goodbye"],
  "language": "urdu"
}
```

### 3. Chat (Groq Copilot)

```bash
POST /chat
Content-Type: application/json

{
  "text": "Hello, how are you?",
  "session_id": "optional-session-id"
}
```

### 4. Text-to-Speech

```bash
POST /api/tts
Content-Type: application/json

{
  "text": "یہ ایک ٹیسٹ ہے",
  "language": "urdu"  # or "english"
}
```

### 5. Export

**Export to PDF:**
```bash
POST /api/export/pdf
Content-Type: application/json

{
  "original_text": "Original sentence",
  "results": ["Paraphrase 1", "Paraphrase 2"],
  "result_type": "Paraphrased"
}
```

**Export to DOCX:**
```bash
POST /api/export/docx
Content-Type: application/json

{
  "original_text": "Original sentence",
  "results": ["Translation"],
  "result_type": "Translated"
}
```

### 6. OCR (Image to Text)

**Extract Text from Image:**
```bash
POST /api/ocr
Content-Type: multipart/form-data

image: [image file]
language: eng  # or 'urd', 'eng+urd'
preprocess: true  # optional, enhances image quality
```

**OCR + Rephrase (Combined):**
```bash
POST /api/ocr-rephrase
Content-Type: multipart/form-data

image: [image file]
language: eng
preprocess: true
```

**OCR + Translate (Combined):**
```bash
POST /api/ocr-translate
Content-Type: multipart/form-data

image: [image file]
ocr_language: eng
target_language: urdu
preprocess: true
```

**Get Supported OCR Languages:**
```bash
GET /api/ocr/languages
```

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api.py
```

## PowerShell Examples

```powershell
# Rephrase
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/rephrase `
  -Body (@{text="Education shapes society."} | ConvertTo-Json) `
  -ContentType "application/json"

# Translate
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/translate `
  -Body (@{text="Hello"; language="urdu"} | ConvertTo-Json) `
  -ContentType "application/json"

# Batch rephrase
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/batch/rephrase `
  -Body (@{texts=@("Text 1", "Text 2")} | ConvertTo-Json) `
  -ContentType "application/json"

# OCR from image
$imagePath = "C:\path\to\image.png"
$form = @{
    image = Get-Item -Path $imagePath
    language = "eng"
    preprocess = "true"
}
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/ocr -Form $form

# OCR + Rephrase
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/ocr-rephrase -Form $form
```

## Model Information

| Feature | Model | Size |
|---------|-------|------|
| Paraphrasing | humarin/chatgpt_paraphraser_on_T5_base | ~900MB |
| Translation | facebook/nllb-200-distilled-600M | ~2.5GB |
| Chat | Groq API (llama-3.1-8b-instant) | API-based |
| TTS | Google Text-to-Speech (gTTS) | API-based |
| OCR | Tesseract OCR | ~100MB (separate install) |

## Project Structure

```
Rephrasia/
├── app.py                 # Main Flask application (routes + input validation)
├── config.py              # Centralized constants (models, limits, paths)
├── model.py               # Paraphrasing logic (chatgpt_paraphraser_on_T5)
├── translation.py         # Translation logic (NLLB-200 distilled-600M)
├── chat.py                # Chat session management (Groq API integration)
├── batch_processor.py     # Sequential bulk processing
├── tts.py                 # Text-to-speech (gTTS)
├── export_utils.py        # PDF/DOCX export (reportlab + python-docx)
├── ocr.py                 # Image to text (Tesseract OCR)
├── requirements.txt       # Python dependencies (pinned versions)
├── Dockerfile             # Docker image definition
├── frontend/              # Modern React frontend (Vite + TailwindCSS)
│   ├── src/pages/         # React pages (Dashboard, OCR, Chat, etc.)
│   └── src/components/    # Reusable React components (CopilotSidebar, etc.)
└── static/                # Generated files (auto-created at runtime)
    ├── audio/             # TTS audio files (auto-cleaned after 24h)
    └── exports/           # PDF/DOCX exports (auto-cleaned after 24h)
```

## Performance Tips

- Models are lazy-loaded on first request
- Use batch endpoints for multiple texts
- Audio/export files auto-cleanup after 24 hours
- Chat sessions are stored in-memory (consider Redis for production)

## Troubleshooting

**Tesseract Not Found:**
- Download Tesseract from [here](https://github.com/UB-Mannheim/tesseract/wiki)
- Install to default location or update path in `ocr.py`
- Restart terminal after installation

**OCR Not Detecting Text:**
- Try with `preprocess: true` parameter
- Ensure image has clear, readable text
- Check image format (PNG, JPG supported)
- Use correct language code (eng, urd, etc.)

**Out of Memory:**
- Reduce `num_beams` in model generation
- Use smaller model variants (DialoGPT-small)
- Process fewer items in batch requests

**Slow First Request:**
- Models download and load on first use (~5-10 mins)
- Subsequent requests are fast

**Import Errors:**
- Ensure all requirements are installed: `pip install -r requirements.txt`
- Python 3.9+ required

## License

Open source - free to use and modify

## Support

For issues or questions, check the code comments or test files for usage examples.

"""
app.py — Main Flask application for Rephrasia AI Text Processing API.

Endpoints:
  POST /api/rephrase                  → Paraphrase text (now accepts optional 'mode')
  POST /api/translate                 → Translate text (EN↔UR)
  POST /chat                          → Chat with DialoGPT
  POST /api/batch/rephrase            → Bulk paraphrase
  POST /api/batch/translate           → Bulk translate
  GET  /api/batch/status/<job_id>     → Batch job status
  POST /api/tts                       → Text-to-speech
  POST /api/export/pdf                → Export to PDF
  POST /api/export/docx               → Export to DOCX
  POST /api/ocr                       → Image → text
  GET  /api/ocr/languages             → Supported OCR languages
  POST /api/ocr-rephrase              → OCR + paraphrase
  POST /api/ocr-translate             → OCR + translate
  POST /api/pdf/extract               → PDF → text chunks
  POST /api/async/rephrase            → Long-doc async paraphrase
  POST /api/async/translate           → Long-doc async translate
  POST /api/async/pdf/rephrase        → PDF upload → async paraphrase
  POST /api/async/pdf/translate       → PDF upload → async translate
  GET  /api/async/status/<job_id>     → Async job status
  POST /admin/reload-models           → Force-evict model cache
  --- NEW (v3.0) ---
  POST /api/auth/register             → User registration
  POST /api/auth/login                → User login (JWT)
  GET  /api/user/profile              → Get user profile
  PUT  /api/user/profile              → Update user profile
  POST /api/grammar                   → Grammar check
  GET  /api/history                   → List activity history
  DELETE /api/history/<item_id>       → Delete history item
  GET  /api/stats                     → Dashboard statistics
  PUT  /api/user/preferences          → Save preferences

CHANGELOG v3.0 (Missing API Contracts):
  - Added authentication (JWT) via auth.py module.
  - Added dedicated grammar-check endpoint via grammar_checker.py.
  - Added history tracking via history_store.py module.
  - Added dashboard stats, preferences, and profile management endpoints.
  - Extended /api/rephrase to accept optional 'mode' parameter.
  - Added Pydantic v2 request/response validation via schemas.py.
"""

import asyncio
import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from batch_processor import batch_processor
from chat import chat_manager
from config import MAX_TEXT_LENGTH, MAX_BATCH_SIZE, MAX_UPLOAD_MB, PORT, STATIC_CLEANUP_HOURS
from export_utils import cleanup_old_exports, export_to_docx, export_to_pdf
from model import paraphrase, force_reload_paraphrase_model
from ocr import extract_text_from_image, get_supported_languages, preprocess_image, validate_image
from pdf_parser import extract_chunks_from_pdf, extract_text_from_pdf
from translation import translate_to_english, translate_to_urdu, force_reload_translation_model
from tts import cleanup_old_audio_files, text_to_speech
from chunking import get_semantic_chunks, get_paraphrase_chunks, get_translation_chunks
from llm_wrapper import process_chunks_parallel

# v3.0 — New module imports
from auth import register_user, login_user, get_user, update_user, update_preferences, require_auth, require_admin
from grammar_checker import check_grammar
from history_store import record_activity, list_history, delete_history_item, get_stats
from pydantic import ValidationError
from schemas import (
    RegisterRequest, LoginRequest, ProfileUpdateRequest,
    PreferencesRequest, GrammarCheckRequest,
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

# ── CORS Configuration ────────────────────────────────────────────────────────
# Explicitly allow requests from the local development server and staging.
allowed_origins = [origin.strip() for origin in os.environ.get("FRONTEND_URLS", "http://localhost:5173").split(",") if origin.strip()]
CORS(app, origins=allowed_origins)

# Global store for last processed outputs (used by chatbot for definition queries)
last_results: dict = {
    "rephrase":  [],
    "translate": "",
}

# Thread pool for background jobs
executor = ThreadPoolExecutor(max_workers=4)

# In-memory async job store
async_jobs_db: dict = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_json_text(data: dict | None) -> tuple[str, None] | tuple[None, tuple]:
    """
    Extract and validate 'text' from a JSON body.

    Returns (text, None) on success, or (None, error_response) on failure.
    """
    if not data or "text" not in data:
        return None, (jsonify({"error": "Missing 'text' in request body"}), 400)
    text = str(data["text"]).strip()
    if not text:
        return None, (jsonify({"error": "'text' must not be empty"}), 400)
    if len(text) > MAX_TEXT_LENGTH:
        return None, (
            jsonify({"error": f"'text' exceeds maximum length of {MAX_TEXT_LENGTH} characters"}),
            413,
        )
    return text, None


# ── Routes ────────────────────────────────────────────────────────────────────


# ── Core API ──────────────────────────────────────────────────────────────────

@app.route("/api/rephrase", methods=["POST"])
def rephrase():
    text, err = _require_json_text(request.json)
    if err:
        return err

    # v3.0: Accept optional 'mode' parameter (standard|fluency|creative|academic)
    mode = (request.json.get("mode") or "standard").lower()
    valid_modes = ("standard", "fluency", "creative", "academic")
    if mode not in valid_modes:
        return jsonify({"error": f"Invalid mode. Use one of: {', '.join(valid_modes)}"}), 400

    try:
        # NOTE: The T5 model does not natively support mode-specific generation.
        # For now, mode is logged and passed through; a future enhancement could
        # adjust beam parameters or prompt prefix per mode.
        logger.info("Paraphrase requested with mode: %s, length: %d chars", mode, len(text))
        
        if len(text) > 800:
            logger.info("Text > 800 chars detected. Routing to parallel chunk processor.")
            chunks = get_paraphrase_chunks(text)
            final_text = asyncio.run(process_chunks_parallel(chunks, "paraphrase"))
            rephrased_sentences = [final_text]
        else:
            rephrased_sentences = paraphrase(text)
            
        last_results["rephrase"] = rephrased_sentences
    except Exception as exc:
        logger.exception("Paraphrasing endpoint failed.")
        return jsonify({"error": "Paraphrasing failed", "details": str(exc)}), 500

    return jsonify({"rephrased_results": rephrased_sentences, "mode": mode})


@app.route("/api/translate", methods=["POST"])
def translate():
    text, err = _require_json_text(request.json)
    if err:
        return err

    language = (request.json.get("language") or "urdu").lower()

    try:
        if language == "urdu":
            translated_text = translate_to_urdu(text)
        elif language == "english":
            translated_text = translate_to_english(text)
        else:
            return jsonify({"error": "Unsupported language. Use 'urdu' or 'english'"}), 400
    except Exception as exc:
        logger.exception("Translation endpoint failed.")
        return jsonify({"error": "Translation failed", "details": str(exc)}), 500

    last_results["translate"] = translated_text
    return jsonify({"translated_text": translated_text})


@app.route("/chat", methods=["POST"])
def chat_endpoint():
    data = request.json or {}
    message = str(data.get("text", "")).strip()
    session_id = data.get("session_id")

    if not message:
        return jsonify({"error": "Missing 'text' in request body"}), 400
    if len(message) > MAX_TEXT_LENGTH:
        return jsonify({"error": f"Message exceeds {MAX_TEXT_LENGTH} characters"}), 413

    try:
        chat_manager.update_context(last_results)
        reply, session_id, history = chat_manager.handle_message(session_id, message)
    except Exception as exc:
        logger.exception("Chat endpoint failed.")
        return jsonify({"error": "Chat generation failed", "details": str(exc)}), 500

    return jsonify({"session_id": session_id, "reply": reply, "history": history})


# ── Batch ─────────────────────────────────────────────────────────────────────

@app.route("/api/batch/rephrase", methods=["POST"])
def batch_rephrase():
    data = request.json or {}
    texts = data.get("texts", [])
    if not texts or not isinstance(texts, list):
        return jsonify({"error": "Missing 'texts' array in request body"}), 400
    if len(texts) > MAX_BATCH_SIZE:
        return jsonify({"error": f"Batch exceeds maximum of {MAX_BATCH_SIZE} items"}), 413

    try:
        job_id = batch_processor.create_job("rephrase", texts)
        batch_processor.process_job(job_id, paraphrase)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("Batch rephrase failed.")
        return jsonify({"error": "Batch rephrase failed", "details": str(exc)}), 500

    return jsonify(batch_processor.get_job(job_id).to_dict())


@app.route("/api/batch/translate", methods=["POST"])
def batch_translate():
    data = request.json or {}
    texts = data.get("texts", [])
    language = (data.get("language") or "urdu").lower()

    if not texts or not isinstance(texts, list):
        return jsonify({"error": "Missing 'texts' array in request body"}), 400
    if len(texts) > MAX_BATCH_SIZE:
        return jsonify({"error": f"Batch exceeds maximum of {MAX_BATCH_SIZE} items"}), 413

    if language == "urdu":
        translate_func = translate_to_urdu
    elif language == "english":
        translate_func = translate_to_english
    else:
        return jsonify({"error": "Unsupported language. Use 'urdu' or 'english'"}), 400

    try:
        job_id = batch_processor.create_job("translate", texts, {"language": language})
        batch_processor.process_job(job_id, translate_func)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("Batch translate failed.")
        return jsonify({"error": "Batch translate failed", "details": str(exc)}), 500

    return jsonify(batch_processor.get_job(job_id).to_dict())


@app.route("/api/batch/status/<job_id>", methods=["GET"])
def batch_status(job_id):
    job = batch_processor.get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job.to_dict())


# ── TTS ───────────────────────────────────────────────────────────────────────

@app.route("/api/tts", methods=["POST"])
def tts_endpoint():
    data = request.json or {}
    text = str(data.get("text", "")).strip()
    language = str(data.get("language", "ur")).lower()

    if not text:
        return jsonify({"error": "Missing 'text' in request body"}), 400

    lang_map = {"urdu": "ur", "english": "en", "ur": "ur", "en": "en"}
    lang_code = lang_map.get(language, "ur")

    try:
        audio_path = text_to_speech(text, lang_code)
        return jsonify({"audio_url": f"/static/{audio_path}", "text": text, "language": lang_code})
    except Exception as exc:
        logger.exception("TTS endpoint failed.")
        return jsonify({"error": "TTS generation failed", "details": str(exc)}), 500


# ── Export (DEPRECATED) ──────────────────────────────────────────────────────────

# @app.route("/api/export/pdf", methods=["POST"])
# def export_pdf():
#     """
#     DEPRECATED: Frontend now handles PDF generation entirely client-side 
#     via jsPDF. This endpoint is commented out to prevent unauthorized access.
#     """
#     data = request.json or {}
#     original_text = str(data.get("original_text", "")).strip()
#     results = data.get("results", [])
#     result_type = data.get("result_type", "Paraphrased")
# 
#     if not original_text or not results:
#         return jsonify({"error": "Missing 'original_text' or 'results' in request body"}), 400
# 
#     try:
#         pdf_path = export_to_pdf(original_text, results, result_type)
#         return jsonify({"download_url": f"/static/{pdf_path}", "format": "pdf"})
#     except Exception as exc:
#         logger.exception("PDF export endpoint failed.")
#         return jsonify({"error": "PDF export failed", "details": str(exc)}), 500
# 
# 
# @app.route("/api/export/docx", methods=["POST"])
# def export_docx():
#     """
#     DEPRECATED: Frontend now handles DOCX generation entirely client-side.
#     This endpoint is commented out to prevent unauthorized access.
#     """
#     data = request.json or {}
#     original_text = str(data.get("original_text", "")).strip()
#     results = data.get("results", [])
#     result_type = data.get("result_type", "Paraphrased")
# 
#     if not original_text or not results:
#         return jsonify({"error": "Missing 'original_text' or 'results' in request body"}), 400
# 
#     try:
#         docx_path = export_to_docx(original_text, results, result_type)
#         return jsonify({"download_url": f"/static/{docx_path}", "format": "docx"})
#     except Exception as exc:
#         logger.exception("DOCX export endpoint failed.")
#         return jsonify({"error": "DOCX export failed", "details": str(exc)}), 500


# ── Static ────────────────────────────────────────────────────────────────────

@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)


# ── OCR ───────────────────────────────────────────────────────────────────────

def _read_ocr_image() -> tuple[bytes | None, tuple | None]:
    """
    Read and validate the uploaded image from the current request.
    Returns (image_data, None) on success, or (None, error_response) on failure.
    """
    if "image" not in request.files:
        return None, (jsonify({"error": "No image file provided"}), 400)
    file = request.files["image"]
    if not file.filename:
        return None, (jsonify({"error": "Empty filename"}), 400)

    image_data = file.read()
    if not validate_image(image_data):
        return None, (jsonify({"error": "Invalid or corrupted image file"}), 400)

    if request.form.get("preprocess", "false").lower() == "true":
        image_data = preprocess_image(image_data)

    return image_data, None


@app.route("/api/ocr", methods=["POST"])
def ocr_endpoint():
    image_data, err = _read_ocr_image()
    if err:
        return err

    language = request.form.get("language", "eng")
    try:
        extracted_text = extract_text_from_image(image_data, language)
        return jsonify({
            "extracted_text": extracted_text,
            "language": language,
            "preprocessed": request.form.get("preprocess", "false").lower() == "true",
        })
    except Exception as exc:
        logger.exception("OCR endpoint failed.")
        return jsonify({"error": "OCR failed", "details": str(exc)}), 500


@app.route("/api/ocr/languages", methods=["GET"])
def ocr_languages():
    return jsonify(get_supported_languages())


@app.route("/api/ocr-rephrase", methods=["POST"])
def ocr_rephrase():
    image_data, err = _read_ocr_image()
    if err:
        return err

    language = request.form.get("language", "eng")
    try:
        extracted_text = extract_text_from_image(image_data, language)
        rephrased_results = paraphrase(extracted_text)
        return jsonify({
            "original_text": extracted_text,
            "rephrased_results": rephrased_results,
            "ocr_language": language,
        })
    except Exception as exc:
        logger.exception("OCR-Rephrase endpoint failed.")
        return jsonify({"error": "OCR-Rephrase failed", "details": str(exc)}), 500


@app.route("/api/ocr-translate", methods=["POST"])
def ocr_translate():
    image_data, err = _read_ocr_image()
    if err:
        return err

    ocr_language    = request.form.get("ocr_language", "eng")
    target_language = request.form.get("target_language", "urdu").lower()

    try:
        extracted_text = extract_text_from_image(image_data, ocr_language)

        if target_language == "urdu":
            translated_text = translate_to_urdu(extracted_text)
        elif target_language == "english":
            translated_text = translate_to_english(extracted_text)
        else:
            return jsonify({"error": "Unsupported target language. Use 'urdu' or 'english'"}), 400

        return jsonify({
            "original_text":   extracted_text,
            "translated_text": translated_text,
            "ocr_language":    ocr_language,
            "target_language": target_language,
        })
    except Exception as exc:
        logger.exception("OCR-Translate endpoint failed.")
        return jsonify({"error": "OCR-Translate failed", "details": str(exc)}), 500


# ── PDF ───────────────────────────────────────────────────────────────────────

@app.route("/api/pdf/extract", methods=["POST"])
def pdf_extract():
    if "pdf" not in request.files:
        return jsonify({"error": "No pdf file provided"}), 400
    file = request.files["pdf"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "File must be a PDF"}), 400

    # mode determines chunk size: 'paraphrase' → 700 chars (fits T5's 256-token limit)
    #                             'translate'  → 1200 chars (fits NLLB's 512-token limit)
    mode = request.form.get("mode", "paraphrase").lower()
    if mode not in ("paraphrase", "translate"):
        mode = "paraphrase"

    pdf_bytes = file.read()
    try:
        chunks = extract_chunks_from_pdf(pdf_bytes, mode=mode)
        return jsonify({"chunks": chunks, "total_chunks": len(chunks), "mode": mode})
    except Exception as exc:
        logger.exception("PDF extraction failed.")
        return jsonify({"error": "PDF extraction failed", "details": str(exc)}), 500


# ── Async Document Processing ──────────────────────────────────────────────────

def background_document_processor(
    job_id: str,
    text: str,
    task_type: str,
    target_lang: str | None = None,
) -> None:
    """
    Background worker: chunk → parallel process → reassemble.

    Uses asyncio.gather (via process_chunks_parallel) to run all chunk
    inference calls concurrently, bounded by a semaphore in llm_wrapper.py
    to prevent OOM crashes.

    Args:
        job_id:      UUID string identifying this job in async_jobs_db.
        text:        Full input text (may be very long).
        task_type:   'paraphrase' or 'translate'.
        target_lang: Required when task_type == 'translate'.
    """
    async_jobs_db[job_id]["status"] = "processing"
    try:
        if task_type == "paraphrase":
            chunks = get_paraphrase_chunks(text)
        elif task_type == "translate":
            chunks = get_translation_chunks(text)
        else:
            chunks = get_semantic_chunks(text)
            
        logger.info("Job %s divided into %d chunk(s).", job_id, len(chunks))

        # asyncio.run() creates a fresh event loop in this background thread.
        # process_chunks_parallel uses asyncio.gather internally.
        final_text = asyncio.run(process_chunks_parallel(chunks, task_type, target_lang))

        async_jobs_db[job_id]["status"] = "completed"
        async_jobs_db[job_id]["result"] = final_text
        logger.info("Job %s completed successfully.", job_id)
    except Exception as exc:
        logger.exception("Job %s failed.", job_id)
        async_jobs_db[job_id]["status"] = "failed"
        async_jobs_db[job_id]["error"] = str(exc)


def _start_async_job(text: str, task_type: str, target_lang: str | None = None) -> str:
    """Create an async job record and submit to thread pool. Returns job_id."""
    job_id = str(uuid.uuid4())
    async_jobs_db[job_id] = {"status": "pending", "result": None, "error": None}
    executor.submit(
        background_document_processor,
        job_id, text, task_type, target_lang
    )
    return job_id


@app.route("/api/async/rephrase", methods=["POST"])
def async_rephrase():
    data = request.json or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"error": "Missing 'text' in request body"}), 400

    job_id = _start_async_job(text, "paraphrase")
    return jsonify({"job_id": job_id, "status": "pending", "message": "Paraphrase job initiated."})


@app.route("/api/async/translate", methods=["POST"])
def async_translate():
    data = request.json or {}
    text = str(data.get("text", "")).strip()
    language = str(data.get("language", "urdu")).strip().lower()
    if not text:
        return jsonify({"error": "Missing 'text' in request body"}), 400
    if language not in ("urdu", "english"):
        return jsonify({"error": "Unsupported language. Use 'urdu' or 'english'"}), 400

    job_id = _start_async_job(text, "translate", language)
    return jsonify({"job_id": job_id, "status": "pending", "message": f"Translation to {language} job initiated."})


@app.route("/api/async/pdf/rephrase", methods=["POST"])
def async_pdf_rephrase():
    """
    Accept a PDF upload, extract full text, and enqueue an async paraphrase job.

    FIX (Issue 3): Previously there was no dedicated PDF→async pipeline.  Large PDFs
    passed through /api/rephrase would hit the MAX_TEXT_LENGTH=1000 char limit and
    be rejected.  This endpoint extracts the full document text and routes it through
    background_document_processor which chunks and processes it in parallel.
    """
    if "pdf" not in request.files:
        return jsonify({"error": "No pdf file provided"}), 400
    file = request.files["pdf"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "File must be a PDF"}), 400

    try:
        full_text = extract_text_from_pdf(file.read())
    except Exception as exc:
        logger.exception("PDF text extraction failed.")
        return jsonify({"error": "PDF extraction failed", "details": str(exc)}), 500

    job_id = _start_async_job(full_text, "paraphrase")
    return jsonify({
        "job_id": job_id,
        "status": "pending",
        "message": "PDF paraphrase job initiated. Poll /api/async/status/<job_id> for progress.",
        "char_count": len(full_text),
    })


@app.route("/api/async/pdf/translate", methods=["POST"])
def async_pdf_translate():
    """
    Accept a PDF upload, extract full text, and enqueue an async translation job.

    FIX (Issue 3): Core fix for the PDF truncation bug.  The text is extracted in
    full (no character limit), then chunked inside background_document_processor
    using RecursiveCharacterTextSplitter (1500 char / 150 overlap), and each chunk
    is translated independently via asyncio.gather.  The results are reassembled
    in order before being stored in async_jobs_db[job_id]['result'].
    """
    if "pdf" not in request.files:
        return jsonify({"error": "No pdf file provided"}), 400
    file = request.files["pdf"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "File must be a PDF"}), 400

    language = request.form.get("language", "urdu").lower()
    if language not in ("urdu", "english"):
        return jsonify({"error": "Unsupported language. Use 'urdu' or 'english'"}), 400

    try:
        full_text = extract_text_from_pdf(file.read())
    except Exception as exc:
        logger.exception("PDF text extraction failed.")
        return jsonify({"error": "PDF extraction failed", "details": str(exc)}), 500

    job_id = _start_async_job(full_text, "translate", language)
    return jsonify({
        "job_id": job_id,
        "status": "pending",
        "message": f"PDF translation to {language} job initiated. Poll /api/async/status/<job_id>.",
        "char_count": len(full_text),
    })


@app.route("/api/async/status/<job_id>", methods=["GET"])
def get_job_status(job_id):
    job = async_jobs_db.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({"job_id": job_id, **job})


# ── Admin / Dev Utilities ─────────────────────────────────────────────────────

@app.route("/admin/reload-models", methods=["POST"])
@require_admin
def admin_reload_models(current_user_id):
    """
    Force-evict the in-process model cache so the next request reloads from disk.

    FIX (Issue 1 — Phantom Changes): Without this endpoint, the only way to pick up
    hyperparameter changes (made to config.py) is a full server restart.  Calling
    this endpoint resets both model globals to None so the next inference call
    re-invokes _load_paraphrase_resources() / _load_model_resources(), which read
    the current config values.

    NOTE: This does NOT clear __pycache__.  A server restart is still required if
    you changed Python source files (as opposed to just swapping model weights).
    """
    force_reload_paraphrase_model()
    force_reload_translation_model()
    return jsonify({"status": "ok", "message": "Model caches cleared. Next request will reload."})


# ── Auth (v3.0) ──────────────────────────────────────────────────────────────

@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    try:
        body = RegisterRequest(**(request.json or {}))
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "details": exc.errors()}), 400

    try:
        user, token = register_user(body.name, body.email, body.password)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 409

    return jsonify({"user": user, "token": token}), 201


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    try:
        body = LoginRequest(**(request.json or {}))
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "details": exc.errors()}), 400

    try:
        user, token = login_user(body.email, body.password)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 401

    return jsonify({"user": user, "token": token})


# ── User Profile (v3.0) ──────────────────────────────────────────────────────

@app.route("/api/user/profile", methods=["GET"])
@require_auth
def get_profile(current_user_id):
    user = get_user(current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)


@app.route("/api/user/profile", methods=["PUT"])
@require_auth
def update_profile(current_user_id):
    try:
        body = ProfileUpdateRequest(**(request.json or {}))
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "details": exc.errors()}), 400

    try:
        from datetime import datetime, timezone
        updated = update_user(
            current_user_id,
            name=body.name,
            email=body.email,
            password=body.password,
        )
        updated["updated_at"] = datetime.now(timezone.utc).isoformat()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(updated)


# ── Grammar (v3.0) ───────────────────────────────────────────────────────────

@app.route("/api/grammar", methods=["POST"])
def grammar_endpoint():
    try:
        body = GrammarCheckRequest(**(request.json or {}))
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "details": exc.errors()}), 400

    if len(body.text) > MAX_TEXT_LENGTH:
        return jsonify({"error": f"'text' exceeds maximum length of {MAX_TEXT_LENGTH} characters"}), 413

    try:
        result = check_grammar(body.text)
    except Exception as exc:
        logger.exception("Grammar check endpoint failed.")
        return jsonify({"error": "Grammar check failed", "details": str(exc)}), 500

    return jsonify(result)


# ── History (v3.0) ────────────────────────────────────────────────────────────

@app.route("/api/history", methods=["GET"])
@require_auth
def get_history(current_user_id):
    search = request.args.get("search")
    activity_type = request.args.get("type")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))

    items, total = list_history(current_user_id, search, activity_type, page, limit)

    return jsonify({
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    })


@app.route("/api/history/<item_id>", methods=["DELETE"])
@require_auth
def delete_history(current_user_id, item_id):
    deleted = delete_history_item(current_user_id, item_id)
    if not deleted:
        return jsonify({"error": "History item not found"}), 404
    return jsonify({"deleted": True, "id": item_id})


# ── Stats (v3.0) ──────────────────────────────────────────────────────────────

@app.route("/api/stats", methods=["GET"])
@require_auth
def stats_endpoint(current_user_id):
    stats = get_stats(current_user_id)
    return jsonify(stats)


# ── Preferences (v3.0) ───────────────────────────────────────────────────────

@app.route("/api/user/preferences", methods=["PUT"])
@require_auth
def save_preferences(current_user_id):
    try:
        body = PreferencesRequest(**(request.json or {}))
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "details": exc.errors()}), 400

    try:
        from datetime import datetime, timezone
        prefs = update_preferences(current_user_id, body.notifications, body.dark_mode)
        prefs["updated_at"] = datetime.now(timezone.utc).isoformat()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(prefs)


# ── Startup cleanup ───────────────────────────────────────────────────────────

def _run_startup_cleanup() -> None:
    """Delete old static files left from previous runs."""
    deleted_audio   = cleanup_old_audio_files(STATIC_CLEANUP_HOURS)
    deleted_exports = cleanup_old_exports(STATIC_CLEANUP_HOURS)
    logger.info(
        "Startup cleanup: removed %d audio file(s), %d export file(s).",
        deleted_audio, deleted_exports,
    )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _run_startup_cleanup()
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, port=PORT)

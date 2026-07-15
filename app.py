"""
app.py — Main Flask application for Rephrasia AI Text Processing API.

Endpoints:
  GET  /                         → Serve the frontend (templates/index.html)
  POST /api/rephrase              → Paraphrase text
  POST /api/translate             → Translate text (EN↔UR)
  POST /chat                     → Chat with DialoGPT
  POST /api/batch/rephrase        → Bulk paraphrase
  POST /api/batch/translate       → Bulk translate
  GET  /api/batch/status/<job_id> → Batch job status
  POST /api/tts                  → Text-to-speech
  POST /api/export/pdf            → Export to PDF
  POST /api/export/docx           → Export to DOCX
  POST /api/ocr                  → Image → text
  GET  /api/ocr/languages         → Supported OCR languages
  POST /api/ocr-rephrase          → OCR + paraphrase
  POST /api/ocr-translate         → OCR + translate
"""

import logging
import os

from flask import Flask, jsonify, render_template, request, send_from_directory

from batch_processor import batch_processor
from chat import chat_manager
from config import MAX_TEXT_LENGTH, MAX_BATCH_SIZE, MAX_UPLOAD_MB, PORT, STATIC_CLEANUP_HOURS
from export_utils import cleanup_old_exports, export_to_docx, export_to_pdf
from model import paraphrase
from ocr import extract_text_from_image, get_supported_languages, preprocess_image, validate_image
from pdf_parser import extract_chunks_from_pdf
from translation import translate_to_english, translate_to_urdu
from tts import cleanup_old_audio_files, text_to_speech

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

# Global store for last processed outputs (used by chatbot for definition queries)
last_results: dict = {
    "rephrase":  [],
    "translate": "",
}


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

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# ── Core API ──────────────────────────────────────────────────────────────────

@app.route("/api/rephrase", methods=["POST"])
def rephrase():
    text, err = _require_json_text(request.json)
    if err:
        return err

    try:
        rephrased_sentences = paraphrase(text)
        last_results["rephrase"] = rephrased_sentences
    except Exception as exc:
        logger.exception("Paraphrasing endpoint failed.")
        return jsonify({"error": "Paraphrasing failed", "details": str(exc)}), 500

    return jsonify({"rephrased_results": rephrased_sentences})


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


# ── Export ────────────────────────────────────────────────────────────────────

@app.route("/api/export/pdf", methods=["POST"])
def export_pdf():
    data = request.json or {}
    original_text = str(data.get("original_text", "")).strip()
    results = data.get("results", [])
    result_type = data.get("result_type", "Paraphrased")

    if not original_text or not results:
        return jsonify({"error": "Missing 'original_text' or 'results' in request body"}), 400

    try:
        pdf_path = export_to_pdf(original_text, results, result_type)
        return jsonify({"download_url": f"/static/{pdf_path}", "format": "pdf"})
    except Exception as exc:
        logger.exception("PDF export endpoint failed.")
        return jsonify({"error": "PDF export failed", "details": str(exc)}), 500


@app.route("/api/export/docx", methods=["POST"])
def export_docx():
    data = request.json or {}
    original_text = str(data.get("original_text", "")).strip()
    results = data.get("results", [])
    result_type = data.get("result_type", "Paraphrased")

    if not original_text or not results:
        return jsonify({"error": "Missing 'original_text' or 'results' in request body"}), 400

    try:
        docx_path = export_to_docx(original_text, results, result_type)
        return jsonify({"download_url": f"/static/{docx_path}", "format": "docx"})
    except Exception as exc:
        logger.exception("DOCX export endpoint failed.")
        return jsonify({"error": "DOCX export failed", "details": str(exc)}), 500


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

    pdf_bytes = file.read()
    try:
        chunks = extract_chunks_from_pdf(pdf_bytes)
        return jsonify({"chunks": chunks, "total_chunks": len(chunks)})
    except Exception as exc:
        logger.exception("PDF extraction failed.")
        return jsonify({"error": "PDF extraction failed", "details": str(exc)}), 500


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

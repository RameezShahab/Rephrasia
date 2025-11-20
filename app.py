from flask import Flask, request, jsonify, send_from_directory, render_template

# 1. Import your 'paraphrase' function from model.py
from model import paraphrase

# 2. Import translation helpers and chatbot manager
from translation import translate_to_urdu, translate_to_english
from chat import chat_manager

# 3. Import new features
from batch_processor import batch_processor
from tts import text_to_speech
from export_utils import export_to_pdf, export_to_docx
from ocr import extract_text_from_image, validate_image, preprocess_image, get_supported_languages

app = Flask(__name__)

# Configure max upload size (16MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# 🚀 --- ROOT ROUTE FIX ---
@app.route('/', methods=['GET'])
def index():
    """Returns a simple status message for health check or serves the main frontend page."""
    # If your Hugging Face Space uses a simple API backend, a JSON response is fine.
    # If it expects a UI, you would uncomment the line below and ensure index.html exists:
    # return render_template('index.html') 
    
    return jsonify({
        "status": "ok", 
        "service": "Rephrasia App API is running", 
        "message": "Access API endpoints via /api/* or /chat."
    }), 200
# -------------------------

# --- Core API Endpoints ---

@app.route('/api/rephrase', methods=['POST'])
def rephrase():
    data = request.json
    if 'text' not in data:
        return jsonify({"error": "Missing 'text' in request body"}), 400
    
    input_text = data['text']
    try:
        rephrased_sentences = paraphrase(input_text)
    except Exception as exc:
        return jsonify({"error": "Paraphrasing failed", "details": str(exc)}), 500

    return jsonify({"rephrased_results": rephrased_sentences})

@app.route('/api/translate', methods=['POST'])
def translate():
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"error": "Missing 'text' in request body"}), 400
    
    input_text = data['text']
    language = data.get('language', 'urdu')  # Default to Urdu translation

    try:
        # Call the appropriate translation function based on target language
        if language.lower() == 'urdu':
            translated_text = translate_to_urdu(input_text)
        elif language.lower() == 'english':
            translated_text = translate_to_english(input_text)
        else:
            return jsonify({"error": "Unsupported language. Use 'urdu' or 'english'"}), 400
    except Exception as exc:
        return jsonify({"error": "Translation failed", "details": str(exc)}), 500

    # Return the real result
    return jsonify({"translated_text": translated_text})

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    data = request.json or {}
    message = data.get('text')
    session_id = data.get('session_id')

    if not message:
        return jsonify({"error": "Missing 'text' in request body"}), 400

    try:
        reply, session_id, history = chat_manager.handle_message(session_id, message)
    except Exception as exc:
        return jsonify({"error": "Chat generation failed", "details": str(exc)}), 500

    return jsonify({
        "session_id": session_id,
        "reply": reply,
        "history": history
    })

# --- Batch Processing Endpoints ---

@app.route('/api/batch/rephrase', methods=['POST'])
def batch_rephrase():
    data = request.json or {}
    texts = data.get('texts', [])
    
    if not texts or not isinstance(texts, list):
        return jsonify({"error": "Missing 'texts' array in request body"}), 400
    
    # Create batch job
    job_id = batch_processor.create_job("rephrase", texts)
    
    # Process synchronously for now
    batch_processor.process_job(job_id, paraphrase)
    
    job = batch_processor.get_job(job_id)
    return jsonify(job.to_dict())

@app.route('/api/batch/translate', methods=['POST'])
def batch_translate():
    data = request.json or {}
    texts = data.get('texts', [])
    language = data.get('language', 'urdu')
    
    if not texts or not isinstance(texts, list):
        return jsonify({"error": "Missing 'texts' array in request body"}), 400
    
    # Select translation function
    if language.lower() == 'urdu':
        translate_func = translate_to_urdu
    elif language.lower() == 'english':
        translate_func = translate_to_english
    else:
        return jsonify({"error": "Unsupported language. Use 'urdu' or 'english'"}), 400
    
    # Create and process batch job
    job_id = batch_processor.create_job("translate", texts, {"language": language})
    batch_processor.process_job(job_id, translate_func)
    
    job = batch_processor.get_job(job_id)
    return jsonify(job.to_dict())

@app.route('/api/batch/status/<job_id>', methods=['GET'])
def batch_status(job_id):
    job = batch_processor.get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    return jsonify(job.to_dict())

# --- Text-to-Speech Endpoints ---

@app.route('/api/tts', methods=['POST'])
def tts_endpoint():
    data = request.json or {}
    text = data.get('text')
    language = data.get('language', 'ur')  # Default to Urdu
    
    if not text:
        return jsonify({"error": "Missing 'text' in request body"}), 400
    
    # Map language names to codes
    lang_map = {
        'urdu': 'ur',
        'english': 'en',
        'ur': 'ur',
        'en': 'en'
    }
    
    lang_code = lang_map.get(language.lower(), 'ur')
    
    try:
        audio_path = text_to_speech(text, lang_code)
        return jsonify({
            "audio_url": f"/static/{audio_path}",
            "text": text,
            "language": lang_code
        })
    except Exception as exc:
        return jsonify({"error": "TTS generation failed", "details": str(exc)}), 500

# --- Export Endpoints ---

@app.route('/api/export/pdf', methods=['POST'])
def export_pdf():
    data = request.json or {}
    original_text = data.get('original_text', '')
    results = data.get('results', [])
    result_type = data.get('result_type', 'Paraphrased')
    
    if not original_text or not results:
        return jsonify({"error": "Missing 'original_text' or 'results' in request body"}), 400
    
    try:
        pdf_path = export_to_pdf(original_text, results, result_type)
        return jsonify({
            "download_url": f"/static/{pdf_path}",
            "format": "pdf"
        })
    except Exception as exc:
        return jsonify({"error": "PDF export failed", "details": str(exc)}), 500

@app.route('/api/export/docx', methods=['POST'])
def export_docx():
    data = request.json or {}
    original_text = data.get('original_text', '')
    results = data.get('results', [])
    result_type = data.get('result_type', 'Paraphrased')
    
    if not original_text or not results:
        return jsonify({"error": "Missing 'original_text' or 'results' in request body"}), 400
    
    try:
        docx_path = export_to_docx(original_text, results, result_type)
        return jsonify({
            "download_url": f"/static/{docx_path}",
            "format": "docx"
        })
    except Exception as exc:
        return jsonify({"error": "DOCX export failed", "details": str(exc)}), 500

# --- Static File Serving ---

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# --- OCR (Image to Text) Endpoints ---

@app.route('/api/ocr', methods=['POST'])
def ocr_endpoint():
    """Extract text from uploaded image."""
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    
    # Get optional language parameter
    language = request.form.get('language', 'eng')
    preprocess = request.form.get('preprocess', 'false').lower() == 'true'
    
    try:
        # Read image data
        image_data = file.read()
        
        # Validate image
        if not validate_image(image_data):
            return jsonify({"error": "Invalid image file"}), 400
        
        # Preprocess if requested
        if preprocess:
            image_data = preprocess_image(image_data)
        
        # Extract text
        extracted_text = extract_text_from_image(image_data, language)
        
        return jsonify({
            "extracted_text": extracted_text,
            "language": language,
            "preprocessed": preprocess
        })
    
    except Exception as exc:
        return jsonify({"error": "OCR failed", "details": str(exc)}), 500

@app.route('/api/ocr/languages', methods=['GET'])
def ocr_languages():
    """Get supported OCR languages."""
    return jsonify(get_supported_languages())

@app.route('/api/ocr-rephrase', methods=['POST'])
def ocr_rephrase():
    """Extract text from image and rephrase it."""
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    language = request.form.get('language', 'eng')
    preprocess = request.form.get('preprocess', 'false').lower() == 'true'
    
    try:
        # Extract text from image
        image_data = file.read()
        
        if not validate_image(image_data):
            return jsonify({"error": "Invalid image file"}), 400
        
        if preprocess:
            image_data = preprocess_image(image_data)
        
        extracted_text = extract_text_from_image(image_data, language)
        
        # Rephrase the extracted text
        rephrased_results = paraphrase(extracted_text)
        
        return jsonify({
            "original_text": extracted_text,
            "rephrased_results": rephrased_results,
            "ocr_language": language
        })
    
    except Exception as exc:
        return jsonify({"error": "OCR-Rephrase failed", "details": str(exc)}), 500

@app.route('/api/ocr-translate', methods=['POST'])
def ocr_translate():
    """Extract text from image and translate it."""
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    ocr_language = request.form.get('ocr_language', 'eng')
    target_language = request.form.get('target_language', 'urdu')
    preprocess = request.form.get('preprocess', 'false').lower() == 'true'
    
    try:
        # Extract text from image
        image_data = file.read()
        
        if not validate_image(image_data):
            return jsonify({"error": "Invalid image file"}), 400
        
        if preprocess:
            image_data = preprocess_image(image_data)
        
        extracted_text = extract_text_from_image(image_data, ocr_language)
        
        # Translate the extracted text
        if target_language.lower() == 'urdu':
            translated_text = translate_to_urdu(extracted_text)
        elif target_language.lower() == 'english':
            translated_text = translate_to_english(extracted_text)
        else:
            return jsonify({"error": "Unsupported target language"}), 400
        
        return jsonify({
            "original_text": extracted_text,
            "translated_text": translated_text,
            "ocr_language": ocr_language,
            "target_language": target_language
        })
    
    except Exception as exc:
        return jsonify({"error": "OCR-Translate failed", "details": str(exc)}), 500

if __name__ == '__main__':
    app.run(debug=True)
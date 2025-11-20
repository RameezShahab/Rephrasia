from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# --- Model Definitions ---
# Using separate, small MarianMT models to guarantee stability and avoid memory crashes.
EN_UR_MODEL_NAME = "Helsinki-NLP/opus-mt-en-ur"
UR_EN_MODEL_NAME = "Helsinki-NLP/opus-mt-ur-en"

# Lazy-loading variables for EN-UR model
_en_ur_tokenizer = None
_en_ur_model = None

# Lazy-loading variables for UR-EN model
_ur_en_tokenizer = None
_ur_en_model = None

# --- Resource Loading Functions ---

def _load_en_ur_resources():
    """Loads the English-to-Urdu MarianMT model."""
    global _en_ur_tokenizer, _en_ur_model
    if _en_ur_tokenizer is None or _en_ur_model is None:
        _en_ur_tokenizer = AutoTokenizer.from_pretrained(EN_UR_MODEL_NAME)
        _en_ur_model = AutoModelForSeq2SeqLM.from_pretrained(EN_UR_MODEL_NAME)
    return _en_ur_tokenizer, _en_ur_model

def _load_ur_en_resources():
    """Loads the Urdu-to-English MarianMT model."""
    global _ur_en_tokenizer, _ur_en_model
    if _ur_en_tokenizer is None or _ur_en_model is None:
        _ur_en_tokenizer = AutoTokenizer.from_pretrained(UR_EN_MODEL_NAME)
        _ur_en_model = AutoModelForSeq2SeqLM.from_pretrained(UR_EN_MODEL_NAME)
    return _ur_en_tokenizer, _ur_en_model

# --- Translation Functions ---

def translate_to_urdu(text):
    """Translates English text to Urdu."""
    tokenizer, model = _load_en_ur_resources()

    try:
        # MarianMT requires the target language token to start the generation
        # We use '>>ur<<' as the start token for this model pair.
        TGT_LANG_TOKEN = '>>ur<<' 
        
        input_ids = tokenizer.encode(text, return_tensors='pt')
        
        generated_tokens = model.generate(
            input_ids,
            # CRITICAL FIX: Use the specific language token ID for MarianMT
            decoder_start_token_id=tokenizer.lang_code_to_id[TGT_LANG_TOKEN],
            num_beams=5,
            max_length=128
        )

        return tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]

    except Exception as exc:
        raise RuntimeError("Translation to Urdu failed (MarianMT Final)") from exc

def translate_to_english(text):
    """Translates Urdu text to English."""
    tokenizer, model = _load_ur_en_resources()

    try:
        # MarianMT requires the target language token to start the generation
        # We use '>>en<<' as the start token for this reverse model pair.
        TGT_LANG_TOKEN = '>>en<<'
        
        input_ids = tokenizer.encode(text, return_tensors='pt')

        generated_tokens = model.generate(
            input_ids,
            # CRITICAL FIX: Use the specific language token ID for MarianMT
            decoder_start_token_id=tokenizer.lang_code_to_id[TGT_LANG_TOKEN],
            num_beams=5,
            max_length=128
        )

        return tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]

    except Exception as exc:
        raise RuntimeError("Translation to English failed (MarianMT Final)") from exc

# --- Example Usage ---
if __name__ == "__main__":
    # Test English to Urdu
    input_text_en = "This is a final test of the translation API."
    translated_text_ur = translate_to_urdu(input_text_en)
    
    print(f"Original (English): {input_text_en}")
    print(f"Translated (Urdu): {translated_text_ur}")
    
    # Test Urdu to English translation
    input_text_ur = "یہ ایپلیکیشن کامیابی سے چل رہی ہے۔"
    translated_text_en = translate_to_english(input_text_ur)
    print(f"\nOriginal (Urdu): {input_text_ur}")
    print(f"Translated back (English): {translated_text_en}")
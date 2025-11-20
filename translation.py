from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# --- Model Definition ---
# Using NLLB-200 Distilled (600M) for high-quality, natural translations.
# This single model handles both English (eng_Latn) and Urdu (urd_Arab).
MODEL_NAME = "facebook/nllb-200-distilled-600M"

_tokenizer = None
_model = None

def _load_model_resources():
    """Loads the NLLB tokenizer and model (cached)."""
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        print(f"Loading translation model: {MODEL_NAME}...")
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return _tokenizer, _model

def translate_to_urdu(text):
    """Translates English text to Urdu."""
    tokenizer, model = _load_model_resources()

    try:
        # 1. Set the source language to English
        tokenizer.src_lang = "eng_Latn"
        
        # 2. Prepare inputs
        inputs = tokenizer(text, return_tensors="pt")

        # 3. Generate output with target language forced to Urdu
        generated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.lang_code_to_id["urd_Arab"],
            max_length=128,
            num_beams=5
        )

        # 4. Decode result
        return tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]

    except Exception as exc:
        raise RuntimeError(f"NLLB Translation to Urdu failed: {str(exc)}")

def translate_to_english(text):
    """Translates Urdu text to English."""
    tokenizer, model = _load_model_resources()

    try:
        # 1. Set the source language to Urdu
        tokenizer.src_lang = "urd_Arab"
        
        # 2. Prepare inputs
        inputs = tokenizer(text, return_tensors="pt")

        # 3. Generate output with target language forced to English
        generated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.lang_code_to_id["eng_Latn"],
            max_length=128,
            num_beams=5
        )

        # 4. Decode result
        return tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]

    except Exception as exc:
        raise RuntimeError(f"NLLB Translation to English failed: {str(exc)}")

# --- Test Logic (Runs only if you execute this file directly) ---
if __name__ == "__main__":
    print("--- Testing NLLB Model ---")
    sample_text = "The quick brown fox jumps over the lazy dog."
    print(f"Original: {sample_text}")
    
    urdu_text = translate_to_urdu(sample_text)
    print(f"Urdu: {urdu_text}")
    
    english_text = translate_to_english(urdu_text)
    print(f"Back to English: {english_text}")
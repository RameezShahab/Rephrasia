from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# --- Model Definition ---
# Using NLLB-200 Distilled (600M)
MODEL_NAME = "facebook/nllb-200-distilled-600M"

_tokenizer = None
_model = None

def _load_model_resources():
    """Loads the NLLB tokenizer and model."""
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

        # 3. Get the token ID for Urdu
        # FIX: Use convert_tokens_to_ids instead of lang_code_to_id
        target_lang_id = tokenizer.convert_tokens_to_ids("urd_Arab")

        # 4. Generate output
        generated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=target_lang_id,
            max_length=128,
            num_beams=5
        )

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

        # 3. Get the token ID for English
        # FIX: Use convert_tokens_to_ids instead of lang_code_to_id
        target_lang_id = tokenizer.convert_tokens_to_ids("eng_Latn")

        # 4. Generate output
        generated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=target_lang_id,
            max_length=128,
            num_beams=5
        )

        return tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]

    except Exception as exc:
        raise RuntimeError(f"NLLB Translation to English failed: {str(exc)}")
from transformers import PegasusTokenizer, PegasusForConditionalGeneration

# 1. Lazy-load the PEGASUS paraphrasing model so imports stay quick
model_name = "tuner007/pegasus_paraphrase"
_tokenizer = None
_model = None


def _load_paraphrase_resources():
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        _tokenizer = PegasusTokenizer.from_pretrained(model_name)
        _model = PegasusForConditionalGeneration.from_pretrained(model_name)
    return _tokenizer, _model

def paraphrase(text):
    # 4. No prefix is needed for this model
    tokenizer, model = _load_paraphrase_resources()

    try:
        input_ids = tokenizer.encode(text, return_tensors='pt', truncation=True)

        # 5. Generate multiple (e.g., 3) paraphrases
        outputs = model.generate(
            input_ids=input_ids,
            num_beams=5,
            num_return_sequences=3,  # Generate 3 different options
            max_length=128
        )

        # 6. Decode the list of output sequences
        return [tokenizer.decode(output, skip_special_tokens=True) for output in outputs]

    except Exception as exc:
        raise RuntimeError("Paraphrasing failed") from exc

# 7. A better example sentence to test academic paraphrasing
if __name__ == "__main__":
    input_text = "The study investigates the correlation between socioeconomic status and academic achievement."
    paraphrased_sentences = paraphrase(input_text)

    print(f"Original sentence: {input_text}")
    print("\nParaphrased sentences:")
    for i, sentence in enumerate(paraphrased_sentences):
        print(f"{i+1}. {sentence}")
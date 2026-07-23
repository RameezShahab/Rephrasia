import pytest
from chunking import get_semantic_chunks, get_paraphrase_chunks, get_translation_chunks

def test_semantic_chunks():
    text = "This is sentence one. This is sentence two! And three?"
    chunks = get_semantic_chunks(text, chunk_size=20, chunk_overlap=5)
    # The exact output depends on LangChain's RecursiveCharacterTextSplitter logic.
    assert len(chunks) > 0
    assert type(chunks) == list

def test_paraphrase_chunks():
    # Paraphrase has a max length of 700
    text = "A" * 800
    chunks = get_paraphrase_chunks(text)
    assert len(chunks) > 1
    assert all(len(c) <= 700 for c in chunks)

def test_translation_chunks():
    # Translation has a max length of 1200
    text = "B" * 1300
    chunks = get_translation_chunks(text)
    assert len(chunks) > 1
    assert all(len(c) <= 1200 for c in chunks)

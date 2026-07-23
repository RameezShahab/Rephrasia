import pytest

def test_grammar_happy_path(client, mocker):
    mocker.patch("app.check_grammar", return_value={"errors": []})
    response = client.post("/api/grammar", json={"text": "This is a correct sentence."})
    assert response.status_code == 200
    assert response.get_json()["errors"] == []

def test_grammar_sad_path_missing_text(client):
    response = client.post("/api/grammar", json={})
    assert response.status_code == 400
    assert "Validation failed" in response.get_json()["error"]

def test_grammar_edge_path_too_long(client):
    # MAX_TEXT_LENGTH is 100000 in config.py usually, let's trigger it
    text = "A" * 100001
    response = client.post("/api/grammar", json={"text": text})
    assert response.status_code == 413
    assert "exceeds maximum length" in response.get_json()["error"]

def test_rephrase_happy_path(client, mocker):
    mocker.patch("app.paraphrase", return_value=["This is paraphrased."])
    response = client.post("/api/rephrase", json={"text": "This is a test."})
    assert response.status_code == 200
    data = response.get_json()
    assert "rephrased_results" in data
    assert data["rephrased_results"] == ["This is paraphrased."]

def test_translate_happy_path(client, mocker):
    mocker.patch("app.translate_to_urdu", return_value="یہ ایک ٹیسٹ ہے۔")
    response = client.post("/api/translate", json={"text": "This is a test.", "language": "urdu"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["translated_text"] == "یہ ایک ٹیسٹ ہے۔"

def test_chat_happy_path(client, mocker):
    mocker.patch("app.chat_manager.handle_message", return_value=("Hello there!", "session-123", [{"role": "bot", "content": "Hello there!"}]))
    mocker.patch("app.chat_manager.update_context")
    response = client.post("/chat", json={"text": "Hi", "session_id": "session-123"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["reply"] == "Hello there!"

def test_batch_rephrase_happy_path(client, mocker):
    mocker.patch("app.paraphrase", return_value=["Batch rephrased."])
    response = client.post("/api/batch/rephrase", json={"texts": ["T1", "T2"]})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] in ["pending", "processing", "completed"]

def test_async_rephrase_happy_path(client, mocker):
    # _start_async_job pushes to a thread pool which calls background_document_processor
    # We can mock the background_document_processor so it doesn't actually run,
    # or just let it run but mock the chunk process.
    # To keep it isolated, let's just assert the endpoint returns 200.
    response = client.post("/api/async/rephrase", json={"text": "Long text"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "pending"
    assert "job_id" in data

import pytest
import io

def test_ocr_missing_image(client):
    response = client.post("/api/ocr", data={})
    assert response.status_code == 400
    assert "No image file provided" in response.get_json()["error"]

def test_ocr_invalid_image(client):
    data = {
        "image": (io.BytesIO(b"not an image"), "test.txt")
    }
    response = client.post("/api/ocr", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    assert "Invalid or corrupted image file" in response.get_json()["error"]

def test_pdf_extract_missing_file(client):
    response = client.post("/api/pdf/extract", data={})
    assert response.status_code == 400
    assert "No pdf file provided" in response.get_json()["error"]

def test_pdf_extract_invalid_file(client):
    data = {
        "pdf": (io.BytesIO(b"not a pdf"), "test.txt")
    }
    response = client.post("/api/pdf/extract", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    assert "File must be a PDF" in response.get_json()["error"]

import pytest
import jwt
from auth import JWT_SECRET, JWT_ALGORITHM

def test_register_happy_path(client):
    response = client.post("/api/auth/register", json={
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "strongpassword"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert "user" in data
    assert "token" in data
    assert data["user"]["email"] == "jane@example.com"
    assert "password_hash" not in data["user"]

def test_register_sad_path_duplicate(client):
    payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "strongpassword"
    }
    client.post("/api/auth/register", json=payload)
    # Try again
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    assert "Email already registered" in response.get_json()["error"]

def test_register_edge_case_missing_fields(client):
    response = client.post("/api/auth/register", json={
        "name": "Jane Doe"
    })
    assert response.status_code == 400
    assert "Validation failed" in response.get_json()["error"]

def test_login_happy_path(client, test_user):
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "token" in data
    assert data["user"]["email"] == "test@example.com"

def test_login_sad_path_invalid_creds(client, test_user):
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_jwt_validation_protected_route(client, test_user):
    token = test_user["token"]
    response = client.get("/api/user/profile", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    assert response.get_json()["email"] == "test@example.com"

def test_jwt_validation_missing_token(client):
    response = client.get("/api/user/profile")
    assert response.status_code == 401

def test_jwt_validation_invalid_token(client):
    response = client.get("/api/user/profile", headers={
        "Authorization": "Bearer invalid.token.here"
    })
    assert response.status_code == 401

def test_jwt_validation_expired_token(client, test_user, mocker):
    token = test_user["token"]
    # Mock jwt.decode to raise ExpiredSignatureError
    mocker.patch("auth.jwt.decode", side_effect=jwt.ExpiredSignatureError)
    
    response = client.get("/api/user/profile", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 401

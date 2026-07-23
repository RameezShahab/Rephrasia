import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from app import app as flask_app
import auth
import history_store

@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
    })
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def clean_in_memory_dbs():
    """Clear the mock in-memory DBs before each test to ensure isolation."""
    auth._users_db.clear()
    history_store._history_db.clear()
    history_store._stats = {
        "words_generated": 0,
        "documents_created": 0,
        "ai_requests": 0,
    }
    yield

@pytest.fixture
def test_user(client):
    """Helper fixture to create and return a valid test user with token."""
    user, token = auth.register_user("Test User", "test@example.com", "password123")
    return {"user": user, "token": token}

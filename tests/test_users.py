import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture
def mock_users_db(mocker):
    """Mocks the database query utilities for the users route."""
    return mocker.patch("api.routes.users.get_or_create_user")

def test_get_or_create_user_success(mock_users_db):
    """Tests successful retrieval or creation of a user profile."""
    # Simulate database returning a valid generated user ID
    mock_users_db.return_value = 101

    payload = {
        "username": "presh_j",
        "email": "presh@example.com"
    }
    
    response = client.post("/users/", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 101
    assert data["username"] == "presh_j"
    assert data["email"] == "presh@example.com"

def test_get_or_create_user_database_failure(mock_users_db):
    """Ensures the API safely catches and bubbles up a 500 error if Supabase/DB crashes."""
    # Force an unexpected system or operational database failure
    mock_users_db.side_effect = Exception("Connection timeout with database cluster")

    payload = {
        "username": "presh_j",
        "email": "presh@example.com"
    }
    
    response = client.post("/users/", json=payload)
    
    assert response.status_code == 500
    assert response.json()["detail"] == "Connection timeout with database cluster"
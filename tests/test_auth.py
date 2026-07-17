import pytest
from fastapi.testclient import TestClient
from api.main import app  

client = TestClient(app)

@pytest.fixture
def mock_auth_db_utils(mocker):
    """Mocks backend database handlers inside the auth route."""
    mock_get_user = mocker.patch("api.routes.auth.get_user_by_email")
    mock_create_user = mocker.patch("api.routes.auth.create_user")
    mock_hash = mocker.patch("api.routes.auth.hash_password")
    mock_verify = mocker.patch("api.routes.auth.verify_password")
    mock_token = mocker.patch("api.routes.auth.create_access_token")
    
    return {
        "get_user_by_email": mock_get_user,
        "create_user": mock_create_user,
        "hash_password": mock_hash,
        "verify_password": mock_verify,
        "create_access_token": mock_token
    }

def test_register_user_success(mock_auth_db_utils):
    """Tests successful user account creation and token issuance."""
    mock_auth_db_utils["get_user_by_email"].return_value = None
    mock_auth_db_utils["hash_password"].return_value = "hashed_pw_123"
    mock_auth_db_utils["create_user"].return_value = 42
    mock_auth_db_utils["create_access_token"].return_value = "mocked_jwt_token"

    payload = {"username": "testuser", "email": "test@example.com", "password": "securepassword"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 42
    assert data["access_token"] == "mocked_jwt_token"
    assert data["token_type"] == "bearer"

def test_register_duplicate_email_fails(mock_auth_db_utils):
    """Verifies that registration errors out if the email is already registered."""
    mock_auth_db_utils["get_user_by_email"].return_value = {"id": 1, "email": "test@example.com"}

    payload = {"username": "testuser", "email": "test@example.com", "password": "securepassword"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_login_success(mock_auth_db_utils):
    """Tests authenticating a user with valid matching credentials."""
    mock_auth_db_utils["get_user_by_email"].return_value = {"id": 42, "password": "hashed_pw_123"}
    mock_auth_db_utils["verify_password"].return_value = True
    mock_auth_db_utils["create_access_token"].return_value = "login_jwt_token"

    payload = {"email": "test@example.com", "password": "securepassword"}
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 42
    assert data["access_token"] == "login_jwt_token"

def test_login_invalid_credentials_fails(mock_auth_db_utils):
    """Ensures login route drops unauthorized requests with bad credentials."""
    mock_auth_db_utils["get_user_by_email"].return_value = None  

    payload = {"email": "bad@example.com", "password": "wrongpassword"}
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
# tests/test_auth.py
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from database.base import get_db

from main import app  # Assuming your FastAPI app instance is in main.py
from schemas.auth import TokenOut, UserOut, TokenRefreshOut
from utils.exceptions import (
    InvalidCredentialsError,
    UserCantBeCreatedError,
    MissingTokenError,
)


# It's good practice to have a test client fixture
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# --- Mocks for services ---
@pytest.fixture
def mock_login_service():
    with patch("routers.auth.login_service") as mock:
        yield mock


@pytest.fixture
def mock_register_service():
    with patch("routers.auth.register_service") as mock:
        yield mock


@pytest.fixture
def mock_refresh_service():
    with patch("routers.auth.refresh_service") as mock:
        yield mock


# --- Mock for get_db ---
# This allows us to inject a mock session without hitting the actual database
@pytest.fixture
def mock_db_session():
    db_session = MagicMock(spec=Session)
    return db_session


@pytest.fixture(autouse=True)  # Apply this fixture to all tests in this module
def override_get_db(mock_db_session):
    # This replaces the actual get_db dependency with our mock for all tests
    def _override_get_db():
        try:
            yield mock_db_session
        finally:
            pass  # No actual db.close() needed for a mock

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


# --- Test Cases ---


## /login Endpoint Tests
def test_login_user_success(client, mock_login_service, mock_db_session):
    # Arrange
    expected_token = TokenOut(
        access_token="fake_access_token",
        refresh_token="fake_refresh_token",
        token_type="bearer",
    )
    mock_login_service.return_value = expected_token
    login_data = {"username": "test@example.com", "password": "password123"}

    # Act
    response = client.post("/auth/login", data=login_data)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_token.model_dump()
    mock_login_service.assert_called_once()
    # Verify form_data structure passed to service (UserLogin schema)
    call_args = mock_login_service.call_args[0]
    assert call_args[0].username == login_data["username"]
    assert call_args[0].password == login_data["password"]
    assert call_args[1] == mock_db_session


def test_login_user_invalid_credentials(client, mock_login_service, mock_db_session):
    # Arrange
    mock_login_service.side_effect = InvalidCredentialsError("Invalid credentials")
    login_data = {"username": "wrong@example.com", "password": "wrongpassword"}

    # Act
    response = client.post("/auth/login", data=login_data)

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Invalid username or password"}
    assert response.headers.get("WWW-Authenticate") == "Bearer"
    mock_login_service.assert_called_once()
    call_args = mock_login_service.call_args[0]
    assert call_args[0].username == login_data["username"]
    assert call_args[0].password == login_data["password"]
    assert call_args[1] == mock_db_session


## /register Endpoint Tests
def test_register_user_success(client, mock_register_service, mock_db_session):
    # Arrange
    expected_user = UserOut(
        usr_id=1,
        usr_name="Test User",
        usr_email="test@example.com",
        usr_isadmin=False,
        usr_created_at=datetime(2025, 5, 26, 1, 31, 12, 571975, tzinfo=timezone.utc),
    )
    mock_register_service.return_value = expected_user
    register_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123",
    }

    # Act
    response = client.post("/auth/register", data=register_data)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    # Pydantic v2 .model_dump() is the new .dict()
    assert response.json() == expected_user.model_dump(mode="json")
    mock_register_service.assert_called_once()
    call_args = mock_register_service.call_args[0]
    assert call_args[0].name == register_data["name"]
    assert call_args[0].email == register_data["email"]
    assert call_args[0].password == register_data["password"]
    assert call_args[1] == mock_db_session


def test_register_user_already_exists(client, mock_register_service, mock_db_session):
    # Arrange
    mock_register_service.side_effect = UserCantBeCreatedError(
        "Email already registered"
    )
    register_data = {
        "name": "Existing User",
        "email": "existing@example.com",
        "password": "password123",
    }

    # Act
    response = client.post("/auth/register", data=register_data)

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Email already registered"}
    mock_register_service.assert_called_once()
    call_args = mock_register_service.call_args[0]
    assert call_args[0].name == register_data["name"]
    assert call_args[0].email == register_data["email"]
    assert call_args[0].password == register_data["password"]
    assert call_args[1] == mock_db_session


## /refresh Endpoint Tests
def test_refresh_user_success(client, mock_refresh_service, mock_db_session):
    # Arrange
    expected_token = TokenRefreshOut(
        access_token="new_fake_access_token", token_type="bearer"
    )
    mock_refresh_service.return_value = expected_token
    refresh_data = {"refresh_token": "valid_refresh_token"}

    # Act
    response = client.post("/auth/refresh", data=refresh_data)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_token.model_dump()
    mock_refresh_service.assert_called_once()
    call_args = mock_refresh_service.call_args[0]
    assert call_args[0].refresh_token == refresh_data["refresh_token"]
    assert call_args[1] == mock_db_session


def test_refresh_user_invalid_token(client, mock_refresh_service, mock_db_session):
    # Arrange
    mock_refresh_service.side_effect = InvalidCredentialsError(
        "Invalid or expired token"
    )
    refresh_data = {"refresh_token": "invalid_or_expired_token"}

    # Act
    response = client.post("/auth/refresh", data=refresh_data)

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Invalid or expired refresh token"}
    assert response.headers.get("WWW-Authenticate") == "Bearer"
    mock_refresh_service.assert_called_once()
    call_args = mock_refresh_service.call_args[0]
    assert call_args[0].refresh_token == refresh_data["refresh_token"]
    assert call_args[1] == mock_db_session


def test_refresh_user_missing_token(client, mock_refresh_service, mock_db_session):
    # Arrange
    # The MissingTokenError should ideally be raised by the service if it expects a token
    # and doesn't find one, or by Pydantic validation if the field is required.
    # Here, we simulate the service raising it.
    mock_refresh_service.side_effect = MissingTokenError("Refresh token not provided")
    # If form_data: Token = Form() makes refresh_token required,
    # FastAPI/Pydantic would return a 422 before hitting the service.
    # Let's assume the service itself can also raise this for some internal logic.
    refresh_data = {"refresh_token": ""}  # Simulate service logic catching empty token

    # Act
    response = client.post("/auth/refresh", data=refresh_data)

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Refresh token not provided"}
    assert response.headers.get("WWW-Authenticate") == "Bearer"
    mock_refresh_service.assert_called_once()  # Service is called even with empty string
    call_args = mock_refresh_service.call_args[0]
    assert call_args[0].refresh_token == refresh_data["refresh_token"]
    assert call_args[1] == mock_db_session


def test_refresh_user_truly_missing_token_field(client):
    # Arrange
    # Test what happens if the 'refresh_token' field is entirely missing from the form data.
    # Pydantic validation in Token schema should catch this.
    # No need to mock the service here, as the request shouldn't reach it.

    # Act
    response = client.post("/auth/refresh", data={})  # Empty form data

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # The exact detail message might vary based on FastAPI/Pydantic versions.
    # It will indicate that 'refresh_token' field is required.
    assert "detail" in response.json()
    assert any(
        err["type"] == "missing" and err["loc"] == ["body", "refresh_token"]
        for err in response.json()["detail"]
    )

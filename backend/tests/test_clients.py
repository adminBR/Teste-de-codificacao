# tests/test_clients.py
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from typing import List

# Import the actual FastAPI app instance from your main.py
from main import app

# We still need these for dependency overriding
from database.base import get_db
from utils.jwt import get_current_user, get_current_user_id_from_token

# Corrected import: use 'clients' as the module name
from routers import clients as client_router

from schemas.clients import ClientCreate, ClientUpdate, ClientOut
from schemas.auth import UserOut

# --- Fixtures ---


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient instance for making requests to the app."""
    # Use the imported app from main.py
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_db_session():
    """Mocks the SQLAlchemy database session."""
    db_session = MagicMock(spec=Session)
    return db_session


@pytest.fixture
def mock_current_user_obj():
    """Mocks the UserOut object returned by get_current_user."""
    return UserOut(
        usr_id=1,
        usr_name="Test User",
        usr_email="test@example.com",
        usr_isadmin=False,
        usr_created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_current_user_id():
    """Mocks the user ID returned by get_current_user_id_from_token."""
    return 1


@pytest.fixture(autouse=True)  # Apply this to all tests in this module
def override_dependencies(mock_db_session, mock_current_user_obj, mock_current_user_id):
    """Overrides app dependencies for get_db, get_current_user, and get_current_user_id_from_token."""

    def _override_get_db():
        try:
            yield mock_db_session
        finally:
            pass  # No actual db.close() needed for a mock

    def _override_get_current_user():
        return mock_current_user_obj

    def _override_get_current_user_id_from_token():
        return mock_current_user_id

    # Override dependencies on the main app instance
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    app.dependency_overrides[get_current_user_id_from_token] = (
        _override_get_current_user_id_from_token
    )
    yield
    app.dependency_overrides.clear()


# --- Mocks for client services ---
@pytest.fixture
def mock_create_client_service():
    with patch("routers.clients.create_client_service") as mock:
        yield mock


@pytest.fixture
def mock_get_clients_service():
    with patch("routers.clients.get_clients_service") as mock:
        yield mock


@pytest.fixture
def mock_get_client_by_id_service():
    with patch("routers.clients.get_client_by_id_service") as mock:
        yield mock


@pytest.fixture
def mock_update_client_service():
    with patch("routers.clients.update_client_service") as mock:
        yield mock


@pytest.fixture
def mock_delete_client_service():
    with patch("routers.clients.delete_client_service") as mock:
        yield mock


# --- Test Data ---
fixed_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

sample_client_out_data = {
    "cli_id": 1,
    "cli_name": "Test Client",
    "cli_email": "client@example.com",
    "cli_cpf": "12345678901",
    "cli_created_at": fixed_time,
    "cli_updated_at": fixed_time,
    "cli_created_by": 1,  # Matches mock_current_user_obj.usr_id
}
sample_client_out = ClientOut(**sample_client_out_data)

sample_client_create_data = {
    "cli_name": "New Client",
    "cli_email": "newclient@example.com",
    "cli_cpf": "11122233344",
}

sample_client_update_data = {
    "cli_name": "Updated Client Name",
    "cli_email": "updatedclient@example.com",
}


# --- Test Cases ---


## POST /clients/ (add_client)
def test_add_client_success(
    client, mock_create_client_service, mock_db_session, mock_current_user_obj
):
    # Arrange
    mock_create_client_service.return_value = sample_client_out

    # Act
    response = client.post(
        "/clients/", json=sample_client_create_data
    )  # Path is /clients/ as per main.py

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == sample_client_out.model_dump(
        mode="json"
    )  # mode='json' for datetime
    mock_create_client_service.assert_called_once()
    # Access keyword arguments using .kwargs
    call_kwargs = mock_create_client_service.call_args.kwargs
    assert call_kwargs["db"] == mock_db_session
    assert isinstance(call_kwargs["client_data"], ClientCreate)
    assert call_kwargs["client_data"].cli_name == sample_client_create_data["cli_name"]
    assert call_kwargs["current_user"] == mock_current_user_obj


def test_add_client_service_http_exception(client, mock_create_client_service):
    # Arrange
    mock_create_client_service.side_effect = HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail="Client already exists"
    )

    # Act
    response = client.post("/clients/", json=sample_client_create_data)

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": "Client already exists"}


def test_add_client_service_generic_exception(client, mock_create_client_service):
    # Arrange
    mock_create_client_service.side_effect = Exception("Some internal error")

    # Act
    response = client.post("/clients/", json=sample_client_create_data)

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Could not create client."}


## GET /clients/ (fetch_clients)
def test_fetch_clients_success(
    client, mock_get_clients_service, mock_db_session, mock_current_user_id
):
    # Arrange
    clients_list_data = [
        sample_client_out_data,
        {**sample_client_out_data, "cli_id": 2, "cli_cpf": "98765432109"},
    ]
    clients_list_models = [ClientOut(**data) for data in clients_list_data]
    mock_get_clients_service.return_value = clients_list_models

    # Act
    response = client.get("/clients/?skip=0&limit=10")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    expected_json = [c.model_dump(mode="json") for c in clients_list_models]
    assert response.json() == expected_json
    mock_get_clients_service.assert_called_once_with(mock_db_session, skip=0, limit=10)


def test_fetch_clients_empty(client, mock_get_clients_service, mock_db_session):
    # Arrange
    mock_get_clients_service.return_value = []

    # Act
    response = client.get("/clients/")  # Uses default skip=0, limit=100

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []
    mock_get_clients_service.assert_called_once_with(mock_db_session, skip=0, limit=100)


## GET /clients/{client_id} (fetch_client)
def test_fetch_client_by_id_success(
    client, mock_get_client_by_id_service, mock_db_session, mock_current_user_id
):
    # Arrange
    mock_get_client_by_id_service.return_value = sample_client_out
    client_id = 1

    # Act
    response = client.get(f"/clients/{client_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == sample_client_out.model_dump(mode="json")
    mock_get_client_by_id_service.assert_called_once_with(
        mock_db_session, client_id=client_id
    )


def test_fetch_client_by_id_not_found(
    client, mock_get_client_by_id_service, mock_db_session
):
    # Arrange
    mock_get_client_by_id_service.return_value = None
    client_id = 999

    # Act
    response = client.get(f"/clients/{client_id}")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Client not found or access denied"}
    mock_get_client_by_id_service.assert_called_once_with(
        mock_db_session, client_id=client_id
    )


## PUT /clients/{client_id} (update_client_service_details)
def test_update_client_success(
    client, mock_update_client_service, mock_db_session, mock_current_user_obj
):
    # Arrange
    client_id = 1
    # Create a new datetime for updated_at to ensure it's different if the test runs quickly
    now_utc = datetime.now(timezone.utc)
    updated_client_data = {
        **sample_client_out_data,  # Base data
        **sample_client_update_data,  # Updates
        "cli_updated_at": now_utc,  # New updated time
    }
    updated_data_response_model = ClientOut(**updated_client_data)
    mock_update_client_service.return_value = updated_data_response_model

    # Act
    response = client.put(f"/clients/{client_id}", json=sample_client_update_data)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == updated_data_response_model.model_dump(mode="json")
    mock_update_client_service.assert_called_once()
    # Access keyword arguments using .kwargs
    call_kwargs = mock_update_client_service.call_args.kwargs
    assert call_kwargs["db"] == mock_db_session
    assert call_kwargs["client_id"] == client_id
    assert isinstance(call_kwargs["client_data"], ClientUpdate)
    assert call_kwargs["client_data"].cli_name == sample_client_update_data["cli_name"]
    assert call_kwargs["current_user"] == mock_current_user_obj


def test_update_client_not_found_or_denied(client, mock_update_client_service):
    # Arrange
    mock_update_client_service.return_value = None
    client_id = 999

    # Act
    response = client.put(f"/clients/{client_id}", json=sample_client_update_data)

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Client not found or access denied for update"}


def test_update_client_service_http_exception(client, mock_update_client_service):
    # Arrange
    mock_update_client_service.side_effect = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CPF format"
    )
    client_id = 1

    # Act
    response = client.put(f"/clients/{client_id}", json=sample_client_update_data)

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid CPF format"}


def test_update_client_service_generic_exception(client, mock_update_client_service):
    # Arrange
    mock_update_client_service.side_effect = Exception("Some internal update error")
    client_id = 1

    # Act
    response = client.put(f"/clients/{client_id}", json=sample_client_update_data)

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Could not update client."}


## DELETE /clients/{client_id} (remove_client)
def test_remove_client_success(
    client, mock_delete_client_service, mock_db_session, mock_current_user_obj
):
    # Arrange
    mock_delete_client_service.return_value = (
        sample_client_out  # Or True, or any object that is not None
    )
    client_id = 1

    # Act
    response = client.delete(f"/clients/{client_id}")

    # Assert
    # The router returns `None` which FastAPI converts to 204 No Content if no response_model is set
    # or if the response_model allows None. Here, it returns None implicitly.
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_delete_client_service.assert_called_once_with(
        db=mock_db_session, client_id=client_id, current_user=mock_current_user_obj
    )


def test_remove_client_not_found_or_denied(client, mock_delete_client_service):
    # Arrange
    mock_delete_client_service.return_value = None
    client_id = 999

    # Act
    response = client.delete(f"/clients/{client_id}")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Client not found or access denied for deletion"
    }


def test_remove_client_service_http_exception(client, mock_delete_client_service):
    # Arrange
    mock_delete_client_service.side_effect = HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail="Client has active orders"
    )
    client_id = 1

    # Act
    response = client.delete(f"/clients/{client_id}")

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": "Client has active orders"}
    mock_delete_client_service.assert_called_once()


# Example of testing Pydantic validation for request body (e.g., invalid CPF)
def test_add_client_invalid_cpf_format(client):
    # Arrange
    invalid_create_data = {
        "cli_name": "Bad CPF Client",
        "cli_email": "badcpf@example.com",
        "cli_cpf": "123",  # Too short, as per ClientBase schema
    }
    # No service mock needed as Pydantic validation should fail first

    # Act
    response = client.post("/clients/", json=invalid_create_data)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Example check for the error detail:
    error_detail = response.json().get("detail", [])
    assert any(
        err.get("loc") == ["body", "cli_cpf"]
        and "string_too_short" in err.get("type", "")
        for err in error_detail
    )

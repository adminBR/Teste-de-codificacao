import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from typing import List, Generator

# Assuming your FastAPI app instance is in main.py
from main import app

# Dependencies to be mocked or overridden
from database.base import get_db
from utils.jwt import get_current_user  # Assuming orders router uses get_current_user

# Import the router and schemas
from routers import orders as order_router  # Ensure this import is correct
from schemas.orders import (
    OrderCreate,
    OrderUpdate,
    OrderOut,
    OrderItemCreate,
    OrderItemOut,
)
from schemas.auth import UserOut

# --- Mock User Data ---
MOCK_ADMIN_USER = UserOut(
    usr_id=1,
    usr_name="Admin User",
    usr_email="admin@example.com",
    usr_isadmin=True,
    usr_created_at=datetime.now(timezone.utc),
)
MOCK_NORMAL_USER = UserOut(
    usr_id=2,
    usr_name="Normal User",
    usr_email="user@example.com",
    usr_isadmin=False,
    usr_created_at=datetime.now(timezone.utc),
)

# --- Fixtures ---


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Provides a TestClient instance for making requests to the app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_db_session() -> MagicMock:
    """Mocks the SQLAlchemy database session."""
    db_session = MagicMock(spec=Session)
    return db_session


# Fixture to override get_db globally for this test module
@pytest.fixture(autouse=True)
def override_get_db_dependency(
    mock_db_session: MagicMock,
) -> Generator[None, None, None]:
    """Overrides the get_db dependency for all tests in this module."""

    def _override_get_db():
        try:
            yield mock_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


# --- Mocks for order services ---
@pytest.fixture
def mock_create_order_service() -> MagicMock:
    with patch("routers.orders.create_order_service") as mock:
        yield mock


@pytest.fixture
def mock_get_orders_service() -> MagicMock:
    with patch("routers.orders.get_orders_service") as mock:
        yield mock


@pytest.fixture
def mock_get_order_by_id_service() -> MagicMock:
    with patch("routers.orders.get_order_by_id_service") as mock:
        yield mock


@pytest.fixture
def mock_update_order_status_service() -> MagicMock:
    with patch("routers.orders.update_order_status_service") as mock:
        yield mock


@pytest.fixture
def mock_delete_order_service() -> MagicMock:
    with patch("routers.orders.delete_order_service") as mock:
        yield mock


# --- Test Data ---
fixed_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

sample_order_item_out_data_1 = {
    "ord_it_id": 1,
    "ord_id": 1,
    "ord_prd_id": 101,
    "ord_it_quant": 2,
    "ord_it_price": 10.00,
    "ord_created_at": fixed_time,
    "ord_updated_at": fixed_time,
}
sample_order_item_out_1 = OrderItemOut(**sample_order_item_out_data_1)

sample_order_item_out_data_2 = {
    "ord_it_id": 2,
    "ord_id": 1,
    "ord_prd_id": 102,
    "ord_it_quant": 1,
    "ord_it_price": 25.50,
    "ord_created_at": fixed_time,
    "ord_updated_at": fixed_time,
}
sample_order_item_out_2 = OrderItemOut(**sample_order_item_out_data_2)


sample_order_out_data = {
    "ord_id": 1,
    "ord_usr_id": MOCK_NORMAL_USER.usr_id,  # Associated with the normal user
    "ord_status": "PENDING",
    "ord_created_at": fixed_time,
    "ord_updated_at": fixed_time,
    "items": [sample_order_item_out_data_1, sample_order_item_out_data_2],
}
sample_order_out = OrderOut(**sample_order_out_data)

sample_order_create_data = {
    "ord_status": "PENDING",  # Optional, can be omitted to use default
    "items": [
        {"ord_prd_id": 101, "ord_it_quant": 2},
        {"ord_prd_id": 102, "ord_it_quant": 1},
    ],
}

sample_order_update_data = {"ord_status": "SHIPPED"}


# --- Helper for setting current user ---
def set_current_user(user: UserOut):
    def _override_get_current_user():
        return user

    app.dependency_overrides[order_router.get_current_user] = _override_get_current_user


def clear_current_user():
    app.dependency_overrides.pop(order_router.get_current_user, None)


# --- Test Cases ---


## POST /orders/ (create_order)
def test_create_order_success(
    client: TestClient, mock_create_order_service: MagicMock, mock_db_session: MagicMock
):
    set_current_user(MOCK_NORMAL_USER)
    mock_create_order_service.return_value = sample_order_out

    response = client.post("/orders/", json=sample_order_create_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == sample_order_out.model_dump(mode="json")
    mock_create_order_service.assert_called_once()
    call_args = mock_create_order_service.call_args.kwargs
    assert call_args["db"] == mock_db_session
    assert isinstance(call_args["order_data"], OrderCreate)
    assert (
        call_args["order_data"].items[0].ord_prd_id
        == sample_order_create_data["items"][0]["ord_prd_id"]
    )
    assert call_args["current_user"] == MOCK_NORMAL_USER
    clear_current_user()


def test_create_order_service_http_exception(
    client: TestClient, mock_create_order_service: MagicMock
):
    set_current_user(MOCK_NORMAL_USER)
    mock_create_order_service.side_effect = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock"
    )
    response = client.post("/orders/", json=sample_order_create_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Insufficient stock"}
    clear_current_user()


def test_create_order_service_generic_exception(
    client: TestClient, mock_create_order_service: MagicMock
):
    set_current_user(MOCK_NORMAL_USER)
    mock_create_order_service.side_effect = Exception(
        "Internal server error during order creation"
    )
    response = client.post("/orders/", json=sample_order_create_data)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Could not create order."}
    clear_current_user()


def test_create_order_pydantic_validation_no_items(client: TestClient):
    set_current_user(MOCK_NORMAL_USER)
    invalid_data = {
        "items": []
    }  # Assuming items list cannot be empty based on OrderCreate
    response = client.post("/orders/", json=invalid_data)
    # The service layer has a check for this, if Pydantic doesn't catch it first
    # If OrderCreate has `items: List[OrderItemCreate] = Field(..., min_items=1)`
    # then Pydantic would return 422. Otherwise, service layer handles it.
    # Based on current service: create_order_service raises 400 if not order_data.items
    # Let's assume the service layer handles it as per the code.
    # If you add Pydantic validation `min_items=1` to OrderCreate.items, this would be 422.
    # For now, let's assume the service mock will be called and would raise.
    # This test is better if we don't mock the service and test the actual service logic,
    # but to follow the pattern:
    # To test Pydantic, we wouldn't mock the service.
    # For this example, let's assume it's a 422 from Pydantic if `min_items=1` is set.
    # If not, the service mock would need to be configured to raise the error.
    # For a direct Pydantic test:
    response_pydantic = client.post("/orders/", json={"items": []})  # No items
    assert response_pydantic.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response_pydantic.json()["detail"] == "Order must contain at least one item."

    clear_current_user()


## GET /orders/ (fetch_orders)
def test_fetch_orders_success(
    client: TestClient, mock_get_orders_service: MagicMock, mock_db_session: MagicMock
):
    set_current_user(MOCK_NORMAL_USER)
    orders_list = [sample_order_out]
    mock_get_orders_service.return_value = orders_list

    response = client.get("/orders/?skip=0&limit=10")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [o.model_dump(mode="json") for o in orders_list]
    mock_get_orders_service.assert_called_once_with(
        db=mock_db_session, current_user=MOCK_NORMAL_USER, skip=0, limit=10
    )
    clear_current_user()


## GET /orders/{order_id} (fetch_order)
def test_fetch_order_by_id_success(
    client: TestClient,
    mock_get_order_by_id_service: MagicMock,
    mock_db_session: MagicMock,
):
    set_current_user(MOCK_NORMAL_USER)
    mock_get_order_by_id_service.return_value = sample_order_out
    order_id = sample_order_out.ord_id

    response = client.get(f"/orders/{order_id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == sample_order_out.model_dump(mode="json")
    mock_get_order_by_id_service.assert_called_once_with(
        db=mock_db_session, order_id=order_id, current_user=MOCK_NORMAL_USER
    )
    clear_current_user()


def test_fetch_order_by_id_not_found(
    client: TestClient, mock_get_order_by_id_service: MagicMock
):
    set_current_user(MOCK_NORMAL_USER)
    mock_get_order_by_id_service.return_value = None
    order_id = 999

    response = client.get(f"/orders/{order_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Order not found or access denied."}
    clear_current_user()


## PUT /orders/{order_id} (update_order_status)
def test_update_order_status_success_as_admin(
    client: TestClient,
    mock_update_order_status_service: MagicMock,
    mock_db_session: MagicMock,
):
    set_current_user(MOCK_ADMIN_USER)
    order_id = sample_order_out.ord_id
    updated_order_data = sample_order_out.model_copy(update={"ord_status": "SHIPPED"})
    mock_update_order_status_service.return_value = updated_order_data

    response = client.put(f"/orders/{order_id}", json=sample_order_update_data)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == updated_order_data.model_dump(mode="json")
    mock_update_order_status_service.assert_called_once()
    call_args = mock_update_order_status_service.call_args.kwargs
    assert call_args["db"] == mock_db_session
    assert call_args["order_id"] == order_id
    assert isinstance(call_args["order_update_data"], OrderUpdate)
    assert (
        call_args["order_update_data"].ord_status
        == sample_order_update_data["ord_status"]
    )
    assert call_args["current_user"] == MOCK_ADMIN_USER
    clear_current_user()


def test_update_order_status_forbidden_as_normal_user(
    client: TestClient, mock_update_order_status_service: MagicMock
):
    set_current_user(MOCK_NORMAL_USER)
    order_id = sample_order_out.ord_id
    # Service mock will raise HTTPException for permission denied
    mock_update_order_status_service.side_effect = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admins only for updating order status.",
    )

    response = client.put(f"/orders/{order_id}", json=sample_order_update_data)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Admins only for updating order status."}
    # Service is called, and it's the service's job to check permissions
    mock_update_order_status_service.assert_called_once()
    clear_current_user()


def test_update_order_status_order_not_found(
    client: TestClient, mock_update_order_status_service: MagicMock
):
    set_current_user(MOCK_ADMIN_USER)
    mock_update_order_status_service.return_value = None  # Service indicates not found
    order_id = 999

    response = client.put(f"/orders/{order_id}", json=sample_order_update_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Order not found"}
    clear_current_user()


## DELETE /orders/{order_id} (remove_order)
def test_delete_order_success_as_admin(
    client: TestClient, mock_delete_order_service: MagicMock, mock_db_session: MagicMock
):
    set_current_user(MOCK_ADMIN_USER)
    order_id = sample_order_out.ord_id
    # Service returns the deleted object (or True) if successful
    mock_delete_order_service.return_value = sample_order_out

    response = client.delete(f"/orders/{order_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_delete_order_service.assert_called_once_with(
        db=mock_db_session, order_id=order_id, current_user=MOCK_ADMIN_USER
    )
    clear_current_user()


def test_delete_order_forbidden_as_normal_user(
    client: TestClient, mock_delete_order_service: MagicMock
):
    set_current_user(MOCK_NORMAL_USER)
    order_id = sample_order_out.ord_id
    mock_delete_order_service.side_effect = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Admins only for deleting orders."
    )

    response = client.delete(f"/orders/{order_id}")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Admins only for deleting orders."}
    mock_delete_order_service.assert_called_once()
    clear_current_user()


def test_delete_order_not_found_as_admin(
    client: TestClient, mock_delete_order_service: MagicMock
):
    set_current_user(MOCK_ADMIN_USER)
    mock_delete_order_service.return_value = None  # Service indicates not found
    order_id = 999

    response = client.delete(f"/orders/{order_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Order not found for deletion"}
    clear_current_user()

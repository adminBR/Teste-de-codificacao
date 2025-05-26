import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, date
from typing import List, Generator, Any
from decimal import Decimal

# Import the actual FastAPI app instance from your main.py
from main import app

# Dependencies to be mocked or overridden
from database.base import get_db
from utils.jwt import get_current_user  # Assuming product router uses get_current_user

# Import the router and schemas
from routers import products as product_router  # Ensure this import is correct
from schemas.products import (
    ProductCreate,
    ProductUpdate,
    ProductOut,
    ProductImageCreate,
    ProductImageOut,
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
            pass  # No actual db.close() needed for a mock

    original_get_db = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override_get_db
    yield
    if original_get_db:
        app.dependency_overrides[get_db] = original_get_db
    else:
        app.dependency_overrides.pop(get_db, None)


# --- Helper for setting current user and managing its override ---


def set_current_user_for_test(user: UserOut):
    def _override_get_current_user():
        return user

    app.dependency_overrides[get_current_user] = _override_get_current_user


@pytest.fixture(autouse=True)
def manage_current_user_override():
    """
    Manages the get_current_user dependency override for each test.
    Tests should call set_current_user_for_test if they need a specific user.
    This fixture ensures the override state is reset after each test.
    """
    original_override_exists = get_current_user in app.dependency_overrides
    original_override_value = app.dependency_overrides.get(get_current_user)

    yield  # Test runs here

    # Restore the original state of the get_current_user override
    if original_override_exists:
        app.dependency_overrides[get_current_user] = original_override_value
    else:
        # If it wasn't overridden before this test, remove any override set during the test.
        app.dependency_overrides.pop(get_current_user, None)


# --- Mocks for product services ---
@pytest.fixture
def mock_create_product_service() -> MagicMock:
    with patch("routers.products.create_product_service") as mock:
        yield mock


@pytest.fixture
def mock_get_products_service() -> MagicMock:
    with patch("routers.products.get_products_service") as mock:
        yield mock


@pytest.fixture
def mock_get_product_by_id_service() -> MagicMock:
    with patch("routers.products.get_product_by_id_service") as mock:
        yield mock


@pytest.fixture
def mock_update_product_service() -> MagicMock:
    with patch("routers.products.update_product_service") as mock:
        yield mock


@pytest.fixture
def mock_delete_product_service() -> MagicMock:
    with patch("routers.products.delete_product_service") as mock:
        yield mock


@pytest.fixture
def mock_add_product_images_service() -> MagicMock:
    with patch("routers.products.add_product_images_service") as mock:
        yield mock


@pytest.fixture
def mock_get_product_images_service() -> MagicMock:
    with patch("routers.products.get_product_images_service") as mock:
        yield mock


@pytest.fixture
def mock_delete_product_image_service() -> MagicMock:
    with patch("routers.products.delete_product_image_service") as mock:
        yield mock


# --- Test Data ---
fixed_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
fixed_date = date(2025, 12, 31)

sample_image_out_data_1 = {
    "img_id": 1,
    "prd_id": 1,
    "img_url": "http://example.com/image1.jpg",
    "img_created_at": fixed_time,
}
sample_image_out_1 = ProductImageOut(**sample_image_out_data_1)

sample_image_out_data_2 = {
    "img_id": 2,
    "prd_id": 1,
    "img_url": "http://example.com/image2.png",
    "img_created_at": fixed_time,
}
sample_image_out_2 = ProductImageOut(**sample_image_out_data_2)

sample_product_out_data_1 = {
    "prd_id": 1,
    "prd_desc": "Test Product 1",
    "prd_category": "Electronics",
    "prd_price": Decimal("99.99"),
    "prd_barcode": "1234567890123",
    "prd_initial_stock": 100,
    "prd_current_stock": 100,
    "prd_expiring_date": fixed_date,
    "prd_created_at": fixed_time,
    "prd_updated_at": fixed_time,
    "images": [sample_image_out_data_1],  # Example with one image
}
sample_product_out_1 = ProductOut(**sample_product_out_data_1)

sample_product_out_data_2 = {
    "prd_id": 2,
    "prd_desc": "Test Product 2",
    "prd_category": "Books",
    "prd_price": Decimal("19.99"),
    "prd_barcode": "9876543210987",
    "prd_initial_stock": 50,
    "prd_current_stock": 50,
    "prd_expiring_date": None,
    "prd_created_at": fixed_time,
    "prd_updated_at": fixed_time,
    "images": [],
}
sample_product_out_2 = ProductOut(**sample_product_out_data_2)


sample_product_create_data = {
    "prd_desc": "New Product",
    "prd_category": "Gadgets",
    "prd_price": 49.99,  # Will be converted to Decimal by Pydantic
    "prd_barcode": "0000000000000",
    "prd_initial_stock": 10,
    "prd_current_stock": 10,
    "prd_expiring_date": fixed_date.isoformat(),  # Send as string
}

sample_product_update_data = {
    "prd_desc": "Updated Product Name",
    "prd_price": 120.50,
}

sample_image_create_data_1 = {"img_url": "http://example.com/new_image1.jpg"}
sample_image_create_data_2 = {"img_url": "http://example.com/new_image2.png"}


# --- Product Tests ---


def test_create_product_as_admin(
    client: TestClient,
    mock_create_product_service: MagicMock,
    mock_db_session: MagicMock,
):
    set_current_user_for_test(MOCK_ADMIN_USER)
    # Adjust sample_product_out_1 to not have images for creation test if create doesn't handle images
    created_product_response_data = {
        **sample_product_out_data_1,
        "prd_id": 1,
        "images": [],
    }  # No images on initial create
    created_product_response_model = ProductOut(**created_product_response_data)
    mock_create_product_service.return_value = created_product_response_model

    response = client.post("/products/", json=sample_product_create_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == created_product_response_model.model_dump(mode="json")
    mock_create_product_service.assert_called_once()
    call_kwargs = mock_create_product_service.call_args.kwargs
    assert call_kwargs["db"] == mock_db_session
    assert isinstance(call_kwargs["product_data"], ProductCreate)
    assert (
        call_kwargs["product_data"].prd_desc == sample_product_create_data["prd_desc"]
    )
    assert call_kwargs["current_user"] == MOCK_ADMIN_USER


def test_create_product_as_user(
    client: TestClient, mock_create_product_service: MagicMock
):
    set_current_user_for_test(MOCK_NORMAL_USER)
    mock_create_product_service.side_effect = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admins only for creating products.",
    )
    response = client.post("/products/", json=sample_product_create_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Admins only for creating products."
    # Service should be called, and it's responsible for the 403
    mock_create_product_service.assert_called_once()


def test_create_product_duplicate_barcode(
    client: TestClient, mock_create_product_service: MagicMock
):
    set_current_user_for_test(MOCK_ADMIN_USER)
    mock_create_product_service.side_effect = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Barcode already registered."
    )
    response = client.post("/products/", json=sample_product_create_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Barcode already registered."


def test_get_all_products(
    client: TestClient, mock_get_products_service: MagicMock, mock_db_session: MagicMock
):
    set_current_user_for_test(MOCK_NORMAL_USER)  # Any authenticated user can fetch
    products_list = [sample_product_out_1, sample_product_out_2]
    mock_get_products_service.return_value = products_list

    response = client.get("/products/?skip=0&limit=10")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [p.model_dump(mode="json") for p in products_list]

    # Diagnostic prints
    print(
        f"\nDEBUG: test_get_all_products - mock_get_products_service.call_count: {mock_get_products_service.call_count}"
    )
    print(
        f"DEBUG: test_get_all_products - mock_get_products_service.call_args_list: {mock_get_products_service.call_args_list}"
    )

    # The service function get_products_service does not take current_user
    mock_get_products_service.assert_called_once_with(
        db=mock_db_session, skip=0, limit=10
    )


def test_get_product_by_id(
    client: TestClient,
    mock_get_product_by_id_service: MagicMock,
    mock_db_session: MagicMock,
):
    set_current_user_for_test(MOCK_NORMAL_USER)
    mock_get_product_by_id_service.return_value = sample_product_out_1
    product_id = sample_product_out_1.prd_id

    response = client.get(f"/products/{product_id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == sample_product_out_1.model_dump(mode="json")

    # Diagnostic prints
    print(
        f"\nDEBUG: test_get_product_by_id - mock_get_product_by_id_service.call_count: {mock_get_product_by_id_service.call_count}"
    )
    print(
        f"DEBUG: test_get_product_by_id - mock_get_product_by_id_service.call_args_list: {mock_get_product_by_id_service.call_args_list}"
    )

    # The service function get_product_by_id_service does not take current_user
    mock_get_product_by_id_service.assert_called_once_with(
        db=mock_db_session, product_id=product_id
    )


def test_get_product_by_id_not_found(
    client: TestClient, mock_get_product_by_id_service: MagicMock
):
    set_current_user_for_test(MOCK_NORMAL_USER)
    mock_get_product_by_id_service.return_value = None
    response = client.get("/products/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Product not found."


def test_update_product_as_admin(
    client: TestClient,
    mock_update_product_service: MagicMock,
    mock_db_session: MagicMock,
):
    set_current_user_for_test(MOCK_ADMIN_USER)
    product_id = sample_product_out_1.prd_id
    # Create an updated version of the product for the mock response
    # Ensure all fields of ProductOut are present in the mock response data
    updated_product_data_dict = sample_product_out_1.model_dump()
    updated_product_data_dict.update(sample_product_update_data)  # Apply updates
    updated_product_data_dict["prd_price"] = Decimal(
        str(sample_product_update_data["prd_price"])
    )  # Ensure Decimal
    updated_product_data_dict["prd_updated_at"] = datetime.now(
        timezone.utc
    )  # Simulate update time

    updated_product_response_model = ProductOut(**updated_product_data_dict)
    mock_update_product_service.return_value = updated_product_response_model

    response = client.put(f"/products/{product_id}", json=sample_product_update_data)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == updated_product_response_model.model_dump(mode="json")
    mock_update_product_service.assert_called_once()
    call_kwargs = mock_update_product_service.call_args.kwargs
    assert call_kwargs["db"] == mock_db_session
    assert call_kwargs["product_id"] == product_id
    assert isinstance(call_kwargs["product_data"], ProductUpdate)
    assert (
        call_kwargs["product_data"].prd_desc == sample_product_update_data["prd_desc"]
    )
    assert call_kwargs["current_user"] == MOCK_ADMIN_USER


def test_update_product_as_user(
    client: TestClient, mock_update_product_service: MagicMock
):
    set_current_user_for_test(MOCK_NORMAL_USER)
    product_id = sample_product_out_1.prd_id
    mock_update_product_service.side_effect = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admins only for updating products.",
    )
    response = client.put(f"/products/{product_id}", json=sample_product_update_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Admins only for updating products."
    mock_update_product_service.assert_called_once()


def test_delete_product_as_admin(
    client: TestClient,
    mock_delete_product_service: MagicMock,
    mock_db_session: MagicMock,
):
    set_current_user_for_test(MOCK_ADMIN_USER)
    product_id = sample_product_out_1.prd_id
    mock_delete_product_service.return_value = (
        sample_product_out_1  # Service returns deleted obj
    )

    response = client.delete(f"/products/{product_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_delete_product_service.assert_called_once_with(
        db=mock_db_session, product_id=product_id, current_user=MOCK_ADMIN_USER
    )


def test_delete_product_as_user(
    client: TestClient, mock_delete_product_service: MagicMock
):
    set_current_user_for_test(MOCK_NORMAL_USER)
    product_id = sample_product_out_1.prd_id
    mock_delete_product_service.side_effect = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admins only for deleting products.",
    )
    response = client.delete(f"/products/{product_id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Admins only for deleting products."
    mock_delete_product_service.assert_called_once()


# --- Product Image Tests ---


def test_add_images_to_product_as_admin(
    client: TestClient,
    mock_add_product_images_service: MagicMock,
    mock_db_session: MagicMock,
):
    set_current_user_for_test(MOCK_ADMIN_USER)
    product_id = sample_product_out_1.prd_id
    images_to_add_payload = [sample_image_create_data_1, sample_image_create_data_2]
    # Mock service to return list of ProductImageOut
    mocked_created_images = [
        ProductImageOut(
            img_id=3,
            prd_id=product_id,
            img_url=sample_image_create_data_1["img_url"],
            img_created_at=fixed_time,
        ),
        ProductImageOut(
            img_id=4,
            prd_id=product_id,
            img_url=sample_image_create_data_2["img_url"],
            img_created_at=fixed_time,
        ),
    ]
    mock_add_product_images_service.return_value = mocked_created_images

    response = client.post(f"/products/{product_id}/images", json=images_to_add_payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == [
        img.model_dump(mode="json") for img in mocked_created_images
    ]
    mock_add_product_images_service.assert_called_once()
    call_kwargs = mock_add_product_images_service.call_args.kwargs
    assert call_kwargs["db"] == mock_db_session
    assert call_kwargs["product_id"] == product_id
    assert len(call_kwargs["images_data"]) == 2
    assert isinstance(call_kwargs["images_data"][0], ProductImageCreate)
    assert call_kwargs["current_user"] == MOCK_ADMIN_USER


def test_add_images_to_product_as_user(
    client: TestClient, mock_add_product_images_service: MagicMock
):
    set_current_user_for_test(MOCK_NORMAL_USER)
    product_id = sample_product_out_1.prd_id
    mock_add_product_images_service.side_effect = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Admins only for adding images."
    )
    response = client.post(
        f"/products/{product_id}/images", json=[sample_image_create_data_1]
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Admins only for adding images."
    mock_add_product_images_service.assert_called_once()


def test_add_images_to_non_existent_product(
    client: TestClient, mock_add_product_images_service: MagicMock
):
    set_current_user_for_test(MOCK_ADMIN_USER)
    mock_add_product_images_service.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
    )
    response = client.post("/products/999/images", json=[sample_image_create_data_1])
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Product not found."


def test_get_images_for_product(
    client: TestClient,
    mock_get_product_images_service: MagicMock,
    mock_db_session: MagicMock,
):
    set_current_user_for_test(MOCK_NORMAL_USER)  # Any authenticated user
    product_id = sample_product_out_1.prd_id
    mock_images = [sample_image_out_1, sample_image_out_2]
    mock_get_product_images_service.return_value = mock_images

    response = client.get(f"/products/{product_id}/images")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [img.model_dump(mode="json") for img in mock_images]
    # The service function get_product_images_service does not take current_user
    mock_get_product_images_service.assert_called_once_with(
        db=mock_db_session, product_id=product_id
    )


def test_get_images_for_product_also_shows_in_product_details(
    client: TestClient,
    mock_get_product_by_id_service: MagicMock,  # Mock the product service
):
    set_current_user_for_test(MOCK_NORMAL_USER)
    product_id = (
        sample_product_out_1.prd_id
    )  # This already has images in its definition
    mock_get_product_by_id_service.return_value = sample_product_out_1

    response = client.get(f"/products/{product_id}")  # Fetch the product

    assert response.status_code == status.HTTP_200_OK
    product_data = response.json()  # This is a dict
    assert "images" in product_data
    assert len(product_data["images"]) == len(sample_product_out_1.images)
    # product_data["images"][0]["img_url"] is a string from JSON
    # sample_product_out_1.images[0].img_url is an HttpUrl object
    assert product_data["images"][0]["img_url"] == str(
        sample_product_out_1.images[0].img_url
    )
    mock_get_product_by_id_service.assert_called_once()


def test_delete_product_image_as_admin(
    client: TestClient,
    mock_delete_product_image_service: MagicMock,
    mock_db_session: MagicMock,
):
    set_current_user_for_test(MOCK_ADMIN_USER)
    image_id = sample_image_out_1.img_id
    mock_delete_product_image_service.return_value = (
        sample_image_out_1  # Service returns deleted image
    )

    response = client.delete(f"/products/images/{image_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_delete_product_image_service.assert_called_once_with(
        db=mock_db_session, image_id=image_id, current_user=MOCK_ADMIN_USER
    )


def test_delete_product_image_as_user(
    client: TestClient, mock_delete_product_image_service: MagicMock
):
    set_current_user_for_test(MOCK_NORMAL_USER)
    image_id = sample_image_out_1.img_id
    mock_delete_product_image_service.side_effect = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Admins only for deleting images."
    )
    response = client.delete(f"/products/images/{image_id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Admins only for deleting images."
    mock_delete_product_image_service.assert_called_once()


def test_delete_product_image_not_found(
    client: TestClient, mock_delete_product_image_service: MagicMock
):
    set_current_user_for_test(MOCK_ADMIN_USER)
    mock_delete_product_image_service.return_value = None  # Service indicates not found
    response = client.delete("/products/images/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Image not found for deletion"


# --- Pydantic Validation Tests (Example) ---
def test_create_product_invalid_price_type(client: TestClient):
    set_current_user_for_test(MOCK_ADMIN_USER)  # Needs auth to attempt creation
    invalid_data = {**sample_product_create_data, "prd_price": "not_a_number"}
    response = client.post("/products/", json=invalid_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Pydantic's error message for decimal parsing is "Input should be a valid decimal"
    assert "input should be a valid decimal" in response.text.lower()

from fastapi import APIRouter, HTTPException, Depends, status, Response
from sqlalchemy.orm import Session
from typing import List

from database.base import get_db
from schemas.auth import UserOut
from schemas.products import (
    ProductCreate,
    ProductUpdate,
    ProductOut,
    ProductImageCreate,
    ProductImageOut,
)
from services.products import (
    create_product_service,
    get_products_service,
    get_product_by_id_service,
    update_product_service,
    delete_product_service,
    add_product_images_service,
    get_product_images_service,
    delete_product_image_service,
)
from utils.jwt import (
    get_current_user,
)

router = APIRouter()


# [auth,admin] Create a single product
@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def add_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):
    try:
        created_product = create_product_service(
            db=db, product_data=product_data, current_user=current_user
        )

        return created_product
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create product.",
        )


# [auth] Fetch all products with pagination
@router.get("/", response_model=List[ProductOut])
async def fetch_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):
    products = get_products_service(db, skip=skip, limit=limit)
    return products


# [auth] Fetch a single product with pagination
@router.get("/{product_id}", response_model=ProductOut)
async def fetch_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):
    db_product = get_product_by_id_service(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    return db_product


# [auth,admin] Update a single product info, based on the id
@router.put("/{product_id}", response_model=ProductOut)
async def update_product_details(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):
    try:
        updated_product = update_product_service(
            db=db,
            product_id=product_id,
            product_data=product_data,
            current_user=current_user,
        )
        if updated_product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        return updated_product
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update product.",
        )


# [auth,admin] Remove a single product from the products table, based on the id
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):

    deleted_product = delete_product_service(
        db=db, product_id=product_id, current_user=current_user
    )
    if deleted_product is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found for deletion",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Product Image Endpoints ---


## [auth,admin] Add one or more new images (by URL) to a specific product.
## - **product_id**: The ID of the product to add images to.
## - **Request body**: A JSON list of image objects, e.g., `[{"img_url": "http://..."}, {"img_url": "http://..."}]`
## - If an image URL already exists for the product, it will be skipped.
@router.post(
    "/{product_id}/images",
    response_model=List[ProductImageOut],
    status_code=status.HTTP_201_CREATED,
    summary="Add one or more images to a product",
)
async def add_images_to_product(
    product_id: int,
    images_data: List[ProductImageCreate],  # Expects a list of objects with "img_url"
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):

    try:
        created_images = add_product_images_service(
            db=db,
            product_id=product_id,
            images_data=images_data,
            current_user=current_user,
        )
        if not created_images and images_data:
            pass
        return created_images
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not add images to product.",
        )


# [auth] Fetch the images from a single product, base don the id
## Retrieve all images associated with a specific product.
## - **product_id**: The ID of the product.
@router.get(
    "/{product_id}/images",
    response_model=List[ProductImageOut],
    summary="Get all images for a product",
)
async def get_images_for_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):

    images = get_product_images_service(db=db, product_id=product_id)
    return images


# [auth,admin] Remove the images of a single product, based on the id
## Delete a specific product image by its unique image ID.
## - **image_id**: The ID of the image to delete.
## - Only admins can perform this action.
@router.delete(
    "/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a specific product image",
)
async def remove_product_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):

    # Service handles admin check and returns image if found, or None
    deleted_image = delete_product_image_service(
        db=db, image_id=image_id, current_user=current_user
    )
    if deleted_image is None:
        # This means image was not found (admin check is done in service)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found for deletion",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

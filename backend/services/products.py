from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from database.models import Product, User, ProductImage
from schemas.products import (
    ProductCreate,
    ProductUpdate,
    ProductImageCreate,
)
from schemas.auth import UserOut


# Helper function to check for duplicate barcode (if barcode is unique)
def _check_duplicate_barcode(
    db: Session, barcode: str, product_id: Optional[int] = None
):
    query = db.query(Product).filter(Product.prd_barcode == barcode)
    if product_id:
        query = query.filter(Product.prd_id != product_id)
    existing_product = query.first()
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Barcode already registered.",
        )


# --- Product Services ---


## Only admins can create products
## Create a single product without images
def create_product_service(
    db: Session, product_data: ProductCreate, current_user: UserOut
) -> Product:
    if not current_user.usr_isadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins only for creating products.",
        )

    if product_data.prd_barcode:
        _check_duplicate_barcode(db, product_data.prd_barcode)

    db_product = Product(**product_data.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


## Any authenticated user
## Fetch the a single product info based on the id
def get_product_by_id_service(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.prd_id == product_id).first()


## Any authenticated user
## Fetch all the products info with pagination
def get_products_service(db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
    return db.query(Product).offset(skip).limit(limit).all()


## Only admins
## Update the product info based on the id
def update_product_service(
    db: Session, product_id: int, product_data: ProductUpdate, current_user: UserOut
) -> Optional[Product]:
    if not current_user.usr_isadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins only for updating products.",
        )

    db_product = db.query(Product).filter(Product.prd_id == product_id).first()
    if not db_product:
        return None

    update_data = product_data.model_dump(exclude_unset=True)

    if (
        "prd_barcode" in update_data
        and update_data["prd_barcode"] != db_product.prd_barcode
    ):
        if update_data["prd_barcode"]:
            _check_duplicate_barcode(db, update_data["prd_barcode"], product_id)

    for key, value in update_data.items():
        setattr(db_product, key, value)

    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


## Only admins
## Delete a single product based on the id
def delete_product_service(
    db: Session, product_id: int, current_user: UserOut
) -> Optional[Product]:
    if not current_user.usr_isadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins only for deleting products.",
        )

    db_product = db.query(Product).filter(Product.prd_id == product_id).first()
    if not db_product:
        return None

    # Deletion will cascade to the images
    db.delete(db_product)
    db.commit()
    return db_product


# --- Product Image Services ---


## Only admins
## Add images to a single product based ont he id
def add_product_images_service(
    db: Session,
    product_id: int,
    images_data: List[ProductImageCreate],
    current_user: UserOut,
) -> List[ProductImage]:
    if not current_user.usr_isadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins only for adding images.",
        )

    db_product = get_product_by_id_service(db, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )

    created_images = []
    for image_data in images_data:
        # Check if the exact same image URL already exists for this product to avoid duplicates
        existing_image = (
            db.query(ProductImage)
            .filter(
                ProductImage.prd_id == product_id,
                ProductImage.img_url == str(image_data.img_url),
            )
            .first()
        )

        if existing_image:

            continue

        db_image = ProductImage(prd_id=product_id, img_url=str(image_data.img_url))
        db.add(db_image)
        created_images.append(db_image)

    if created_images:
        db.commit()
        for (
            img
        ) in (
            created_images
        ):  # Refresh each new image to get its generated ID and timestamps
            db.refresh(img)

    return created_images


## Any authenticated user
## Get all images for a specific product
def get_product_images_service(db: Session, product_id: int) -> List[ProductImage]:
    db_product = get_product_by_id_service(db, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )
    return db.query(ProductImage).filter(ProductImage.prd_id == product_id).all()


## Only admins
## Delete a single product images based on the id
def delete_product_image_service(
    db: Session, image_id: int, current_user: UserOut
) -> Optional[ProductImage]:
    if not current_user.usr_isadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins only for deleting images.",
        )

    db_image = db.query(ProductImage).filter(ProductImage.img_id == image_id).first()
    if not db_image:
        # No need to raise 404 here, router will handle if None is returned
        return None

    db.delete(db_image)
    db.commit()
    return db_image

from pydantic import BaseModel, ConfigDict, constr, HttpUrl
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# --- Product Image Schemas ---
class ProductImageBase(BaseModel):
    img_url: HttpUrl  # Using HttpUrl for validation


class ProductImageCreate(ProductImageBase):
    pass


class ProductImageOut(ProductImageBase):
    model_config = ConfigDict(from_attributes=True)

    img_id: int
    prd_id: int
    img_created_at: datetime


# --- Original Product Schemas ) ---


# Shared properties
class ProductBase(BaseModel):
    prd_desc: str
    prd_category: Optional[str] = None
    prd_section: Optional[str] = None
    prd_price: Decimal
    prd_barcode: Optional[constr(max_length=255)] = None
    prd_initial_stock: int
    prd_current_stock: int
    prd_expiring_date: Optional[date] = None


# Properties to receive on product creation
class ProductCreate(ProductBase):
    pass


# Properties to receive on product update
class ProductUpdate(BaseModel):
    prd_desc: Optional[str] = None
    prd_category: Optional[str] = None
    prd_section: Optional[str] = None
    prd_price: Optional[Decimal] = None
    prd_barcode: Optional[constr(max_length=255)] = None
    prd_initial_stock: Optional[int] = None
    prd_current_stock: Optional[int] = None
    prd_expiring_date: Optional[date] = None


# Properties to return to client
class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    prd_id: int
    prd_created_at: datetime
    prd_updated_at: datetime
    images: List[ProductImageOut] = []


class ProductRemove(BaseModel):
    prd_id: int

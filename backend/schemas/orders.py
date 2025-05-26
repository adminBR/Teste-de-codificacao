from pydantic import BaseModel, ConfigDict, conint
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

# --- OrderItem Schemas ---


class OrderItemBase(BaseModel):
    ord_prd_id: int
    ord_it_quant: conint(gt=0)  # Quantity must be greater than 0


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemOut(OrderItemBase):
    model_config = ConfigDict(from_attributes=True)

    ord_it_id: int
    ord_id: int
    ord_it_price: Decimal
    ord_created_at: datetime
    ord_updated_at: datetime


# --- Order Schemas ---


class OrderBase(BaseModel):
    ord_status: str = "PENDING"  # Default status on creation


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]


class OrderUpdate(BaseModel):
    ord_status: str


class OrderOut(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    ord_id: int
    ord_usr_id: int
    ord_created_at: datetime
    ord_updated_at: datetime
    items: List[OrderItemOut] = []

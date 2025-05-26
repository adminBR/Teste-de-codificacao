from fastapi import APIRouter, HTTPException, Depends, status, Response
from sqlalchemy.orm import Session
from typing import List

from database.base import get_db
from schemas.auth import UserOut
from schemas.orders import OrderCreate, OrderUpdate, OrderOut
from services.orders import (
    create_order_service,
    get_orders_service,
    get_order_by_id_service,
    update_order_status_service,
    delete_order_service,
)
from utils.jwt import get_current_user

router = APIRouter()


# [auth,admin] Creates a new order and the order items
## Create a new order.
## - The order will be associated with the authenticated user.
## - Product stock will be checked and decremented.
## - **Request body**: Includes order status (optional, defaults to "PENDING") and a list of items with product IDs and quantities.
@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):

    try:
        created_order = create_order_service(
            db=db, order_data=order_data, current_user=current_user
        )
        return created_order
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create order.",
        )


# [auth] Fetch all orders
## Fetch orders.
## - Currently, any authenticated user can fetch all orders (paginated).
## - Consider adding role-based access (e.g., users see their own, admins see all).
@router.get("/", response_model=List[OrderOut])
async def fetch_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):

    orders = get_orders_service(db=db, skip=skip, limit=limit)
    return orders


# [auth] Fetch a single order, based on the id
## Fetch a single order by its ID.
## - Currently, any authenticated user can fetch any order.
## - Consider adding role-based access.
@router.get("/{order_id}", response_model=OrderOut)
async def fetch_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):

    db_order = get_order_by_id_service(db=db, order_id=order_id)
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or access denied.",  # Generic message
        )
    return db_order


# [auth] Update the basic info of an order
## Update an order's status.
## - Only admins can perform this action.
## - **Request body**: Contains the new `ord_status`.
@router.put("/{order_id}", response_model=OrderOut)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):

    try:
        updated_order = update_order_status_service(
            db=db,
            order_id=order_id,
            order_update_data=order_data,
            current_user=current_user,
        )
        if updated_order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        return updated_order
    except HTTPException as e:
        raise e
    except Exception:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update order status.",
        )


# [auth] Update the basic info of an order
## Delete an order by its ID.
## - Only admins can perform this action.
## - Associated order items will be deleted due to database cascade.
## - Product stock is NOT automatically reverted upon deletion.
@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):

    deleted_order = delete_order_service(
        db=db, order_id=order_id, current_user=current_user
    )
    if (
        deleted_order is None
    ):  # Service returns None if order not found (admin check is internal)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found for deletion",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

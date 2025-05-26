from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from typing import List, Optional

from database.models import Order, OrderItem, Product, User
from schemas.orders import OrderCreate, OrderUpdate, OrderOut
from schemas.auth import UserOut
from decimal import Decimal


## Only admins can create orders
## Validate the item(s) info
## Create a single user
def create_order_service(
    db: Session, order_data: OrderCreate, current_user: UserOut
) -> Order:
    # Basic validation for items
    if not order_data.items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Order must contain at least one item.",
        )

    # Create the main order record
    db_order = Order(
        ord_usr_id=current_user.usr_id,
        ord_status=order_data.ord_status or "PENDING",
    )
    db.add(db_order)
    try:
        db.flush()

        total_order_value = Decimal("0.0")

        for item_data in order_data.items:
            # Fetch the product
            product = (
                db.query(Product).filter(Product.prd_id == item_data.ord_prd_id).first()
            )

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {item_data.ord_prd_id} not found.",
                )

            # Check stock
            if product.prd_current_stock < item_data.ord_it_quant:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Not enough stock for product ID {product.prd_id} (Requested: {item_data.ord_it_quant}, Available: {product.prd_current_stock}).",
                )

            # Create order item
            db_order_item = OrderItem(
                ord_id=db_order.ord_id,
                ord_prd_id=item_data.ord_prd_id,
                ord_it_quant=item_data.ord_it_quant,
                ord_it_price=product.prd_price,
            )
            db.add(db_order_item)

            # Decrement product stock
            product.prd_current_stock -= item_data.ord_it_quant
            db.add(product)

            total_order_value += product.prd_price * item_data.ord_it_quant

        db.commit()
        db.refresh(db_order)
        # Refresh and load items for the response
        db.refresh(db_order, attribute_names=["items"])
        for item in db_order.items:
            db.refresh(item)

        return db_order

    except HTTPException as e:
        db.rollback()
        raise e
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the order.",
        )


## Any authenticated user
##  Get an order by its ID
def get_order_by_id_service(db: Session, order_id: int) -> Optional[Order]:
    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.ord_id == order_id)
        .first()
    )
    return order


## Any authenticated user
## Get all orders with pagination
def get_orders_service(db: Session, skip: int = 0, limit: int = 100) -> List[Order]:
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product)
    )
    return query.offset(skip).limit(limit).all()


## Only admins can update orders
## Update order status
def update_order_status_service(
    db: Session, order_id: int, order_update_data: OrderUpdate, current_user: UserOut
) -> Optional[OrderOut]:
    if not current_user.usr_isadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins only for updating order status.",
        )

    db_order = OrderOut.model_validate(
        db.query(Order).filter(Order.ord_id == order_id).first()
    )
    if not db_order:
        return None

    db_order.ord_status = order_update_data.ord_status
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    db.refresh(db_order, attribute_names=["items"])
    return db_order


## Only admins can delete orders
## Delete an order based on the id
def delete_order_service(
    db: Session, order_id: int, current_user: UserOut
) -> Optional[Order]:
    if not current_user.usr_isadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins only for deleting orders.",
        )

    db_order = db.query(Order).filter(Order.ord_id == order_id).first()
    if not db_order:
        return None

    db.delete(db_order)  # Cascade delete will handle OrderItems
    db.commit()
    return db_order

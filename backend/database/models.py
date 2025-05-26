## database/models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Numeric,
    DateTime,
    ForeignKey,
    Text,
    Date,
)
from sqlalchemy.orm import relationship, DeclarativeBase
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    usr_id = Column(Integer, primary_key=True)
    usr_name = Column(Text, nullable=False)
    usr_email = Column(Text, nullable=False, unique=True)
    usr_password = Column(Text, nullable=False)
    usr_isadmin = Column(Boolean, default=False)
    usr_created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    usr_updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    orders = relationship("Order", back_populates="user")


class Client(Base):
    __tablename__ = "clients"

    cli_id = Column(Integer, primary_key=True)
    cli_name = Column(Text, nullable=False)
    cli_email = Column(Text, nullable=False, unique=True)
    cli_cpf = Column(String(11), nullable=False, unique=True)
    cli_created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    cli_updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    cli_created_by = Column(Integer, nullable=False)


class Product(Base):
    __tablename__ = "products"

    prd_id = Column(Integer, primary_key=True)
    prd_desc = Column(Text, nullable=False)
    prd_category = Column(Text)
    prd_section = Column(Text)
    prd_price = Column(Numeric(10, 2), nullable=False)
    prd_barcode = Column(Text, unique=True)
    prd_initial_stock = Column(Integer, nullable=False)
    prd_current_stock = Column(Integer, nullable=False)
    prd_expiring_date = Column(Date)
    prd_created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    prd_updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    images = relationship(
        "ProductImage", back_populates="product", cascade="all, delete-orphan"
    )
    order_items = relationship("OrderItem", back_populates="product")


class ProductImage(Base):
    __tablename__ = "product_images"

    img_id = Column(Integer, primary_key=True)
    prd_id = Column(
        Integer, ForeignKey("products.prd_id", ondelete="CASCADE"), nullable=False
    )
    img_url = Column(Text, nullable=False)
    img_created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    product = relationship("Product", back_populates="images")


class Order(Base):
    __tablename__ = "orders"

    ord_id = Column(Integer, primary_key=True)
    ord_status = Column(Text, nullable=False)
    ord_usr_id = Column(Integer, ForeignKey("users.usr_id"))
    ord_created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    ord_updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="orders")
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "orders_items"

    ord_it_id = Column(Integer, primary_key=True)
    ord_id = Column(
        Integer, ForeignKey("orders.ord_id", ondelete="CASCADE"), nullable=False
    )
    ord_prd_id = Column(Integer, ForeignKey("products.prd_id"), nullable=False)
    ord_it_quant = Column(Integer, nullable=False)
    ord_it_price = Column(Numeric(10, 2), nullable=False)
    ord_created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    ord_updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

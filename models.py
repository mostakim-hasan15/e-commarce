from database import Base
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, ForeignKey, JSON, Numeric,UniqueConstraint,CheckConstraint
from datetime import datetime, timezone
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    id = Column(Integer,primary_key=True,index=True)
    user_name = Column(String, unique= True, nullable=False)
    email = Column(String,unique=True,nullable=False)
    hashed_password = Column(String,nullable=False)
    phone_number = Column(String)
    role = Column(String, default="user") # admin or user
    created_at = Column(DateTime, default=datetime.now)
    refresh_tokens = relationship("RefreshToken",back_populates="user",cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer,primary_key=True, index=True)
    name = Column(String, unique= True, nullable=False)
    description = Column(String)
    created_at = Column(DateTime,default=datetime.now)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer,primary_key=True, index=True)
    name = Column(String,nullable=False)
    description = Column(String)
    stock_quantity = Column(Integer, default=0)
    price = Column(Numeric(12,2),nullable=False)
    image = Column(String)
    category_id = Column(Integer,ForeignKey("categories.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime,default=datetime.now, onupdate=datetime.now)

class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer,primary_key=True, index=True)
    user_id = Column(Integer,ForeignKey("users.id"),unique=True, nullable=False)
    created_at = Column(DateTime, default= datetime.now)
    updated_at = Column(DateTime,default=datetime.now, onupdate=datetime.now)

class Cart_items(Base):
    __tablename__ = "cart_items"
    id = Column(Integer,primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"),nullable=False)
    product_id = Column(Integer,ForeignKey("products.id"),nullable=False)
    quantity = Column(Integer,default=1,nullable=False)
    __table_args__ = (
      UniqueConstraint("cart_id", "product_id", name="unique_cart_product"),
  )

class Orders(Base):
    __tablename__ = "orders"
    id = Column(Integer,primary_key=True, index=True)
    user_id = Column(Integer,ForeignKey("users.id"),nullable=False)
    order_number = Column(String, unique=True,nullable=False)
    total_amount = Column(Numeric(12,2),nullable=False)
    status = Column(String, default="pending", nullable=False)
    payment_status = Column(String, default="unpaid", nullable=False)
    shipping_address = Column(String,nullable=False)
    created_at = Column(DateTime, default= datetime.now)
    updated_at = Column(DateTime,default=datetime.now, onupdate=datetime.now)
    order_items = relationship("Order_item", back_populates="order",cascade="all, delete-orphan")

class Order_item(Base):
     __tablename__ = "order_item"
     id = Column(Integer,primary_key=True, index=True)
     order_id = Column(Integer,ForeignKey("orders.id"),nullable=False)
     product_id = Column(Integer,ForeignKey("products.id"),nullable=False)
     product_name = Column(String,nullable=False)
     unit_price = Column(Numeric(12,2),nullable=False)
     quantity  = Column(Integer,default=1, nullable=False)
     sub_total = Column(Numeric(12,2),nullable=False)
     order = relationship("Orders", back_populates="order_items")

class Payment(Base):
     __tablename__ = "payments"
     id = Column(Integer,primary_key=True, index=True)
     order_id = Column(Integer,ForeignKey("orders.id"),nullable=False)
     user_id = Column(Integer,ForeignKey("users.id"), nullable=False)
     transaction_id = Column(String, unique=True, nullable=False)
     gateway = Column(String)
     amount = Column(Numeric(12,2),nullable=False)
     currency = Column(String, default="BDT")
     status = Column(String, default="pending") # pending, success, failed, refunded 
     payment_method = Column(String)
     gateway_response = Column(JSON)
     paid_at = Column(DateTime)
     created_at = Column(DateTime, default=datetime.now)

class Address(Base):
    __tablename__ = "addresses"
    id = Column(Integer,primary_key=True, index=True)
    user_id = Column(Integer,ForeignKey("users.id"),nullable=False) 
    full_name = Column(String,nullable=False)
    phone = Column(String,nullable=False)
    division = Column(String,nullable=False) 
    district = Column(String,nullable=False) 
    city = Column(String,nullable=False) 
    address_line = Column(String)
    is_default = Column(Boolean, default=False)


class Reviews(Base):
     __tablename__ = "reviews"
     id = Column(Integer,primary_key=True, index=True)
     user_id = Column(Integer,ForeignKey("users.id"),nullable=False)
     product_id = Column(Integer,ForeignKey("products.id"),nullable=False)
     rating = Column(Float, default=5.0)
     comment = Column(String)
     created_at = Column(DateTime, default=datetime.now)
     __table_args__ = (
      UniqueConstraint("user_id", "product_id", name="unique_user_product_review"),
      CheckConstraint("rating >= 1.0 AND rating <= 5.0", name="check_rating_range"),
  )

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    user = relationship("User", back_populates="refresh_tokens")



    






from fastapi import FastAPI, APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional
from database import SessionLocal
from models import User, RefreshToken, Category,Product, Cart, Cart_items,Orders,Order_item
from router.auth import get_current_user
from fastapi.responses import JSONResponse
from decimal import Decimal
from uuid import uuid4

router = APIRouter()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency =  Annotated[dict, Depends(get_current_user)]

class OrderCreate(BaseModel):
    shipping_address: str = Field(min_length=5)

class OrderStatusUpdate(BaseModel):
    status: str

class PaymentStatusUpdate(BaseModel):
    payment_status: str

@router.post("/create_order")
def create_order( data: OrderCreate,db: db_dependency, current_user: user_dependency):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")
    
    cart = db.query(Cart).filter(Cart.user_id == current_user["id"]).first()
    if not cart:
        raise HTTPException( status_code=404,detail="Cart not found")

    cart_items = db.query(Cart_items).filter(Cart_items.cart_id == cart.id).all()
    if not cart_items:
        raise HTTPException( status_code=400, detail="Cart is empty")

    total_amount = Decimal("0.00")
    order_items_data = []

    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id,Product.is_active == True).first()
        if not product:
            raise HTTPException(status_code=404,detail=f"Product {item.product_id} not found or inactive")

        if item.quantity <= 0:
            raise HTTPException(status_code=400,detail="Invalid quantity" )

        if product.stock_quantity < item.quantity:
            raise HTTPException(status_code=400,detail=f"Insufficient stock for {product.name}")

        unit_price = product.price
        sub_total = unit_price * item.quantity

        total_amount += sub_total

        order_items_data.append({
            "product_id": product.id,
            "product_name": product.name,
            "unit_price": unit_price,
            "quantity": item.quantity,
            "sub_total": sub_total
        })

    try:
        new_order = Orders(
            user_id=current_user["id"],
            order_number=f"ORD-{uuid4().hex[:12].upper()}",
            total_amount=total_amount,
            shipping_address=data.shipping_address,
            status="pending",
            payment_status="unpaid"
        )

        db.add(new_order)
        db.flush()

        for item in order_items_data:
            new_order_item = Order_item(
                order_id=new_order.id,
                product_id=item["product_id"],
                product_name=item["product_name"],
                unit_price=item["unit_price"],
                quantity=item["quantity"],
                sub_total=item["sub_total"]
            )

            db.add(new_order_item)

        db.commit()
        db.refresh(new_order)

        return {"message": "Order created successfully"}

    except Exception:
        db.rollback()
        raise

@router.get("/view/my_order")
def my_order(db: db_dependency, current_user: user_dependency):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    user = db.query(Orders).filter(Orders.user_id == current_user.get("id")).all()
    if not user:
        raise HTTPException(status_code= 404, detail="Order not found")
    return user

@router.get("/view/my_order_id/{order_id}")
def my_order(db: db_dependency, current_user: user_dependency, order_id: int):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    user = db.query(Orders).filter(Orders.user_id == current_user.get("id"),Orders.id == order_id).first()
    if not user:
        raise HTTPException(status_code= 404, detail="Order not found")
    return user

@router.delete("/delete/my_order_id/{order_id}")
def my_order(db: db_dependency, current_user: user_dependency, order_id: int):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    user = db.query(Orders).filter(Orders.user_id == current_user.get("id"),Orders.id == order_id).first()
    if not user:
        raise HTTPException(status_code= 404, detail="Order not found")
    
    db.query(Orders).filter(Orders.user_id == current_user.get("id"),Orders.id == order_id).delete()
    db.commit()
    return JSONResponse(status_code=200, content={"message" : "Order Delete Successfuly"})

@router.get("/view/my_order_items/{order_id}")
def view_my_order_items(order_id: int, db: db_dependency, current_user: user_dependency):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")
    
    order = db.query(Orders).filter( Orders.id == order_id, Orders.user_id == current_user.get("id")).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items = db.query(Order_item).filter(Order_item.order_id == order_id).all()
    return items

# pending, confirmed, shipped, shipped , delivered, cancelled
# Admin

@router.put("/admin/update_order_status/{order_id}")
def update_order_status(order_id: int, data: OrderStatusUpdate, db: db_dependency, current_user: user_dependency):
    if current_user is None or current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Faile Authinticate Or Admin access required")

    order = db.query(Orders).filter(Orders.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    allowed_status = ["pending", "processing", "shipped", "delivered", "cancelled"]

    if data.status not in allowed_status:
        raise HTTPException(status_code=400, detail="Invalid order status")

    order.status = data.status
    db.commit()
    db.refresh(order)
    return {"message": "Order status updated successfully", "order_id": order.id, "status": order.status}

@router.put("/admin/update_payment_status/{order_id}")
def update_payment_status(order_id: int, data: PaymentStatusUpdate, db: db_dependency, current_user: user_dependency):
    if current_user is None or current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Faile Authinticate Or Admin access required")

    order = db.query(Orders).filter(Orders.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "delivered":
        raise HTTPException(status_code=400, detail="Order is not delivered yet")

    if data.payment_status not in ["paid", "unpaid", "refunded", "failed"]:
        raise HTTPException(status_code=400, detail="Invalid payment status")

    order.payment_status = data.payment_status
    db.commit()
    db.refresh(order)
    return {"message": "Payment status updated successfully"}

@router.get("/admin/orders/status/{status}")
def view_orders_by_status(status: str, db: db_dependency, current_user: user_dependency):
    if current_user is None or current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Faile Authinticate Or Admin access required")

    allowed_status = ["pending", "processing", "shipped", "delivered", "cancelled"]
    if status not in allowed_status:
        raise HTTPException(status_code=400, detail="Invalid order status")

    orders = db.query(Orders).filter(Orders.status == status).all()
    if not orders:
        raise HTTPException(status_code=404, detail="No orders found with this status")
    return orders

@router.get("/admin/payment/status/{payment_status}")
def view_orders_by_status(payment_status: str, db: db_dependency, current_user: user_dependency):
    if current_user is None or current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Faile Authinticate Or Admin access required")

    allowed_status = ["paid", "unpaid", "refunded", "failed"]
    if payment_status not in allowed_status:
        raise HTTPException(status_code=400, detail="Invalid order status")

    orders = db.query(Orders).filter(Orders.payment_status == payment_status).all()
    if not orders:
        raise HTTPException(status_code=404, detail="No orders found with this status")
    return orders




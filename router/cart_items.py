from fastapi import FastAPI, APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional
from database import SessionLocal
from models import User, RefreshToken, Category,Product, Cart, Cart_items
from router.auth import get_current_user
from fastapi.responses import JSONResponse

router = APIRouter()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency =  Annotated[dict, Depends(get_current_user)]

class CartItemsCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1)

class Update_quentity(BaseModel):
    quantity: int = Field(default=1)

@router.post("/create/cart_items")
def create_cart_items(cart_item: CartItemsCreate, user: user_dependency,db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    product = db.query(Product).filter(Product.id == cart_item.product_id,Product.is_active == True).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found or inactive")

    cart = db.query(Cart).filter(Cart.user_id == user.get("id")).first()
    if cart is None:
        cart = Cart(user_id=user.get("id"))
        db.add(cart)
        db.commit()
        db.refresh(cart)

    existing_item = db.query(Cart_items).filter(Cart_items.cart_id == cart.id,Cart_items.product_id == cart_item.product_id).first()
    if existing_item:
        existing_item.quantity += cart_item.quantity
    else:
        new_item = Cart_items(
            cart_id=cart.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity
        )
        db.add(new_item)

    db.commit()
    return {"message": "Product added to cart successfully"}

@router.get("/cart_items/my_cart")
def get_cart_items(user: user_dependency, db: db_dependency):

    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    cart = db.query(Cart).filter(Cart.user_id == user.get("id")).first()
    if cart is None:
        raise HTTPException(status_code=404,detail="Cart not found")

    cart_items = db.query(Cart_items).filter(Cart_items.cart_id == cart.id).all()
    return cart_items


@router.put("/cart_items/{product_id}/quantity")
def update_quentity( product_id: int, user: user_dependency, db: db_dependency,quentity_update: Update_quentity):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    cart = db.query(Cart).filter(Cart.user_id == user.get("id")).first()

    if cart is None:
        raise HTTPException(status_code=404, detail="Cart not found")

    cart_item = db.query(Cart_items).filter(Cart_items.cart_id == cart.id,Cart_items.product_id == product_id).first()

    if cart_item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if quentity_update.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")

    cart_item.quantity = quentity_update.quantity

    db.commit()
    db.refresh(cart_item)

    return {"message": "Quantity updated successfully","product_id": cart_item.product_id, "quantity": cart_item.quantity }

@router.delete("/delete/cart_items/{product_id}")
def delete_cart_items(user: user_dependency,db: db_dependency,product_id: int):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    cart = db.query(Cart).filter(Cart.user_id == user.get("id")).first()
    if cart is None:
        raise HTTPException(status_code=404, detail='Cart Not Found')

    cart_items = db.query(Cart_items).filter(Cart_items.cart_id == cart.id, Cart_items.product_id == product_id).first()
    if cart_items is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    db.query(Cart_items).filter(Cart_items.cart_id == cart.id, Cart_items.product_id == product_id).delete()
    db.commit()
    return {"message": "Delete Cart_item" }

    
   
    
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional
from database import SessionLocal
from models import User, RefreshToken, Category,Product, Cart
from router.auth import get_current_user
from fastapi.responses import JSONResponse
from decimal import Decimal
router = APIRouter()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency =  Annotated[dict, Depends(get_current_user)]

@router.post("/create_cart")
def create_cart(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=403, detail="Failed Authentication")

    existing_cart = db.query(Cart).filter(Cart.user_id == user.get("id")).first()
    if existing_cart:
        raise HTTPException(status_code=400, detail="Cart already exists")

    new_model = Cart(
        user_id=user.get("id")
    )

    db.add(new_model)
    db.commit()

    return JSONResponse(status_code=201, content={"message": "Create Cart Successfully"})


@router.get("/view_cart")
def view_cart(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=403, detail="Failed Authentication")

    cart_user = db.query(Cart).filter(Cart.user_id == user.get("id")).first()
    if cart_user is None:
        raise HTTPException(status_code=404, detail="Cart not found")

    return cart_user
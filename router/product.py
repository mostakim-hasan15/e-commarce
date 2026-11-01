from fastapi import FastAPI, APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional
from database import SessionLocal
from models import User, RefreshToken, Category,Product
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

class ValidProduct(BaseModel):
    name: str
    description: str
    stock_quantity: int
    price: Decimal
    image: str
    is_active: bool
    category_id: int

class UpdateProduct(BaseModel):
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    stock_quantity: Optional[int] = Field(default=None)
    price: Optional[Decimal] = Field(default=None)
    image: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)
    category_id: Optional[int] = Field(default=None)


# User

@router.get("/veiw_product")
def view_product(user: user_dependency, db: db_dependency):
    if user is None:
            raise HTTPException(status_code=403, detail="Faile Authinticate")
    return db.query(Product).all()

@router.get("/veiws_product/{product_id}")
def view_product(user: user_dependency, db: db_dependency,product_id: int):
    if user is None:
            raise HTTPException(status_code=403, detail="Faile Authinticate")
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product Not Found")
    return product

# Admin

@router.post("/admin/create_product")
def create_category(user: user_dependency, db: db_dependency, newproduct: ValidProduct):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Faile Authinticate")

    category = db.query(Category).filter(Category.id == newproduct.category_id).first()
    if category is None:
        raise HTTPException(status_code=404,detail="Category not found")

    new_data = Product(
        name = newproduct.name,
        description = newproduct.description,
        stock_quantity = newproduct.stock_quantity,
        price = newproduct.price,
        image = newproduct.image,
        is_active = newproduct.is_active,
        category_id = newproduct.category_id
    )
    db.add(new_data)
    db.commit()
    return JSONResponse(status_code=201, content={"message":"Create Product Successfuly"})

@router.put("/admin/update_product/{product_id}")
def create_category(user: user_dependency, db: db_dependency, product_id: int, newproduct: UpdateProduct):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Faile Authinticate")

    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product Not Found")

    new_data = newproduct.model_dump(exclude_unset=True)

    if "category_id" in new_data:
        category = db.query(Category).filter(Category.id == new_data["category_id"]).first()
        if category is None: 
            raise HTTPException(status_code=404,detail="Category not found")

    for key, value in new_data.items():
        setattr(product, key, value)
    db.commit()
    return JSONResponse(status_code=200, content={"message":"Update Product Successfuly"})

@router.delete("/admin/delete_product/{product_id}")
def create_category(user: user_dependency, db: db_dependency, product_id: int):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Faile Authinticate")

    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product Not Found")
    
    db.query(Product).filter(Product.id == product_id).delete()
    db.commit()
    return JSONResponse(status_code=200, content={"message":"Delete Product Successfuly"})

from fastapi import FastAPI, APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional
from database import SessionLocal
from models import User, RefreshToken, Category,Product
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

class ValidCategory(BaseModel):
    name: str
    description: str

class UpdateCategory(BaseModel):
    name: Optional[str] = Field(default = None)
    description: Optional[str] = Field(default = None)



#user

@router.get("/views_catagory")
def view_catagory(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Faile Authinticate")
    return db.query(Category).all()

@router.get("/view_catagory/{category_id}")
def view_catagory(db: db_dependency, user: user_dependency, category_id: int):
    if user is None:
        raise HTTPException(status_code=401, detail="Faile Authinticate")

    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
         raise HTTPException(status_code=404, detail="Category Not Found")
    return category

# amdin

@router.post("/admin/create_category")
def create_category(user: user_dependency, db: db_dependency, newcategory: ValidCategory):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Faile Authinticate")

    existing_category = db.query(Category).filter(Category.name == newcategory.name).first()
    if existing_category:
        raise HTTPException(status_code=400, detail="Category name already exist")

    new_data = Category(
        name = newcategory.name,
        description = newcategory.description
    )
    db.add(new_data)
    db.commit()
    return JSONResponse(status_code=201, content={"message":"Create Catagory Successfuly"})

@router.put("/admin/update_category/{category_id}")
def update_category(user: user_dependency, db: db_dependency,category_id:int, new_category: UpdateCategory):
    if user is None or user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Faile Authinticate")

    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category_name = db.query(Category).filter(Category.name == new_category.name).filter(Category.id != category_id).first()
    if category_name is not None:
            raise HTTPException(status_code=400, detail="category_name already existing")

    new_data = new_category.model_dump(exclude_unset=True)
    for key,value in new_data.items():
        setattr(category, key,value)

    db.commit()
    return  JSONResponse (status_code=200, content={"message":"Update Catagory Successfuly"})
    
@router.delete("/admin/delete_category/{category_id}")
def update_category(user: user_dependency, db: db_dependency,category_id:int):
    if user is None or user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Faile Authinticate")

    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    product = db.query(Product).filter(Product.category_id == category_id).first()
    if product is not None:
        raise HTTPException(status_code=400, detail="Cannot delete category because products exist in this category")
    
    db.query(Category).filter(Category.id == category_id).delete()
    db.commit()
    return  JSONResponse (status_code=200, content={"message":"Delete Catagory Successfuly"})
    
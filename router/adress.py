from fastapi import FastAPI, APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional
from database import SessionLocal
from models import User, RefreshToken, Category,Product, Address
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

class AddressCreate(BaseModel):
    full_name: str
    phone: str
    division: str
    district: str
    city: str
    address_line: str
    is_default: bool = False

class AddressUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None) 
    phone: Optional[str] = Field(default=None) 
    division: Optional[str] = Field(default=None) 
    district: Optional[str] = Field(default=None) 
    city: Optional[str] = Field(default=None) 
    address_line: Optional[str] = Field(default=None)

@router.get("/View_address")
def create_address( db: db_dependency, current_user: user_dependency):
     if current_user is None:
        raise HTTPException(status_code=403, detail="Faile Authinticate")

     user = db.query(Address).filter(Address.user_id == current_user.get("id")).all()
     if not user:
        raise  HTTPException(status_code=404, detail="Address Not Found")
     return user

@router.post("/create_address")
def create_address(data: AddressCreate, db: db_dependency, current_user: user_dependency):
     if current_user is None:
        raise HTTPException(status_code=403, detail="Faile Authinticate")
     
     new_address = Address(
        user_id=current_user.get("id"),
        full_name=data.full_name,
        phone=data.phone,
        division=data.division,
        district=data.district,
        city=data.city,
        address_line=data.address_line,
        is_default=data.is_default
     )

     if data.is_default:
        db.query(Address).filter(Address.user_id == current_user.get("id")).update({"is_default": False})

     db.add(new_address)
     db.commit()
     db.refresh(new_address)
     return { "message": "Address created successfully"}

@router.put("/update_address/{address_id}")
def create_address(data: AddressUpdate, address_id: int, db: db_dependency, current_user: user_dependency):
     if current_user is None:
        raise HTTPException(status_code=403, detail="Faile Authinticate")

     user = db.query(Address).filter(Address.id == address_id).filter(Address.user_id == current_user.get("id")).first()
     if user  is None:
         raise  HTTPException(status_code=404, detail="Address Not Found")

     new_data = data.model_dump(exclude_unset=True)
     for key,value in new_data.items():
         setattr(user, key, value)

     db.commit()
     return JSONResponse(status_code=200, content={"message":"address update successfuly"})

@router.put("/set_default_address/{address_id}")
def set_default_address(address_id: int,db: db_dependency,current_user: user_dependency):
    if current_user is None:
        raise HTTPException(status_code=403, detail="Failed Authentication")

    address = db.query(Address).filter(Address.id == address_id,Address.user_id == current_user.get("id")).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address Not Found")

    db.query(Address).filter( Address.user_id == current_user.get("id")).update({"is_default": False})
    address.is_default = True
    db.commit()
    db.refresh(address)
    return JSONResponse(status_code=200, content={"message":"is default update successfuly"})

@router.delete("/delete_address/{address_id}")
def create_address( address_id: int, db: db_dependency, current_user: user_dependency):
     if current_user is None:
        raise HTTPException(status_code=403, detail="Faile Authinticate")

     user = db.query(Address).filter(Address.id == address_id).filter(Address.user_id == current_user.get("id")).first()
     if user  is None:
         raise  HTTPException(status_code=404, detail="Address Not Found")

     db.query(Address).filter(Address.id == address_id).filter(Address.user_id == current_user.get("id")).delete()
     db.commit()
     return JSONResponse(status_code=200, content={"message":"address delete successfuly"})

# Admin

@router.get("/admin/View_address")
def view_address(db: db_dependency, current_user: user_dependency):
    if current_user is None or current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Failed Authentication")

    user = db.query(Address).all()

    if not user:
        raise HTTPException(status_code=404, detail="Address Not Found")

    return user

@router.delete("/admin/delete_address/{address_id}")
def create_address( address_id: int, db: db_dependency, current_user: user_dependency):
     if current_user is None or current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Faile Authinticate")

     user = db.query(Address).filter(Address.id == address_id).first()
     if not user:
         raise  HTTPException(status_code=404, detail="Address Not Found")

     db.query(Address).filter(Address.id == address_id).delete()
     db.commit()
     return JSONResponse(status_code=200, content={"message":"address delete successfuly"})





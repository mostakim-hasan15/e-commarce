from fastapi import FastAPI, APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional
from database import SessionLocal
from models import User, RefreshToken, Category
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

class UpdateRole(BaseModel):
    role: str

@router.get("/admin/all_user")
def get_all_user(user: user_dependency, db: db_dependency):

    if user is None or user.get("role") not in ["admin"]:
        raise HTTPException(status_code=401, detail="Failed Authentication")
    return db.query(User).all()

@router.get("/admin/all_user/{user_id}")
def get_all_user(user: user_dependency, db: db_dependency, user_id: int):

    if user is None or user.get("role") not in ["admin"]:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="user not fount")
    return user

@router.delete("/admin/delete_user/{user_id}")
def get_all_user(user: user_dependency, db: db_dependency, user_id: int):

    if user is None or user.get("role") not in ["admin"]:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="user not fount")

    db.query(User).filter(User.id == user_id).delete()
    db.commit()
    return  JSONResponse(status_code=200, content={"message":"user delete successfuly"})

@router.put("/admin/update/user_role/{user_id}")
def update_role(user: user_dependency, db: db_dependency,user_id:int, roleupdate: UpdateRole):
    if user is None or user.get("role") != "admin":
        raise HTTPException( status_code=403, detail="Faile Authinticate")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise  HTTPException(status_code=404, detail="User not found")

    user_data = roleupdate.model_dump(exclude_unset=True)
    for key,value in user_data.items():
        setattr(user,key,value)
    db.commit()
    return JSONResponse(status_code=200, content={"message" : "Role update successfuly"})

@router.get("/admin/view_profile")
def admin_profile(user: user_dependency, db:db_dependency):
    if user is None or user.get("role") != "admin":
        raise HTTPException (status_code=403, detail="Faile Authinticate")
    
    user = db.query(User).filter(User.id == user.get("id")).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
    
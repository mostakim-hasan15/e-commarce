from fastapi import FastAPI, APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional
from database import SessionLocal
from models import User, RefreshToken
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
import hashlib
import os
import smtplib
from email.message import EmailMessage
import secrets
from dotenv import load_dotenv



router = APIRouter()
load_dotenv()
reset_otp = {}
verified_reset_tokens = {}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
SECRET_KEY ='86746eeb8285ca279c6251e0bd83cdd50c88027b934a93f19d8b9af782139516'
ALGORITHM = 'HS256' 
OAuth2_bearer = OAuth2PasswordBearer(tokenUrl='login')

class CreateUsers(BaseModel):
    email : str
    user_name : str
    password : str
    phone_number: str
    role : str

class UpdateUser(BaseModel):
    email : Optional[str] = Field(default=None)
    user_name : Optional[str] = Field(default=None)
    phone_number : Optional[str] = Field(default=None)

class UpdatePassword(BaseModel):
    current_password : str
    new_password: str

class NewPassword(BaseModel):
    email: str

class Veryfy_otp(BaseModel):
    email: str
    otp: str = Field(min_length=6, max_length=6)

class ResetPassword(BaseModel):
    reset_token: str
    new_password: str
    confirm_password: str

class LogoutRequest(BaseModel):
    refresh_token: str


def authinticate_user(user_name, password, db):
    user = db.query(User).filter(User.user_name == user_name).first()
    if user is None:
        return False
    if bcrypt_context.verify(password, user.hashed_password):
        return user
    return False

def create_access_token(user_name: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {'sub': user_name, 'id': user_id, 'role': role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_name: str, user_id: int, role: str):

    expires = datetime.now(timezone.utc) + timedelta(days=7)
    encode = { "sub": user_name, "id": user_id, "role": role, "token_type": "refresh", "exp": expires}

    token = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
    return token, expires

def get_current_user(token : Annotated[str, Depends(OAuth2_bearer)]):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username :str = payload.get("sub")
        user_id: int = payload.get("id")
        role: str = payload.get("role")

        if username is None or user_id is None:
            raise HTTPException(status_code=404, detail="User Not found")
        return {"user_name" : username, "id": user_id, "role" : role}
    except:
         raise HTTPException(status_code=404, detail="User Not found")
    
user_dependency =  Annotated[dict, Depends(get_current_user)]

@router.post("/create_user")
def create_user(db: db_dependency, new_user: CreateUsers):
    existing_username = db.query(User).filter(User.user_name == new_user.user_name).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username allready exist")

    existing_email = db.query(User).filter(User.email == new_user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email allready exist")

    new_model = User(
        user_name = new_user.user_name,
        email = new_user.email,
        hashed_password  = bcrypt_context.hash(new_user.password),
        phone_number = new_user.phone_number,
        role = new_user.role
    )
    db.add(new_model)
    db.commit()
    return JSONResponse(status_code=201, content={'message' : 'User created successfully'})

@router.post("/login")
def login(db: db_dependency, from_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authinticate_user(from_data.username, from_data.password, db)

    if not user:
        raise HTTPException(status_code=401, detail="Failed authentication")

    token = create_access_token(user.user_name, user.id, user.role,timedelta(minutes=30))

    refresh_token, refresh_expires = create_refresh_token(user.user_name,user.id,user.role)

    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

    new_refresh_token = RefreshToken(user_id = user.id,token_hash=token_hash,expires_at=refresh_expires)

    db.add(new_refresh_token)
    db.commit()

    return { "access_token": token,"refresh_token": refresh_token,"token_type": "bearer"}

@router.put("/edit_user")
def edit_user( db: db_dependency, users: user_dependency, update_user: UpdateUser):
    
    user = db.query(User).filter(User.id == users.get("id")).first()

    if user is None:
        raise HTTPException( status_code=404, detail="User not found in database")

    user_data = update_user.model_dump(exclude_unset=True)

    for key, value in user_data.items():
        setattr(user, key, value)

    db.commit()
    return {"message": "User updated successfully"}

@router.put('/passwordchange')
def update_password(user: user_dependency, db : db_dependency, update_password : UpdatePassword):

    if user is None: 
        raise HTTPException(status_code=401, detail='Failed Authentication')
    
    user = db.query(User).filter(User.id == user.get('id')).first()
    
    if not bcrypt_context.verify(update_password.current_password, user.hashed_password):
        raise HTTPException(status_code=401, detail='Wrong Password')

    user.hashed_password = bcrypt_context.hash(update_password.new_password)

    db.add(user)
    db.commit()
    return JSONResponse(status_code=200, content={'message' : 'Password updated successfully'})

@router.get('/user')
def get_user_details(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    
    current_user = db.query(User).filter(User.id == user.get('id')).first()
    if current_user is None:
        raise HTTPException(status_code=404, detail='User not found')
    
    return {
        'id': current_user.id,
        'email': current_user.email,
        'username': current_user.user_name,
        'phone_number': current_user.phone_number,
        'role': current_user.role,
        'created_at': current_user.created_at,
    }


@router.post("/logout")
def logout(logout_data: LogoutRequest, db: db_dependency, user: user_dependency):

    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    token_hash = hashlib.sha256(logout_data.refresh_token.encode()).hexdigest()
    stored_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash,RefreshToken.user_id == user.get("id")).first()

    if stored_token is None:
        raise HTTPException(status_code=404,detail="Refresh token not found")

    if stored_token.revoked_at is not None:
        raise HTTPException( status_code=400,detail="Refresh token already revoked")

    if stored_token.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        stored_token.revoked_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=401,detail="Refresh token expired")

    stored_token.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return { "message": "Logout successful"}

@router.post("/refresh-token")
def refresh_access_token(refresh_token: str, db: db_dependency):
    try:
        payload = jwt.decode( refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("token_type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user_id = payload.get("id")
        user_name = payload.get("sub")
        role = payload.get("role")

        if user_id is None or user_name is None or role is None:
            raise HTTPException( status_code=401,detail="Invalid refresh token")

    except JWTError:
        raise HTTPException(status_code=401,detail="Invalid or expired refresh token")

    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

    stored_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash,RefreshToken.user_id == user_id).first()

    if stored_token is None:
        raise HTTPException( status_code=401, detail="Refresh token not found")

    if stored_token.revoked_at is not None:
        raise HTTPException( status_code=401,detail="Refresh token has been revoked")

    if stored_token.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    new_access_token = create_access_token(user.user_name, user.id, user.role, timedelta(minutes=30))

    return { "access_token": new_access_token,"token_type": "bearer" }

@router.post("/forgot_password")
def forgot_pasword(db: db_dependency, password: NewPassword):
    user = db.query(User).filter(User.email == password.email).first()

    if user is None:
        raise HTTPException(status_code=404, detail="Email not found")

    otp = str(secrets.randbelow(1000000)).zfill(6)

    msg = EmailMessage()
    msg["Subject"] = "Password Reset OTP"
    msg["From"] = os.getenv("SMTP_EMAIL")
    msg["To"] = user.email
    msg.set_content(f"Your OTP is: {otp}\nIt will expire in 5 minutes.")

    # "smtp.gmail.com"  ar kaj hlo google server ar sathe connect hye mail receive kre user ar email ar mail take sent kra 

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:

        server.login( os.getenv("SMTP_EMAIL"), os.getenv("SMTP_PASSWORD"))
        server.send_message(msg)

    reset_otp[user.email] = {
        "otp": otp,
        "expires": datetime.now(timezone.utc) + timedelta(minutes=5)
    }

    return {"message": "OTP sent to your Gmail"}


@router.post("/verify_otp")
def verify_otp(data: Veryfy_otp):

    stored_data = reset_otp.get(data.email)

    if stored_data is None:
        raise HTTPException( status_code=400,detail="OTP not found or expired")

    if datetime.now(timezone.utc) > stored_data["expires"]:
        reset_otp.pop(data.email, None)
        raise HTTPException(status_code=400, detail="OTP expired" )

    if stored_data["otp"] != data.otp:
        raise HTTPException(status_code=400,detail="Invalid OTP")

    reset_token = secrets.token_urlsafe(32)

    verified_reset_tokens[reset_token] = {
        "email": data.email,
        "expires": datetime.now(timezone.utc) + timedelta(minutes=5)
    }

    reset_otp.pop(data.email, None)

    return {"message": "OTP verified successfully", "reset_token": reset_token}


@router.post("/reset_password")
def reset_password(data: ResetPassword, db: db_dependency):

    if data.new_password != data.confirm_password:
        raise HTTPException( status_code=400,detail="Password does not match")

    # Reset token verify korte hobe
    reset_data = verified_reset_tokens.get(data.reset_token)

    if reset_data is None:
        raise HTTPException( status_code=400,detail="Invalid or expired reset token")

    email = reset_data["email"]

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=404,detail="User not found")

    user.hashed_password = bcrypt_context.hash(data.new_password)
    db.commit()

    verified_reset_tokens.pop(data.reset_token, None)
    return {"message": "Password reset successfully"}

@router.delete("/delete/user")
def delete_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=403, detail="Faile Authinticate")
    
    remove_user = db.query(User).filter(User.id == user.get("id")).first()
    if remove_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.query(User).filter(User.id == user.get("id")).delete()
    db.commit()
    return JSONResponse(status_code=200, content={"message":"User delete profile"})



    
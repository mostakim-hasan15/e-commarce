from fastapi import FastAPI, Depends
from database import SessionLocal, engine
import models
from typing import Annotated
from sqlalchemy.orm import Session
from router import auth
from router import ad
from router import catagory,product,cart,cart_items,order,adress


app = FastAPI()
models.Base.metadata.create_all(bind = engine)
app.include_router(auth.router)
app.include_router(ad.router)
app.include_router(catagory.router)
app.include_router(product.router)
app.include_router(cart.router)
app.include_router(cart_items.router)
app.include_router(order.router)
app.include_router(adress.router)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session,Depends(get_db)]


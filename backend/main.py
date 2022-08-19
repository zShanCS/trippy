
from square.client import Client
import os
import uuid
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI, HTTPException, Form, UploadFile
from sqlalchemy.orm import Session
from PIL import Image
import crud, models, schemas
from database import SessionLocal, engine
from fastapi.staticfiles import StaticFiles
models.Base.metadata.create_all(bind=engine)

from utils import create_checkout_link

app = FastAPI()
origins = [
    "*",
    "http://localhost:3000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = 'http://127.0.0.1:8000/'


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/items/", response_model=schemas.Item )
def create_item_for_user(
    user_id: int,file: UploadFile, title:str = Form(...), description: str = Form(...), price:int = Form(...), stock:int = Form(...),   db: Session = Depends(get_db)
):
    print(file, file.filename)
    try:
        im = Image.open(file.file)
    except Exception:
        raise HTTPException(status_code=400, detail="Image Error")
    db_user = crud.get_user(db=db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    item =  schemas.ItemCreate(
        title=title,
        description=description,
        stock= stock,
        price=price,
        image=file.filename
    )
    item = crud.create_user_item(db=db, item=item, user_id=user_id)
    im.save(f'images/{file.filename}')
    return item


@app.get("/items/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items

@app.get("/items/{item_id}", response_model=schemas.Item)
def read_items(item_id:int, db: Session = Depends(get_db)):
    items = crud.get_item(db, item_id = item_id)
    return items


@app.get('/create_checkout')
def create_checkout(item_id:int, quantity:int, db: Session = Depends(get_db)):
    if quantity<1:
        raise HTTPException(status_code=400, detail="quantity cant be less than 1")
    
    db_item = crud.get_item(db=db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=400, detail="item not found")
    
    if db_item.stock < quantity:
        raise HTTPException(status_code=400, detail="not enough items left. try fewer quantity")
    db_user = crud.get_user(db=db, user_id=db_item.owner_id)
    if not db_user:
        raise HTTPException(status_code=400, detail="ticket owner doesnt exist anymore")
    result =  create_checkout_link(db_user.access_key, db_user.location_id, db_item.title, str(quantity), db_item.price, BASE_URL+'ticket-bought')
    
    if result.is_success():
        #save transaction
        db_checkout = crud.create_checkout(
            db=db, 
            item_id=item_id, 
            quantity=quantity, 
            checkout_id=result.body['checkout']['id'],
            checkout_total=result.body['checkout']['order']['net_amount_due_money']['amount'],
            checkout_url=result.body['checkout']['checkout_page_url']
        )
        return {'status':'success', 'checkout_url':result.body['checkout']['checkout_page_url']}
    elif result.is_error():
        print(result.errors)
        return HTTPException(status_code=400, detail=result.errors)


@app.get('/ticket-bought')
def ticket_bought(checkoutId:str, transactionId:str, db: Session = Depends(get_db) ):
    print(checkoutId, transactionId)

    db_checkout = db.query(models.Checkout).filter(models.Checkout.checkout_id == checkoutId).first()
    if not db_checkout:
        raise HTTPException(status_code=400, detail="Checkout not found")

    #decrease available stock    
    itemid = db_checkout.item_id
    quantity = db_checkout.quantity
    db_item = crud.get_item(db=db, item_id=itemid)
    old_stock = db_item.stock
    new_stock = old_stock - quantity
    if new_stock <=0:
        new_stock = 0
    
    db_item.stock = new_stock
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    #save transaction id so we can verify it later
    db_checkout.transaction_id = transactionId
    db.add(db_checkout)
    db.commit()
    db.refresh(db_checkout)
    return {'message':"thank you for buying from us", 'checkout': checkoutId, 'transaction':transactionId}

app.mount("/images", StaticFiles(directory="images"), name="static_images")
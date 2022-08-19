from enum import unique
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_active = Column(Boolean, default=True)
    access_key = Column(String)
    location_id = Column(String)
    items = relationship("Item", back_populates="owner")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    price = Column(Integer)
    stock = Column(Integer)
    image = Column(String)

    owner = relationship("User", back_populates="items")

class Checkout(Base):
    __tablename__ = "checkouts"
    
    id = Column(Integer, primary_key=True, index=True)

    item_id = Column(Integer, ForeignKey("items.id"))
    quantity = Column(Integer)

    checkout_id = Column(String, index=True)
    checkout_url = Column(String)
    checkout_total = Column(Integer)
    transaction_id = Column(String)
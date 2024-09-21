# Contains data types for the data provider service

from pydantic import BaseModel


class OpeningSchedule(BaseModel):
    day: str
    start: str
    end: str
    status: str


class Address(BaseModel):
    street: str
    city: str
    state: str
    zip: str
    country: str


class Customer(BaseModel):
    first_name: str
    last_name: str
    email: str
    user_id: str
    phone: str
    special: bool
    address: Address
    card_digits: str


from typing import List, Optional

from pydantic import BaseModel


class SoupItem(BaseModel):
    name: str
    price: float
    ingredients: List[str]
    label: str


class BowlItem(BaseModel):
    name: str
    price: float
    ingredients: List[str]
    label: str


class Menu(BaseModel):
    day: str
    soup: List[SoupItem]
    bowl: List[BowlItem]


class Order(BaseModel):
    id: str = None
    user_id: str
    date: str
    total: float
    detail: str
    status: str


class Dish(BaseModel):
    name: str
    kind: str
    price: float
    ingredients: List[str]
    label: str


class OrderResponse(BaseModel):
    order_id: str = ""
    user_name: str = ""
    messages: List[str] = []
    status: str = "success"
    total_price: float = 0.0
    currency: str = "EUR"
    card_digits: str = ""


class DeleteOrderResponse(BaseModel):
    message: str
    status: str

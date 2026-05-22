# core/models/order.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List
from datetime import datetime


class OrderItem(BaseModel):
    name: str
    price: float
    quantity: int


class Order(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")  # Унікальне id чека
    email: str
    items: List[OrderItem]  # Список покупок
    total_price: float
    date: datetime = Field(default_factory=datetime.now)

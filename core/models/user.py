# core/models/user.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional


class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(None, alias="_id")
    email: EmailStr  # Автоматична валідація формату email (вимога безпеки)
    first_name: str
    last_name: str
    phone: str
    order_ids: List[str] = []  # Список ID минулих замовлень

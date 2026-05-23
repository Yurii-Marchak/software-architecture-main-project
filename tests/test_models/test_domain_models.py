import pytest
from pydantic import ValidationError
from core.models.user import User
from core.models.order import Order, OrderItem
from datetime import datetime

def test_user_creation_success():
    """Тест успішного створення користувача"""
    user = User(email="test@gmail.com", first_name="John", last_name="Doe", phone="+380990000000")
    assert user.email == "test@gmail.com"
    assert user.order_ids == []

def test_user_creation_invalid_email():
    """Edge Case: Спроба створити користувача з неправильним форматом пошти"""
    with pytest.raises(ValidationError):
        User(email="invalid-email", first_name="John", last_name="Doe", phone="123")

def test_order_creation_success():
    """Тест успішного створення чека"""
    item = OrderItem(name="CPU Intel", price=200.0, quantity=2)
    order = Order(_id="123", email="client@test.com", items=[item], total_price=400.0)
    assert order.total_price == 400.0
    assert len(order.items) == 1

def test_order_missing_fields():
    """Edge Case: Створення чека без обов'язкових полів"""
    with pytest.raises(ValidationError):
        Order(_id="123", items=[]) # Немає email та total_price
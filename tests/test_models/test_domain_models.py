import pytest
from pydantic import ValidationError
from datetime import datetime


from core.models.user import User
from core.models.order import Order, OrderItem
from core.models.pc_build import PCBuild


def test_user_creation_success():
    """Тест: Успішне створення користувача з усіма валідними даними."""
    user = User(
        email="test@gmail.com", 
        first_name="John", 
        last_name="Doe", 
        phone="+380990000000"
    )
    assert user.email == "test@gmail.com"
    assert user.first_name == "John"
    assert user.order_ids == []  # Перевірка дефолтного значення

def test_user_creation_invalid_email():
    """Edge Case: Спроба створити користувача з неправильним форматом email."""
    with pytest.raises(ValidationError) as exc_info:
        User(
            email="invalid-email-format", 
            first_name="John", 
            last_name="Doe", 
            phone="+380990000000"
        )
    assert "value is not a valid email address" in str(exc_info.value).lower()

def test_user_missing_required_fields():
    """Edge Case: Спроба створити користувача без обов'язкових полів."""
    with pytest.raises(ValidationError):

        User(first_name="John", last_name="Doe")

def test_user_with_order_ids():
    """Тест: Створення користувача зі списком існуючих замовлень."""
    user = User(
        email="client@test.com", 
        first_name="Alice", 
        last_name="Smith", 
        phone="123456789",
        order_ids=["order_1", "order_2"]
    )
    assert len(user.order_ids) == 2
    assert "order_1" in user.order_ids



def test_order_item_valid_creation():
    """Тест: Успішне створення позиції замовлення."""
    item = OrderItem(name="AMD Ryzen 5 5600X", price=250.0, quantity=2)
    assert item.name == "AMD Ryzen 5 5600X"
    assert item.price == 250.0
    assert item.quantity == 2

def test_order_item_type_conversion():
    """Тест: Pydantic має автоматично конвертувати типи (напр. рядок у число)."""
    item = OrderItem(name="Corsair RAM", price="80.5", quantity="1")
    assert isinstance(item.price, float)
    assert item.price == 80.5
    assert isinstance(item.quantity, int)
    assert item.quantity == 1

def test_order_item_missing_fields():
    """Edge Case: Відсутність обов'язкових полів у позиції замовлення."""
    with pytest.raises(ValidationError):
        OrderItem(name="Missing Price and Quantity")



def test_order_creation_success():
    """Тест: Успішне створення чеку з кількома позиціями."""
    items = [
        OrderItem(name="CPU", price=200.0, quantity=1),
        OrderItem(name="GPU", price=500.0, quantity=1)
    ]
    order = Order(
        _id="order_123", 
        email="client@test.com", 
        items=items, 
        total_price=700.0
    )
    assert order.email == "client@test.com"
    assert order.total_price == 700.0
    assert len(order.items) == 2

    assert isinstance(order.date, datetime)

def test_order_with_explicit_date():
    """Тест: Створення чеку із заданою датою."""
    custom_date = datetime(2023, 1, 1, 12, 0)
    order = Order(
        _id="order_124", 
        email="test@test.com", 
        items=[], 
        total_price=0.0, 
        date=custom_date
    )
    assert order.date == custom_date

def test_order_missing_email():
    """Edge Case: Спроба створити чек без прив'язки до email."""
    with pytest.raises(ValidationError):
        Order(_id="125", items=[], total_price=10.0)



def test_pc_build_creation_success():
    """Тест: Успішне створення збереженої збірки ПК."""
    components = {
        "CPU": "Intel Core i5-12400F",
        "Motherboard": "ASUS B660M",
        "GPU": "RTX 3060"
    }
    build = PCBuild(name="Budget Gaming 2024", components=components)
    assert build.name == "Budget Gaming 2024"
    assert "GPU" in build.components
    assert build.components["CPU"] == "Intel Core i5-12400F"

def test_pc_build_empty_components():
    """Тест: Створення збірки без комплектуючих (якщо це дозволено моделлю)."""
    build = PCBuild(name="Empty Build", components={})
    assert build.components == {}

def test_pc_build_missing_name():
    """Edge Case: Збірка обов'язково повинна мати унікальну назву."""
    with pytest.raises(ValidationError):
        PCBuild(components={"CPU": "AMD"})
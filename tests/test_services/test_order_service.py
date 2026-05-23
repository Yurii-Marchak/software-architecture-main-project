import pytest
from unittest.mock import AsyncMock
from datetime import datetime
from core.services.order_service import OrderService
from core.models.order import Order
from core.models.user import User

@pytest.fixture
def mock_order_repo(): return AsyncMock()

@pytest.fixture
def mock_comp_repo(): return AsyncMock()

@pytest.fixture
def mock_user_repo(): return AsyncMock()

@pytest.fixture
def mock_email_adapter(): return AsyncMock()

@pytest.fixture
def order_service(mock_order_repo, mock_comp_repo, mock_user_repo, mock_email_adapter):
    return OrderService(
        order_repo=mock_order_repo, 
        component_repo=mock_comp_repo, 
        user_repo=mock_user_repo, 
        email_sender=mock_email_adapter
    )

# ==========================================
# ТЕСТИ ФІЛЬТРАЦІЇ ЧЕКІВ (Лямбда-вирази)
# ==========================================

@pytest.mark.asyncio
async def test_get_filtered_orders_no_dates(order_service, mock_order_repo):
    """Тест: Без фільтрів повертаються всі чеки, відсортовані від найновішого до найстарішого."""
    o1 = Order(id="1", email="a@a.com", items=[], total_price=10, date=datetime(2023, 1, 5))
    o2 = Order(id="2", email="b@b.com", items=[], total_price=20, date=datetime(2023, 1, 10))
    mock_order_repo.get_all.return_value = [o1, o2]

    res = await order_service.get_filtered_orders()
    assert len(res) == 2
    assert res[0].id == "2" 

@pytest.mark.asyncio
async def test_get_filtered_orders_start_date(order_service, mock_order_repo):
    """Тест: Лямбда-фільтр 'Починаючи з дати' працює коректно."""
    o1 = Order(id="1", email="a@a.com", items=[], total_price=10, date=datetime(2023, 1, 5))
    o2 = Order(id="2", email="b@b.com", items=[], total_price=20, date=datetime(2023, 1, 15))
    mock_order_repo.get_all.return_value = [o1, o2]

    res = await order_service.get_filtered_orders(start_date="2023-01-10")
    assert len(res) == 1
    assert res[0].id == "2"

@pytest.mark.asyncio
async def test_get_filtered_orders_end_date(order_service, mock_order_repo):
    """Тест: Лямбда-фільтр 'Закінчуючи датою'."""
    o1 = Order(id="1", email="a@a.com", items=[], total_price=10, date=datetime(2023, 1, 5, 14, 0))
    o2 = Order(id="2", email="b@b.com", items=[], total_price=20, date=datetime(2023, 1, 10, 20, 0))
    mock_order_repo.get_all.return_value = [o1, o2]

    res = await order_service.get_filtered_orders(end_date="2023-01-10")
    assert len(res) == 2

# ==========================================
# ТЕСТИ СКЛАДСЬКОГО ОБЛІКУ (Оформлення та Поставки)
# ==========================================

@pytest.mark.asyncio
async def test_receive_supply(order_service, mock_comp_repo):
    """Тест: Прийняття поставки взаємодіє з репозиторієм для оновлення залишку."""
    supply_cart = [{"category": "CPU", "name": "Intel i5", "quantity": 10}]
    await order_service.receive_supply(supply_cart)
    # Перевіряємо, чи викликався метод з правильними параметрами
    mock_comp_repo.update_stock.assert_called_once_with("CPU", "Intel i5", 10)

@pytest.mark.asyncio
async def test_checkout_unregistered_user(order_service, mock_user_repo):
    """Edge Case: Спроба оформити замовлення на неіснуючий email."""
    # Імітуємо, що база даних не знайшла користувача
    mock_user_repo.get_by_email.return_value = None
    
    with pytest.raises(ValueError) as exc:
        # Передаємо рівно ТРИ аргументи: self (неявно), email та порожній кошик []
        await order_service.checkout("notfound@gmail.com", [])
        
    assert "не зареєстрований" in str(exc.value)

@pytest.mark.asyncio
async def test_checkout_insufficient_stock(order_service, mock_user_repo, mock_comp_repo):
    """Edge Case: Спроба купити більше товару, ніж є на складі."""
    # Імітуємо знайденого користувача
    mock_user_repo.get_by_email.return_value = User(email="test@gmail.com", first_name="A", last_name="B", phone="1")
    # Імітуємо компонент, якого на складі лише 1 штука
    mock_comp_repo.get_by_name.return_value = {"name": "Intel i9", "stock": 1}
    
    # Клієнт хоче купити 5 штук
    cart = [{"category": "CPU", "name": "Intel i9", "price": 500, "quantity": 5}]
    
    with pytest.raises(ValueError) as exc:
        await order_service.checkout("test@gmail.com", cart)
        
    assert "немає в достатній кількості" in str(exc.value)

@pytest.mark.asyncio
async def test_checkout_success(order_service, mock_user_repo, mock_comp_repo, mock_order_repo):
    """Тест: Успішне створення замовлення."""
    mock_user_repo.get_by_email.return_value = User(email="test@gmail.com", first_name="A", last_name="B", phone="1")
    mock_comp_repo.get_by_name.return_value = {"name": "Intel i9", "stock": 10}
    
    cart = [{"category": "CPU", "name": "Intel i9", "price": 500, "quantity": 2}]
    
    order_id = await order_service.checkout("test@gmail.com", cart)
    
    # Перевіряємо, що ID чека згенерувався
    assert order_id is not None
    assert len(order_id) == 8
    
    # Перевіряємо, чи чек був записаний у БД
    mock_order_repo.create.assert_called_once()
    
    # Перевіряємо, чи зі складу було списано 2 штуки (передається як -2)
    mock_comp_repo.update_stock.assert_called_once_with("CPU", "Intel i9", -2)

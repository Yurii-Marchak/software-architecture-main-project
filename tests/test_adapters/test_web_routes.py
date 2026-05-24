import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from main import app
from adapters.web.dependencies import get_catalog_service, get_builder_service, get_order_service
from core.models.user import User


mock_catalog_service = AsyncMock()
mock_catalog_service.component_repo = AsyncMock() 

mock_builder_service = AsyncMock()

mock_order_service = AsyncMock()
mock_order_service.user_repo = AsyncMock()  # Мок для реєстрації та інфо

app.dependency_overrides[get_catalog_service] = lambda: mock_catalog_service
app.dependency_overrides[get_builder_service] = lambda: mock_builder_service
app.dependency_overrides[get_order_service] = lambda: mock_order_service

client = TestClient(app)

FAKE_ITEM = {
    "_id": "1",
    "name": "Intel Core i5",
    "price": 200.0,
    "brand": "Intel",
    "image": "https://example.com/img.png",
    "url": "https://example.com",
    "stock": 10
}


def test_index_page():
    response = client.get("/")
    assert response.status_code == 200

def test_catalog_page():
    mock_catalog_service.get_filtered_catalog.return_value = [FAKE_ITEM]
    response = client.get("/catalog/cpu")
    assert response.status_code == 200
    assert "Intel Core i5" in response.text

def test_search_page():
    search_item = FAKE_ITEM.copy()
    search_item["category"] = "CPU"
    mock_catalog_service.search_by_name.return_value = [search_item]
    response = client.get("/search?q=intel")
    assert response.status_code == 200

def test_orders_page():
    mock_order_service.get_filtered_orders.return_value = []
    response = client.get("/orders")
    assert response.status_code == 200


def test_register_client():
    """Тест: Реєстрація нового клієнта."""
    mock_order_service.user_repo.create.return_value = True
    response = client.post(
        "/register", 
        data={"email": "new@test.com", "first_name": "John", "last_name": "Doe", "phone": "12345"},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"

def test_client_info_found():
    """Тест: Пошук існуючого клієнта."""
    mock_order_service.user_repo.get_by_email.return_value = User(
        email="test@test.com", first_name="John", last_name="Doe", phone="123"
    )
    response = client.get("/client-info?email=test@test.com", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"

def test_client_info_not_found():
    """Edge Case: Пошук неіснуючого клієнта."""
    mock_order_service.user_repo.get_by_email.return_value = None
    response = client.get("/client-info?email=notfound@test.com", follow_redirects=False)
    assert response.status_code == 303


def test_cart_flow():
    """Інтеграційний тест кошика: Додавання -> Перегляд -> Оформлення -> Очищення."""

    with TestClient(app) as c:

        res_add = c.post("/cart/add", data={"category": "CPU", "name": "Intel Core i5", "price": "200.0", "quantity": "1"}, follow_redirects=False)
        assert res_add.status_code == 303
        

        res_view = c.get("/cart")
        assert res_view.status_code == 200
        

        mock_order_service.checkout.return_value = "ORD123"
        res_checkout = c.post("/cart/checkout", data={"email": "test@test.com"}, follow_redirects=False)
        assert res_checkout.status_code == 303
        assert res_checkout.headers["location"] == "/"
        

        res_clear = c.post("/cart/clear", follow_redirects=False)
        assert res_clear.status_code == 303

def test_checkout_empty_cart():
    """Edge Case: Оформлення порожнього кошика."""
    response = client.post("/cart/checkout", data={"email": "test@test.com"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/cart"


def test_supply_flow():
    """Інтеграційний тест поставки: Відображення -> Додавання -> Прийняття -> Очищення."""
    with TestClient(app) as c:

        assert c.get("/supply").status_code == 200
        

        res_add = c.post("/supply/add", data={"category": "GPU", "name": "RTX 3060"}, follow_redirects=False)
        assert res_add.status_code == 303
        

        mock_order_service.receive_supply.return_value = None
        res_commit = c.post("/supply/commit", data={"quantity_1": "5"}, follow_redirects=False)
        assert res_commit.status_code == 303
        assert res_commit.headers["location"] == "/"
        

        res_clear = c.post("/supply/clear", follow_redirects=False)
        assert res_clear.status_code == 303

def test_commit_empty_supply():
    """Edge Case: Прийняття порожньої поставки."""
    response = client.post("/supply/commit", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/supply"


def test_builder_view():
    assert client.get("/builder").status_code == 200

def test_builder_add_component():
    mock_catalog_service.component_repo.get_by_name.return_value = FAKE_ITEM
    response = client.post("/builder/add", data={"category": "CPU", "name": "Intel Core i5"}, follow_redirects=False)
    assert response.status_code == 303

def test_builder_save_success():
    mock_builder_service.save_build.return_value = True
    response = client.post("/builder/save", data={"build_name": "My Super PC"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"

def test_builder_save_failure():
    mock_builder_service.save_build.return_value = False
    response = client.post("/builder/save", data={"build_name": "Existing PC"}, follow_redirects=False)
    assert response.status_code == 303


def test_dependencies_initialization():
    """
    Технічний тест для файлу dependencies.py. 
    Перевіряє, чи успішно ініціалізуються сервіси.
    """
    from adapters.web.dependencies import get_catalog_service, get_builder_service, get_order_service
    assert get_catalog_service() is not None
    assert get_builder_service() is not None
    assert get_order_service() is not None
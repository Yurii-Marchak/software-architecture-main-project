import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from adapters.database.mongo_repository import (
    MongoComponentRepository,
    MongoOrderRepository,
    MongoUserRepository,
    MongoPCBuildRepository
)
from core.models.order import Order, OrderItem
from core.models.user import User
from core.models.pc_build import PCBuild
from core.ports.repository import IComponentRepository


@pytest.fixture
def mock_db():
    db = MagicMock()
    mock_collection = AsyncMock()
    

    mock_cursor = MagicMock()  
    mock_cursor.to_list = AsyncMock(return_value=[]) 
    

    mock_collection.find = MagicMock(return_value=mock_cursor)
    

    mock_update_result = MagicMock()
    mock_update_result.modified_count = 1
    mock_collection.update_one.return_value = mock_update_result
    

    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = "fake_id"
    mock_collection.insert_one.return_value = mock_insert_result

    db.__getitem__.return_value = mock_collection
    return db, mock_collection, mock_cursor

@pytest.mark.asyncio
async def test_component_get_by_name(mock_db):
    db, mock_col, _ = mock_db
    mock_col.find_one.return_value = {"_id": "1", "name": "Intel Core i5", "price": 200}
    
    repo = MongoComponentRepository(db)
    result = await repo.get_by_name("cpu", "Intel Core i5")
    
    assert result["name"] == "Intel Core i5"

@pytest.mark.asyncio
def test_ports_interfaces():
    class MockRepo(IComponentRepository):
        async def get_all_by_category(self, cat): pass
        async def get_by_name(self, cat, name): pass
        async def update_stock(self, cat, name, qty): pass
    
    repo = MockRepo()

    import asyncio
    asyncio.run(repo.get_all_by_category("cpu"))
    assert True

@pytest.mark.asyncio
async def test_component_update_stock(mock_db):
    db, mock_col, _ = mock_db
    repo = MongoComponentRepository(db)
    
    await repo.update_stock("cpu", "Intel Core i5", -2)
    
    mock_col.update_one.assert_called_once_with(
        {"name": "Intel Core i5"},
        {"$inc": {"stock": -2}}
    )


@pytest.mark.asyncio
async def test_order_create(mock_db):
    db, mock_col, _ = mock_db
    repo = MongoOrderRepository(db)
    
    order = Order(
        id="ord_123", 
        email="test@test.com", 
        items=[OrderItem(name="CPU", price=100, quantity=1)], 
        total_price=100.0, 
        date=datetime.now()
    )
    
    await repo.create(order)
    
    mock_col.insert_one.assert_called_once()
    inserted_data = mock_col.insert_one.call_args[0][0]
    assert inserted_data["email"] == "test@test.com"

@pytest.mark.asyncio
async def test_order_get_all(mock_db):
    db, _, mock_cursor = mock_db
    mock_cursor.to_list.return_value = [
        {"_id": "1", "email": "a@a.com", "items": [], "total_price": 10, "date": datetime.now()}
    ]
    
    repo = MongoOrderRepository(db)
    orders = await repo.get_all()
    
    assert len(orders) == 1
    assert orders[0].email == "a@a.com"

@pytest.mark.asyncio
async def test_user_get_by_email(mock_db):
    db, mock_col, _ = mock_db
    # ФІКС: Додали поле _id у тестові дані
    mock_col.find_one.return_value = {
        "_id": "some_mongo_id", "email": "user@gmail.com", "first_name": "A", "last_name": "B", "phone": "1", "order_ids": []
    }
    
    repo = MongoUserRepository(db)
    user = await repo.get_by_email("user@gmail.com")
    
    assert isinstance(user, User)
    assert user.email == "user@gmail.com"

@pytest.mark.asyncio
async def test_user_add_order(mock_db):
    db, mock_col, _ = mock_db
    repo = MongoUserRepository(db)
    
    await repo.add_order_to_user("user@gmail.com", "order_999")
    
    mock_col.update_one.assert_called_once_with(
        {"email": "user@gmail.com"},
        {"$push": {"order_ids": "order_999"}}
    )

@pytest.mark.asyncio
async def test_pc_build_create(mock_db):
    db, mock_col, _ = mock_db
    repo = MongoPCBuildRepository(db)
    
    build = PCBuild(name="Dream PC", components={"CPU": "Intel"})
    
    result = await repo.create(build)
    
    assert result is True
    mock_col.insert_one.assert_called_once()
    assert mock_col.insert_one.call_args[0][0]["name"] == "Dream PC"
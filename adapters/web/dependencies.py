# adapters/web/dependencies.py
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Request

from core.services.catalog_service import CatalogService
from core.services.builder_service import BuilderService
from core.services.order_service import OrderService

from adapters.database.mongo_repository import (
    MongoComponentRepository, 
    MongoUserRepository, 
    MongoOrderRepository, 
    MongoPCBuildRepository
)
from adapters.email.smtp_email import GoogleSMTPAdapter

# Ініціалізація підключення до MongoDB
client = AsyncIOMotorClient('mongodb://localhost:27017/')
db = client['pc_warehouse']

# Налаштування Email Адаптера (замініть на ваші дані або використовуйте змінні оточення .env)
email_adapter = GoogleSMTPAdapter("your_email@gmail.com", "your_app_password")

# Фабричні функції для FastAPI Depends
def get_catalog_service() -> CatalogService:
    repo = MongoComponentRepository(db)
    return CatalogService(repo)

def get_builder_service() -> BuilderService:
    repo = MongoPCBuildRepository(db)
    return BuilderService(repo)

def get_order_service() -> OrderService:
    order_repo = MongoOrderRepository(db)
    comp_repo = MongoComponentRepository(db)
    user_repo = MongoUserRepository(db)
    return OrderService(order_repo, comp_repo, user_repo, email_adapter)
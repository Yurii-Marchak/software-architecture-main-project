import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

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


load_dotenv()



client = AsyncIOMotorClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client['pc_warehouse']


email_adapter = GoogleSMTPAdapter(
    sender_email=os.getenv("SMTP_EMAIL"), 
    app_password=os.getenv("SMTP_PASSWORD")
)

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
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional

from core.ports.repository import IComponentRepository, IUserRepository, IOrderRepository, IPCBuildRepository
from core.models.user import User
from core.models.order import Order
from core.models.pc_build import PCBuild

class MongoComponentRepository(IComponentRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_all_by_category(self, category: str) -> List[dict]:
        cursor = self.db[category].find({})
        return await cursor.to_list(length=None)

    async def get_by_name(self, category: str, name: str) -> Optional[dict]:
        return await self.db[category].find_one({"name": name})

    async def update_stock(self, category: str, name: str, quantity_change: int) -> bool:
        result = await self.db[category].update_one(
            {"name": name},
            {"$inc": {"stock": quantity_change}}
        )
        return result.modified_count > 0


class MongoUserRepository(IUserRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        doc = await self.db['users'].find_one({"email": email})
        if doc:
            doc['_id'] = str(doc['_id'])
            return User(**doc)
        return None

    async def create(self, user: User) -> bool:
        result = await self.db['users'].insert_one(user.model_dump(by_alias=True, exclude_none=True))
        return result.inserted_id is not None

    async def add_order_to_user(self, email: str, order_id: str) -> bool:
        result = await self.db['users'].update_one(
            {"email": email},
            {"$push": {"order_ids": order_id}}
        )
        return result.modified_count > 0


class MongoOrderRepository(IOrderRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def create(self, order: Order) -> bool:
        result = await self.db['orders'].insert_one(order.model_dump(by_alias=True))
        return result.inserted_id is not None

    async def get_all(self) -> List[Order]:
        cursor = self.db['orders'].find({})
        docs = await cursor.to_list(length=None)
        for doc in docs:
            doc['_id'] = str(doc['_id'])
        return [Order(**doc) for doc in docs]

class MongoPCBuildRepository(IPCBuildRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def create(self, build: PCBuild) -> bool:
        result = await self.db['pc_builds'].insert_one(build.model_dump(by_alias=True, exclude_none=True))
        return result.inserted_id is not None

    async def get_by_name(self, name: str) -> Optional[PCBuild]:
        doc = await self.db['pc_builds'].find_one({"name": name})
        if doc:
            doc['_id'] = str(doc['_id'])
            return PCBuild(**doc)
        return None
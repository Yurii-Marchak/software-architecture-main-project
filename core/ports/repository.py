from abc import ABC, abstractmethod
from typing import List, Optional
from core.models.user import User
from core.models.order import Order
from core.models.pc_build import PCBuild

class IComponentRepository(ABC):
    @abstractmethod
    async def get_all_by_category(self, category: str) -> List[dict]:
        """Повертає всі компоненти з певної категорії (колекції)"""
        pass

    @abstractmethod
    async def get_by_name(self, category: str, name: str) -> Optional[dict]:
        """Пошук конкретного компонента за назвою"""
        pass

    @abstractmethod
    async def update_stock(self, category: str, name: str, quantity_change: int) -> bool:
        """Змінює кількість товару на складі (додає або віднімає)"""
        pass

class IUserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Пошук клієнта за електронною поштою"""
        pass

    @abstractmethod
    async def create(self, user: User) -> bool:
        """Реєстрація нового клієнта"""
        pass
    
    @abstractmethod
    async def add_order_to_user(self, email: str, order_id: str) -> bool:
        """Додає ID нового чеку в історію користувача"""
        pass

class IOrderRepository(ABC):
    @abstractmethod
    async def create(self, order: Order) -> bool:
        """Збереження нового чеку"""
        pass

    @abstractmethod
    async def get_all(self) -> List[Order]:
        """Отримання списку всіх закритих замовлень"""
        pass

class IPCBuildRepository(ABC):
    @abstractmethod
    async def create(self, build: PCBuild) -> bool:
        """Збереження унікальної конфігурації ПК"""
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[PCBuild]:
        """Перевірка чи існує збірка з такою назвою"""
        pass
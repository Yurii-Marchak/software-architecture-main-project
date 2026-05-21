# core/ports/email.py
from abc import ABC, abstractmethod
from core.models.order import Order

class IEmailSender(ABC):
    @abstractmethod
    async def send_receipt(self, email: str, order: Order) -> bool:
        """Відправляє чек клієнту на вказану електронну пошту"""
        pass
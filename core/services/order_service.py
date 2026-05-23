
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any

from core.ports.repository import IOrderRepository, IComponentRepository, IUserRepository
from core.ports.email import IEmailSender
from core.models.order import Order, OrderItem

class OrderService:
    def __init__(self, 
                 order_repo: IOrderRepository, 
                 component_repo: IComponentRepository, 
                 user_repo: IUserRepository,
                 email_sender: IEmailSender):
        self.order_repo = order_repo
        self.component_repo = component_repo
        self.user_repo = user_repo
        self.email_sender = email_sender

    async def checkout(self, email: str, cart_items: List[Dict[str, Any]]) -> str:
        """Оформлення замовлення, зняття зі складу та відправка чеку."""
        
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("Помилка: Клієнт з таким email не зареєстрований у системі.")

        total_price = 0.0
        order_items = []

        for item in cart_items:
            component = await self.component_repo.get_by_name(item["category"], item["name"])
            if not component or component.get("stock", 0) < item["quantity"]:
                raise ValueError(f"Товару '{item['name']}' немає в достатній кількості на складі.")
            
            total_price += item["price"] * item["quantity"]
            order_items.append(OrderItem(name=item["name"], price=item["price"], quantity=item["quantity"]))

        order_id = str(uuid.uuid4())[:8] 
        new_order = Order(
            _id=order_id,
            email=email,
            items=order_items,
            total_price=total_price,
            date=datetime.now()
        )


        await self.order_repo.create(new_order)
        await self.user_repo.add_order_to_user(email, order_id)

        for item in cart_items:

            await self.component_repo.update_stock(item["category"], item["name"], -item["quantity"])

        asyncio.create_task(self._send_email_background(email, new_order))

        return order_id

    async def _send_email_background(self, email: str, order: Order):
        """Фонове завдання для оптимізації відправки пошти."""
        try:
            await self.email_sender.send_receipt(email, order)
        except Exception as e:

            print(f"Помилка відправки чеку: {e}")

    async def receive_supply(self, supply_items: List[Dict[str, Any]]):
        """
        Кнопка 'прийняти поставку'.
        supply_items має вигляд: [{"category": "CPU", "name": "Intel Core i5...", "quantity": 5}, ...]
        """
        for item in supply_items:
            await self.component_repo.update_stock(item["category"], item["name"], item["quantity"])
    async def get_filtered_orders(self, start_date: str = None, end_date: str = None) -> List[Order]:
        """Отримання чеків з фільтрацією по даті за допомогою функціонального програмування."""
        orders = await self.order_repo.get_all()
        
        if start_date and start_date.strip():
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            orders = list(filter(lambda o: o.date >= start_dt, orders))
            
        if end_date and end_date.strip():
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

            end_dt = end_dt.replace(hour=23, minute=59, second=59)

            orders = list(filter(lambda o: o.date <= end_dt, orders))
            
        orders.sort(key=lambda o: o.date, reverse=True)
        return orders

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.ports.email import IEmailSender
from core.models.order import Order

class GoogleSMTPAdapter(IEmailSender):
    def __init__(self, sender_email: str, app_password: str):
        self.sender_email = sender_email
        self.app_password = app_password

    async def send_receipt(self, email: str, order: Order) -> bool:
        """
        Відправляє лист-чек використовуючи SMTP.
        Хоча smtplib є синхронною, ми обернули її в async метод для збереження архітектурного контракту.
        """
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = email
        msg['Subject'] = f"Чек про покупку #{order.id}"

        # Формування HTML-списку покупок з найменуванням, кількістю та роздрібною ціною
        items_html = "".join([
            f"<li>{item.name} — {item.quantity} шт. (Ціна: ${item.price})</li>" 
            for item in order.items
        ])
        
        # Повні деталі замовлення включно з id чеку, часом покупки та загальною ціною
        body = f"""
        <html>
            <body>
                <h2>Дякуємо за ваше замовлення!</h2>
                <p>Email клієнта: <b>{email}</b></p>
                <p>Унікальний ID чеку: <b>{order.id}</b></p>
                <p>Час покупки: {order.date.strftime("%Y-%m-%d %H:%M:%S")}</p>
                <hr>
                <h3>Деталі замовлення:</h3>
                <ul>
                    {items_html}
                </ul>
                <hr>
                <h3>Загальна вартість: ${order.total_price}</h3>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))

        try:
            # Використання контекстного менеджера (with) гарантує безпечне закриття з'єднання з сервером
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.sender_email, self.app_password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Помилка відправки листа: {e}")
            return False
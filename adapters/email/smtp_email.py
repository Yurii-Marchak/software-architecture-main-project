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
        """
        if not self.sender_email or not self.app_password:
            print("Помилка: Не задано EMAIL або ПАРОЛЬ у конфігурації!")
            return False

        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = email
        msg['Subject'] = f"Чек про покупку #{order.id}"

        # Формування HTML-списку покупок
        items_html = "".join([
            f"<li>{item.name} — {item.quantity} шт. (Ціна: ${item.price})</li>"
            for item in order.items
        ])

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
            # Використовуємо порт 587 та STARTTLS (як у вашому старому проєкті)
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.ehlo()  # Ініціалізація з'єднання
                server.starttls()  # Шифрування
                server.login(self.sender_email, self.app_password)
                server.send_message(msg)
            print(f"Чек успішно відправлено на {email}!")
            return True
        except Exception as e:
            print(f"Помилка відправки листа: {e}")
            return False

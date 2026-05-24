import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from adapters.email.smtp_email import GoogleSMTPAdapter
from core.models.order import Order, OrderItem


@pytest.fixture
def sample_order():
    """Генеруємо тестовий чек для відправки у листі."""
    items = [
        OrderItem(name="Intel Core i9", price=500.0, quantity=1),
        OrderItem(name="RTX 4090", price=1500.0, quantity=1)
    ]
    return Order(
        id="test_order_123",
        email="client@example.com",
        items=items,
        total_price=2000.0,
        date=datetime(2023, 10, 1, 12, 0)
    )

@pytest.fixture
def email_adapter():
    """Ініціалізуємо адаптер з тестовими даними."""
    return GoogleSMTPAdapter(sender_email="admin@test.com", app_password="fake_password")


@pytest.mark.asyncio
@patch("adapters.email.smtp_email.smtplib.SMTP")  # Підміняємо реальний SMTP сервер на Mock
async def test_send_receipt_success(mock_smtp_class, email_adapter, sample_order):
    """Тест: Успішне формування та відправка листа (без реального інтернету)."""
    

    mock_server_instance = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_server_instance

    result = await email_adapter.send_receipt("client@example.com", sample_order)


    assert result is True
    

    mock_server_instance.ehlo.assert_called()
    mock_server_instance.starttls.assert_called()
    

    mock_server_instance.login.assert_called_once_with("admin@test.com", "fake_password")
    

    mock_server_instance.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_send_receipt_missing_credentials(sample_order):
    """Edge Case: Спроба відправки без пароля/пошти у конфігурації."""

    bad_adapter = GoogleSMTPAdapter(sender_email="", app_password="")
    
    result = await bad_adapter.send_receipt("client@example.com", sample_order)
    

    assert result is False

@pytest.mark.asyncio
@patch("adapters.email.smtp_email.smtplib.SMTP")
async def test_send_receipt_smtp_exception(mock_smtp_class, email_adapter, sample_order):
    """Edge Case: Обробка помилки (наприклад, Google відхилив з'єднання)."""
    
    mock_server_instance = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_server_instance
    

    mock_server_instance.send_message.side_effect = Exception("Google SMTP Error: Bad Credentials")


    result = await email_adapter.send_receipt("client@example.com", sample_order)
    
    assert result is False
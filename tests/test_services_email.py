import pytest
from unittest.mock import patch, AsyncMock
from fastapi_mail.errors import ConnectionErrors
from src.services import email
from pydantic import EmailStr


@pytest.mark.asyncio
async def test_send_email_success():
    test_email = EmailStr("test@example.com")
    test_username = "testuser"
    test_host = "http://testhost"


    with patch("src.services.email.FastMail.send_message", new_callable=AsyncMock) as mock_send:
        await email.send_email(test_email, test_username, test_host)
        mock_send.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_email_exception():
    test_email = EmailStr("test@example.com")
    test_username = "testuser"
    test_host = "http://testhost"


    with patch("src.services.email.FastMail.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = ConnectionErrors("SMTP connection error")

        await email.send_email(test_email, test_username, test_host)
        mock_send.assert_awaited_once()

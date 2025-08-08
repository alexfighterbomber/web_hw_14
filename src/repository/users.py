import sys
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result

from src.database.models import User
from src.schemas import UserModel
from src.repository.users import (
    get_user_by_email,
    create_user,
    update_token,
    confirmed_email,
    update_avatar,
)

class TestUsers(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = AsyncMock(spec=AsyncSession)
        self.user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            password="pass123",
            created_at=datetime.now(),
            confirmed=False,
            avatar=None,
            refresh_token=None
        )
        self.user_model = UserModel(
            username="testuser",
            email="test@example.com",
            password="pass123"
        )

    async def test_get_user_by_email_found(self):
        mock_result = MagicMock(spec=Result)
        mock_result.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mock_result

        result = await get_user_by_email(email="test@example.com", db=self.session)
        
        self.assertEqual(result, self.user)
        self.assertEqual(result.email, "test@example.com")

    async def test_get_user_by_email_not_found(self):
        mock_result = MagicMock(spec=Result)
        mock_result.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mock_result

        result = await get_user_by_email(email="notfound@example.com", db=self.session)
        
        self.assertIsNone(result)

    @patch("libgravatar.Gravatar.get_image")
    async def test_create_user(self, mock_gravatar_get_image):
        mock_gravatar_get_image.return_value = "http://example.com/avatar.jpg"
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        result = await create_user(body=self.user_model, db=self.session)
        
        self.session.add.assert_called_once()
        self.session.commit.assert_awaited_once()
        self.session.refresh.assert_awaited_once()
        self.assertEqual(result.email, self.user_model.email)
        self.assertEqual(result.avatar, "http://example.com/avatar.jpg")

    @patch("libgravatar.Gravatar.get_image")
    async def test_create_user_gravatar_fails(self, mock_gravatar_get_image):
        mock_gravatar_get_image.side_effect = Exception("Gravatar error")
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        result = await create_user(body=self.user_model, db=self.session)
        
        self.assertEqual(result.avatar, None)

    async def test_update_token(self):
        token = "new_refresh_token"
        self.session.commit = AsyncMock()

        await update_token(user=self.user, token=token, db=self.session)
        
        self.session.commit.assert_awaited_once()
        self.assertEqual(self.user.refresh_token, token)

    async def test_confirmed_email(self):
        mock_result = MagicMock()
        self.session.execute.return_value = mock_result
        self.session.commit = AsyncMock()

        await confirmed_email(email="test@example.com", db=self.session)
        
        self.session.commit.assert_awaited_once()

    async def test_update_avatar(self):
        mock_result = MagicMock(spec=Result)
        mock_result.scalar_one.return_value = self.user
        self.session.execute.return_value = mock_result
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        new_avatar_url = "http://newavatar.com/image.jpg"
        result = await update_avatar(email="test@example.com", url=new_avatar_url, db=self.session)
        
        self.session.commit.assert_awaited_once()
        self.session.refresh.assert_awaited_once()
        self.assertEqual(result.avatar, new_avatar_url)

    async def test_update_avatar_not_found(self):
        mock_result = MagicMock(spec=Result)
        mock_result.scalar_one.side_effect = Exception("No user found")
        self.session.execute.return_value = mock_result

        new_avatar_url = "http://newavatar.com/image.jpg"
        with self.assertRaises(Exception):
            await update_avatar(email="notfound@example.com", url=new_avatar_url, db=self.session)

if __name__ == '__main__':
    unittest.main()
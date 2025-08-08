import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from src.database.models import User
from src.schemas import UserModel
from src.repository.users import (
    get_user_by_email,
    create_user,
    update_token,
    confirmed_email,
    update_avatar,
)
from datetime import datetime

class TestUsers(unittest.TestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            password="pass123",  # Исправлено: пароль длиной ≤ 10 символов
            created_at=datetime.now(),
            confirmed=False,
            avatar=None,
            refresh_token=None
        )
        self.user_model = UserModel(
            username="testuser",
            email="test@example.com",
            password="pass123"  # Исправлено: пароль длиной ≤ 10 символов
        )

    def test_get_user_by_email_found(self):
        mock_user = User(email="test@example.com")
        self.session.query().filter().first.return_value = mock_user
        result = get_user_by_email(email="test@example.com", db=self.session)
        self.session.query().filter().first.assert_called_once()
        self.assertEqual(result, mock_user)
        self.assertEqual(result.email, "test@example.com")

    def test_get_user_by_email_not_found(self):
        self.session.query().filter().first.return_value = None
        result = get_user_by_email(email="notfound@example.com", db=self.session)
        self.session.query().filter().first.assert_called_once()
        self.assertIsNone(result)

    @patch("libgravatar.Gravatar.get_image")
    def test_create_user(self, mock_gravatar_get_image):
        mock_gravatar_get_image.return_value = "http://example.com/avatar.jpg"
        self.session.add = MagicMock()
        self.session.commit = MagicMock()
        self.session.refresh = MagicMock()
        result = create_user(body=self.user_model, db=self.session)
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once()
        self.assertEqual(result.email, self.user_model.email)
        self.assertEqual(result.username, self.user_model.username)
        self.assertEqual(result.password, self.user_model.password)
        self.assertEqual(result.avatar, "http://example.com/avatar.jpg")
        self.assertFalse(result.confirmed)

    @patch("libgravatar.Gravatar.get_image")
    def test_create_user_gravatar_fails(self, mock_gravatar_get_image):
        mock_gravatar_get_image.side_effect = Exception("Gravatar error")
        self.session.add = MagicMock()
        self.session.commit = MagicMock()
        self.session.refresh = MagicMock()
        result = create_user(body=self.user_model, db=self.session)
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once()
        self.assertEqual(result.email, self.user_model.email)
        self.assertEqual(result.username, self.user_model.username)
        self.assertEqual(result.password, self.user_model.password)
        self.assertIsNone(result.avatar)
        self.assertFalse(result.confirmed)

    def test_update_token(self):
        token = "new_refresh_token"
        self.session.commit = MagicMock()
        update_token(user=self.user, token=token, db=self.session)
        self.session.commit.assert_called_once()
        self.assertEqual(self.user.refresh_token, token)

    def test_confirmed_email(self):
        self.session.query().filter().first.return_value = self.user
        self.session.commit = MagicMock()
        confirmed_email(email="test@example.com", db=self.session)
        self.session.query().filter().first.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertTrue(self.user.confirmed)

    def test_confirmed_email_not_found(self):
        self.session.query().filter().first.return_value = None
        self.session.commit = MagicMock()
        confirmed_email(email="notfound@example.com", db=self.session)
        self.session.query().filter().first.assert_called_once()
        self.session.commit.assert_not_called()

    def test_update_avatar(self):
        new_avatar_url = "http://newavatar.com/image.jpg"
        self.session.query().filter().first.return_value = self.user
        self.session.commit = MagicMock()
        self.session.refresh = MagicMock()
        result = update_avatar(email="test@example.com", url=new_avatar_url, db=self.session)
        self.session.query().filter().first.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(self.user)
        self.assertEqual(result.avatar, new_avatar_url)
        self.assertEqual(result, self.user)

    def test_update_avatar_not_found(self):
        new_avatar_url = "http://newavatar.com/image.jpg"
        self.session.query().filter().first.return_value = None
        self.session.commit = MagicMock()
        self.session.refresh = MagicMock()
        result = update_avatar(email="notfound@example.com", url=new_avatar_url, db=self.session)
        self.session.query().filter().first.assert_called_once()
        self.session.commit.assert_not_called()
        self.session.refresh.assert_not_called()
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
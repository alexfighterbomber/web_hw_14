import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result

from src.database.models import User, Contact
from src.schemas import ContactCreate, ContactUpdate
from src.repository.contacts import *


class TestContacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        today = date.today()
        self.session = AsyncMock(spec=AsyncSession)
        self.user = User(id=1)
        self.contact_data = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="1234567890",
            birthday=today + timedelta(days=3)
        )
        self.mock_contact = Contact(
            id=1,
            first_name=self.contact_data.first_name,
            last_name=self.contact_data.last_name,
            email=self.contact_data.email,
            phone=self.contact_data.phone,
            birthday=self.contact_data.birthday,
            owner_id=self.user.id
        )

    async def test_get_contacts(self):
        mock_result = MagicMock(spec=Result)
        mock_result.scalars.return_value.all.return_value = [self.mock_contact]
        self.session.execute.return_value = mock_result

        result = await get_contacts(db=self.session, owner_id=self.user.id)
        self.assertEqual(result, [self.mock_contact])

    async def test_get_contact_found(self):
        mock_result = MagicMock(spec=Result)
        mock_result.scalar_one_or_none.return_value = self.mock_contact
        self.session.execute.return_value = mock_result

        result = await get_contact(db=self.session, contact_id=1, owner_id=self.user.id)
        self.assertEqual(result, self.mock_contact)

    async def test_get_contact_not_found(self):
        mock_result = MagicMock(spec=Result)
        mock_result.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mock_result

        result = await get_contact(db=self.session, contact_id=1, owner_id=self.user.id)
        self.assertIsNone(result)

    async def test_create_contact(self):
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        result = await create_contact(
            db=self.session, 
            contact=self.contact_data, 
            owner_id=self.user.id)

        self.session.add.assert_called_once()
        self.session.commit.assert_awaited_once()
        self.session.refresh.assert_awaited_once()

        self.assertEqual(result.first_name, self.contact_data.first_name)
        self.assertEqual(result.owner_id, self.user.id)

    async def test_update_contact_found(self):
        mock_result = MagicMock(spec=Result)
        mock_result.scalar_one_or_none.return_value = self.mock_contact
        self.session.execute.return_value = mock_result
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        result = await update_contact(
            db=self.session,
            contact_id=1,
            contact=self.contact_data,
            owner_id=self.user.id)

        self.session.commit.assert_awaited_once()
        self.session.refresh.assert_awaited_once()
        self.assertEqual(result.first_name, self.contact_data.first_name)

    async def test_update_contact_not_found(self):
        mock_result = MagicMock(spec=Result)
        mock_result.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mock_result

        result = await update_contact(
            db=self.session,
            contact_id=1,
            contact=self.contact_data,
            owner_id=self.user.id)

        self.assertIsNone(result)

    async def test_delete_contact_found(self):
        mock_result = MagicMock(spec=Result)
        mock_result.scalar_one_or_none.return_value = self.mock_contact
        self.session.execute.return_value = mock_result
        self.session.commit = AsyncMock()

        result = await delete_contact(
            db=self.session,
            contact_id=1,
            owner_id=self.user.id)

        self.session.commit.assert_awaited_once()
        self.assertEqual(result, self.mock_contact)

    async def test_delete_contact_not_found(self):
        mock_result = MagicMock(spec=Result)
        mock_result.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mock_result

        result = await delete_contact(
            db=self.session,
            contact_id=1,
            owner_id=self.user.id)

        self.assertIsNone(result)

    async def test_search_contacts(self):
        mock_result = MagicMock(spec=Result)
        mock_result.scalars.return_value.all.return_value = [self.mock_contact]
        self.session.execute.return_value = mock_result

        result = await search_contacts(
            db=self.session,
            query="John",
            owner_id=self.user.id)

        self.assertEqual(result, [self.mock_contact])

    async def test_get_upcoming_birthdays(self):
        mock_result = MagicMock(spec=Result)
        mock_result.scalars.return_value.all.return_value = [self.mock_contact]
        self.session.execute.return_value = mock_result

        result = await get_upcoming_birthdays(
            db=self.session,
            owner_id=self.user.id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, self.mock_contact.id)


if __name__ == '__main__':
    unittest.main()
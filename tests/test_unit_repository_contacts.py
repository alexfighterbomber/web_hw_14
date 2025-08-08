import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from src.database.models import User, Contact
from src.schemas import Contact, ContactCreate, ContactUpdate
from src.repository.contacts import *


class TestContacts(unittest.TestCase):

    def setUp(self):
        today = date.today()
        self.session = MagicMock(spec=Session)
        self.user = User(id=1)
        self.contact_data = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="1234567890",
            birthday=today + timedelta(days=3)
        )
        self.mock_contact = Contact(
            first_name=self.contact_data.first_name,
            last_name=self.contact_data.last_name,
            email=self.contact_data.email,
            phone=self.contact_data.phone,
            birthday=today + timedelta(days=3),
            owner_id=self.user.id
        )

        
    def test_get_contacts(self):
        contacts = [Contact(), Contact(), Contact()]
        self.session.query().filter().offset().limit().all.return_value = contacts
        result = get_contacts(db=self.session, owner_id=self.user.id, skip=0, limit=10)
        self.assertEqual(result, contacts)

    def test_get_contact_found(self):
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = get_contact(db=self.session, contact_id = contact.id, owner_id=self.user.id)
        self.assertEqual(result, contact)

    def test_get_contact_not_found(self):
        contact = Contact()
        self.session.query().filter().first.return_value = None
        result = get_contact(db=self.session, contact_id = contact.id, owner_id=self.user.id)
        self.assertIsNone(result)

    def test_create_contact(self):
        contact_data = self.contact_data
        mock_contact = self.mock_contact
        
        self.session.query().filter().first.return_value = mock_contact        
        self.session.add = MagicMock()
        self.session.commit = MagicMock()

        result = create_contact(db=self.session, contact=contact_data, owner_id=self.user.id)

        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()

        self.assertEqual(result.first_name, contact_data.first_name)
        self.assertEqual(result.last_name, contact_data.last_name)
        self.assertEqual(result.email, contact_data.email)
        self.assertEqual(result.phone, contact_data.phone)
        self.assertEqual(result.owner_id, self.user.id)

    def test_update_contact_found(self):
        contact_data = self.contact_data
        mock_contact = self.mock_contact

        self.session.query().filter().first.return_value = mock_contact
        self.session.commit = MagicMock()
        self.session.refresh = MagicMock()
        result = update_contact(db=self.session, contact_id=1, contact=contact_data, owner_id=self.user.id)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(mock_contact)
        self.assertEqual(result.first_name, contact_data.first_name)
        self.assertEqual(result.last_name, contact_data.last_name)
        self.assertEqual(result.email, contact_data.email)
        self.assertEqual(result.phone, contact_data.phone)
        self.assertEqual(result.owner_id, self.user.id)

    def test_update_contact_not_found(self):
        contact_data = self.contact_data

        self.session.query().filter().first.return_value = None
        result = update_contact(db=self.session, contact_id=1, contact=contact_data, owner_id=self.user.id)
        self.assertIsNone(result)

    def test_delete_contact_found(self):
        mock_contact = self.mock_contact

        self.session.query().filter().first.return_value = mock_contact
        self.session.delete = MagicMock()
        self.session.commit = MagicMock()
        result = delete_contact(db=self.session, contact_id=1, owner_id=self.user.id)
        self.session.delete.assert_called_once_with(mock_contact)
        self.session.commit.assert_called_once()
        self.assertEqual(result, mock_contact)

    def test_delete_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        result = delete_contact(db=self.session, contact_id=1, owner_id=self.user.id)
        self.assertIsNone(result)

def test_get_upcoming_birthdays(self):
        today = date.today()
        mock_contact = self.mock_contact
        self.session.query().filter().all.return_value = [mock_contact]
        result = get_upcoming_birthdays(db=self.session, owner_id=self.user.id)
        self.assertEqual(result, [mock_contact.birthday])
        
if __name__ == '__main__':
    unittest.main()


import pytest
from httpx import AsyncClient
from sqlalchemy import select
from src.database.models import User, Contact
from src.schemas import ContactCreate, ContactUpdate

@pytest.mark.asyncio
async def test_create_contact(logged_in_client):
    client = await logged_in_client
    contact_data = {"first_name": "Tony", "last_name": "Stark", "email": "tony@stark.com", "phone": "123456789"}
    response = await client.post("/api/contacts/", json=contact_data)
    assert response.status_code == 201
    data = response.json()
    pytest.contact_id = data["id"]
    assert data["first_name"] == "Tony"

@pytest.mark.asyncio
async def test_read_all_contacts(logged_in_client):
    client = await logged_in_client
    response = await client.get("/api/contacts/")
    assert response.status_code == 200
    data = response.json()
    assert any(c["id"] == pytest.contact_id for c in data)

@pytest.mark.asyncio
async def test_read_single_contact(logged_in_client):
    client = await logged_in_client
    response = await client.get(f"/api/contacts/{pytest.contact_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == pytest.contact_id

@pytest.mark.asyncio
async def test_update_contact(logged_in_client):
    client = await logged_in_client
    update_data = {"first_name": "Anthony", "last_name": "Stark"}
    response = await client.put(f"/api/contacts/{pytest.contact_id}", json=update_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == "Anthony"

@pytest.mark.asyncio
async def test_search_contacts(logged_in_client):
    client = await logged_in_client
    response = await client.get("/api/contacts/search/", params={"query": "Anthony"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert any(c["id"] == pytest.contact_id for c in data)

@pytest.mark.asyncio
async def test_delete_contact(logged_in_client):
    client = await logged_in_client
    response = await client.delete(f"/api/contacts/{pytest.contact_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == pytest.contact_id

import io
import pytest
from unittest.mock import patch
from src.database.models import User

@pytest.mark.asyncio
async def test_read_users_me(logged_in_client, user):
    client = await logged_in_client

    with patch("src.services.auth.auth_service.get_current_user") as mock_get_user:
        mock_get_user.return_value = User(
            id=1,
            username=user["username"],
            email=user["email"],
            avatar="",
            confirmed=True,
        )

        response = await client.get("/api/users/me/")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user["email"]
        assert data["username"] == user["username"]


@pytest.mark.asyncio
async def test_update_avatar_user(logged_in_client, user):
    client = await logged_in_client

    dummy_file = io.BytesIO(b"fake image data")
    dummy_file.name = "avatar.png"

    with patch("src.services.auth.auth_service.get_current_user") as mock_get_user, \
         patch("cloudinary.uploader.upload") as mock_upload, \
         patch("cloudinary.CloudinaryImage.build_url", return_value="http://fake.url/avatar.png"):

        mock_get_user.return_value = User(
            id=1,
            username=user["username"],
            email=user["email"],
            avatar=None,
            confirmed=True,
        )

        response = await client.patch(
            "/api/users/avatar",
            files={"file": ("avatar.png", dummy_file, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user["email"]
        assert "http://fake.url/avatar.png" in data["avatar"]

        mock_upload.assert_called_once()

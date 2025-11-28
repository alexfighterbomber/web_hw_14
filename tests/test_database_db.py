import pytest
from unittest.mock import AsyncMock, patch

from src.database.db import get_db as async_get_db

@pytest.mark.asyncio
async def test_async_get_db():

    with patch('src.database.db.AsyncSessionLocal') as mock_async_session_local:
        mock_db = AsyncMock()
        mock_async_session_local.return_value = mock_db
        
        generator = async_get_db()
        db = await generator.__anext__()
        assert db == mock_db
        mock_async_session_local.assert_called_once()
        try:
            await generator.__anext__()
        except StopAsyncIteration:
            pass
        mock_db.close.assert_awaited_once()
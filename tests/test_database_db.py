import pytest
from unittest.mock import AsyncMock, patch

from src.database.db import get_db as async_get_db

# # Тест для синхронного get_db (строки 14-18)
# def test_sync_get_db():
#     """Тест для синхронной функции get_db"""
#     # Импортируем модуль и временно заменяем асинхронную функцию на синхронную
#     with patch('src.database.db.get_db') as mock_get_db:
#         # Создаем мок для сессии
#         mock_db = Mock()
        
#         # Создаем синхронный генератор для тестирования
#         def sync_generator():
#             yield mock_db
#             mock_db.close()
        
#         mock_get_db.side_effect = sync_generator
        
#         # Тестируем
#         generator = mock_get_db()
#         db = next(generator)
        
#         # Проверяем что получили сессию
#         assert db == mock_db
        
#         # Завершаем генератор и проверяем что close вызван
#         try:
#             next(generator)
#         except StopIteration:
#             pass
        
#         mock_db.close.assert_called_once()

# # Тест для асинхронного get_db (строки 43-47)
@pytest.mark.asyncio
async def test_async_get_db():
    """Тест для асинхронной функции get_db"""
    # Мокаем AsyncSessionLocal чтобы не создавать реальную сессию
    with patch('src.database.db.AsyncSessionLocal') as mock_async_session_local:
        mock_db = AsyncMock()
        mock_async_session_local.return_value = mock_db
        
        # Вызываем асинхронный генератор
        generator = async_get_db()
        
        # Получаем сессию (строка 44: db = AsyncSessionLocal())
        db = await generator.__anext__()
        
        # Проверяем что сессия создана
        assert db == mock_db
        mock_async_session_local.assert_called_once()
        
        # Завершаем генератор (строка 46: finally: await db.close())
        try:
            await generator.__anext__()
        except StopAsyncIteration:
            pass
        
        # Проверяем что сессия закрыта (строка 47: await db.close())
        mock_db.close.assert_awaited_once()
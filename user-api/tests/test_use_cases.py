import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
import pytest
import pytest_asyncio
from app.application.use_cases import UserUseCases
from app.domain.entities import User

@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    return repo

@pytest.fixture
def mock_cache():
    cache = AsyncMock()
    cache.get.return_value = None
    return cache

@pytest.fixture
def mock_search():
    return AsyncMock()

@pytest.fixture
def mock_publisher():
    return AsyncMock()

@pytest.fixture
def use_cases(mock_repo, mock_cache, mock_search, mock_publisher):
    return UserUseCases(repository=mock_repo, cache=mock_cache, search=mock_search, event_publisher=mock_publisher)

@pytest.fixture
def sample_user():
    return User(id='123e4567-e89b-12d3-a456-426614174000', name='Douglas Freitas', cpf='52998224725', email='douglas@example.com', phone_number='+5511999998888', created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1))

class TestCreateUser:

    @pytest.mark.asyncio
    async def test_create_user_success(self, use_cases, mock_repo, mock_publisher, sample_user):
        mock_repo.get_by_cpf.return_value = None
        mock_repo.create.return_value = sample_user
        result = await use_cases.create_user(name='Douglas Freitas', cpf='52998224725', email='douglas@example.com', phone_number='+5511999998888')
        assert result.id == '123e4567-e89b-12d3-a456-426614174000'
        assert result.name == 'Douglas Freitas'
        mock_repo.create.assert_called_once()
        from unittest.mock import ANY
        mock_publisher.publish.assert_called_once_with('user.created', ANY)

    @pytest.mark.asyncio
    async def test_create_user_duplicate_cpf(self, use_cases, mock_repo, sample_user):
        mock_repo.get_by_cpf.return_value = sample_user
        with pytest.raises(ValueError, match='already exists'):
            await use_cases.create_user(name='Another User', cpf='52998224725', email='another@example.com', phone_number='+5511888887777')

class TestGetUser:

    @pytest.mark.asyncio
    async def test_get_user_cache_miss(self, use_cases, mock_repo, mock_cache, sample_user):
        mock_cache.get.return_value = None
        mock_repo.get_by_id.return_value = sample_user
        result = await use_cases.get_user('123e4567-e89b-12d3-a456-426614174000')
        assert result.id == '123e4567-e89b-12d3-a456-426614174000'
        mock_repo.get_by_id.assert_called_once_with('123e4567-e89b-12d3-a456-426614174000')
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_cache_hit(self, use_cases, mock_repo, mock_cache, sample_user):
        cached_data = json.dumps({'id': '123e4567-e89b-12d3-a456-426614174000', 'name': 'Douglas Freitas', 'cpf': '52998224725', 'email': 'douglas@example.com', 'phone_number': '+5511999998888', 'created_at': '2024-01-01T00:00:00', 'updated_at': '2024-01-01T00:00:00'})
        mock_cache.get.return_value = cached_data
        result = await use_cases.get_user('123e4567-e89b-12d3-a456-426614174000')
        assert result.name == 'Douglas Freitas'
        mock_repo.get_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, use_cases, mock_repo, mock_cache):
        mock_cache.get.return_value = None
        mock_repo.get_by_id.return_value = None
        result = await use_cases.get_user('invalid-uuid-999')
        assert result is None

class TestDeleteUser:

    @pytest.mark.asyncio
    async def test_delete_user_success(self, use_cases, mock_repo, mock_publisher):
        mock_repo.delete.return_value = True
        result = await use_cases.delete_user('123e4567-e89b-12d3-a456-426614174000')
        assert result is True
        mock_publisher.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, use_cases, mock_repo, mock_publisher):
        mock_repo.delete.return_value = False
        result = await use_cases.delete_user('invalid-uuid-999')
        assert result is False
        mock_publisher.publish.assert_not_called()

class TestEncryption:

    def test_encrypt_decrypt_roundtrip(self):
        from app.infrastructure.encryption import EncryptionService
        enc = EncryptionService()
        original = '52998224725'
        encrypted = enc.encrypt(original)
        decrypted = enc.decrypt(encrypted)
        assert encrypted != original
        assert decrypted == original

    def test_encrypt_empty_string(self):
        from app.infrastructure.encryption import EncryptionService
        enc = EncryptionService()
        assert enc.encrypt('') == ''
        assert enc.decrypt('') == ''

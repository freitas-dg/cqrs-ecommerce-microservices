from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock
import pytest
from app.application.use_cases import OrderUseCases
from app.domain.entities import Order

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def mock_cache():
    cache = MagicMock()
    cache.get.return_value = None
    return cache

@pytest.fixture
def mock_user_service():
    svc = MagicMock()
    svc.user_exists.return_value = True
    svc.get_user.return_value = {'id': 'user-uuid', 'name': 'Douglas', 'email': 'd@s.com'}
    return svc

@pytest.fixture
def mock_publisher():
    return MagicMock()

@pytest.fixture
def use_cases(mock_repo, mock_cache, mock_user_service, mock_publisher):
    return OrderUseCases(repository=mock_repo, cache=mock_cache, user_service=mock_user_service, event_publisher=mock_publisher)

@pytest.fixture
def sample_order():
    return Order(id='order-uuid', user_id='user-uuid', item_description='Notebook Dell', item_quantity=2, item_price=Decimal('5500.00'), total_value=Decimal('11000.00'), created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1))

class TestCreateOrder:

    def test_create_order_success(self, use_cases, mock_repo, mock_user_service, sample_order):
        mock_repo.create.return_value = sample_order
        result = use_cases.create_order(user_id='user-uuid', item_description='Notebook Dell', item_quantity=2, item_price=5500.0)
        assert result.id == 'order-uuid'
        assert result.total_value == Decimal('11000.00')
        mock_user_service.user_exists.assert_called_once_with('user-uuid')
        mock_repo.create.assert_called_once()

    def test_create_order_user_not_found(self, use_cases, mock_user_service):
        mock_user_service.user_exists.return_value = False
        with pytest.raises(ValueError, match='does not exist'):
            use_cases.create_order(user_id='missing-user-uuid', item_description='Item', item_quantity=1, item_price=10.0)

class TestGetOrder:

    def test_get_order_cache_miss(self, use_cases, mock_repo, mock_cache, sample_order):
        mock_cache.get.return_value = None
        mock_repo.get_by_id.return_value = sample_order
        result = use_cases.get_order('order-uuid')
        assert result is not None
        assert result['id'] == 'order-uuid'
        assert 'user' in result
        mock_repo.get_by_id.assert_called_once_with('order-uuid')

    def test_get_order_not_found(self, use_cases, mock_repo, mock_cache):
        mock_cache.get.return_value = None
        mock_repo.get_by_id.return_value = None
        result = use_cases.get_order('missing-order-uuid')
        assert result is None

class TestDeleteOrder:

    def test_delete_order_success(self, use_cases, mock_repo, mock_publisher):
        mock_repo.delete.return_value = True
        result = use_cases.delete_order('order-uuid')
        assert result is True
        mock_publisher.publish.assert_called_once()

    def test_delete_order_not_found(self, use_cases, mock_repo, mock_publisher):
        mock_repo.delete.return_value = False
        result = use_cases.delete_order('missing-order-uuid')
        assert result is False
        mock_publisher.publish.assert_not_called()

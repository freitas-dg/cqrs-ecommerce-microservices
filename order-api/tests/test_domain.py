from decimal import Decimal
import pytest
from app.domain.entities import Order

class TestOrderEntity:

    def test_create_valid_order(self):
        order = Order(user_id='user-uuid', item_description='Notebook Dell XPS', item_quantity=2, item_price=Decimal('5500.00'))
        assert order.user_id == 'user-uuid'
        assert order.item_description == 'Notebook Dell XPS'
        assert order.item_quantity == 2
        assert order.item_price == Decimal('5500.00')
        assert order.total_value == Decimal('11000.00')

    def test_auto_calculate_total(self):
        order = Order(user_id='user-uuid', item_description='Mouse', item_quantity=3, item_price=Decimal('49.90'))
        assert order.total_value == Decimal('3') * Decimal('49.90')

    def test_reject_invalid_user_id(self):
        with pytest.raises(ValueError, match='user_id cannot be empty'):
            Order(user_id='', item_description='Test', item_quantity=1, item_price=Decimal('10.00'))

    def test_reject_empty_description(self):
        with pytest.raises(ValueError, match='item_description cannot be empty'):
            Order(user_id='user-uuid', item_description='', item_quantity=1, item_price=Decimal('10.00'))

    def test_reject_invalid_quantity(self):
        with pytest.raises(ValueError, match='item_quantity must be a positive'):
            Order(user_id='user-uuid', item_description='Test', item_quantity=0, item_price=Decimal('10.00'))

    def test_reject_invalid_price(self):
        with pytest.raises(ValueError, match='item_price must be a positive'):
            Order(user_id='user-uuid', item_description='Test', item_quantity=1, item_price=Decimal('-5.00'))

    def test_update_recalculates_total(self):
        order = Order(user_id='user-uuid', item_description='Product', item_quantity=2, item_price=Decimal('100.00'))
        assert order.total_value == Decimal('200.00')
        order.update(item_quantity=5)
        assert order.total_value == Decimal('500.00')
        assert order.updated_at is not None

    def test_update_rejects_invalid_values(self):
        order = Order(user_id='user-uuid', item_description='Product', item_quantity=1, item_price=Decimal('10.00'))
        with pytest.raises(ValueError, match='item_quantity must be a positive'):
            order.update(item_quantity=-1)

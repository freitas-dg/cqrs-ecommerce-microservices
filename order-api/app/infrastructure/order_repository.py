from __future__ import annotations
import logging
from decimal import Decimal
from typing import List, Optional
from app.domain.entities import Order
from app.domain.repositories import OrderRepositoryInterface
from app.infrastructure.database import OrderModel, db

logger = logging.getLogger(__name__)

class MySQLOrderRepository(OrderRepositoryInterface):

    def create(self, order: Order) -> Order:
        model = OrderModel(id=order.id, user_id=order.user_id, item_description=order.item_description, item_quantity=order.item_quantity, item_price=float(order.item_price), total_value=float(order.total_value))
        db.session.add(model)
        db.session.commit()
        db.session.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, order_id: str) -> Optional[Order]:
        model = db.session.get(OrderModel, order_id)
        return self._to_entity(model) if model else None

    def list_all(self, skip: int=0, limit: int=100) -> List[Order]:
        models = OrderModel.query.order_by(OrderModel.id).offset(skip).limit(limit).all()
        return [self._to_entity(m) for m in models]

    def list_by_user(self, user_id: str, skip: int=0, limit: int=100) -> List[Order]:
        models = OrderModel.query.filter_by(user_id=user_id).order_by(OrderModel.id).offset(skip).limit(limit).all()
        return [self._to_entity(m) for m in models]

    def update(self, order: Order) -> Order:
        model = db.session.get(OrderModel, order.id)
        if not model:
            raise ValueError(f'Order with id {order.id} not found.')
        model.item_description = order.item_description
        model.item_quantity = order.item_quantity
        model.item_price = float(order.item_price)
        model.total_value = float(order.total_value)
        db.session.commit()
        db.session.refresh(model)
        return self._to_entity(model)

    def delete(self, order_id: str) -> bool:
        model = db.session.get(OrderModel, order_id)
        if not model:
            return False
        db.session.delete(model)
        db.session.commit()
        return True

    @staticmethod
    def _to_entity(model: OrderModel) -> Order:
        return Order(id=model.id, user_id=model.user_id, item_description=model.item_description, item_quantity=model.item_quantity, item_price=Decimal(str(model.item_price)), total_value=Decimal(str(model.total_value)), created_at=model.created_at, updated_at=model.updated_at)

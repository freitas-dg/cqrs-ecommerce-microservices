from __future__ import annotations
import json
import logging
from decimal import Decimal
from typing import List, Optional
from app.domain.entities import Order
from app.domain.repositories import CacheInterface, EventPublisherInterface, OrderRepositoryInterface, SearchInterface, UserServiceInterface

logger = logging.getLogger(__name__)
CACHE_PREFIX = 'order'
CACHE_LIST_KEY = f'{CACHE_PREFIX}:list'
CACHE_TTL = 300

class OrderUseCases:

    def __init__(self, repository: OrderRepositoryInterface, cache: CacheInterface, user_service: UserServiceInterface, event_publisher: EventPublisherInterface, search_adapter: SearchInterface) -> None:
        self._repo = repository
        self._cache = cache
        self._user_svc = user_service
        self._events = event_publisher
        self._search = search_adapter

    def create_order(self, user_id: str, item_description: str, item_quantity: int, item_price: float) -> Order:
        if not self._user_svc.user_exists(user_id):
            raise ValueError(f'User with id {user_id} does not exist.')
        order = Order(user_id=user_id, item_description=item_description, item_quantity=item_quantity, item_price=Decimal(str(item_price)))
        created = self._repo.create(order)
        self._cache.delete_pattern(f'{CACHE_LIST_KEY}:*')
        self._events.publish('order.created', self._order_to_dict(created))
        logger.info('Order created: id=%s, user_id=%s', created.id, user_id)
        return created

    def get_order(self, order_id: str) -> Optional[dict]:
        cache_key = f'{CACHE_PREFIX}:{order_id}'
        cached = self._cache.get(cache_key)
        if cached:
            logger.debug('Cache hit for order %s', order_id)
            return json.loads(cached)
        order = self._repo.get_by_id(order_id)
        if not order:
            return None
        result = self._enrich_order(order)
        self._cache.set(cache_key, json.dumps(result, default=str), CACHE_TTL)
        return result

    def list_orders(self, skip: int=0, limit: int=100) -> List[dict]:
        cache_key = f'{CACHE_LIST_KEY}:{skip}:{limit}'
        cached = self._cache.get(cache_key)
        if cached:
            return json.loads(cached)
        orders = self._repo.list_all(skip=skip, limit=limit)
        results = [self._enrich_order(o) for o in orders]
        if results:
            self._cache.set(cache_key, json.dumps(results, default=str), CACHE_TTL)
        return results

    def list_orders_by_user(self, user_id: str, skip: int=0, limit: int=100) -> List[dict]:
        cache_key = f'{CACHE_LIST_KEY}:user:{user_id}:{skip}:{limit}'
        cached = self._cache.get(cache_key)
        if cached:
            return json.loads(cached)
        orders = self._repo.list_by_user(user_id, skip=skip, limit=limit)
        results = [self._enrich_order(o) for o in orders]
        if results:
            self._cache.set(cache_key, json.dumps(results, default=str), CACHE_TTL)
        return results

    def update_order(self, order_id: str, item_description: Optional[str]=None, item_quantity: Optional[int]=None, item_price: Optional[float]=None) -> Optional[Order]:
        order = self._repo.get_by_id(order_id)
        if not order:
            return None
        order.update(item_description=item_description, item_quantity=item_quantity, item_price=Decimal(str(item_price)) if item_price else None)
        updated = self._repo.update(order)
        self._cache.delete(f'{CACHE_PREFIX}:{order_id}')
        self._cache.delete_pattern(f'{CACHE_LIST_KEY}:*')
        self._events.publish('order.updated', self._order_to_dict(updated))
        logger.info('Order updated: id=%s', order_id)
        return updated

    def delete_order(self, order_id: str) -> bool:
        deleted = self._repo.delete(order_id)
        if not deleted:
            return False
        self._cache.delete(f'{CACHE_PREFIX}:{order_id}')
        self._cache.delete_pattern(f'{CACHE_LIST_KEY}:*')
        self._events.publish('order.deleted', {'id': order_id})
        logger.info('Order deleted: id=%s', order_id)
        return True

    def _enrich_order(self, order: Order) -> dict:
        order_dict = self._order_to_dict(order)
        user_data = self._user_svc.get_user(order.user_id)
        order_dict['user'] = user_data
        return order_dict

    @staticmethod
    def _order_to_dict(order: Order) -> dict:
        return {'id': order.id, 'user_id': order.user_id, 'item_description': order.item_description, 'item_quantity': order.item_quantity, 'item_price': str(order.item_price), 'total_value': str(order.total_value), 'created_at': order.created_at.isoformat() if order.created_at else None, 'updated_at': order.updated_at.isoformat() if order.updated_at else None}

    def search_orders(self, query: str) -> List[dict]:
        return self._search.search_orders(query)

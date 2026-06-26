from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities import Order

class OrderRepositoryInterface(ABC):

    @abstractmethod
    def create(self, order: Order) -> Order:
        ...

    @abstractmethod
    def get_by_id(self, order_id: str) -> Optional[Order]:
        ...

    @abstractmethod
    def list_all(self, skip: int=0, limit: int=100) -> List[Order]:
        ...

    @abstractmethod
    def list_by_user(self, user_id: str, skip: int=0, limit: int=100) -> List[Order]:
        ...

    @abstractmethod
    def update(self, order: Order) -> Order:
        ...

    @abstractmethod
    def delete(self, order_id: str) -> bool:
        ...

class CacheInterface(ABC):

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        ...

    @abstractmethod
    def set(self, key: str, value: str, ttl: int=300) -> None:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...

    @abstractmethod
    def delete_pattern(self, pattern: str) -> None:
        ...

class UserServiceInterface(ABC):

    @abstractmethod
    def get_user(self, user_id: str) -> Optional[dict]:
        ...

    @abstractmethod
    def user_exists(self, user_id: str) -> bool:
        ...

class EventPublisherInterface(ABC):

    @abstractmethod
    def publish(self, event_type: str, payload: dict) -> None:
        ...

class SearchInterface(ABC):

    @abstractmethod
    def ensure_index(self) -> None:
        ...

    @abstractmethod
    def index_order(self, order: Order) -> None:
        ...

    @abstractmethod
    def delete_order(self, order_id: str) -> None:
        ...

    @abstractmethod
    def search_orders(self, query: str) -> List[dict]:
        ...

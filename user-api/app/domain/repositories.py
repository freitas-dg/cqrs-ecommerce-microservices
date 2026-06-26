from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities import User

class UserRepositoryInterface(ABC):

    @abstractmethod
    async def create(self, user: User) -> User:
        ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        ...

    @abstractmethod
    async def get_by_cpf(self, cpf: str) -> Optional[User]:
        ...

    @abstractmethod
    async def list_all(self, skip: int=0, limit: int=100) -> List[User]:
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        ...

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        ...

class CacheInterface(ABC):

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int=300) -> None:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...

    @abstractmethod
    async def delete_pattern(self, pattern: str) -> None:
        ...

class SearchInterface(ABC):

    @abstractmethod
    async def index_user(self, user: User) -> None:
        ...

    @abstractmethod
    async def delete_user(self, user_id: str) -> None:
        ...

    @abstractmethod
    async def search_users(self, query: str) -> List[dict]:
        ...

class EventPublisherInterface(ABC):

    @abstractmethod
    async def publish(self, event_type: str, payload: dict) -> None:
        ...

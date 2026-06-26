import logging
from typing import List
from elasticsearch import AsyncElasticsearch, NotFoundError
from app.domain.entities import User
from app.domain.repositories import SearchInterface
from app.infrastructure.config import get_settings

logger = logging.getLogger(__name__)
USER_INDEX_MAPPING = {'mappings': {'properties': {'id': {'type': 'keyword'}, 'name': {'type': 'text', 'analyzer': 'standard'}, 'cpf': {'type': 'keyword'}, 'email': {'type': 'text', 'fields': {'keyword': {'type': 'keyword'}}}, 'phone_number': {'type': 'keyword'}, 'created_at': {'type': 'date'}, 'updated_at': {'type': 'date'}}}}

class ElasticsearchAdapter(SearchInterface):

    def __init__(self) -> None:
        settings = get_settings()
        self._es = AsyncElasticsearch(settings.elasticsearch_url)
        self._index = settings.elasticsearch_user_index

    async def ensure_index(self) -> None:
        try:
            exists = await self._es.indices.exists(index=self._index)
            if not exists:
                await self._es.indices.create(index=self._index, body=USER_INDEX_MAPPING)
                logger.info('Created Elasticsearch index: %s', self._index)
        except Exception as e:
            logger.error('Failed to create ES index: %s', e)

    async def index_user(self, user: User) -> None:
        try:
            doc = {'id': user.id, 'name': user.name, 'cpf': user.cpf, 'email': user.email, 'phone_number': user.phone_number, 'created_at': user.created_at.isoformat() if user.created_at else None, 'updated_at': user.updated_at.isoformat() if user.updated_at else None}
            await self._es.index(index=self._index, id=str(user.id), document=doc)
            logger.debug('Indexed user %s in Elasticsearch', user.id)
        except Exception as e:
            logger.error('Failed to index user %s: %s', user.id, e)

    async def delete_user(self, user_id: str) -> None:
        try:
            await self._es.delete(index=self._index, id=str(user_id))
            logger.debug('Deleted user %s from Elasticsearch', user_id)
        except NotFoundError:
            logger.debug('User %s not found in ES index — skipping', user_id)
        except Exception as e:
            logger.error('Failed to delete user %s from ES: %s', user_id, e)

    async def search_users(self, query: str) -> List[dict]:
        try:
            body = {'query': {'multi_match': {'query': query, 'fields': ['name', 'email', 'cpf', 'phone_number'], 'fuzziness': 'AUTO'}}}
            result = await self._es.search(index=self._index, body=body, size=50)
            return [hit['_source'] for hit in result['hits']['hits']]
        except Exception as e:
            logger.error('Elasticsearch search failed: %s', e)
            return []

    async def close(self) -> None:
        await self._es.close()

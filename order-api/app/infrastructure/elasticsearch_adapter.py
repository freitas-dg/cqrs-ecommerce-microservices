import logging
from typing import List
from elasticsearch import Elasticsearch, NotFoundError
from app.domain.entities import Order
from app.domain.repositories import SearchInterface
from app.infrastructure.config import Config

logger = logging.getLogger(__name__)
ORDER_INDEX_MAPPING = {'mappings': {'properties': {'id': {'type': 'keyword'}, 'user_id': {'type': 'keyword'}, 'item_description': {'type': 'text', 'analyzer': 'standard'}, 'item_quantity': {'type': 'integer'}, 'item_price': {'type': 'float'}, 'total_value': {'type': 'float'}, 'created_at': {'type': 'date'}, 'updated_at': {'type': 'date'}}}}

class ElasticsearchAdapter(SearchInterface):

    def __init__(self) -> None:
        self._es = Elasticsearch(Config.ELASTICSEARCH_URL)
        self._index = Config.ELASTICSEARCH_ORDER_INDEX

    def ensure_index(self) -> None:
        try:
            if not self._es.indices.exists(index=self._index):
                self._es.indices.create(index=self._index, body=ORDER_INDEX_MAPPING)
                logger.info('Created Elasticsearch index: %s', self._index)
        except Exception as e:
            logger.error('Failed to create ES index: %s', e)

    def index_order(self, order: Order) -> None:
        try:
            doc = {'id': order.id, 'user_id': order.user_id, 'item_description': order.item_description, 'item_quantity': order.item_quantity, 'item_price': float(order.item_price), 'total_value': float(order.total_value), 'created_at': order.created_at.isoformat() if order.created_at else None, 'updated_at': order.updated_at.isoformat() if order.updated_at else None}
            self._es.index(index=self._index, id=str(order.id), document=doc)
            logger.debug('Indexed order %s in Elasticsearch', order.id)
        except Exception as e:
            logger.error('Failed to index order %s: %s', order.id, e)

    def delete_order(self, order_id: str) -> None:
        try:
            self._es.delete(index=self._index, id=str(order_id))
            logger.debug('Deleted order %s from Elasticsearch', order_id)
        except NotFoundError:
            logger.debug('Order %s not found in ES index — skipping', order_id)
        except Exception as e:
            logger.error('Failed to delete order %s from ES: %s', order_id, e)

    def search_orders(self, query: str) -> List[dict]:
        try:
            body = {'query': {'multi_match': {'query': query, 'fields': ['item_description', 'user_id'], 'fuzziness': 'AUTO'}}}
            result = self._es.search(index=self._index, body=body, size=50)
            return [hit['_source'] for hit in result['hits']['hits']]
        except Exception as e:
            logger.error('Elasticsearch search failed: %s', e)
            return []

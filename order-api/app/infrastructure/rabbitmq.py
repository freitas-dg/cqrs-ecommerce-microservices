import json
import logging
import threading
from datetime import datetime
import pika
from app.domain.repositories import EventPublisherInterface

logger = logging.getLogger(__name__)
EXCHANGE_NAME = 'ecommerce_events'
ORDER_EVENTS_QUEUE = 'order_events_es_indexing'
USER_EVENTS_CONSUMER_QUEUE = 'order_api_user_events'

class RabbitMQPublisher(EventPublisherInterface):

    def __init__(self, rabbitmq_url: str) -> None:
        self._url = rabbitmq_url
        self._connection = None
        self._channel = None

    def connect(self) -> None:
        try:
            params = pika.URLParameters(self._url)
            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()
            self._channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)
            logger.info('RabbitMQ publisher connected.')
        except Exception as e:
            logger.error('RabbitMQ connection failed: %s', e)

    def publish(self, event_type: str, payload: dict) -> None:
        if not self._channel:
            logger.warning('RabbitMQ not connected — skipping publish for %s', event_type)
            return
        try:
            message = json.dumps({'event_type': event_type, 'payload': payload, 'timestamp': datetime.utcnow().isoformat()}, default=str)
            self._channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=event_type, body=message.encode(), properties=pika.BasicProperties(content_type='application/json', delivery_mode=2))
            logger.debug('Published event: %s', event_type)
        except Exception as e:
            logger.error('Failed to publish event %s: %s', event_type, e)
            self.connect()

    def close(self) -> None:
        if self._connection and self._connection.is_open:
            self._connection.close()

class RabbitMQUserEventConsumer:

    def __init__(self, rabbitmq_url: str, user_client) -> None:
        self._url = rabbitmq_url
        self._user_client = user_client
        self._thread = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._consume, daemon=True)
        self._thread.start()
        logger.info('User events consumer thread started.')

    def _consume(self) -> None:
        try:
            params = pika.URLParameters(self._url)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)
            channel.queue_declare(queue=USER_EVENTS_CONSUMER_QUEUE, durable=True)
            channel.queue_bind(exchange=EXCHANGE_NAME, queue=USER_EVENTS_CONSUMER_QUEUE, routing_key='user.*')
            channel.basic_qos(prefetch_count=10)
            channel.basic_consume(queue=USER_EVENTS_CONSUMER_QUEUE, on_message_callback=self._on_message)
            logger.info("Consuming user events on '%s'...", USER_EVENTS_CONSUMER_QUEUE)
            channel.start_consuming()
        except Exception as e:
            logger.error('User events consumer error: %s', e)

    def _on_message(self, channel, method, properties, body) -> None:
        try:
            data = json.loads(body.decode())
            event_type = data.get('event_type', '')
            payload = data.get('payload', {})
            user_id = payload.get('id')
            if user_id and event_type in ('user.updated', 'user.deleted'):
                self._user_client.invalidate_user_cache(user_id)
                logger.info('Processed %s for user %s — cache invalidated', event_type, user_id)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error('Error processing user event: %s', e)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

class RabbitMQOrderEventConsumer:

    def __init__(self, rabbitmq_url: str, search_adapter) -> None:
        self._url = rabbitmq_url
        self._search = search_adapter
        self._thread = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._consume, daemon=True)
        self._thread.start()
        logger.info('Order events consumer thread started.')

    def _consume(self) -> None:
        try:
            params = pika.URLParameters(self._url)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)
            channel.queue_declare(queue=ORDER_EVENTS_QUEUE, durable=True)
            channel.queue_bind(exchange=EXCHANGE_NAME, queue=ORDER_EVENTS_QUEUE, routing_key='order.*')
            channel.basic_qos(prefetch_count=10)
            channel.basic_consume(queue=ORDER_EVENTS_QUEUE, on_message_callback=self._on_message)
            logger.info("Consuming order events on '%s'...", ORDER_EVENTS_QUEUE)
            channel.start_consuming()
        except Exception as e:
            logger.error('Order events consumer error: %s', e)

    def _on_message(self, channel, method, properties, body) -> None:
        try:
            from app.domain.entities import Order
            data = json.loads(body.decode())
            event_type = data.get('event_type', '')
            payload = data.get('payload', {})
            order_id = payload.get('id')
            if order_id:
                if event_type in ('order.created', 'order.updated'):
                    order = Order(id=payload['id'], user_id=payload['user_id'], item_description=payload['item_description'], item_quantity=payload['item_quantity'], item_price=payload['item_price'])
                    order.total_value = payload['total_value']
                    order.created_at = datetime.fromisoformat(payload['created_at']) if payload.get('created_at') else None
                    order.updated_at = datetime.fromisoformat(payload['updated_at']) if payload.get('updated_at') else None
                    self._search.index_order(order)
                    logger.info('Processed %s for order %s — indexed in ES', event_type, order_id)
                elif event_type == 'order.deleted':
                    self._search.delete_order(order_id)
                    logger.info('Processed %s for order %s — deleted from ES', event_type, order_id)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error('Error processing order event: %s', e)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

import asyncio
import json
import logging
from datetime import datetime
import aio_pika
from app.domain.entities import User
from app.domain.repositories import EventPublisherInterface
from app.infrastructure.config import get_settings
from app.infrastructure.elasticsearch_adapter import ElasticsearchAdapter

logger = logging.getLogger(__name__)
EXCHANGE_NAME = 'ecommerce_events'
USER_EVENTS_QUEUE = 'user_events_es_indexing'

class RabbitMQPublisher(EventPublisherInterface):

    def __init__(self) -> None:
        self._connection = None
        self._channel = None

    async def connect(self) -> None:
        settings = get_settings()
        try:
            self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            self._channel = await self._connection.channel()
            await self._channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True)
            logger.info('RabbitMQ publisher connected.')
        except Exception as e:
            logger.error('RabbitMQ connection failed: %s', e)

    async def publish(self, event_type: str, payload: dict) -> None:
        if not self._channel:
            logger.warning('RabbitMQ not connected — skipping publish for %s', event_type)
            return
        try:
            exchange = await self._channel.get_exchange(EXCHANGE_NAME)
            message = aio_pika.Message(body=json.dumps({'event_type': event_type, 'payload': payload, 'timestamp': datetime.utcnow().isoformat()}, default=str).encode(), content_type='application/json', delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
            await exchange.publish(message, routing_key=event_type)
            logger.debug('Published event: %s', event_type)
        except Exception as e:
            logger.error('Failed to publish event %s: %s', event_type, e)

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()

class RabbitMQConsumer:

    def __init__(self, es_adapter: ElasticsearchAdapter) -> None:
        self._es = es_adapter
        self._connection = None

    async def start(self) -> None:
        settings = get_settings()
        try:
            self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            channel = await self._connection.channel()
            await channel.set_qos(prefetch_count=10)
            exchange = await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True)
            queue = await channel.declare_queue(USER_EVENTS_QUEUE, durable=True)
            await queue.bind(exchange, routing_key='user.*')
            logger.info("RabbitMQ consumer started — listening on '%s'", USER_EVENTS_QUEUE)
            await queue.consume(self._process_message)
        except Exception as e:
            logger.error('RabbitMQ consumer failed to start: %s', e)

    async def _process_message(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                event_type = data.get('event_type', '')
                payload = data.get('payload', {})
                logger.debug('Processing event: %s', event_type)
                if event_type in ('user.created', 'user.updated'):
                    user = User(id=payload['id'], name=payload['name'], cpf=payload['cpf'], email=payload['email'], phone_number=payload['phone_number'], created_at=datetime.fromisoformat(payload['created_at']) if payload.get('created_at') else None, updated_at=datetime.fromisoformat(payload['updated_at']) if payload.get('updated_at') else None)
                    await self._es.index_user(user)
                elif event_type == 'user.deleted':
                    await self._es.delete_user(payload['id'])
                logger.info('Processed event: %s', event_type)
            except Exception as e:
                logger.error('Error processing message: %s', e)

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()

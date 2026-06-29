import logging
from flask import Flask
from flask_migrate import Migrate
from app.infrastructure.config import Config
from app.infrastructure.database import db
from app.infrastructure.telemetry import init_telemetry

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)
migrate = Migrate()

def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    with app.app_context():
        db.create_all()
        init_telemetry(app=app, engine=db.engine)
        from app.infrastructure.redis_cache import RedisCache
        from app.infrastructure.order_repository import MySQLOrderRepository
        from app.infrastructure.user_client import UserAPIClient
        from app.infrastructure.elasticsearch_adapter import ElasticsearchAdapter
        from app.infrastructure.rabbitmq import RabbitMQPublisher, RabbitMQUserEventConsumer, RabbitMQOrderEventConsumer
        from app.application.use_cases import OrderUseCases
        from app.presentation.routes import init_routes, orders_bp
        
        cache = RedisCache(app.config['REDIS_URL'])
        user_client = UserAPIClient(base_url=app.config['USER_API_URL'], timeout=app.config['USER_API_TIMEOUT'], cache=cache)
        publisher = RabbitMQPublisher(app.config['RABBITMQ_URL'])
        publisher.connect()
        repository = MySQLOrderRepository()
        search_adapter = ElasticsearchAdapter()
        search_adapter.ensure_index()
        use_cases = OrderUseCases(repository=repository, cache=cache, user_service=user_client, event_publisher=publisher, search_adapter=search_adapter)
        init_routes(use_cases)
        app.register_blueprint(orders_bp)
        consumer = RabbitMQUserEventConsumer(rabbitmq_url=app.config['RABBITMQ_URL'], user_client=user_client)
        consumer.start()
        order_consumer = RabbitMQOrderEventConsumer(rabbitmq_url=app.config['RABBITMQ_URL'], search_adapter=search_adapter)
        order_consumer.start()
        logger.info('Order API is ready!')

    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'order-api'}
    return app

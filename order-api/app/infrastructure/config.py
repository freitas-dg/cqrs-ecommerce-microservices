import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    DEBUG = os.environ.get('ORDER_API_DEBUG', 'false').lower() == 'true'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://my_user:my_order_2026@localhost:3306/order_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_size': 10, 'max_overflow': 20, 'pool_pre_ping': True}
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6380/0')
    REDIS_CACHE_TTL = int(os.environ.get('REDIS_CACHE_TTL', '300'))
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200')
    ELASTICSEARCH_ORDER_INDEX = 'orders'
    RABBITMQ_URL = os.environ.get('RABBITMQ_URL', 'amqp://ecommercemq:ecommerce_mq_2026@localhost:5672/')
    USER_API_URL = os.environ.get('USER_API_URL', 'http://localhost:8000')
    USER_API_TIMEOUT = int(os.environ.get('USER_API_TIMEOUT', '5'))

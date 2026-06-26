from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = 'User API'
    debug: bool = False
    database_url: str = 'postgresql+asyncpg://db_user:user_pass_2026@localhost:5432/user_db'
    database_url_sync: str = 'postgresql+psycopg2://db_user:user_pass_2026@localhost:5432/user_db'
    redis_url: str = 'redis://localhost:6379/0'
    redis_cache_ttl: int = 300
    elasticsearch_url: str = 'http://localhost:9200'
    elasticsearch_user_index: str = 'users'
    rabbitmq_url: str = 'amqp://ecommercemq:ecommerce_mq_2026@localhost:5672/'
    encryption_key: str = 'ZmVybmV0LWtleS1mb3ItZGV2ZWxvcG1lbnQtb25seQ=='

    class Config:
        env_file = '.env'
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.infrastructure.auth_service import AuthService
from app.infrastructure.config import get_settings
from app.infrastructure.elasticsearch_adapter import ElasticsearchAdapter
from app.infrastructure.encryption import EncryptionService
from app.infrastructure.rabbitmq import RabbitMQConsumer, RabbitMQPublisher
from app.infrastructure.redis_cache import RedisCache
from app.infrastructure.telemetry import init_telemetry
from app.presentation.auth_routes import auth_router, init_auth_dependencies
from app.presentation.routes import init_dependencies, router

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    logger.info('Starting %s...', settings.app_name)
    
    cache = RedisCache()
    search = ElasticsearchAdapter()
    publisher = RabbitMQPublisher()
    encryption = EncryptionService()
    auth_service = AuthService(
        keycloak_url=settings.keycloak_url,
        realm=settings.keycloak_realm,
        client_id=settings.keycloak_client_id,
        admin_user=settings.keycloak_admin_user,
        admin_password=settings.keycloak_admin_password
    )
    
    await publisher.connect()
    await search.ensure_index()
    
    consumer = RabbitMQConsumer(search)
    consumer_task = asyncio.create_task(consumer.start())
    
    init_dependencies(cache, search, publisher, encryption, auth_service)
    init_auth_dependencies(auth_service, encryption)
    
    logger.info('%s is ready!', settings.app_name)
    yield
    
    logger.info('Shutting down %s...', settings.app_name)
    consumer_task.cancel()
    await consumer.close()
    await publisher.close()
    await cache.close()
    await search.close()
    logger.info('%s stopped.', settings.app_name)

app = FastAPI(title='E-commerce Microservices - User API', description='Microsserviço de cadastro de usuários. Dados sensíveis (CPF, email, telefone) são criptografados com AES-256.', version='1.0.0', docs_url='/docs', redoc_url='/redoc', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(router)
app.include_router(auth_router)
init_telemetry(app=app)

@app.get('/health', tags=['Health'])
async def health_check():
    return {'status': 'healthy', 'service': 'user-api'}


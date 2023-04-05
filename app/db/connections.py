import redis
from databases import Database
from system_config import system_config

redis_conn = redis.from_url(system_config.redis_url)

if system_config.environment == 'TESTING':
    postgre_db = Database(system_config.db_url_test, force_rollback=True)
else:
    postgre_db = Database(system_config.database_url)


async def get_db() -> Database:
    return postgre_db


async def connect_db():
    await postgre_db.connect()


async def close_postgre():
    await postgre_db.disconnect()


async def get_redis():
    return redis_conn


async def close_redis():
    redis_conn.close()

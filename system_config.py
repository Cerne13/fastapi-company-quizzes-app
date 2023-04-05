from dotenv import load_dotenv
import os

load_dotenv()

db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")
db_host = os.getenv("POSTGRES_HOST")
db_name = os.getenv("POSTGRES_DB")
db_port = os.getenv("POSTGRES_PORT")

redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")
redis_db = os.getenv("REDIS_DB_NUM")

test_host = os.getenv("TEST_HOST")
test_port = os.getenv("TEST_DB_PORT")


class SystemConfig:
    secret_key = os.getenv("SECRET_KEY")

    database_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

    db_url_test = f'postgresql+asyncpg://{db_user}:{db_password}@{test_host}:{test_port}/{db_name}'

    redis_url = f'redis://{redis_host}:{redis_port}/{redis_db}'

    app_host = os.getenv("APP_HOST")
    app_port = int(os.getenv("APP_PORT"))
    debug = os.getenv("DEBUG")

    environment = os.getenv("ENVIRONMENT")

    algorithm = os.getenv("ALGORITHM")

    origins = [
        "http://localhost",
        "http://localhost:8000",
    ]

    auth0_domain = os.getenv("AUTH0_DOMAIN")
    auth0_api_audience = os.getenv("AUTH0_API_AUDIENCE")
    auth0_issuer = os.getenv("AUTH0_ISSUER")
    auth0_algorithms = os.getenv("AUTH0_ALGORITHMS")
    auth0_test_token = os.getenv("AUTH0_TEST_TOKEN")
    auth0_secret = os.getenv("AUTH0_SECRET")


system_config = SystemConfig()

from motor.motor_asyncio import AsyncIOMotorClient
from core import settings


class AsyncDatabase:
    client: AsyncIOMotorClient = None


db = AsyncDatabase()


def get_database_async():
    return db.client[settings.MONGODB_NAME]


def get_database(client, db_name: str = settings.MONGODB_NAME):
    return client[db_name]

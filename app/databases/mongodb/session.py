from motor.motor_asyncio import AsyncIOMotorClient
from core import settings


class MongoSession:
    client = None


db = MongoSession()


def get_database(db_name: str = settings.MONGODB_NAME):
    return db.client[db_name]

from tkinter.messagebox import NO
from motor.motor_asyncio import AsyncIOMotorClient
from core import settings

class MongoSession:
    client: AsyncIOMotorClient = None

db = MongoSession()

def get_database() -> AsyncIOMotorClient:
    return db.client[settings.MONGODB_NAME]
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from core import settings


async def add_company_async(
    db: AsyncIOMotorClient,
    company_data: dict,
    company_collection: str = settings.COMPANY_COLLECTION,
) -> dict:
    company = await db[company_collection].insert_one(company_data)
    new_company = await db[company_collection].find_one({"_id": company.inserted_id})
    return new_company


def add_company(
    db: MongoClient,
    company_data: dict,
    company_collection: str = settings.COMPANY_COLLECTION,
) -> dict:
    company = db[company_collection].insert_one(company_data)
    new_company = db[company_collection].find_one({"_id": company.inserted_id})
    return new_company

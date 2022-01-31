from motor.motor_asyncio import AsyncIOMotorClient
from core import settings

company_collection = settings.COMPANY_COLLECTION

async def add_company(db: AsyncIOMotorClient, company_data: dict) -> dict:
    company = await db[company_collection].insert_one(company_data)
    new_company = await db[company_collection].find_one({"_id": company.inserted_id})
    return new_company
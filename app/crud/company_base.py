from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient
from core import settings


async def get_company_base_async(
    db: AsyncIOMotorClient,
    cik: int,
    company_base_collection: str = settings.COMPANY_BASE_COLLECTION,
) -> Any:
    
    company_base = await db[company_base_collection].find_one({"cik": cik})
    if company_base:
        return company_base
    